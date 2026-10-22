// lib/api/types — DTO backend → frontend (single source untuk bentuk data).

export interface Note {
	slug: string;
	title: string;
	content: string;
	type: string;
	tags: string[];
	status: string;
	source: string | null;
	created_at: string;
	updated_at: string;
}

export interface ChatMessage {
	role: 'user' | 'assistant';
	content: string;
}

// Satu baris riwayat di tab "Recent Chat": judul = pesan user pertama,
// isi penuh diambil terpisah via loadHistory(id).
export interface ChatSession {
	id: string;
	title: string;
	updated_at: string;
}

export interface SearchResult {
	rank: number;
	slug: string;
	title: string;
	heading_path: string;
	anchor: string;
	snippet: string;
	score: number;
}

// REVISI-4: satu langkah jejak ReAct minimal (Thought → Action → Observation).
// Dipakai ChatTranscript untuk menampilkan "pikiran" agen sebelum jawaban.
export interface ReactStep {
	step: 'thought' | 'action' | 'observation';
	text: string;
}

export interface AnswerEvent {
	event: 'answer';
	session_id?: string;
	content: string;
}
