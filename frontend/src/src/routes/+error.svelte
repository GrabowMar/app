<script lang="ts">
	import { page } from '$app/state';
	import * as Card from '$lib/components/ui/card';
	import { Button } from '$lib/components/ui/button';
</script>

<svelte:head>
	<title>Error - LLM Lab</title>
</svelte:head>

<div class="flex min-h-[60vh] items-center justify-center">
	<Card.Root class="w-full max-w-md text-center">
		<Card.Header>
			<Card.Title class="text-6xl font-bold">{page.status}</Card.Title>
			<Card.Description class="text-lg">
				{#if page.status === 404}
					Page not found
				{:else if page.status === 403}
					Access denied
				{:else if page.status === 500}
					Internal server error
				{:else}
					Something went wrong
				{/if}
			</Card.Description>
		</Card.Header>
		<Card.Content>
			{#if page.error?.message}
				<p class="text-muted-foreground">{page.error.message}</p>
			{/if}
		</Card.Content>
		<Card.Footer class="justify-center">
			<Button href="/">Go Home</Button>
		</Card.Footer>
	</Card.Root>
</div>
