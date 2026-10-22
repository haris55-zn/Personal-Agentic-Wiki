// lib/api/notes — CRUD note + backlinks (reading view) + apply diff.

import { apiFetch } from './client';
import type { Note } from './types';
	import {
		FIXTURES_ON,
		fixtureApplyDiff,
		fixtureCreateNote,
		fixtureDeleteNote,
		fixtureGetBacklinks,
		fixtureGetNote,
		fixtureListNotes,
		fixtureUpdateNote
	} from './dummy';

export async function listNotes(limit = 50): Promise<Note[]> {
	if (FIXTURES_ON) return fixtureListNotes(limit);
	return apiFetch<Note[]>(`/api/notes?limit=${limit}`);
}

export async function getNote(slug: string): Promise<Note> {
	if (FIXTURES_ON) return fixtureGetNote(slug);
	return apiFetch<Note>(`/api/notes/${slug}`);
}

export async function getBacklinks(slug: string): Promise<Note[]> {
	if (FIXTURES_ON) return fixtureGetBacklinks(slug);
	return apiFetch<Note[]>(`/api/notes/${slug}/backlinks`);
}

export async function createNote(body: { title: string; content: string; tags: string[] }): Promise<Note> {
	if (FIXTURES_ON) return fixtureCreateNote(body);
	return apiFetch<Note>('/api/notes', { method: 'POST', body: JSON.stringify(body) });
}

export async function updateNote(
	slug: string,
	body: { title: string; content: string; tags: string[] }
): Promise<Note> {
	if (FIXTURES_ON) return fixtureUpdateNote(slug, body);
	return apiFetch<Note>(`/api/notes/${slug}`, { method: 'PUT', body: JSON.stringify(body) });
}

export async function deleteNote(slug: string): Promise<{ deleted: string }> {
	if (FIXTURES_ON) return fixtureDeleteNote(slug);
	return apiFetch<{ deleted: string }>(`/api/notes/${slug}`, { method: 'DELETE' });
}

export async function applyDiff(draft: {
	slug: string;
	title: string;
	content_markdown: string;
	tags: string[];
	source: string | null;
	type_: string;
}): Promise<{ saved: boolean; slug: string; path: string }> {
	if (FIXTURES_ON) return fixtureApplyDiff(draft);
	return apiFetch<{ saved: boolean; slug: string; path: string }>('/api/notes/apply-diff', {
		method: 'POST',
		body: JSON.stringify({
			slug: draft.slug,
			title: draft.title,
			content_markdown: draft.content_markdown,
			tags: draft.tags,
			source: draft.source,
			type_: draft.type_
		})
	});
}
