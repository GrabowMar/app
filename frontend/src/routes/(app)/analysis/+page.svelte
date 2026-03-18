<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Skeleton } from '$lib/components/ui/skeleton';
	import { Button } from '$lib/components/ui/button';
	import Plus from '@lucide/svelte/icons/plus';
</script>

<svelte:head>
	<title>Analysis Hub - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-bold tracking-tight">Analysis Hub</h1>
			<p class="text-muted-foreground">Run and monitor analysis tasks across your applications.</p>
		</div>
		<Button disabled>
			<Plus class="mr-2 h-4 w-4" />
			New Analysis
		</Button>
	</div>

	<Card.Root>
		<Card.Header>
			<div class="flex items-center justify-between">
				<Card.Title>Analysis Tasks</Card.Title>
				<Badge variant="secondary">Coming Soon</Badge>
			</div>
		</Card.Header>
		<Card.Content>
			<div class="space-y-4">
				{#each Array(5) as _}
					<div class="flex items-center gap-4 rounded-lg border p-4">
						<Skeleton class="h-5 w-5 rounded-full" />
						<div class="flex-1 space-y-2">
							<Skeleton class="h-4 w-48" />
							<Skeleton class="h-3 w-32" />
						</div>
						<Skeleton class="h-6 w-20 rounded-full" />
						<Skeleton class="h-4 w-24" />
					</div>
				{/each}
			</div>
		</Card.Content>
	</Card.Root>
</div>
