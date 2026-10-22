<script lang="ts">
	// Editor DRAFT (deferred create): note TIDAK tercipta sebelum tombol
	// Simpan pertama sukses — semua state lokal, tanpa fetch awal.
	// Catatan rute: folder statis `new` menang atas dinamis `[slug]` —
	// slug 'new' tidak bisa lagi dibuka sebagai note biasa di /editor/new
	// (konsekuensi desain yang diterima).
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import EditorPane from '../../../lib/components/EditorPane.svelte';
	import { createNote } from '../../../lib/api/notes';
	import { showToast } from '../../../lib/toast.svelte';

	let title = $state('');
	let content = $state('');
	let tags = $state('');
	let saving = $state(false);

	// Timestamp "now" untuk label EditorPane (draft belum pernah disimpan).
	const nowIso = new Date().toISOString();

	// save() = createNote PERTAMA dan SATU-SATUNYA di halaman ini.
	// Sukses → toast + reading view note baru; gagal → toast, tetap di
	// draft (semua isian aman). `saving` guard anti klik dobel.
	async function save(): Promise<boolean> {
		if (saving) return false;
		saving = true;
		try {
			const created = await createNote({
				title: title.trim() || 'Tanpa Judul',
				content,
				tags: tags
					.split(',')
					.map((tag) => tag.trim())
					.filter(Boolean)
			});
			showToast('ok', 'Note tersimpan.');
			goto(resolve('/note/[slug]', { slug: created.slug }));
			return true;
		} catch (e) {
			showToast('err', e instanceof Error ? e.message : 'gagal menyimpan');
			return false;
		} finally {
			saving = false;
		}
	}
</script>

<div class="flex flex-col gap-4">
	<header class="flex flex-wrap items-baseline justify-between gap-3 pt-4">
		<h1 class="prose-claude text-3xl font-semibold tracking-tight">Note Baru</h1>
		<div class="flex items-baseline gap-4 font-ui text-sm">
			<a href={resolve('/')} class="text-muted underline hover:text-ink">← Dashboard</a>
		</div>
	</header>

	<!-- NoteAssistant sengaja tidak dipasang: note belum ada di backend,
	 jadi belum ada apa pun untuk direvisi agen — EditorPane full-width. -->
	<EditorPane
		bind:title
		bind:content
		bind:tags
		updatedAt={nowIso}
		savedAt=""
		{saving}
		onSave={save}
	/>
</div>
