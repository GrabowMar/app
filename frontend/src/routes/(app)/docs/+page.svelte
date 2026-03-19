<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Input } from '$lib/components/ui/input';
	import Search from '@lucide/svelte/icons/search';
	import BookOpen from '@lucide/svelte/icons/book-open';
	import Rocket from '@lucide/svelte/icons/rocket';
	import Settings from '@lucide/svelte/icons/settings';
	import Code from '@lucide/svelte/icons/code';
	import ArrowRight from '@lucide/svelte/icons/arrow-right';
	import type { Component } from 'svelte';

	interface DocCategory {
		title: string;
		description: string;
		icon: Component;
		count: number;
		color: string;
	}

	const categories: DocCategory[] = [
		{ title: 'Getting Started', description: 'Installation, setup, and quickstart guides.', icon: Rocket, count: 4, color: 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/50' },
		{ title: 'Architecture', description: 'System design, components, and data flow.', icon: Code, count: 6, color: 'text-violet-600 dark:text-violet-400 bg-violet-50 dark:bg-violet-950/50' },
		{ title: 'User Guides', description: 'Step-by-step guides for features.', icon: BookOpen, count: 8, color: 'text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/50' },
		{ title: 'Configuration', description: 'Settings, environment variables, and tuning.', icon: Settings, count: 5, color: 'text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/50' },
	];
</script>

<svelte:head>
	<title>Documentation - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<div class="page-header">
		<h1>Documentation</h1>
		<p>Browse guides, references, and technical documentation.</p>
	</div>

	<div class="relative max-w-md">
		<Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
		<Input placeholder="Search documentation... (Ctrl+K)" class="pl-9" disabled />
	</div>

	<div class="grid gap-4 sm:grid-cols-2">
		{#each categories as cat (cat.title)}
			<Card.Root class="group hover:border-primary/30 cursor-pointer">
				<Card.Header>
					<div class="flex items-center gap-3">
						<div class="flex h-10 w-10 items-center justify-center rounded-lg {cat.color} transition-colors">
							<cat.icon class="h-5 w-5" />
						</div>
						<div class="flex-1">
							<div class="flex items-center justify-between">
								<Card.Title class="text-base">{cat.title}</Card.Title>
								<Badge variant="outline" class="text-xs">{cat.count} docs</Badge>
							</div>
						</div>
					</div>
				</Card.Header>
				<Card.Content>
					<div class="flex items-center justify-between">
						<p class="text-sm text-muted-foreground">{cat.description}</p>
						<ArrowRight class="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity shrink-0 ml-2" />
					</div>
				</Card.Content>
			</Card.Root>
		{/each}
	</div>
</div>
