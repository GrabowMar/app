<script lang="ts">
	import { getAuth } from '$lib/stores/auth.svelte';
	import * as Card from '$lib/components/ui/card';
	import { Button } from '$lib/components/ui/button';
	import { Skeleton } from '$lib/components/ui/skeleton';
	import BarChart3 from '@lucide/svelte/icons/bar-chart-3';
	import Boxes from '@lucide/svelte/icons/boxes';
	import AppWindow from '@lucide/svelte/icons/app-window';
	import FileText from '@lucide/svelte/icons/file-text';

	const auth = getAuth();

	const summaryCards = [
		{ title: 'Models', value: '--', icon: Boxes, href: '/models' },
		{ title: 'Applications', value: '--', icon: AppWindow, href: '/applications' },
		{ title: 'Analyses', value: '--', icon: BarChart3, href: '/analysis' },
		{ title: 'Reports', value: '--', icon: FileText, href: '/reports' },
	];
</script>

<svelte:head>
	<title>Dashboard - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<div>
		<h1 class="text-2xl font-bold tracking-tight">Dashboard</h1>
		<p class="text-muted-foreground">
			{#if auth.isAuthenticated && auth.user}
				Welcome back, {auth.user.display || auth.user.email}.
			{:else}
				Your research platform overview.
			{/if}
		</p>
	</div>

	<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
		{#each summaryCards as card (card.title)}
			<a href={card.href} class="block">
				<Card.Root
					class="transition-colors hover:border-primary/50"
				>
					<Card.Header class="flex flex-row items-center justify-between space-y-0 pb-2">
						<Card.Title class="text-sm font-medium">{card.title}</Card.Title>
						<card.icon class="h-4 w-4 text-muted-foreground" />
					</Card.Header>
					<Card.Content>
						<Skeleton class="h-8 w-16" />
					</Card.Content>
				</Card.Root>
			</a>
		{/each}
	</div>

	<div class="grid gap-4 lg:grid-cols-2">
		<Card.Root>
			<Card.Header>
				<Card.Title>Recent Analyses</Card.Title>
				<Card.Description>Latest analysis tasks and their status.</Card.Description>
			</Card.Header>
			<Card.Content>
				<div class="space-y-3">
					{#each Array(3) as _}
						<div class="flex items-center gap-3">
							<Skeleton class="h-4 w-4 rounded-full" />
							<Skeleton class="h-4 flex-1" />
							<Skeleton class="h-4 w-16" />
						</div>
					{/each}
				</div>
			</Card.Content>
		</Card.Root>

		<Card.Root>
			<Card.Header>
				<Card.Title>System Status</Card.Title>
				<Card.Description>Current system health and service status.</Card.Description>
			</Card.Header>
			<Card.Content>
				<div class="space-y-3">
					{#each Array(4) as _}
						<div class="flex items-center justify-between">
							<Skeleton class="h-4 w-24" />
							<Skeleton class="h-5 w-16 rounded-full" />
						</div>
					{/each}
				</div>
			</Card.Content>
		</Card.Root>
	</div>
</div>
