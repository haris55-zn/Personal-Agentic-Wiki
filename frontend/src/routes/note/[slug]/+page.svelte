<script lang="ts">
	// Reading view (port v2 + HAPUS): prose serif, meta, backlinks.
	// Alur data: $effect re-run setiap page.params.slug berubah —
	// itu cara navigasi wikilink antar-note tanpa reload penuh.
	// Hapus = confirm() dulu → DELETE API → goto Dashboard.
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import MarkdownPreview from '../../../lib/components/MarkdownPreview.svelte';
	import { deleteNote, getBacklinks, getNote } from '../../../lib/api/notes';
	import type { Note } from '../../../lib/api/types';

	let note = $state<Note | null>(null);
	let backlinks = $state<Note[]>([]);
	let error = $state('');
	let deleting = $state(false);

	$effect(() => {
		// re-load saat slug berubah (navigasi antar note via wikilink)
		const slug = page.params.slug;
		if (slug) loadNote(slug);
	});

	onMount(() => {
		const slug = page.params.slug;
		if (slug) loadNote(slug);
	});

	async function loadNote(slug: string) {
		error = '';
		note = null;
		try {
			note = await getNote(slug);
			backlinks = await getBacklinks(slug).catch(() => []);
		} catch (e) {
			error = e instanceof Error ? e.message : 'gagal memuat note';
			return;
		}
		scrollToHash();
	}

	function scrollToHash(): void {
		// browser scroll saat DOM masih kosong (note di-fetch async) — ulangi
		// setelah render, agar anchor dari search (#heading) berfungsi.
		const hash = decodeURIComponent(location.hash.slice(1));
		if (!hash) return;
		requestAnimationFrame(() => {
			document.getElementById(hash)?.scrollIntoView();
		});
	}

	async function removeNote(): Promise<void> {
		if (!note || deleting) return;
		if (!confirm(`Hapus note "${note.title}"? File markdown-nya ikut terhapus dan tidak bisa dikembalikan dari aplikasi.`)) return;
		deleting = true;
		try {
			await deleteNote(note.slug);
			goto(resolve('/'));
		} catch (e) {
			error = e instanceof Error ? e.message : 'gagal menghapus note';
			deleting = false;
		}
	}
</script>

{#if error}
	<div class="rounded-card border border-accent/40 bg-accent-soft/50 px-6 py-4 font-ui text-sm text-ink">
		{error} — kembali ke <a href={resolve('/')} class="text-accent underline">Dashboard</a>.
	</div>
{:else if note}
	<article class="mx-auto max-w-3xl">
		<header class="mb-6 flex flex-wrap items-baseline justify-between gap-3 border-b border-border pb-4">
			<h1 class="prose-claude text-4xl font-semibold tracking-tight">{note.title}</h1>
			<div class="flex items-center gap-3">
				<a
					href={resolve('/editor/[slug]', { slug: note.slug })}
					class="rounded-2xl bg-accent px-4 py-2 font-ui text-sm font-medium text-white shadow-sm
					       hover:bg-accent/90 transition"
				>
					Edit
				</a>
				<button
					type="button"
					onclick={removeNote}
					disabled={deleting}
					class="rounded-2xl border border-accent/50 px-4 py-2 font-ui text-sm text-accent transition
					       hover:bg-accent-soft disabled:opacity-40"
				>
					{deleting ? 'menghapus…' : 'Hapus'}
				</button>
			</div>
		</header>

		<div class="mb-6 flex flex-wrap items-center gap-3 font-ui text-xs text-muted">
			<a href={resolve('/')} class="text-accent underline">← Dashboard</a>
			<span>diubah {note.updated_at.slice(0, 10)}</span>
			{#if note.type === 'web-clipping' && note.source}
				<a href={note.source} target="_blank" rel="noopener" class="text-accent underline">
					sumber: {note.source}
				</a>
			{/if}
			{#each note.tags as tag (tag)}
				<span class="rounded-full bg-accent-soft px-2.5 py-0.5 text-accent">{tag}</span>
			{/each}
		</div>

		<MarkdownPreview markdown={note.content} />

		{#if backlinks.length > 0}
			<section class="mt-12 border-t border-border pt-6">
				<h2 class="font-ui text-xs font-semibold uppercase tracking-wider text-muted">
					↩ Ditautkan dari
				</h2>
				<ul class="mt-3 flex flex-col gap-1.5">
					{#each backlinks as link (link.slug)}
						<li>
							<a href={resolve('/note/[slug]', { slug: link.slug })} class="prose-claude text-accent hover:underline">
								{link.title}
							</a>
						</li>
					{/each}
				</ul>
			</section>
		{/if}
	</article>
{:else}
	<div class="py-16 text-center font-ui text-muted">memuat note…</div>
{/if}
