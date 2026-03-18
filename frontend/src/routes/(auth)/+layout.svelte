<script lang="ts">
	import FlaskConical from '@lucide/svelte/icons/flask-conical';
	import ThemeToggle from '$lib/components/ThemeToggle.svelte';

	let { children } = $props();
</script>

<div class="flex min-h-screen flex-col items-center justify-center p-4">
	<div class="w-full max-w-md space-y-6">
		<div class="flex flex-col items-center space-y-2 text-center">
			<div
				class="flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-primary-foreground"
			>
				<FlaskConical class="h-6 w-6" />
			</div>
			<h1 class="text-2xl font-bold tracking-tight">LLM Lab</h1>
		</div>

		{@render children()}

		<div class="flex justify-center">
			<ThemeToggle />
		</div>
	</div>
</div>
