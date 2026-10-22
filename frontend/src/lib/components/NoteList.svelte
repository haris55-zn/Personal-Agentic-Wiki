<script lang="ts">
	// NoteList (Goals.md §8 F3): daftar wiki ala mdbook — judul + snippet + tanggal.
	import type { Note } from '../api/types';
	import { resolve } from '$app/paths';

	// $props = data MASUK dari parent (Dashboard): daftar note + mode tampilan.
	// Komponen ini SENGAJA "bodoh": tidak fetch, tidak simpan state —
	// hanya render. Semua logika (urut, simpan, hapus) hidup di halaman induk.
	let { notes, view = 'list' }: { notes: Note[]; view?: 'list' | 'grid' } = $props();

	// snippet(): buang karakter markdown (#, *, `, dll) jadi teks polos,
	// potong 140 karakter — preview "excerpt" untuk kartu.
	function snippet(note: Note): string {
		const body = note.content.replace(/[#*`>\-\[\]]/g, ' ').replace(/\s+/g, ' ').trim();
		return body.length > 140 ? `${body.slice(0, 140)}…` : body;
	}

	function formatDate(iso: string): string {
		return iso.slice(0, 10);
	}
</script>

	<!-- Blok if/else = bercabang: kosong vs berisi.
	(note.slug) pada blok each = KEY: Svelte pakai identitas ini untuk
	membedakan baris saat daftar berubah — tanpa key, DOM bisa tertukar. -->
{#if notes.length === 0}
	<div class="rounded-card border border-dashed border-border bg-card/50 px-6 py-10 text-center text-muted font-ui">
		Belum ada note — buat lewat <a href={resolve('/editor')} class="text-accent underline">Editor</a> atau chat.
	</div>
{:else}
	<!-- view grid = 2 kolom di layar ≥640px; selain itu kolom tunggal -->
	<ul class={view === 'grid' ? 'grid gap-3 sm:grid-cols-2' : 'flex flex-col gap-3'}>
		{#each notes as note (note.slug)}
			<li>
				<a
					href={resolve('/note/[slug]', { slug: note.slug })}
					class="block rounded-card border border-border bg-card px-6 py-4 shadow-sm
					       hover:-translate-y-0.5 hover:shadow-md transition no-underline"
				>
					<div class="flex items-baseline justify-between gap-4">
						<h2 class="prose-claude text-lg font-semibold text-ink">{note.title}</h2>
						<span class="font-ui text-xs text-muted shrink-0">{formatDate(note.updated_at)}</span>
					</div>
					<p class="prose-claude mt-1 text-sm text-muted line-clamp-2">{snippet(note)}</p>
					{#if note.tags.length > 0}
						<div class="mt-2 flex gap-2">
							{#each note.tags as tag (tag)}
								<span class="rounded-full bg-accent-soft px-2.5 py-0.5 font-ui text-xs text-accent">
									{tag}
								</span>
							{/each}
						</div>
					{/if}
				</a>
			</li>
		{/each}
	</ul>
{/if}
