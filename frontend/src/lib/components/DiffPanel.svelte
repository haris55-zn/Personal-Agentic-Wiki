<script lang="ts">
	// DiffPanel (F6): tampilkan draft diff agent + tombol Apply/Reject.
	// GERBANG KEAMANAN agentic-wiki: agen HANYA mengusul (draft prop);
	// Apply → POST apply-diff (menulis betulan); Reject → draft dibuang
	// lewat onRejected tanpa efek apa pun. Tidak ada jalur otomatis tulis.
	import { applyDiff } from '../api/notes';
	import type { Draft } from '../api/draft';

	let {
		draft,
		onApplied,
		onRejected
	}: { draft: Draft; onApplied?: () => void; onRejected?: () => void } = $props();
	let status = $state<'idle' | 'saving' | 'saved' | 'error'>('idle');
	let message = $state('');

	async function apply(): Promise<void> {
		if (status === 'saving' || status === 'saved') return;
		status = 'saving';
		message = '';
		try {
			const result = await applyDiff(draft);
			status = 'saved';
			message = `tersimpan: /note/${result.slug}`;
			onApplied?.();
		} catch (e) {
			status = 'error';
			message = e instanceof Error ? e.message : 'gagal apply';
		}
	}

	function reject(): void {
		if (status === 'saving') return;
		onRejected?.();
	}
</script>

<div class="rounded-card border border-accent/40 bg-card px-5 py-4">
	<div class="flex flex-wrap items-baseline justify-between gap-2">
		<h3 class="font-ui text-sm font-semibold text-ink">
			Draft — {draft.action} “{draft.title}”
		</h3>
		<div class="flex gap-2">
			<button
				type="button"
				onclick={apply}
				disabled={status === 'saving' || status === 'saved'}
				class="rounded-2xl bg-accent px-4 py-1.5 font-ui text-xs font-medium text-white
				       hover:bg-accent/90 disabled:opacity-40 transition"
			>
				{status === 'saving' ? 'menyimpan…' : 'Apply'}
			</button>
			<button
				type="button"
				onclick={reject}
				class="rounded-2xl border border-border bg-card px-4 py-1.5 font-ui text-xs
				       font-medium text-muted hover:text-ink hover:border-accent transition"
			>
				Reject
			</button>
		</div>
	</div>
	{#if draft.preview}
		<p class="mt-3 font-ui text-sm text-muted">{draft.preview}</p>
	{/if}
	<pre class="mt-3 max-h-64 overflow-auto rounded-2xl bg-paper p-4 font-mono text-xs leading-relaxed text-ink">{draft.diff}</pre>
	{#if message}
		<p class="mt-2 font-ui text-xs {status === 'error' ? 'text-accent' : 'text-muted'}">{message}</p>
	{/if}
</div>
