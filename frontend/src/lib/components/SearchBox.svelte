<script lang="ts">
	// SearchBox mdbook-style (Goals.md §8 F3): debounce → GET../api/search,
	// hasil ranked + snippet, klik/Enter → /note/{slug}#{anchor}.
	import { goto } from '$app/navigation';
	import { searchWiki } from '../api/search';
	import type { SearchResult } from '../api/types';
	import { resolve } from '$app/paths';

	// State lokal: query (teks), results (dropdown), activeIndex (sorotan),
	// loading, dan pegangan timer debounce.
	let query = $state('');
	let results = $state<SearchResult[]>([]);
	let activeIndex = $state(0);
	let loading = $state(false);
	let debounceTimer: ReturnType<typeof setTimeout>;

	async function runSearch(value: string) {
		if (value.trim().length < 2) {
			results = [];
			return;
		}
		loading = true;
		try {
			results = await searchWiki(value);
			activeIndex = 0;
		} catch {
			results = [];
		} finally {
			loading = false;
		}
	}

	// DEBOUNCE 300ms: tiap ketikan me-reset timer; panggilan API sungguhan
	// hanya terjadi setelah user berhenti mengetik — hemat request.
	function onInput(event: Event) {
		const value = (event.target as HTMLInputElement).value;
		query = value;
		clearTimeout(debounceTimer);
		debounceTimer = setTimeout(() => runSearch(value), 300);
	}

	// Navigasi keyboard ala command-palette: ↑/↓ pindah sorotan, Enter buka,
	// Esc tutup dropdown. preventDefault = jangan biarkan panah juga
	// menggerakkan kursor input.
	function onKeyDown(event: KeyboardEvent) {
		if (!results.length) return;
		if (event.key === 'ArrowDown') {
			event.preventDefault();
			activeIndex = Math.min(activeIndex + 1, results.length - 1);
		} else if (event.key === 'ArrowUp') {
			event.preventDefault();
			activeIndex = Math.max(activeIndex - 1, 0);
		} else if (event.key === 'Enter') {
			event.preventDefault();
			openResult(results[activeIndex]);
		} else if (event.key === 'Escape') {
			results = [];
		}
	}

	// Hasil klik/Enter → /note/{slug}#{anchor}: halaman membaca akan
	// men-scroll ke heading yang cocok (lihat scrollToHash di note page).
	function openResult(result: SearchResult) {
		const anchor = result.anchor ? `#${result.anchor}` : '';
		results = [];
		query = '';
		goto(resolve('/note/[slug]', { slug: result.slug }) + anchor);
	}
</script>

<div class="relative">
	<input
		type="search"
		placeholder="Cari di wiki…"
		value={query}
		oninput={onInput}
		onkeydown={onKeyDown}
		class="w-full rounded-2xl border border-border bg-card px-5 py-3 font-ui text-ink shadow-sm
		       placeholder:text-muted focus:border-accent focus:outline-none focus:ring-2
		       focus:ring-accent/20 transition"
	/>
	{#if loading}
		<div class="absolute right-4 top-1/2 -translate-y-1/2 text-muted text-xs">mencari…</div>
	{/if}

	{#if results.length > 0}
		<ul
			class="absolute z-20 mt-2 w-full overflow-hidden rounded-2xl border border-border bg-card shadow-lg"
		>
			{#each results as result, index (result.rank)}
				<li>
					<button
						class="w-full px-5 py-3 text-left transition-colors
						       {index === activeIndex ? 'bg-accent-soft' : 'hover:bg-accent-soft/60'}"
						onclick={() => openResult(result)}
					>
						<div class="font-ui text-sm font-medium text-ink">
							{result.title}
							{#if result.heading_path !== '-'}
								<span class="text-muted"> › {result.heading_path}</span>
							{/if}
						</div>
						<div class="prose-claude mt-0.5 text-xs text-muted line-clamp-2">
							{result.snippet}
						</div>
					</button>
				</li>
			{/each}
		</ul>
	{/if}
</div>
