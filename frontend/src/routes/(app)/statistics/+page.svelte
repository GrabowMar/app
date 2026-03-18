<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Skeleton } from '$lib/components/ui/skeleton';
</script>

<svelte:head>
	<title>Statistics - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<div>
		<h1 class="text-2xl font-bold tracking-tight">Statistics</h1>
		<p class="text-muted-foreground">Platform-wide analytics and performance metrics.</p>
	</div>

	<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
		{#each ['Total Analyses', 'Success Rate', 'Avg. Duration', 'Active Models'] as title}
			<Card.Root>
				<Card.Header class="pb-2">
					<Card.Title class="text-sm font-medium text-muted-foreground">{title}</Card.Title>
				</Card.Header>
				<Card.Content>
					<Skeleton class="h-8 w-20" />
					<Skeleton class="mt-1 h-3 w-16" />
				</Card.Content>
			</Card.Root>
		{/each}
	</div>

	<div class="grid gap-4 lg:grid-cols-2">
		<Card.Root>
			<Card.Header>
				<div class="flex items-center justify-between">
					<Card.Title>Analysis Trends</Card.Title>
					<Badge variant="secondary">Coming Soon</Badge>
				</div>
			</Card.Header>
			<Card.Content>
				<div class="flex h-48 items-center justify-center rounded-md border border-dashed">
					<p class="text-sm text-muted-foreground">Chart placeholder</p>
				</div>
			</Card.Content>
		</Card.Root>

		<Card.Root>
			<Card.Header>
				<div class="flex items-center justify-between">
					<Card.Title>Severity Distribution</Card.Title>
					<Badge variant="secondary">Coming Soon</Badge>
				</div>
			</Card.Header>
			<Card.Content>
				<div class="flex h-48 items-center justify-center rounded-md border border-dashed">
					<p class="text-sm text-muted-foreground">Chart placeholder</p>
				</div>
			</Card.Content>
		</Card.Root>
	</div>

	<Card.Root>
		<Card.Header>
			<div class="flex items-center justify-between">
				<Card.Title>Model Comparison</Card.Title>
				<Badge variant="secondary">Coming Soon</Badge>
			</div>
		</Card.Header>
		<Card.Content>
			<div class="rounded-md border">
				<div class="grid grid-cols-5 gap-4 border-b p-4 text-sm font-medium text-muted-foreground">
					<span>Model</span>
					<span>Apps Generated</span>
					<span>Avg. Security</span>
					<span>Avg. Performance</span>
					<span>Overall Score</span>
				</div>
				{#each Array(4) as _}
					<div class="grid grid-cols-5 gap-4 border-b p-4 last:border-0">
						<Skeleton class="h-4 w-28" />
						<Skeleton class="h-4 w-8" />
						<Skeleton class="h-4 w-12" />
						<Skeleton class="h-4 w-12" />
						<Skeleton class="h-4 w-12" />
					</div>
				{/each}
			</div>
		</Card.Content>
	</Card.Root>
</div>
