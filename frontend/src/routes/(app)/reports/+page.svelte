<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Skeleton } from '$lib/components/ui/skeleton';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import Plus from '@lucide/svelte/icons/plus';
	import Search from '@lucide/svelte/icons/search';
</script>

<svelte:head>
	<title>Reports - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<div class="flex items-center justify-between">
		<div class="page-header">
			<h1>Reports</h1>
			<p>Generate and view analysis reports.</p>
		</div>
		<Button disabled>
			<Plus class="mr-2 h-4 w-4" />
			New Report
		</Button>
	</div>

	<div class="flex items-center gap-3">
		<div class="relative flex-1 max-w-sm">
			<Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
			<Input placeholder="Search reports..." class="pl-9" disabled />
		</div>
		<Badge variant="outline" class="text-xs">0 reports</Badge>
	</div>

	<Card.Root>
		<Card.Content class="p-0">
			<div class="overflow-x-auto">
				<table class="w-full">
					<thead>
						<tr class="border-b bg-muted/30">
							<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Title</th>
							<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Type</th>
							<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Created</th>
							<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Status</th>
						</tr>
					</thead>
					<tbody class="divide-y">
						{#each Array(4) as _}
							<tr class="transition-colors hover:bg-muted/30">
								<td class="px-4 py-3"><Skeleton class="h-4 w-36" /></td>
								<td class="px-4 py-3"><Skeleton class="h-5 w-20 rounded-full" /></td>
								<td class="px-4 py-3"><Skeleton class="h-4 w-24" /></td>
								<td class="px-4 py-3"><Skeleton class="h-5 w-16 rounded-full" /></td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</Card.Content>
	</Card.Root>
</div>
