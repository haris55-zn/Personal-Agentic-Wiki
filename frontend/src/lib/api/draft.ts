// Draft note returned by note_create/note_update and passed to Apply.
export interface Draft {
	action: 'create' | 'update';
	slug: string;
	title: string;
	content_markdown: string;
	tags: string[];
	source: string | null;
	type_: string;
	diff: string;
	preview?: string;
}
