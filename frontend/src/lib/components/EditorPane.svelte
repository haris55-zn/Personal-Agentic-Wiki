<script lang="ts">
	// EditorPane: form edit note — kolom meta + SPLIT VIEW.
	// Kiri textarea markdown mentah, kanan MarkdownPreview hasil render;
	// keduanya bind ke SATU state `content` (via $bindable), jadi preview
	// hidup tanpa tombol refresh. Simpan = panggil onSave milik parent.
	import MarkdownPreview from './MarkdownPreview.svelte';

	let {
		title = $bindable(''),
		content = $bindable(''),
		tags = $bindable(''),
		updatedAt,
		savedAt,
		saving,
		onSave,
	}: {
		title?: string;
		content?: string;
		tags?: string;
		updatedAt: string;
		savedAt: string;
		saving: boolean;
		onSave: () => void;
	} = $props();
</script>

<div class="flex flex-col gap-3">
	<input
		type="text"
		bind:value={title}
		placeholder="Judul"
		class="w-full rounded-2xl border border-border bg-card px-5 py-3 font-ui text-lg text-ink shadow-sm
		       focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/20"
	/>
	<input
		type="text"
		bind:value={tags}
		placeholder="tag, koma pemisah (kosong = tidak ada)"
		class="w-full rounded-2xl border border-border bg-card px-5 py-2 font-ui text-sm text-ink shadow-sm
		       focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/20"
	/>
	<div class="flex items-center justify-between gap-4">
		<span class="font-ui text-xs text-muted">
			{savedAt ? `tersimpan ${savedAt}` : `diubah ${updatedAt.slice(0, 10)}`}
		</span>
		<div class="flex gap-2">
			<button
				type="button"
				onclick={onSave}
				disabled={saving}
				class="rounded-2xl bg-accent px-6 py-2.5 font-ui text-sm font-medium text-white shadow-sm
				       hover:bg-accent/90 disabled:opacity-40 disabled:cursor-not-allowed transition"
			>
				{saving ? 'menyimpan…' : 'Simpan'}
			</button>
		</div>
	</div>
	<div class="grid gap-4 lg:grid-cols-2">
		<textarea
			bind:value={content}
			spellcheck="false"
			class="min-h-[60vh] rounded-2xl border border-border bg-card px-5 py-4 font-mono text-sm
			       leading-relaxed text-ink shadow-sm focus:border-accent focus:outline-none
			       focus:ring-2 focus:ring-accent/20 resize-y"
		></textarea>
		<div class="min-h-[60vh] overflow-y-auto rounded-2xl border border-border bg-card px-5 py-4 shadow-sm">
			<MarkdownPreview markdown={content} />
		</div>
	</div>
</div>
