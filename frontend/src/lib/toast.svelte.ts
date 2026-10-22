// ═══ TOAST GLOBAL (REVISI-6b) ═══
// Store toast di LUAR komponen supaya toast bertahan saat pindah halaman:
// klik "Simpan dan Selesai" → editor dihancurkan → toast TETAP tampil
// sampai hilang lembut. Kalau state toast milik halaman editor, pindah
// halaman = toast ikut mati di tengah kalimat.
//
// PANDUAN: nama file `.svelte.ts` = modul yang boleh memakai runes ($state).
// Membaca: `toastStore.current` (getter = ikut reaktif ke perubahan $state).
// Mengubah: hanya lewat `showToast()` — satu pemilik, tidak ada state liar.
export interface ToastMessage {
	kind: 'ok' | 'err';
	text: string;
}

let current = $state<ToastMessage | null>(null);

// Perlindungan klik beruntun TANPA handle timer: tiap toast dapat nomor
// urut; callback setTimeout hanya boleh mematikan toast bila nomornya
// masih yang terakhir — toast baru otomatis "membatalkan" timer lamanya.
let seq = 0;

/** Tampilkan toast; auto-hilang setelah `ms`. */
export function showToast(kind: ToastMessage['kind'], text: string, ms = 2500): void {
	seq += 1;
	const mine = seq;
	current = { kind, text };
	setTimeout(() => {
		if (mine === seq) current = null;
	}, ms);
}

export const toastStore = {
	get current(): ToastMessage | null {
		return current;
	}
};
