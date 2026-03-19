<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import Code from '@lucide/svelte/icons/code';
	import Boxes from '@lucide/svelte/icons/boxes';
	import FileCode from '@lucide/svelte/icons/file-code';
	import SlidersHorizontal from '@lucide/svelte/icons/sliders-horizontal';
	import Sparkles from '@lucide/svelte/icons/sparkles';
	import ChevronRight from '@lucide/svelte/icons/chevron-right';
	import type { Component } from 'svelte';

	const steps: { title: string; description: string; icon: Component }[] = [
		{ title: 'Select Model', description: 'Choose the LLM to generate your app', icon: Boxes },
		{ title: 'Choose Template', description: 'Pick application type and requirements', icon: FileCode },
		{ title: 'Configure Options', description: 'Set parameters and constraints', icon: SlidersHorizontal },
		{ title: 'Generate', description: 'Build and deploy the application', icon: Sparkles },
	];
</script>

<svelte:head>
	<title>Sample Generator - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<div class="flex items-center justify-between">
		<div class="page-header">
			<h1>Sample Generator</h1>
			<p>Generate sample web applications using AI models.</p>
		</div>
		<Button disabled>
			<Code class="mr-2 h-4 w-4" />
			Generate
		</Button>
	</div>

	<Card.Root>
		<Card.Header>
			<Card.Title>Generator Wizard</Card.Title>
			<Card.Description>Select a model, template, and configuration to generate a new application.</Card.Description>
		</Card.Header>
		<Card.Content>
			<div class="space-y-2">
				{#each steps as step, i}
					<div class="flex items-center gap-3 rounded-lg border px-4 py-3 transition-colors hover:bg-muted/30">
						<div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg {i === 0 ? 'bg-blue-50 text-blue-600 dark:bg-blue-950/50 dark:text-blue-400' : 'bg-muted text-muted-foreground'} text-xs font-semibold">
							{i + 1}
						</div>
						<div class="flex-1 min-w-0">
							<p class="text-sm font-medium">{step.title}</p>
							<p class="text-xs text-muted-foreground">{step.description}</p>
						</div>
						<ChevronRight class="h-4 w-4 text-muted-foreground shrink-0" />
					</div>
				{/each}
			</div>
		</Card.Content>
	</Card.Root>
</div>
