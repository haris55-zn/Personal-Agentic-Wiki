<script lang="ts">
	import DiffPanel from './DiffPanel.svelte';
	import MarkdownPreview from './MarkdownPreview.svelte';
	import { proposeEdit, type ProposeResult } from '../api/chat';
	import type { Draft } from '../api/draft';

	const SESSION_KEY_PREFIX = 'wiki-editor-session:';

	let { slug, onApplied }: { slug: string; onApplied?: () => void } = $props();
	let instruction = $state('');
	let proposing = $state(false);
	let answer = $state('');
	let draft = $state<Draft | null>(null);
	let error = $state('');
	let previousSlug = $state('');

	$effect(() => {
		if (slug === previousSlug) return;
		previousSlug = slug;
		instruction = '';
		answer = '';
		draft = null;
		error = '';
	});

	async function propose(): Promise<void> {
		const prompt = instruction.trim();
		if (!prompt || proposing) return;
		proposing = true;
		error = '';
		answer = '';
		draft = null;
		try {
			const sessionId = getSessionId(slug);
			const result = await proposeEdit(slug, prompt, sessionId);

			answer = result.answer;
			if (result.draft) draft = toDraft(result.draft);
			instruction = '';
		} catch (e) {
			error = e instanceof Error ? e.message : 'gagal propose';
		} finally {
			proposing = false;
		}
	}

	function getSessionId(noteSlug: string): string {
		const key = `${SESSION_KEY_PREFIX}${noteSlug}`;
		const existingSessionId = localStorage.getItem(key);
		if (existingSessionId) return existingSessionId;

		const sessionId = crypto.randomUUID();
		localStorage.setItem(key, sessionId);
		return sessionId;
	}

	function toDraft(result: NonNullable<ProposeResult['draft']>): Draft {
		return {
			action: (result.action as Draft['action']) ?? 'update',
			slug: result.slug,
			title: result.title,
			content_markdown: result.content_markdown,
			tags: result.tags ?? [],
			source: result.source ?? null,
			type_: result.type_ ?? 'note',
			diff: result.diff,
			preview: result.preview
		};
	}

	function rejectDraft(): void {
		draft = null;
		answer = '';
	}
</script>

<aside class="flex flex-col gap-3">
	<h2 class="font-ui text-xs font-semibold uppercase tracking-wider text-muted">
		Chat ter-scope note ini
	</h2>
	<form
		class="flex flex-col gap-2"
		onsubmit={(e) => {
			e.preventDefault();
			propose();
		}}
	>
		<textarea
			bind:value={instruction}
			placeholder="Instruksi revisi… (mis. 'rapikan bagian 2')"
			rows="3"
			disabled={proposing}
			class="w-full rounded-2xl border border-border bg-card px-4 py-3 font-ui text-sm text-ink
			       shadow-sm placeholder:text-muted focus:border-accent focus:outline-none
			       focus:ring-2 focus:ring-accent/20 disabled:opacity-60 resize-y"
		></textarea>
		<button
			type="submit"
			disabled={!instruction.trim() || proposing}
			class="rounded-2xl bg-accent px-4 py-2 font-ui text-sm font-medium text-white shadow-sm
			       hover:bg-accent/90 disabled:opacity-40 disabled:cursor-not-allowed transition"
		>
			{proposing ? 'memproses…' : 'Propose'}
		</button>
	</form>

	{#if error}
		<div class="rounded-card border border-accent/40 bg-accent-soft/50 px-4 py-3 font-ui text-xs text-ink">
			{error}
		</div>
	{/if}

	{#if answer}
		<div class="rounded-card border border-border bg-card px-4 py-3">
			<MarkdownPreview markdown={answer} />
		</div>
	{/if}

	{#if draft}
		<DiffPanel {draft} {onApplied} onRejected={rejectDraft} />
	{/if}
</aside>
