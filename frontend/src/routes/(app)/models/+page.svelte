<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Skeleton } from '$lib/components/ui/skeleton';
	import Cpu from '@lucide/svelte/icons/cpu';
</script>

<svelte:head>
	<title>Models - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<div class="page-header">
		<h1>Models</h1>
		<p>Browse and manage AI models available for research.</p>
	</div>

	<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
		{#each Array(6) as _, i}
			<Card.Root class="group hover:border-primary/30">
				<Card.Header class="pb-3">
					<div class="flex items-center gap-3">
						<div class="flex h-9 w-9 items-center justify-center rounded-lg bg-muted group-hover:bg-primary/10 transition-colors">
							<Cpu class="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
						</div>
						<div class="flex-1 min-w-0">
							<Skeleton class="h-4 w-28" />
							<Skeleton class="mt-1.5 h-3 w-20" />
						</div>
					</div>
				</Card.Header>
				<Card.Content class="pt-0">
					<div class="space-y-2">
						<Skeleton class="h-3 w-full" />
						<Skeleton class="h-3 w-3/4" />
					</div>
					<div class="mt-3 flex gap-1.5">
						<Badge variant="outline" class="text-[10px] px-1.5 py-0">API</Badge>
						<Badge variant="outline" class="text-[10px] px-1.5 py-0">Code</Badge>
					</div>
				</Card.Content>
			</Card.Root>
		{/each}
	</div>
</div>
