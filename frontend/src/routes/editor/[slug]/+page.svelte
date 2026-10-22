<script lang="ts">
	// Editor split-view (port v2 + tautan kembali). Alur: load → edit →
	// Simpan → reading view (keputusan user 2026-10-22): setelah simpan
	// sukses, halaman menavigasi ke /note/{slug} hasil render terbaru.
	// Halaman = ORKESTRATOR: load via getNote, simpan via updateNote, dan
	// menyalakan ulang setelah agen Apply (refreshAfterApply). UI-nya murni
	// di EditorPane + NoteAssistant.
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import EditorPane from '../../../lib/components/EditorPane.svelte';
	import NoteAssistant from '../../../lib/components/NoteAssistant.svelte';
	import { getNote, updateNote } from '../../../lib/api/notes';
	import type { Note } from '../../../lib/api/types';
	import { showToast } from '../../../lib/toast.svelte';

	let note = $state<Note | null>(null);
	let title = $state('');
	let content = $state('');
	let tags = $state('');
	let error = $state('');
	let saving = $state(false);
	let savedAt = $state('');
	let loadedSlug = $state('');

	$effect(() => {
		const slug = page.params.slug;
		if (slug && slug !== loadedSlug) loadNote(slug);
	});

	async function loadNote(slug: string): Promise<void> {
		error = '';
		loadedSlug = slug;
		try {
			const loaded = await getNote(slug);
			note = loaded;
			title = loaded.title;
			content = loaded.content;
			tags = loaded.tags.join(', ');
		} catch (e) {
			error = e instanceof Error ? e.message : 'gagal memuat note';
		}
	}

	// save() mengembalikan sukses/gagal. Setelah simpan BERHASIL kita pindah
	// ke reading view note (pakai slug dari respons `updated` — rename judul
	// mengubah slug, rute lama tak berlaku lagi). Gagal simpan: tetap di
	// editor dengan toast error. Toast dibunyikan dari sini.
	async function save(): Promise<boolean> {
		if (!note || saving) return false;
		saving = true;
		error = '';
		try {
			const updated = await updateNote(note.slug, {
				title: title.trim(),
				content,
				tags: tags
					.split(',')
					.map((tag) => tag.trim())
					.filter(Boolean)
			});
			note = updated;
			savedAt = new Date().toLocaleTimeString('id-ID');
			showToast('ok', 'Perubahan tersimpan.');
			goto(resolve('/note/[slug]', { slug: updated.slug }));
			return true;
		} catch (e) {
			error = e instanceof Error ? e.message : 'gagal menyimpan';
			showToast('err', error);
			return false;
		} finally {
			saving = false;
		}
	}

	async function refreshAfterApply(): Promise<void> {
		if (note) await loadNote(note.slug);
		showToast('ok', 'Agen menerapkan revisi ke note.');
	}
</script>

<div class="flex flex-col gap-4">
	<header class="flex flex-wrap items-baseline justify-between gap-3 pt-4">
		<h1 class="prose-claude text-3xl font-semibold tracking-tight">Edit Note</h1>
		<div class="flex items-baseline gap-4 font-ui text-sm">
			{#if note}<a href={resolve('/note/[slug]', { slug: note.slug })} class="text-accent underline">Lihat reading view</a>{/if}
			<a href={resolve('/')} class="text-muted underline hover:text-ink">← Dashboard</a>
		</div>
	</header>

	{#if error}
		<div class="rounded-card border border-accent/40 bg-accent-soft/50 px-6 py-4 font-ui text-sm text-ink">
			{error}
		</div>
	{/if}

	{#if note}
		<div class="grid gap-6 lg:grid-cols-[1fr_320px]">
			<EditorPane
				bind:title
				bind:content
				bind:tags
				updatedAt={note.updated_at}
				{savedAt}
				{saving}
				onSave={save}
			/>
			<NoteAssistant slug={note.slug} onApplied={refreshAfterApply} />
		</div>
	{:else if !error}
		<div class="py-16 text-center font-ui text-muted">memuat note…</div>
	{/if}
</div>

