<script lang="ts">
	import FlaskConical from '@lucide/svelte/icons/flask-conical';
	import ArrowLeft from '@lucide/svelte/icons/arrow-left';
	import ThemeToggle from '$lib/components/ThemeToggle.svelte';

	let { children } = $props();
</script>

<div class="relative flex min-h-screen flex-col items-center justify-center p-4">
	<!-- Subtle radial gradient background -->
	<div
		class="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,var(--color-primary)/0.04,transparent_60%)]" aria-hidden="true"
	></div>

	<div class="relative w-full max-w-md space-y-6">
		<div class="flex flex-col items-center space-y-3 text-center">
			<div
				class="flex size-14 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-lg shadow-primary/20"
			>
				<FlaskConical class="size-7" />
			</div>
			<div>
				<h1 class="text-2xl font-bold tracking-tight">LLM Lab</h1>
				<p class="text-sm text-muted-foreground">Research platform for LLM evaluation</p>
			</div>
		</div>

		{@render children()}

		<div class="flex items-center justify-between">
			<a href="/" class="inline-flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground">
				<ArrowLeft class="size-3.5" />
				Back to home
			</a>
			<ThemeToggle />
		</div>
	</div>
</div>
