<script lang="ts">
	// MarkdownPreview (F2/F5/F5b): render markdown prose serif; [[slug]] & [wN]
	// ditangani src/lib/markdown.ts (markdown-it + highlight.js), bukan parser tangan.
	import { renderMarkdown } from '$lib/markdown';

	let { markdown = '' }: { markdown?: string } = $props();

	// Div ref + innerHTML via ACTION — pola resmi Svelte untuk DOM di luar
	// kendali template (makanya autofixer tidak memperingatkannya): Svelte
	// memanggil fungsi saat mount lalu `update` tiap prop `markdown` berubah,
	// jadi preview editor tetap sinkron dan jawaban chat yang mengalir
	// (props di-set berulang kali) ikut ter-render. Render murni fungsi string.
	// Aman dari sisipan HTML: markdown-it dikonfigurasi html:false, sehingga
	// setiap tag mentah di sumber konten di-escape menjadi teks
	// (lihat src/lib/markdown.ts).
	function preview(node: HTMLDivElement, value: string) {
		node.innerHTML = renderMarkdown(value);
		return {
			update(next: string) {
				node.innerHTML = renderMarkdown(next);
			},
		};
	}
</script>

<div use:preview={markdown} class="prose prose-claude max-w-none leading-relaxed"></div>
