<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Skeleton } from '$lib/components/ui/skeleton';
	import Trophy from '@lucide/svelte/icons/trophy';
</script>

<svelte:head>
	<title>Rankings - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<div>
		<h1 class="text-2xl font-bold tracking-tight">Model Rankings</h1>
		<p class="text-muted-foreground">Compare model performance across coding benchmarks.</p>
	</div>

	<Card.Root>
		<Card.Header>
			<div class="flex items-center justify-between">
				<Card.Title>Leaderboard</Card.Title>
				<Badge variant="secondary">Coming Soon</Badge>
			</div>
		</Card.Header>
		<Card.Content>
			<div class="rounded-md border">
				<div class="grid grid-cols-5 gap-4 border-b p-4 text-sm font-medium text-muted-foreground">
					<span>Rank</span>
					<span>Model</span>
					<span>Score</span>
					<span>Security</span>
					<span>Performance</span>
				</div>
				{#each Array(8) as _, i}
					<div class="grid grid-cols-5 gap-4 border-b p-4 last:border-0">
						<div class="flex items-center gap-2">
							{#if i < 3}
								<Trophy class="h-4 w-4 {i === 0 ? 'text-yellow-500' : i === 1 ? 'text-gray-400' : 'text-amber-600'}" />
							{/if}
							<span class="text-sm font-medium">#{i + 1}</span>
						</div>
						<Skeleton class="h-4 w-28" />
						<Skeleton class="h-4 w-12" />
						<Skeleton class="h-4 w-12" />
						<Skeleton class="h-4 w-12" />
					</div>
				{/each}
			</div>
		</Card.Content>
	</Card.Root>
</div>
