// lib/api/chat — SSE streaming ReAct (jejak react|delta message|answer) + sesi + propose (sidebar).

import { API_BASE_URL } from './client';
import { apiFetch } from './client';
import type { ChatMessage, ChatSession } from './types';

export interface StreamEvent {
	event: string;
	message?: string;
	content?: string;
	// REVISI-4 (ReAct minimal): event `react` membawa satu langkah jejak.
	// step=action memakai tool+args; thought/observation memakai content.
	step?: 'thought' | 'action' | 'observation';
	tool?: string;
	args?: string;
	// draft event fields (dari note_create/note_update tool)
	action?: string;
	slug?: string;
	title?: string;
	content_markdown?: string;
	tags?: string[];
	source?: string | null;
	type_?: string;
	diff?: string;
	preview?: string;
}

export async function* streamChat(
	sessionId: string,
	message: string,
	signal?: AbortSignal
): AsyncGenerator<StreamEvent> {
	const response = await fetch(`${API_BASE_URL}/api/chat`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ session_id: sessionId, message }),
		signal
	});
	if (!response.ok || !response.body) {
		throw new Error(`chat gagal: ${response.status} ${response.statusText}`);
	}
	const reader = response.body.getReader();
	const decoder = new TextDecoder();
	let buffer = '';
	const parseFrame = (frame: string): StreamEvent | undefined => {
		const data = frame
			.split(/\r?\n/)
			.filter((line) => line.startsWith('data:'))
			.map((line) => line.slice(5).replace(/^ /, ''))
			.join('\n');
		return data ? (JSON.parse(data) as StreamEvent) : undefined;
	};
	try {
		while (true) {
			const { done, value } = await reader.read();
			if (done) break;
			buffer += decoder.decode(value, { stream: true });
			const frames = buffer.split(/\r?\n\r?\n/);
			buffer = frames.pop() ?? '';
			for (const frame of frames) {
				const event = parseFrame(frame);
				if (event) yield event;
			}
		}
		buffer += decoder.decode();
		const event = parseFrame(buffer);
		if (event) yield event;
	} finally {
		reader.releaseLock();
	}
}

export async function loadHistory(sessionId: string): Promise<ChatMessage[]> {
	return apiFetch<ChatMessage[]>(`/api/chat/history/${sessionId}`);
}

// REVISI-3 (mockup "Chat | Recent Chat"): daftar sesi lama + hapus sesi.
export async function listSessions(): Promise<ChatSession[]> {
	return apiFetch<ChatSession[]>('/api/chat/sessions');
}

export async function deleteSession(sessionId: string): Promise<{ deleted: string }> {
	return apiFetch<{ deleted: string }>(`/api/chat/sessions/${sessionId}`, { method: 'DELETE' });
}

export interface ProposeResult {
	slug: string;
	instruction: string;
	answer: string;
	draft?: {
		action: string;
		slug: string;
		title: string;
		content_markdown: string;
		tags: string[];
		source: string | null;
		type_: string;
		diff: string;
		preview: string;
	};
}

export async function proposeEdit(
	slug: string,
	instruction: string,
	sessionId: string
): Promise<ProposeResult> {
	return apiFetch<ProposeResult>('/api/editor/propose', {
		method: 'POST',
		body: JSON.stringify({ slug, instruction, session_id: sessionId })
	});
}
