<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Skeleton } from '$lib/components/ui/skeleton';
	import { Button } from '$lib/components/ui/button';
	import Plus from '@lucide/svelte/icons/plus';
	import Activity from '@lucide/svelte/icons/activity';
	import Search from '@lucide/svelte/icons/search';
	import { Input } from '$lib/components/ui/input';
</script>

<svelte:head>
	<title>Analysis Hub - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<div class="flex items-center justify-between">
		<div class="page-header">
			<h1>Analysis Hub</h1>
			<p>Run and monitor analysis tasks across your applications.</p>
		</div>
		<Button disabled>
			<Plus class="mr-2 h-4 w-4" />
			New Analysis
		</Button>
	</div>

	<div class="flex items-center gap-3">
		<div class="relative flex-1 max-w-sm">
			<Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
			<Input placeholder="Filter tasks..." class="pl-9" disabled />
		</div>
		<Badge variant="outline" class="text-xs">0 tasks</Badge>
	</div>

	<Card.Root>
		<Card.Content class="p-0">
			<div class="divide-y">
				{#each Array(5) as _, i}
					<div class="flex items-center gap-4 p-4 transition-colors hover:bg-muted/30">
						<div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-muted">
							<Activity class="h-4 w-4 text-muted-foreground" />
						</div>
						<div class="flex-1 min-w-0 space-y-1">
							<Skeleton class="h-4 w-48" />
							<Skeleton class="h-3 w-32" />
						</div>
						<Skeleton class="h-5 w-20 rounded-full" />
						<Skeleton class="h-3 w-20" />
					</div>
				{/each}
			</div>
		</Card.Content>
	</Card.Root>
</div>
