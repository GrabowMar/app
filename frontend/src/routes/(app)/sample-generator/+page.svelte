<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Skeleton } from '$lib/components/ui/skeleton';
	import { Button } from '$lib/components/ui/button';
	import Code from '@lucide/svelte/icons/code';
</script>

<svelte:head>
	<title>Sample Generator - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-bold tracking-tight">Sample Generator</h1>
			<p class="text-muted-foreground">Generate sample web applications using AI models.</p>
		</div>
		<Button disabled>
			<Code class="mr-2 h-4 w-4" />
			Generate
		</Button>
	</div>

	<Card.Root>
		<Card.Header>
			<div class="flex items-center justify-between">
				<Card.Title>Generator Wizard</Card.Title>
				<Badge variant="secondary">Coming Soon</Badge>
			</div>
			<Card.Description>Select a model, template, and configuration to generate a new application.</Card.Description>
		</Card.Header>
		<Card.Content>
			<div class="space-y-4">
				{#each ['Select Model', 'Choose Template', 'Configure Options', 'Generate'] as step, i}
					<div class="flex items-center gap-3 rounded-lg border p-3">
						<div
							class="flex h-7 w-7 items-center justify-center rounded-full bg-muted text-xs font-medium"
						>
							{i + 1}
						</div>
						<span class="text-sm font-medium">{step}</span>
						<Skeleton class="ml-auto h-4 w-20" />
					</div>
				{/each}
			</div>
		</Card.Content>
	</Card.Root>
</div>
