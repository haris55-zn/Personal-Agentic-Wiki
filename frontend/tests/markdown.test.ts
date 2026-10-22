// ═══ UNIT TEST render markdown (bun test) ═══
// Regresi produksi: parser tangan lama membocorkan fence ``` apa adanya ke
// preview dan tanpa syntax highlight. Sekarang markdown-it + highlight.js
// (src/lib/markdown.ts). Test ini mengunci: fence → <pre> + hljs, HTML mentah
// ter-escape (html:false), wikilink [[slug]], dan perilaku lama token [wN]
// yang TIDAK pernah jadi link (komentar kepala file lama menyebut "→ link"
// tetapi kode lama tidak pernah mengimplementasikannya — lihat temuan task).
//
// Jalankan: cd frontend && bun test
import { describe, expect, test } from 'bun:test';
import { renderMarkdown } from '../src/lib/markdown.ts';

describe('code fence: masalah "burik" lama', () => {
	const html = renderMarkdown('```python\ndef f(x):\n    return x * 2\n```\n');

	test('fence python jadi <pre><code> ber-kelas, bukan ``` bocor', () => {
		expect(html).toContain('<pre><code class="language-python"');
		expect(html).not.toContain('```');
		// highlight.js memecah token jadi span, jadi jangan kunci string utuh
		expect(html).toContain('<span class="hljs-keyword">return</span>');
	});

	test('isi code di-highlight highlight.js', () => {
		expect(html).toContain('<span class="hljs-');
	});

	test('fence bahasa tak dikenal tetap ter-render & ter-escape', () => {
		const out = renderMarkdown('```qtotototo\nx < y\n```\n');
		expect(out).toContain('<pre><code');
		expect(out).toContain('x &lt; y');
	});
});

describe('keamanan (html:false)', () => {
	test('<script> mentah ter-escape jadi teks', () => {
		const html = renderMarkdown('halo <script>alert(1)</script>');
		expect(html).not.toContain('<script>');
		expect(html).toContain('&lt;script&gt;');
	});
});

describe('wikilink [[slug]] & token [wN]', () => {
	test('[[rag-hybrid-search]] jadi link /note/rag-hybrid-search', () => {
		const html = renderMarkdown('Lihat [[rag-hybrid-search]] ya');
		expect(html).toContain('href="/note/rag-hybrid-search"');
		expect(html).toContain('>rag-hybrid-search</a>');
	});

	test('[[slug|Label]] pakai label sebagai teks (perilaku lama)', () => {
		const html = renderMarkdown('[[rag-hybrid-search|Hybrid RAG]]');
		expect(html).toContain('href="/note/rag-hybrid-search"');
		expect(html).toContain('>Hybrid RAG</a>');
	});

	test('[wN] TETAP teks apa adanya — sama seperti output parser lama', () => {
		// Parser lama: regex link menuntut [teks](url); "[w3]" polisi lolos
		// tanpa transform. Kunci agar migrasi tidak diam-diam menambah fitur.
		const html = renderMarkdown('Lihat [w3] ya');
		expect(html).toContain('[w3]');
		expect(html).not.toContain('<a');
	});

	test('wikilink di dalam code span / fence TIDAK diganti', () => {
		const inline = renderMarkdown('contoh kode `[[rag-hybrid-search]]` di sini');
		expect(inline).not.toContain('<a');
		expect(inline).toContain('[[rag-hybrid-search]]');
		const fenced = renderMarkdown('```\n[[rag-hybrid-search]]\n```\n');
		expect(fenced).not.toContain('<a');
	});
});

describe('prosa dasar', () => {
	test('heading + bold + list ter-render', () => {
		const html = renderMarkdown('# Judul\n\n**tebal** dan *miring*\n\n- satu\n- dua\n');
		expect(html).toContain('<h1>Judul</h1>');
		expect(html).toContain('<strong>tebal</strong>');
		expect(html).toContain('<em>miring</em>');
		expect(html).toContain('<ul>\n<li>satu</li>\n<li>dua</li>\n</ul>');
	});
});

describe('REGRESI bug laporan user 2026-10-22: "link tidak bisa dipakai"', () => {
	// Akar terbukti dari probe output nyata: destination wikilink lama
	// `[x](/note/slug ber spasi)` TIDAK membentuk link CommonMark — yang
	// muncul cuma teks mentah, bukan anchor, sehingga "link mati".
	test('wikilink slug ber-spasi jadi anchor valid dengan href ter-encode', () => {
		const html = renderMarkdown('[[slug ber spasi]]');
		expect(html).toContain('<a href="/note/slug%20ber%20spasi">');
		expect(html).not.toContain('[slug ber spasi]('); // tak ada teks mentah tersisa
	});

	test('label dengan kurung (dan slug ber-spasi) tetap jadi satu anchor utuh', () => {
		const html = renderMarkdown('[[slug ber spasi|Label (dengan) kurung]]');
		expect(html).toContain('<a href="/note/slug%20ber%20spasi">Label (dengan) kurung</a>');
	});

	test('`#` di dalam slug ter-encode %23, bukan jadi fragment', () => {
		const html = renderMarkdown('[[Catatan Saya #2|Klik di Sini]]');
		expect(html).toContain('href="/note/Catatan%20Saya%20%232"');
		expect(html).not.toContain('Saya #2');
	});

	test('slug sederhana menghasilkan href PERSIS seperti sebelum perbaikan', () => {
		expect(renderMarkdown('[[setup-bun-dan-vite]]')).toContain(
			'<a href="/note/setup-bun-dan-vite">setup-bun-dan-vite</a>',
		);
	});

	test('![[slug]] = teks "!" + anchor, BUKAN <img> rusak', () => {
		const html = renderMarkdown('Lihat ![[a-b]] ya');
		expect(html).toContain('!<a href="/note/a-b">a-b</a>');
		expect(html).not.toContain('<img');
		expect(html).not.toContain('!!');
	});

	test('label berisi kurung siku tampil apa adanya dalam anchor', () => {
		const html = renderMarkdown('[[a[b]]');
		expect(html).toContain('<a href="/note/a%5Bb">a[b</a>');
	});
});

describe('REGRESI paritas baris: note tak boleh "melebur" satu paragraf', () => {
	// Parser lama baris-per-baris (tiap baris = blok). CommonMark murni
	// menyatukan baris berdekatan — tanpa breaks:true note yang ditulis
	// baris-per-baris berubah wujud jadi tembok teks ("markdown tidak
	// berfungsi dengan baik" bagian gejala umum).
	test('enter tunggal jadi <br>, bukan soft-wrap yang menyatu', () => {
		const html = renderMarkdown('baris satu\nbaris dua');
		expect(html).toContain('<br>');
	});

	test('wikilink di tengah paragraf multi-baris ikut ter-render', () => {
		const html = renderMarkdown('baris satu\n[[dua tiga]]\nbaris tiga');
		expect(html).toContain('<a href="/note/dua%20tiga">dua tiga</a>');
	});
});

describe('destinasi host tanpa skema', () => {
	// Bug produksi 2026-10-22 (screenshot): note berisi
	// `[mbuh](www.google.com)` diklik malah membuka
	// http://localhost:5173/note/www.google.com. Akar: CommonMark
	// memperlakukan destination tanpa skema sebagai URL RELATIF terhadap
	// halaman saat ini (/note/tanpa-judul). rule link_open sekarang
	// men-https-kan destination mirip host SEBELUM memutuskan target.
	test('[mbuh](www.google.com) jadi https absolut, BUKAN relatif thd /note/', () => {
		const html = renderMarkdown('sumber: [mbuh](www.google.com)');
		expect(html).toContain('<a href="https://www.google.com"');
		expect(html).toContain('target="_blank"');
		expect(html).toContain('>mbuh</a>');
		// Bukti inti: tidak ada lagi href "www.google.com" polos yang bisa
		// di-resolve browser jadi /note/www.google.com.
		expect(html).not.toContain('href="www.google.com');
	});

	test('[x](google.com/a?b=1#c) di-prefix https, path/query/fragment utuh', () => {
		const html = renderMarkdown('[x](google.com/a?b=1#c)');
		expect(html).toContain('href="https://google.com/a?b=1#c"');
	});

	test('[x](/note/setup-bun-dan-vite) tetap internal satu tab tanpa target', () => {
		const html = renderMarkdown('[x](/note/setup-bun-dan-vite)');
		expect(html).toContain('<a href="/note/setup-bun-dan-vite">');
		expect(html).not.toContain('target="_blank"');
	});

	test('mailto: dan fragment # lewat utuh tanpa https://', () => {
		const mail = renderMarkdown('[x](mailto:a@b.co)');
		expect(mail).toContain('href="mailto:a@b.co"');
		expect(mail).not.toContain('https://');
		const frag = renderMarkdown('[x](#sudut)');
		expect(frag).toContain('href="#sudut"');
		expect(frag).not.toContain('https://');
	});

	test('[x](notes.md) tetap relatif — ekstensi file bukan host', () => {
		const html = renderMarkdown('[x](notes.md)');
		expect(html).toContain('<a href="notes.md">');
		expect(html).not.toContain('https://');
	});

	test('teks telanjang www.google.com (linkify) tetap anchor absolut http(s)', () => {
		const html = renderMarkdown('lihat www.google.com ya');
		expect(html).toMatch(/<a href="https?:\/\/www\.google\.com"/);
	});

	test('[pergi](https://luar.test) tetap target=_blank rel=noopener (rule lama)', () => {
		const html = renderMarkdown('[pergi](https://luar.test)');
		expect(html).toContain('<a href="https://luar.test"');
		expect(html).toContain('target="_blank"');
		expect(html).toContain('rel="noopener"');
	});
});
