// Render markdown untuk MarkdownPreview & reading view.
//
// KENAPA LIBRARY, BUKAN PARSER TANGAN:
// Parser baris-per-baris lama "burik" di produksi — fence ``` bocor apa adanya
// ke preview dan tidak ada syntax highlight; masih banyak lagi yang tak
// tertangani (nested list, tabel, blockquote, heading di dalam list, dst).
// markdown-it = implementasi CommonMark yang sudah diuji; highlight.js untuk
// warna sintaks. Keamanan TIDAK dikorbankan: html:false membuat setiap tag
// mentah di sumber (konten user/jawaban agen bisa disisipi HTML) di-escape
// menjadi teks, jadi satu-satunya HTML yang pernah masuk innerHTML adalah
// hasil render kita sendiri.
//
// MURNI: tanpa DOM, tanpa state global yang bermutasi — render harus menjadi
// fungsi dari string saja, karena jawaban chat mengalir (props di-set berulang
// kali) dan preview editor harus sinkron.
import MarkdownIt from 'markdown-it';
import tlds from 'tlds';
import hljs from 'highlight.js';

const md = new MarkdownIt({
	// WAJIB false: raw HTML dari konten yang bisa disisipi harus ter-escape.
	html: false,
	// Paritas dengan parser lama yang baris-per-baris: dulu setiap baris sumber
	// jadi blok sendiri; CommonMark murni memperlaku-nya soft-wrap — note yang
	// ditulis baris-per-baris tampak "melebur" jadi satu paragraf panjang
	// (gejala "markdown tidak berfungsi"). breaks:true memulihkan rasa per-baris.
	breaks: true,
	linkify: true,
	typographer: false,
	// '' = tandai "tidak di-highlight" agar markdown-it meng-escape isinya sendiri.
	highlight: (code, lang) =>
		lang && hljs.getLanguage(lang)
			? hljs.highlight(code, { language: lang, ignoreIllegals: true }).value
			: '',
});

// linkify:true mengaktifkan rule-nya, TAPI linkify-it v5+ (dipakai
// markdown-it 15) memangkas daftar TLD bawaan jadi 8 item dan mem-balik
// default fuzzyLink:false — akibatnya teks telanjang seperti
// "www.google.com" berhenti jadi anchor (regresi dari era linkify-it v4
// yang meng-linkify domain apa pun). Registrasi ulang jalur resmi:
// fuzzyLink + daftar TLD IANA lengkap dari paket `tlds` (0 dependensi).
// Urutan penting: set() dulu agar re-cache, baru tlds() membangun ulang
// regex TLD dengan fuzzyLink aktif.
// Dependensi `tlds` (paket data murni, tanpa dependensi sendiri) disetujui
// direktur 2026-10-22: gejala user justru menulis "sumber: google.com"
// telanjang dan mengharapkan teks itu bisa diklik.
md.linkify.set({ fuzzyLink: true });
md.linkify.tlds(tlds);

// Paritas dengan parser lama: tautan markdown [teks](url) dibuka di tab baru
// (jawaban chat sering berisi URL; navigasi pergi = sesi editor hilang).
// Tautan internal hasil wikilink di bawah (relatif) sengaja TIDAK di-attach
// target — persis perilaku lama yang memberi target hanya di regex link.
const defaultLinkOpen = md.renderer.rules.link_open;
// Destination "mirip host tanpa skema": pola host minimal — contoh kena:
// www.google.com, google.com/a?b=1#c, example.org:8080/x. Contoh tak kena:
// ./x, ../x, foo-bar (tanpa titik), path slug /note/... (dikekang cek
// awalan di bawah). Pola ini juga TIDAK mungkin cocok "https://..." karena
// sesudah label pertama harus ada titik, bukan titik dua.
const SCHEMELESS_HOST = /^[A-Za-z0-9-_]+(\.[A-Za-z0-9-_]+)+(:\d+)?([/?#].*)?$/;
// Guard tambahan: segmen titik TERAKHIR yang merupakan ekstensi file umum
// (mis. [x](notes.md)) jangan dianggap host — daftar "Jangan kena" task
// eksplisit menyebut notes.md, padahal ".md" lolos pola minimal di atas.
// Abaikan segmen setelah `/` (mis. hosting.io/md = tetap host), dan domain
// .co/.io dsb. tidak masuk daftar sehingga tetap terprefix.
const LAST_DOT_FILE_EXT = /\.(?:md|markdown|txt|json|ya?ml|csv|tsv|xml|html?|pdf|zip|png|jpe?g|gif|svg|mp[34])$/i;
const EXPLICIT_SCHEME = /^(mailto:|tel:|data:)/i;
md.renderer.rules.link_open = (tokens, idx, options, env, self) => {
	let href = String(tokens[idx].attrGet('href') ?? '');
	// Bug produksi: CommonMark memperlakukan destination tanpa skema dan
	// tanpa "/" di depan sebagai URL RELATIF, jadi [mbuh](www.google.com)
	// diklik dari /note/... mendarat di /note/www.google.com ("note tidak
	// ditemukan"). User menulis `sumber: [x](www.google.com)` secara
	// natural — selama bentuknya mirip host, jadikan absolut https di
	// tokennya (bukan regex HTML pasca-render) lalu perlakukan sebagai
	// tautan eksternal oleh keputusan target di bawah.
	if (
		!href.startsWith('/') &&
		!href.startsWith('#') &&
		!EXPLICIT_SCHEME.test(href) &&
		SCHEMELESS_HOST.test(href) &&
		!LAST_DOT_FILE_EXT.test(href.split(/[/?#]/)[0])
	) {
		href = `https://${href}`;
		tokens[idx].attrSet('href', href);
	}
	if (/^(https?:)?\/\//i.test(href)) {
		tokens[idx].attrSet('target', '_blank');
		tokens[idx].attrSet('rel', 'noopener');
	}
	return defaultLinkOpen
		? defaultLinkOpen(tokens, idx, options, env, self)
		: self.renderToken(tokens, idx, options);
};

// ── Wikilink ─────────────────────────────────────────────────────────────
// 1. [[slug]] → <a href="/note/slug">slug</a>; [[slug|Label]] → label yang
//    jadi teks (slug & label di-trim; label kosong = slug).
// 2. Token [wN] (mis. "[w3]"): komentar kepala file lama menulis "[wN] → link",
//    TAPI kode lama tidak pernah mengubahnya — regex lama menuntut bentuk
//    [teks](url) atau [[..]], sehingga [w3] lewat utuh sebagai TEKS.
//    Keputusan: pertahankan apaadanya (literal), jangan tiba-tiba jadi link —
//    test mengunci ini. Kalau nanti memang ingin [wN] jadi tautan, itu fitur
//    baru, bukan restorasi perilaku lama.
function wikilinkToMarkdown(_m: string, slug: string, label?: string): string {
	const s = slug.trim();
	const text = label?.trim() || s;
	// BUG lama yang terbukti di produksi: destination `[x](/note/slug ber spasi)`
	// TIDAK membentuk link CommonMark — spasi/kurung/`#` merusaknya, pengguna cuma
	// melihat teks mentah "[label](/note/slug ber spasi)" dan menyimpulkan
	// "link tidak bisa dipakai". Solusi: percent-encode per segmen (spasi→%20,
	// `#`→tidak jadi fragment lagi, `<` `>` tersisih) lalu bungkus destination
	// dengan `<...>`. Slug normal (huruf-kecil-dan-tanda-hyphen) menghasilkan href
	// PERSIS sama seperti sebelumnya — rute /note/[slug] meng-decode param, jadi
	// slug ber-spasi tetap dituju apa adanya (kalau tidak ada → halaman "tidak
	// ditemukan", bukan link mati).
	const dest = s.split('/').map(encodeURIComponent).join('/');
	// Karakter struktur markdown pada label di-escape agar tampil apa adanya
	// (perilaku lama) dan tidak merusak parsing teks link.
	const safeText = text
		.replaceAll('\\', '\\\\')
		.replaceAll('[', '\\[')
		.replaceAll(']', '\\]')
		.replaceAll('`', '\\`');
	return `[${safeText}](</note/${dest}>)`;
}

const FENCE_LINE = /^\s*(```|~~~)/;
// Satu alternatif regex: span code inline dimatch duluan sehingga wikilink
// di dalamnya TIDAK pernah tersentuh.
// Grup '(!?)' ikut memakan '!' di depan wikilink: "![[..]]" tanpa perlakuan
// ini akan jadi sintaks <img> rusak; kita cetak ulang '!' sebagai teks literal
// ter-escape (output persis seperti parser lama: `!<a href="/note/..">`).
const CODE_OR_WIKILINK = /(`[^`\n]*`)|(!?)\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g;

/** [[..]] → link markdown HANYA di luar fence dan code span inline.
 * Batasan jujur: deteksi fence = baris yang dimulai ```/~~~ (toggle), jadi
 * fence tak tertutup menelan sisa dokumen seperti CommonMark, dan backtick
 * ganda di dalam code span inline eksotis bisa meleset — keduanya kasus
 * jarang dan dampak kosmetik (teks tetap tampil, hanya link tak dibuat). */
function rewriteWikilinks(source: string): string {
	const out: string[] = [];
	let inFence = false;
	for (const line of source.split('\n')) {
		if (FENCE_LINE.test(line)) {
			inFence = !inFence;
			out.push(line);
			continue;
		}
		if (inFence) {
			out.push(line);
			continue;
		}
		out.push(
			line.replace(CODE_OR_WIKILINK, (m, code?: string, bang?: string, slug?: string, label?: string) => {
				if (code !== undefined) return code;
				const link = wikilinkToMarkdown(m, slug ?? '', label);
				return bang ? `\\!${link}` : link;
			}),
		);
	}
	return out.join('\n');
}

/** Markdown → HTML siap innerHTML. Aman disuapkan string mengalir berapa pun
 * jumlahnya: tidak ada state antar-panggilan selain instance md (read-only). */
export function renderMarkdown(source: string): string {
	return md.render(rewriteWikilinks(source));
}
