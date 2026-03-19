<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Skeleton } from '$lib/components/ui/skeleton';
	import Trophy from '@lucide/svelte/icons/trophy';
	import Medal from '@lucide/svelte/icons/medal';
</script>

<svelte:head>
	<title>Rankings - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<div class="page-header">
		<h1>Model Rankings</h1>
		<p>Compare model performance across coding benchmarks.</p>
	</div>

	<Card.Root>
		<Card.Header>
			<div class="flex items-center justify-between">
				<div class="flex items-center gap-2">
					<Trophy class="h-4 w-4 text-amber-500" />
					<Card.Title>Leaderboard</Card.Title>
				</div>
				<Badge variant="outline" class="text-xs">Coming Soon</Badge>
			</div>
		</Card.Header>
		<Card.Content class="p-0">
			<div class="overflow-x-auto">
				<table class="w-full">
					<thead>
						<tr class="border-b bg-muted/30">
							<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground w-20">Rank</th>
							<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Model</th>
							<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Score</th>
							<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Security</th>
							<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Performance</th>
						</tr>
					</thead>
					<tbody class="divide-y">
						{#each Array(8) as _, i}
							<tr class="transition-colors hover:bg-muted/30 {i < 3 ? 'bg-amber-50/30 dark:bg-amber-950/10' : ''}">
								<td class="px-4 py-3">
									<div class="flex items-center gap-2">
										{#if i < 3}
											<Medal class="h-4 w-4 {i === 0 ? 'text-amber-500' : i === 1 ? 'text-slate-400' : 'text-amber-700'}" />
										{/if}
										<span class="text-sm font-medium {i < 3 ? 'font-semibold' : ''}">#{i + 1}</span>
									</div>
								</td>
								<td class="px-4 py-3"><Skeleton class="h-4 w-28" /></td>
								<td class="px-4 py-3"><Skeleton class="h-4 w-12" /></td>
								<td class="px-4 py-3"><Skeleton class="h-4 w-12" /></td>
								<td class="px-4 py-3"><Skeleton class="h-4 w-12" /></td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</Card.Content>
	</Card.Root>
</div>
