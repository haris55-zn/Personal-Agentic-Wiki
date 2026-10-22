<script lang="ts">
	// Editor list (F4, diport dari v2 + tautan kembali ke Dashboard):
	// daftar note + satu tombol "Buat Note" yang menavigasi ke halaman
	// draft /editor/new — note tidak dibuat di sini (deferred create).
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { listNotes } from '../../lib/api/notes';
	import type { Note } from '../../lib/api/types';

	let notes = $state<Note[]>([]);
	let error = $state('');

	onMount(async () => {
		try {
			notes = await listNotes();
		} catch (e) {
			error = e instanceof Error ? e.message : 'gagal memuat note';
		}
	});
</script>

<div class="flex flex-col gap-6">
	<header class="flex flex-wrap items-baseline justify-between gap-3 pt-4">
		<h1 class="prose-claude text-3xl font-semibold tracking-tight">Editor</h1>
		<a href={resolve('/')} class="font-ui text-sm text-accent underline">← Dashboard</a>
	</header>

	<button
		type="button"
		onclick={() => goto(resolve('/editor/new'))}
		class="self-start rounded-2xl bg-accent px-6 py-3 font-ui font-medium text-white shadow-sm
		       hover:bg-accent/90 transition"
	>
		Buat Note
	</button>

	{#if error}
		<div class="rounded-card border border-accent/40 bg-accent-soft/50 px-6 py-4 font-ui text-sm text-ink">
			{error} — pastikan backend jalan (<code>make run-backend</code>).
		</div>
	{/if}

	<ul class="flex flex-col gap-2">
		{#each notes as note (note.slug)}
			<li>
				<a
					href={resolve('/editor/[slug]', { slug: note.slug })}
					class="flex items-baseline justify-between gap-4 rounded-card border border-border
					       bg-card px-5 py-3 shadow-sm hover:shadow-md transition no-underline"
				>
					<span class="prose-claude font-medium text-ink">{note.title}</span>
					<span class="font-ui text-xs text-muted">{note.updated_at.slice(0, 10)}</span>
				</a>
			</li>
		{:else}
			<li class="rounded-card border border-dashed border-border bg-card/50 px-6 py-8 text-center text-muted font-ui">
				Belum ada note — buat yang pertama di atas.
			</li>
		{/each}
	</ul>
</div>
