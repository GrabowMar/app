<script lang="ts">
	import FlaskConical from '@lucide/svelte/icons/flask-conical';
	import ArrowLeft from '@lucide/svelte/icons/arrow-left';
	import ThemeToggle from '$lib/components/ThemeToggle.svelte';

	let { children } = $props();
</script>

<div class="relative flex min-h-screen flex-col items-center justify-center px-4 py-8 sm:p-4">
	<!-- Subtle radial gradient background -->
	<div
		class="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,var(--color-primary)/0.04,transparent_60%)]" aria-hidden="true"
	></div>

	<div class="relative w-full max-w-md space-y-5 sm:space-y-6">
		<div class="flex flex-col items-center space-y-2 text-center sm:space-y-3">
			<div
				class="flex size-12 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-lg shadow-primary/20 sm:size-14 sm:rounded-2xl"
			>
				<FlaskConical class="size-6 sm:size-7" />
			</div>
			<div>
				<h1 class="text-xl font-bold tracking-tight sm:text-2xl">LLM Lab</h1>
				<p class="text-xs text-muted-foreground sm:text-sm">Research platform for LLM evaluation</p>
			</div>
		</div>

		{@render children()}

		<div class="flex items-center justify-between">
			<a href="/" class="inline-flex items-center gap-1 text-xs text-muted-foreground transition-colors hover:text-foreground sm:text-sm">
				<ArrowLeft class="size-3 sm:size-3.5" />
				Back to home
			</a>
			<ThemeToggle />
		</div>
	</div>
</div>
