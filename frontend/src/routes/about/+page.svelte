<script lang="ts">
	import * as Card from '$lib/components/ui/card';
</script>

<svelte:head>
	<title>About - LLM Lab</title>
</svelte:head>

<div class="max-w-2xl mx-auto space-y-6">
	<h1 class="text-3xl font-bold tracking-tight">About LLM Lab</h1>

	<Card.Root>
		<Card.Content class="pt-6 prose prose-zinc dark:prose-invert">
			<p>
				LLM Lab is a platform for evaluating and experimenting with large language models.
				Built with Django and SvelteKit.
			</p>
		</Card.Content>
	</Card.Root>
</div>
