<script lang="ts">
	// ═══ ROOT LAYOUT ═══ shell semua halaman — file TERPENTEK di routes/.
	// Setiap URL (/, /note/x, /editor/x) dirender DI DALAM kerangka ini.
	//
	// Konsep revisi-2: TANPA navbar Wiki/Chat/Editor — Dashboard satu pintu;
	// keluar dari halaman dalam lewat tautan "← Dashboard" masing-masing.
	// `children` = isi halaman aktif ({@render children()} di bawah).
	import '../app.css'; // token tema Claude + utilitas Tailwind
	import favicon from '$lib/assets/favicon.svg';
	import { fly, fade } from 'svelte/transition';
	import { toastStore } from '../lib/toast.svelte';

	let { children } = $props();
</script>

	<!-- svelte:head = slot khusus layout: tag di sini dipromosikan ke head dokumen. -->
<svelte:head>
	<link rel="icon" href={favicon} />
	<title>Personal Agentic Wiki</title>
</svelte:head>

	<!-- max-w-5xl + mx-auto = kolom konten terpusat; semua halaman mewarisi
	pembungkus ini, jadi tidak ada komponen yang mengatur margin sendiri. -->
<main class="mx-auto max-w-5xl px-6 py-8">{@render children()}</main>

<!-- ═══ TOAST GLOBAL (REVISI-6b) ═══
Dirender di LAYOUT (bukan di halaman) supaya survives pindah rute: "Simpan
dan Selesai" melompat ke dashboard, toast tetap tampil lalu hilang sendiri.
Motion natural: MASUK fly dari atas cepat (200ms), KELUAR fade lembut (500ms)
— in:/out: = local transitions, boleh beda karakter.
Wrapper flex-center menggantikan -translate-x-1/2 supaya transform milik
animasi fly tidak menimpa transform posisi (keduanya berebut `transform`).
pointer-events-none = toast tidak menghalangi klik di bawahnya. -->
<div class="pointer-events-none fixed inset-x-0 top-4 z-30 flex justify-center">
	{#if toastStore.current}
		<div
			role="status"
			in:fly={{ y: -14, duration: 200 }}
			out:fade={{ duration: 500 }}
			class="rounded-2xl px-5 py-2.5 font-ui text-sm text-white shadow-lg {toastStore.current.kind === 'ok' ? 'bg-accent' : 'bg-ink'}"
		>
			{toastStore.current.text}
		</div>
	{/if}
</div>
