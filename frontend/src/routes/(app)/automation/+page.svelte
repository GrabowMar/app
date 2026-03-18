<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Skeleton } from '$lib/components/ui/skeleton';
</script>

<svelte:head>
	<title>Automation - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<div>
		<h1 class="text-2xl font-bold tracking-tight">Automation</h1>
		<p class="text-muted-foreground">Configure and run automated analysis pipelines.</p>
	</div>

	<div class="grid gap-4 lg:grid-cols-3">
		{#each ['Configure Pipeline', 'Select Targets', 'Review & Execute'] as step, i}
			<Card.Root>
				<Card.Header>
					<div class="flex items-center gap-3">
						<div
							class="flex h-8 w-8 items-center justify-center rounded-full bg-muted text-sm font-medium"
						>
							{i + 1}
						</div>
						<div>
							<Card.Title class="text-base">{step}</Card.Title>
						</div>
					</div>
				</Card.Header>
				<Card.Content>
					<div class="space-y-2">
						<Skeleton class="h-3 w-full" />
						<Skeleton class="h-3 w-2/3" />
					</div>
				</Card.Content>
			</Card.Root>
		{/each}
	</div>

	<div class="flex justify-center">
		<Badge variant="secondary" class="text-sm">Coming Soon</Badge>
	</div>
</div>
