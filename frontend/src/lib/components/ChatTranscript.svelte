<script lang="ts">
	// ChatTranscript: daftar balon pesan. user = kanan (accent),
	// assistant = kiri, DIRENDER sebagai markdown (jawaban agen
	// bisa berisi heading/kode/tabel, bukan cuma teks polos).
	// Komponen murni props: tidak punya state percakapan sendiri.
	//
	// REVISI-3: `liveContent` + `ttftMs` — balon asisten "hidup" memanjang
	// selama delta `message` mengalir (TTFT = kirim → token pertama).
	// REVISI-4: `steps` — jejak ReAct minimal (Thought/Action/Observation)
	// dirender blok mono kecil sebelum jawaban final tiba.
	import MarkdownPreview from './MarkdownPreview.svelte';
	import type { ChatMessage, ReactStep } from '../api/types';

	// Label pendek per jenis langkah — peta, bukan komponen (hemat baris).
	const STEP_LABEL: Record<ReactStep['step'], string> = {
		thought: 'T',
		action: 'A',
		observation: 'O'
	};

	let {
		messages,
		streaming,
		steps = [],
		liveContent = '',
		ttftMs = null
	}: {
		messages: ChatMessage[];
		streaming: boolean;
		steps?: ReactStep[];
		liveContent?: string; // teks sementara yang masih mengalir (delta SSE)
		ttftMs?: number | null; // time-to-first-token, ms (null = belum ada delta)
	} = $props();
	let bottomEl = $state<HTMLDivElement | null>(null);

	// Auto-scroll: $effect membaca panjang pesan/stream/delta/jejak
	// SEKADAR untuk mendaftarkan dependensi (nilainya tidak dipakai),
	// lalu menggulir ke elemen penanda bawah — pola "bottom anchor" chat.
	$effect(() => {
		messages.length;
		streaming;
		steps.length;
		liveContent.length;
		requestAnimationFrame(() => bottomEl?.scrollIntoView({ behavior: 'smooth' }));
	});
</script>

<div class="flex flex-col gap-4">
	{#each messages as msg, i (i)}
		{#if msg.role === 'user'}
			<div class="flex justify-end">
				<div class="max-w-[85%] rounded-2xl bg-accent-soft px-5 py-3 font-ui text-sm text-ink">
					{msg.content}
				</div>
			</div>
		{:else}
			<div class="max-w-full">
				<MarkdownPreview markdown={msg.content} />
			</div>
		{/if}
	{/each}

	{#if streaming}
		{#if steps.length > 0}
			<!-- JEJAK REACT: satu baris per langkah; label T/A/O dicetak
			tebal agar loop Thought→Action→Observation terbaca sekilas. -->
			<div class="rounded-card border border-border bg-paper px-4 py-3 font-mono text-xs leading-relaxed text-muted">
				{#each steps as st, i (i)}
					<div>
						<span class="font-semibold text-accent">{STEP_LABEL[st.step]}</span>
						<span>· {st.text}</span>
					</div>
				{/each}
			</div>
		{:else}
			<p class="font-ui text-sm text-muted">agen berpikir…</p>
		{/if}

		{#if liveContent}
			<!-- BALON HIDUP: teks delta yang masih mengalir. Kursornya = blok
			▌ di ujung, berkedip via animate-pulse. -->
			<div class="max-w-full">
				<MarkdownPreview markdown={liveContent} />
				<span class="inline-block animate-pulse font-ui text-accent">▌</span>
			</div>
		{/if}

		<!-- TTFT: terisi begitu delta pertama tiba (sebelumnya kosong). -->
		{#if ttftMs !== null}
			<p class="font-mono text-xs text-muted">TTFT {ttftMs}ms</p>
		{/if}
	{/if}
	<div bind:this={bottomEl}></div>
</div>
