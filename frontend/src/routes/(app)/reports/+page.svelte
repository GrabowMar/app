<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Skeleton } from '$lib/components/ui/skeleton';
	import { Button } from '$lib/components/ui/button';
	import Plus from '@lucide/svelte/icons/plus';
</script>

<svelte:head>
	<title>Reports - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-bold tracking-tight">Reports</h1>
			<p class="text-muted-foreground">Generate and view analysis reports.</p>
		</div>
		<Button disabled>
			<Plus class="mr-2 h-4 w-4" />
			New Report
		</Button>
	</div>

	<Card.Root>
		<Card.Header>
			<div class="flex items-center justify-between">
				<Card.Title>All Reports</Card.Title>
				<Badge variant="secondary">Coming Soon</Badge>
			</div>
		</Card.Header>
		<Card.Content>
			<div class="rounded-md border">
				<div class="grid grid-cols-4 gap-4 border-b p-4 text-sm font-medium text-muted-foreground">
					<span>Title</span>
					<span>Type</span>
					<span>Created</span>
					<span>Status</span>
				</div>
				{#each Array(4) as _}
					<div class="grid grid-cols-4 gap-4 border-b p-4 last:border-0">
						<Skeleton class="h-4 w-36" />
						<Skeleton class="h-5 w-20 rounded-full" />
						<Skeleton class="h-4 w-24" />
						<Skeleton class="h-5 w-16 rounded-full" />
					</div>
				{/each}
			</div>
		</Card.Content>
	</Card.Root>
</div>
