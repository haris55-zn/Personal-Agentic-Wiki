// lib/api/search — search mdbook-style (GET /api/search, ranked + snippet + anchor).

import { apiFetch } from './client';
import type { SearchResult } from './types';
	import { FIXTURES_ON, fixtureSearch } from './dummy';

export async function searchWiki(q: string, limit = 12): Promise<SearchResult[]> {
	if (FIXTURES_ON) return fixtureSearch(q, limit);
	return apiFetch<SearchResult[]>(`/api/search?q=${encodeURIComponent(q)}&limit=${limit}`);
}
