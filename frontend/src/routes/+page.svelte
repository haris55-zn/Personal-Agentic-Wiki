<script lang="ts">
	// Dashboard (konsep revisi-2): satu pintu utama sesuai mockup UI.
	// Isi: Search Box + toolbar (Recent | Abjad | list | grid) + Create Note
	// + daftar recent notes + FAB "munculkan chat" → ChatOverlay menutupi list.
	//
	// PANDUAN MEMBACA: file ini contoh paling padat konsep Svelte 5 (runes).
	// Tiga blok besar: (1) STATE — data yang bisa berubah,
	// (2) TURUNAN & AKSI — nilai hitungan + fungsi, (3) TEMPLATE — HTML + ekspresi.
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import SearchBox from '../lib/components/SearchBox.svelte';
	import NoteList from '../lib/components/NoteList.svelte';
	import ChatOverlay from '../lib/components/ChatOverlay.svelte';
	import { listNotes } from '../lib/api/notes';
	import type { Note } from '../lib/api/types';

	// ═══ STATE ═══
	// $state = "runes" reaktif Svelte 5: setiap nilai di bawah ini kalau
	// DIUBAH (assignment), UI yang memakainya otomatis render ulang.
	// Tidak ada command "refresh" — reaktivitas adalah efek samping assignment.
	let notes = $state<Note[]>([]); // seluruh note hasil listNotes()
	let error = $state(''); // pesan error global (tampil di banner merah)
	let sortBy = $state<'recent' | 'abjad'>('recent'); // mode urutan aktif
	let view = $state<'list' | 'grid'>('list'); // varian tampilan kartu
	let chatOpen = $state(false); // kontrol ChatOverlay

	// ═══ TURUNAN & AKSI ═══
	// $derived = nilai HASIL HITUNGAN, tidak pernah di-set manual.
	// notes atau sortBy berubah → sortedNotes ikut berubah sendiri.
	let sortedNotes = $derived(sortNotes(notes, sortBy));

	// Sort selalu di COPY ([...list]) — .sort() mengubah array aslinya,
	// dan merusak state $state tidak boleh terjadi.
	function sortNotes(list: Note[], mode: 'recent' | 'abjad'): Note[] {
		const copy = [...list];
		if (mode === 'abjad') return copy.sort((a, b) => a.title.localeCompare(b.title, 'id'));
		return copy.sort((a, b) => b.updated_at.localeCompare(a.updated_at));
	}

	// onMount = jalan SEKALI setelah komponen terpasang di browser.
	// Tempat yang benar untuk ambil data awal (sekarang dari data dump).
	onMount(async () => {
		try {
			notes = await listNotes();
		} catch (e) {
			error = e instanceof Error ? e.message : 'gagal memuat note';
		}
	});

	// createNewNote (deferred create): tombol Create Note HANYA membawa user
	// ke /editor/new — note tidak dibuat di sini; pembuatannya terjadi saat
	// Simpan pertama di halaman draft.
	function createNewNote() {
		goto(resolve('/editor/new'));
	}
</script>

<!-- ═══ TEMPLATE ═══
komentar area ini memakai gaya HTML (perintah komentar di dalam kurung kurawal
tidak boleh memuat token template). Di bawah: markup + ekspresi kurung-kurawal. -->

<div class="flex flex-col gap-6">
	<header class="pt-2">
		<h1 class="prose-claude text-3xl font-semibold tracking-tight">Personal Agentic Wiki</h1>
		<p class="mt-1 font-ui text-sm text-muted">Catatan pribadi yang bisa ditanya, dirapikan, dan diperluas oleh agent.</p>
	</header>

	<!-- SearchBox = komponen port dari v2; dia punya state sendiri (query,
	hasil dropdown). Dashboard tidak perlu tahu apa pun tentang internalsnya. -->
	<SearchBox />

	<!-- ─── TOOLBAR ───
	keempat tombol ini hanya MENGUBAH state sortBy / view.
	class dengan backtick = class dinamis: tombol aktif dapat underline+tebal.
	Tidak ada logika render di sini — sorting sudah di $derived,
	tampilan kartu di NoteList. -->
	<div class="flex flex-wrap items-center justify-between gap-3">
		<div class="flex items-baseline gap-4 font-ui text-sm text-muted">
			<button
				type="button"
				onclick={() => (sortBy = 'recent')}
				class={`underline-offset-4 transition ${sortBy === 'recent' ? 'font-semibold text-ink underline' : 'hover:text-ink'}`}
			>
				Recent
			</button>
			<span aria-hidden="true">|</span>
			<button
				type="button"
				onclick={() => (sortBy = 'abjad')}
				class={`underline-offset-4 transition ${sortBy === 'abjad' ? 'font-semibold text-ink underline' : 'hover:text-ink'}`}
			>
				Sort by Abjad
			</button>
			<span class="mx-1" aria-hidden="true">·</span>
			<button
				type="button"
				onclick={() => (view = 'list')}
				class={`underline-offset-4 transition ${view === 'list' ? 'font-semibold text-ink underline' : 'hover:text-ink'}`}
			>
				List view
			</button>
			<span aria-hidden="true">|</span>
			<button
				type="button"
				onclick={() => (view = 'grid')}
				class={`underline-offset-4 transition ${view === 'grid' ? 'font-semibold text-ink underline' : 'hover:text-ink'}`}
			>
				Grid view
			</button>
		</div>

		<button
			type="button"
			onclick={createNewNote}
			class="rounded-2xl bg-accent px-5 py-2 font-ui text-sm font-medium text-white shadow-sm transition hover:bg-accent/90"
		>
			Create Note
		</button>
	</div>

	<!-- Banner error global (bukan alert) — pengguna masih bisa coba aksi lain.
	Selama FIXTURES_ON=true pesan ini praktis tidak muncul (data dump lokal
	tidak bisa gagal network). -->
	{#if error}
		<div class="rounded-card border border-accent/40 bg-accent-soft/50 px-6 py-4 font-ui text-sm text-ink">
			{error} — pastikan backend jalan di <code>localhost:8000</code>.
		</div>
	{/if}

	<!-- NoteList = komponen presentational ("bodoh"): terima data & mode,
	render kartu. view di bawah = shorthand dari variabel view yang同名. -->
	<NoteList notes={sortedNotes} {view} />
</div>

<!-- ─── FAB (Floating Action Button) ───
fixed bottom-6 right-6 = menempel pojok viewport walau halaman di-scroll;
z-10 menaikkan di atas kartu. Satu-satunya pintu menuju chat
(di mockup: tombol "munculkan chat"). -->
<button
	type="button"
	onclick={() => (chatOpen = true)}
	class="fixed bottom-6 right-6 z-10 flex items-center gap-2 rounded-full bg-accent px-5 py-3.5 font-ui text-sm font-medium text-white shadow-lg transition hover:scale-105 hover:bg-accent/90"
>
	💬 <span>munculkan chat</span>
</button>

<!-- ChatOverlay dikendalikan DARI SINI (pola "controlled component"):
open → props masuk (boolean), onclose → callback keluar (anak minta tutup).
Anak tidak punya opini tentang state; parent pemilik tunggalnya. -->
<ChatOverlay open={chatOpen} onclose={() => (chatOpen = false)} />
