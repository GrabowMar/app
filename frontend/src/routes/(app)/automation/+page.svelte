<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Skeleton } from '$lib/components/ui/skeleton';
	import { Button } from '$lib/components/ui/button';
	import Play from '@lucide/svelte/icons/play';
	import Settings from '@lucide/svelte/icons/settings';
	import Target from '@lucide/svelte/icons/target';
	import Rocket from '@lucide/svelte/icons/rocket';
	import type { Component } from 'svelte';

	const steps: { title: string; description: string; icon: Component }[] = [
		{ title: 'Configure Pipeline', description: 'Select analyzers, set thresholds, and define execution parameters.', icon: Settings },
		{ title: 'Select Targets', description: 'Choose models and applications to include in the pipeline run.', icon: Target },
		{ title: 'Review & Execute', description: 'Confirm settings and launch the automated analysis pipeline.', icon: Rocket },
	];
</script>

<svelte:head>
	<title>Automation - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<div class="flex items-center justify-between">
		<div class="page-header">
			<h1>Automation</h1>
			<p>Configure and run automated analysis pipelines.</p>
		</div>
		<Button disabled>
			<Play class="mr-2 h-4 w-4" />
			Run Pipeline
		</Button>
	</div>

	<div class="grid gap-4 lg:grid-cols-3">
		{#each steps as step, i}
			<Card.Root class="relative overflow-hidden">
				<div class="absolute left-0 top-0 bottom-0 w-1 {i === 0 ? 'bg-blue-500' : i === 1 ? 'bg-amber-500' : 'bg-emerald-500'}"></div>
				<Card.Header class="pl-5">
					<div class="flex items-center gap-3">
						<div class="flex h-8 w-8 items-center justify-center rounded-lg bg-muted text-sm font-semibold">
							{i + 1}
						</div>
						<Card.Title class="text-base">{step.title}</Card.Title>
					</div>
				</Card.Header>
				<Card.Content class="pl-5">
					<p class="text-sm text-muted-foreground">{step.description}</p>
				</Card.Content>
			</Card.Root>
		{/each}
	</div>
</div>
