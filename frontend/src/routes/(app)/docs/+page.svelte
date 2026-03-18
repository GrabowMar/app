<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Input } from '$lib/components/ui/input';
	import Search from '@lucide/svelte/icons/search';
	import BookOpen from '@lucide/svelte/icons/book-open';
	import Rocket from '@lucide/svelte/icons/rocket';
	import Settings from '@lucide/svelte/icons/settings';
	import Code from '@lucide/svelte/icons/code';
	import type { Component } from 'svelte';

	interface DocCategory {
		title: string;
		description: string;
		icon: Component;
		count: number;
	}

	const categories: DocCategory[] = [
		{ title: 'Getting Started', description: 'Installation, setup, and quickstart guides.', icon: Rocket, count: 4 },
		{ title: 'Architecture', description: 'System design, components, and data flow.', icon: Code, count: 6 },
		{ title: 'User Guides', description: 'Step-by-step guides for features.', icon: BookOpen, count: 8 },
		{ title: 'Configuration', description: 'Settings, environment variables, and tuning.', icon: Settings, count: 5 },
	];
</script>

<svelte:head>
	<title>Documentation - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<div>
		<h1 class="text-2xl font-bold tracking-tight">Documentation</h1>
		<p class="text-muted-foreground">Browse guides, references, and technical documentation.</p>
	</div>

	<div class="relative max-w-md">
		<Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
		<Input placeholder="Search documentation... (Ctrl+K)" class="pl-9" disabled />
	</div>

	<div class="grid gap-4 sm:grid-cols-2">
		{#each categories as cat (cat.title)}
			<Card.Root class="transition-colors hover:border-primary/50">
				<Card.Header>
					<div class="flex items-center gap-3">
						<div class="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
							<cat.icon class="h-5 w-5 text-muted-foreground" />
						</div>
						<div class="flex-1">
							<div class="flex items-center justify-between">
								<Card.Title class="text-base">{cat.title}</Card.Title>
								<Badge variant="secondary">{cat.count} docs</Badge>
							</div>
						</div>
					</div>
				</Card.Header>
				<Card.Content>
					<p class="text-sm text-muted-foreground">{cat.description}</p>
				</Card.Content>
			</Card.Root>
		{/each}
	</div>

	<div class="flex justify-center">
		<Badge variant="secondary" class="text-sm">Full documentation coming soon</Badge>
	</div>
</div>
