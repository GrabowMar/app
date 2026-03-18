<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Skeleton } from '$lib/components/ui/skeleton';
</script>

<svelte:head>
	<title>Models - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<div>
		<h1 class="text-2xl font-bold tracking-tight">Models</h1>
		<p class="text-muted-foreground">Browse and manage AI models available for research.</p>
	</div>

	<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
		{#each Array(6) as _}
			<Card.Root class="transition-colors hover:border-primary/50">
				<Card.Header>
					<div class="flex items-center justify-between">
						<Skeleton class="h-5 w-32" />
						<Badge variant="secondary">Coming Soon</Badge>
					</div>
					<Skeleton class="h-3 w-24" />
				</Card.Header>
				<Card.Content>
					<div class="space-y-2">
						<Skeleton class="h-3 w-full" />
						<Skeleton class="h-3 w-3/4" />
					</div>
				</Card.Content>
			</Card.Root>
		{/each}
	</div>
</div>
