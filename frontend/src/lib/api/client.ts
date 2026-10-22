// lib/api/client — fetch wrapper ke backend FastAPI (Goals.md §4.1).
// KENAPA wrapper: satu tempat menangani API_BASE_URL, error surface, dan JSON.

export const API_BASE_URL = 'http://localhost:8000';

export class ApiError extends Error {
	constructor(
		public status: number,
		message: string
	) {
		super(message);
	}
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
	const response = await fetch(`${API_BASE_URL}${path}`, {
		...init,
		headers: { 'Content-Type': 'application/json', ...init?.headers }
	});
	if (!response.ok) {
		let detail = `${response.status} ${response.statusText}`;
		try {
			const body = (await response.json()) as { detail?: string };
			if (body.detail) detail = body.detail;
		} catch {
			/* body bukan JSON — pakai status line */
		}
		throw new ApiError(response.status, detail);
	}
	return (await response.json()) as T;
}
