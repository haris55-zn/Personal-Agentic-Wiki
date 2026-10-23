// lib/api/search — search mdbook-style (GET /api/search, ranked + snippet + anchor).

import { apiFetch } from './client';
import type { SearchResult } from './types';

export async function searchWiki(q: string, limit = 12): Promise<SearchResult[]> {
	return apiFetch<SearchResult[]>(`/api/search?q=${encodeURIComponent(q)}&limit=${limit}`);
}
