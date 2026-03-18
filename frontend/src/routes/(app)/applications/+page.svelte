<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Skeleton } from '$lib/components/ui/skeleton';
	import { Button } from '$lib/components/ui/button';
	import Plus from '@lucide/svelte/icons/plus';
</script>

<svelte:head>
	<title>Applications - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-bold tracking-tight">Applications</h1>
			<p class="text-muted-foreground">View and manage generated web applications.</p>
		</div>
		<Button disabled>
			<Plus class="mr-2 h-4 w-4" />
			New Application
		</Button>
	</div>

	<Card.Root>
		<Card.Header>
			<div class="flex items-center justify-between">
				<Card.Title>All Applications</Card.Title>
				<Badge variant="secondary">Coming Soon</Badge>
			</div>
		</Card.Header>
		<Card.Content>
			<div class="rounded-md border">
				<div class="grid grid-cols-5 gap-4 border-b p-4 text-sm font-medium text-muted-foreground">
					<span>Name</span>
					<span>Model</span>
					<span>Status</span>
					<span>Created</span>
					<span>Actions</span>
				</div>
				{#each Array(5) as _}
					<div class="grid grid-cols-5 gap-4 border-b p-4 last:border-0">
						<Skeleton class="h-4 w-28" />
						<Skeleton class="h-4 w-24" />
						<Skeleton class="h-5 w-16 rounded-full" />
						<Skeleton class="h-4 w-20" />
						<Skeleton class="h-8 w-20" />
					</div>
				{/each}
			</div>
		</Card.Content>
	</Card.Root>
</div>
