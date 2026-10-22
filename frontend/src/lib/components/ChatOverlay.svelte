<script lang="ts">
	// ChatOverlay (konsep revisi-2 + REVISI-3/4): widget chat MENGAMBANG di atas Dashboard.
	// Isi = agen ReAct paling bare minimum: OTAK memutuskan tiap langkah
	// (thought / action / finish), RUNNER mengeksekusi — urutan BEBAS.
	// UI hanya merender jejak yang tiba; wadah = modal + backdrop (Esc ✕).
	//
	// REVISI-3: streaming TTFT; tab "Chat | Recent Chat" (multi-sesi + resume);
	// sesi bisa dihapus; New chat.
	// REVISI-4 (keputusan user): mode Normal/Deep DIHAPUS — satu jalur default,
	// yang dimainkan adalah loop ReAct minimal (REVISI-5: yang memutuskan
	// langkah adalah otak — sekarang aturan dummy, nanti LLM — bukan kode UI).
	// Jejak langkah apa pun yang tiba dirender apa adanya, lalu jawaban mengalir.
	//
	// PANDUAN: komponen "controlled" — parent memberi `open`, kita panggil
	// balik `onclose`. Semua STATE chat ada di sini, tidak bocor ke Dashboard.
	import ChatComposer from './ChatComposer.svelte';
	import ChatTranscript from './ChatTranscript.svelte';
	import DiffPanel from './DiffPanel.svelte';
	import {
		deleteSession,
		listSessions,
		loadHistory,
		streamChat,
		type StreamEvent
	} from '../api/chat';
	import type { Draft } from '../api/draft';
	import type { ChatMessage, ChatSession, ReactStep } from '../api/types';

	// Kunci localStorage: sesi AKTIF TERAKHIR — dibuka ulang setelah refresh.
	const SESSION_KEY = 'wiki-chat-session';

	// $props = input komponen. `open` dikontrol parent; `onclose` callback
	// yang kita panggil saat user menutup (parent yang mengubah statenya).
	let { open, onclose }: { open: boolean; onclose: () => void } = $props();

	// ═══ STATE percakapan ═══
	let messages = $state<ChatMessage[]>([]); // transkrip sesi aktif
	let input = $state(''); // isi textbox composer (two-way via bind:input)
	let streaming = $state(false); // ada stream berjalan → tombol jadi Stop
	let error = $state('');
	let draft = $state<Draft | null>(null); // usulan note/diff menunggu Apply
	let sessionId = $state(''); // sesi AKTIF
	let controller: AbortController | null = null; // bukan $state: alat internal
	let initialized = $state(false); // penanda inisialisasi sekali-jalan

	// ═══ STATE REVISI-3/4 ═══
	let activeTab = $state<'chat' | 'recent'>('chat'); // dua tab header mockup
	let sessions = $state<ChatSession[]>([]); // isi tab Recent Chat
	let steps = $state<ReactStep[]>([]); // jejak ReAct run berjalan
	let liveContent = $state(''); // teks delta yang masih mengalir
	let ttftMs = $state<number | null>(null); // time-to-first-token (ms)
	let sentAt = 0; // stempel waktu kirim (bukan $state: cuma alat ukur)

	// ═══ EFEK SAMPING ═══
	// $effect = "jalankan ulang ketika dependensinya berubah".
	// Polanya: SEKALI saja saat overlay pertama dibuka — resume sesi terakhir
	// (dari localStorage) + muat daftar sesi untuk tab Recent Chat.
	$effect(() => {
		if (open && !initialized) {
			initialized = true;
			sessionId = localStorage.getItem(SESSION_KEY) ?? crypto.randomUUID();
			localStorage.setItem(SESSION_KEY, sessionId);
			loadHistory(sessionId)
				.then((h) => (messages = h))
				.catch(() => {
					/* sesi baru — histori kosong, bukan error nyata */
				});
			refreshSessions();
		}
	});

	// Ambil daftar sesi terbaru (dipanggil setelah kirim/hapus).
	async function refreshSessions(): Promise<void> {
		try {
			sessions = await listSessions();
		} catch {
			/* daftar gagal dimuat — biarkan kosong, tab chat tetap jalan */
		}
	}

	// Esc global: batalkan stream yang sedang jalan (hemat token) lalu tutup.
	function onKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape' && open) {
			controller?.abort();
			onclose();
		}
	}

	// ═══ AKSI SESI ═══
	// New chat: reset semua state percakapan; id sesi baru dipakai saat kirim.
	// Sesi baru muncul di Recent Chat SETELAH pesan pertama (dibuat lazily).
	function newChat(): void {
		controller?.abort();
		sessionId = crypto.randomUUID();
		localStorage.setItem(SESSION_KEY, sessionId);
		messages = [];
		draft = null;
		steps = [];
		liveContent = '';
		ttftMs = null;
		error = '';
		activeTab = 'chat';
	}

	// Resume sesi lama dari tab Recent Chat: pindah pointer + muat transkrip.
	async function resumeSession(id: string): Promise<void> {
		controller?.abort();
		sessionId = id;
		localStorage.setItem(SESSION_KEY, id);
		messages = [];
		draft = null;
		steps = [];
		liveContent = '';
		error = '';
		try {
			messages = await loadHistory(id);
		} catch (e) {
			error = e instanceof Error ? e.message : 'gagal memuat sesi';
		}
		activeTab = 'chat';
	}

	// Hapus sesi: konfirmasi dulu; kalau yang dihapus sesi aktif → mulai baru.
	async function removeSession(id: string, title: string): Promise<void> {
		if (!confirm(`Hapus percakapan "${title}"? Riwayatnya hilang.`)) return;
		try {
			await deleteSession(id);
		} catch (e) {
			error = e instanceof Error ? e.message : 'gagal menghapus sesi';
			return;
		}
		if (id === sessionId) newChat();
		await refreshSessions();
	}

	// ═══ KIRIM PESAN ═══
	// streamChat = async generator: hasilnya SEORONG-ORONG event kecil
	// (`for await`): `react` (jejak) → `message` (delta jawaban) → `answer`
	// (final). AbortController memberi tombol Stop gigi nyata: abort()
	// memutus stream di tengah, bukan cuma pura-pura berhenti.
	async function send(): Promise<void> {
		const text = input.trim();
		if (!text || streaming) return;
		input = '';
		error = '';
		draft = null;
		messages = [...messages, { role: 'user', content: text }];
		streaming = true;
		steps = [];
		liveContent = '';
		ttftMs = null;
		sentAt = Date.now();
		controller = new AbortController();
		try {
			for await (const event of streamChat(sessionId, text, controller.signal)) {
				handleEvent(event);
			}
		} catch (e) {
			if ((e as Error).name === 'AbortError') {
				// penghentian manual bukan kegagalan — catat di transkrip
				messages = [...messages, { role: 'assistant', content: '_dihentikan oleh user_' }];
			} else {
				error = e instanceof Error ? e.message : 'chat gagal';
			}
		} finally {
			streaming = false;
			controller = null;
			liveContent = '';
			await refreshSessions(); // judul/updated_at sesi berubah setelah kirim
		}
	}

	// Dispatcher event SSE → state yang tepat:
	//   react → jejak ReAct (thought/action/observation) | message → DELTA:
	//   tambahkan ke balon hidup + ukur TTFT di delta pertama | answer →
	//   pesan final assistant | draft → usulan agen masuk DiffPanel (TIDAK
	//   otomatis ditulis — baru tersimpan kalau user klik Apply) | error → banner.
	function handleEvent(event: StreamEvent): void {
		if (event.event === 'react' && event.step) {
			const text =
				event.step === 'action' ? `${event.tool ?? '?'}(${event.args ?? ''})` : (event.content ?? '');
			steps = [...steps, { step: event.step, text }];
		} else if (event.event === 'error') {
			error = event.message || 'agen gagal memproses permintaan';
		} else if (event.event === 'message' && event.content) {
			if (ttftMs === null) ttftMs = Date.now() - sentAt; // token pertama!
			liveContent += event.content;
		} else if (event.event === 'answer' && event.content) {
			messages = [...messages, { role: 'assistant', content: event.content }];
			liveContent = '';
		} else if (event.event === 'draft' && event.slug) {
			draft = {
				action: (event.action as 'create' | 'update') ?? 'create',
				slug: event.slug,
				title: event.title ?? event.slug,
				content_markdown: event.content_markdown ?? '',
				tags: event.tags ?? [],
				source: event.source ?? null,
				type_: event.type_ ?? 'note',
				diff: event.diff ?? '',
				preview: event.preview ?? ''
			};
		}
	}

	function stop(): void {
		controller?.abort();
	}
</script>

<!-- svelte:window = pasang listener di level window, supaya Esc tetap kerja
walau fokus keyboard sedang di dalam panel/chatbox. -->
<svelte:window onkeydown={onKeydown} />

<!-- Seluruh modal hanya dirender ketika open=true (bukan CSS hidden) —
saat tertutup, DOM chat benar-benar tidak ada di halaman.
tabindex="-1" (lihat div pertama): dialog bisa difokus-kan via JS
tetapi tidak ikut siklus Tab keyboard halaman normal. -->
{#if open}
	<div
		role="dialog"
		aria-modal="true"
		aria-label="Chat"
		tabindex="-1"
		class="fixed inset-0 z-20 flex items-end justify-center p-4 sm:items-center"
		onclick={(e) => {
			// e.target === e.currentTarget artinya yang diklik elemen DIV ini
			// sendiri (area gelap di luar panel), bukan isinya → tutup.
			if (e.target === e.currentTarget) onclose();
		}}
		onkeydown={(e) => e.key === 'Escape' && onclose()}
	>
		<!-- Backdrop: lapisan gelap full-screen; -z-10 mendorongnya ke belakang
		panel. Klik di lapisan inilah yang menutup modal. -->
		<div class="absolute inset-0 -z-10 bg-ink/30 backdrop-blur-sm"></div>

		<!-- Panel chat = kolom flex: header tab (tetap), isi (scroll, flex-1),
		composer (tetap bawah). h-[80vh] = 80% tinggi viewport. -->
		<section
			class="relative flex h-[80vh] w-full max-w-2xl flex-col overflow-hidden rounded-card border border-border bg-card shadow-2xl"
		>
			<header class="flex items-center justify-between gap-3 border-b border-border px-5 py-3">
				<!-- TAB "Chat | Recent Chat" persis mockup: state activeTab,
				class dinamis menandai yang aktif. -->
				<div class="flex items-center gap-1 font-ui text-sm">
					<button
						type="button"
						onclick={() => (activeTab = 'chat')}
						class={`rounded-full px-3.5 py-1 transition ${activeTab === 'chat' ? 'bg-accent text-white' : 'text-muted hover:text-ink'}`}
					>
						Chat
					</button>
					<span class="text-muted" aria-hidden="true">|</span>
					<button
						type="button"
						onclick={() => (activeTab = 'recent')}
						class={`rounded-full px-3.5 py-1 transition ${activeTab === 'recent' ? 'bg-accent text-white' : 'text-muted hover:text-ink'}`}
					>
						Recent Chat
					</button>
				</div>

				<div class="flex items-center gap-2 font-ui text-sm">
					{#if activeTab === 'chat'}
						<!-- New chat = sesi kosong baru (pointer pindah; sesi lama
						aman di tab Recent Chat). REVISI-4: tanpa toggle mode —
						satu jalur ReAct default. -->
						<button
							type="button"
							onclick={newChat}
							class="rounded-full border border-border px-3.5 py-1 text-muted transition hover:text-ink"
						>
							New chat
						</button>
					{/if}
					<!-- aria-label: tombolnya hanya simbol silang — teknologi pembaca
					layar tetap butuh nama teks. -->
					<button
						type="button"
						onclick={onclose}
						aria-label="Tutup chat"
						class="ml-2 rounded-full px-2.5 py-0.5 text-lg text-muted transition hover:bg-accent-soft hover:text-ink"
					>
						✕
					</button>
				</div>
			</header>

			{#if activeTab === 'recent'}
				<!-- ═══ TAB RECENT CHAT ═══ daftar sesi: klik = resume,
				ikon trash = hapus (dengan konfirmasi). -->
				<div class="flex-1 overflow-y-auto px-5 py-4">
					{#if sessions.length === 0}
						<p class="py-8 text-center font-ui text-sm text-muted">
							Belum ada percakapan lama — sesi muncul setelah pesan pertama.
						</p>
					{:else}
						<ul class="flex flex-col gap-2">
							{#each sessions as session (session.id)}
								<li
									class="flex items-center justify-between gap-3 rounded-card border border-border bg-card px-4 py-3 shadow-sm"
								>
									<button
										type="button"
										onclick={() => resumeSession(session.id)}
										class="flex-1 text-left"
									>
										<span class="block font-ui text-sm text-ink">{session.title}</span>
										<span class="font-ui text-xs text-muted">{session.updated_at.slice(0, 10)}</span>
									</button>
									<button
										type="button"
										onclick={() => removeSession(session.id, session.title)}
										aria-label={`Hapus percakapan ${session.title}`}
										class="rounded-full px-2 py-1 text-muted transition hover:bg-accent-soft hover:text-accent"
									>
										🗑
									</button>
								</li>
							{/each}
						</ul>
					{/if}
				</div>
			{:else}
				<!-- ═══ TAB CHAT ═══
				flex-1 + overflow-y-auto = area pesan mengambil ruang sisa lalu
				scroll sendiri tanpa menggerakkan seluruh halaman. -->
				<div class="flex-1 overflow-y-auto px-5 py-4">
					{#if messages.length === 0 && !streaming}
						<p class="py-8 text-center font-ui text-sm text-muted">
							Tanya apa saja tentang Personal Agentic Wiki. Jawaban datang dari agen
							ReAct — jejak pikirannya (Thought → Action → Observation) tampil lebih dulu.
						</p>
					{/if}
					<!-- Transkrip, DiffPanel (draft agen), dan error bersarang di
					area scroll yang sama agar urutannya kronologis. -->
					<ChatTranscript {messages} {streaming} {steps} {liveContent} {ttftMs} />
					{#if draft}
						<!-- DiffPanel = GERBANG KEAMANAN: draft agen hanya tertulis
						kalau user klik Apply (lihat DiffPanel.svelte). -->
						<DiffPanel {draft} onRejected={() => (draft = null)} />
					{/if}
					{#if error}
						<div role="alert" class="mt-3 rounded-card border border-accent/40 bg-accent-soft/50 px-4 py-2.5 font-ui text-sm text-ink">
							{error}
						</div>
					{/if}
				</div>

				<div class="border-t border-border px-5 py-3">
					<!-- bind:input = two-way binding: ketik → state ikut; state
					di-set program (sesudah kirim) → textarea ikut kosong. -->
					<ChatComposer bind:input {streaming} onSend={send} onStop={stop} />
				</div>
			{/if}
		</section>
	</div>
{/if}
