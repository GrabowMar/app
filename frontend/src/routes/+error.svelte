<script lang="ts">
	import { page } from '$app/state';
	import * as Card from '$lib/components/ui/card';
	import { Button } from '$lib/components/ui/button';

	const statusInfo: Record<number, { title: string; message: string }> = {
		404: {
			title: 'Page Not Found',
			message: "The page you're looking for doesn't exist or has been moved."
		},
		403: {
			title: 'Access Denied',
			message: "You don't have permission to access this resource."
		},
		500: {
			title: 'Internal Server Error',
			message: 'Something went wrong on our end. Please try again later.'
		},
		503: {
			title: 'Service Unavailable',
			message: 'The service is temporarily unavailable. Please try again later.'
		}
	};

	const info = statusInfo[page.status] ?? {
		title: 'Something Went Wrong',
		message: 'An unexpected error occurred.'
	};
</script>

<svelte:head>
	<title>{page.status} {info.title} - LLM Lab</title>
</svelte:head>

<div class="flex min-h-[60vh] items-center justify-center p-4">
	<Card.Root class="w-full max-w-lg text-center">
		<Card.Header class="pb-4">
			<div class="mb-4 flex justify-center">
				{#if page.status === 404}
					<span class="text-6xl" aria-hidden="true">🔍</span>
				{:else if page.status === 500}
					<span class="text-6xl" aria-hidden="true">⚠️</span>
				{:else if page.status === 503}
					<span class="text-6xl" aria-hidden="true">⚙️</span>
				{:else}
					<span class="text-6xl" aria-hidden="true">❌</span>
				{/if}
			</div>
			<Card.Title class="text-4xl font-bold tabular-nums">{page.status}</Card.Title>
			<Card.Description class="text-base font-medium text-foreground">
				{info.title}
			</Card.Description>
		</Card.Header>
		<Card.Content>
			<p class="text-muted-foreground">
				{page.error?.message || info.message}
			</p>
		</Card.Content>
		<Card.Footer class="justify-center gap-3">
			<Button href="/">Go to Dashboard</Button>
			<Button variant="outline" onclick={() => history.back()}>Go Back</Button>
		</Card.Footer>
		<div class="pb-4 text-center">
			<p class="text-xs text-muted-foreground">Error Code: {page.status}</p>
		</div>
	</Card.Root>
</div>
