<script lang="ts">
	// ChatComposer: kotak "Ketik sini" + tombol Kirim/Stop.
	// KONSEP PENTING — $bindable: prop `input` boleh DIUBAH oleh anak
	// (parent mem-pass bind:input). Tanpa $bindable, assignment ke prop
	// akan error; dengan ini dua-arah: user ngetik → parent `input` ikut.
	// Tombol menukar wajah: streaming=true → Stop (memicu onStop),
	// streaming=false → Kirim (submit form → onSend).
	let {
		input = $bindable(''),
		streaming,
		onSend,
		onStop
	}: {
		input?: string;
		streaming: boolean;
		onSend: () => void;
		onStop: () => void;
	} = $props();
</script>

<form
	class="sticky bottom-0 flex gap-2 bg-paper/95 py-3 backdrop-blur"
	onsubmit={(e) => {
		e.preventDefault();
		onSend();
	}}
>
	<input
		type="text"
		bind:value={input}
		placeholder="tanya apa saja…"
		disabled={streaming}
		class="flex-1 rounded-2xl border border-border bg-card px-5 py-3 font-ui text-sm text-ink shadow-sm
		       placeholder:text-muted focus:border-accent focus:outline-none focus:ring-2
		       focus:ring-accent/20 disabled:opacity-60"
	/>
	{#if streaming}
		<button
			type="button"
			onclick={onStop}
			class="rounded-2xl border border-border bg-card px-5 py-3 font-ui text-sm font-medium
			       text-ink shadow-sm hover:border-accent transition"
		>
			Stop
		</button>
	{:else}
		<button
			type="submit"
			disabled={!input.trim()}
			class="rounded-2xl bg-accent px-6 py-3 font-ui text-sm font-medium text-white shadow-sm
			       hover:bg-accent/90 disabled:opacity-40 disabled:cursor-not-allowed transition"
		>
			Kirim
		</button>
	{/if}
</form>
