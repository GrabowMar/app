<script lang="ts">
	import { getAuth } from '$lib/stores/auth.svelte';
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { Skeleton } from '$lib/components/ui/skeleton';
	import { Separator } from '$lib/components/ui/separator';
	import BarChart3 from '@lucide/svelte/icons/bar-chart-3';
	import Boxes from '@lucide/svelte/icons/boxes';
	import AppWindow from '@lucide/svelte/icons/app-window';
	import FileText from '@lucide/svelte/icons/file-text';
	import ArrowRight from '@lucide/svelte/icons/arrow-right';
	import Activity from '@lucide/svelte/icons/activity';
	import CircleCheck from '@lucide/svelte/icons/circle-check';
	import CircleX from '@lucide/svelte/icons/circle-x';
	import Clock from '@lucide/svelte/icons/clock';
	import type { Component } from 'svelte';

	const auth = getAuth();

	interface SummaryCard {
		title: string;
		value: string;
		subtitle: string;
		icon: Component;
		href: string;
		color: string;
	}

	const summaryCards: SummaryCard[] = [
		{ title: 'Models', value: '—', subtitle: 'Registered models', icon: Boxes, href: '/models', color: 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/50' },
		{ title: 'Applications', value: '—', subtitle: 'Generated apps', icon: AppWindow, href: '/applications', color: 'text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/50' },
		{ title: 'Analyses', value: '—', subtitle: 'Tasks completed', icon: BarChart3, href: '/analysis', color: 'text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/50' },
		{ title: 'Reports', value: '—', subtitle: 'Generated reports', icon: FileText, href: '/reports', color: 'text-violet-600 dark:text-violet-400 bg-violet-50 dark:bg-violet-950/50' },
	];

	interface ServiceStatus {
		name: string;
		status: 'online' | 'offline' | 'pending';
	}

	const services: ServiceStatus[] = [
		{ name: 'API Server', status: 'online' },
		{ name: 'Celery Worker', status: 'pending' },
		{ name: 'Static Analyzer', status: 'pending' },
		{ name: 'Dynamic Analyzer', status: 'pending' },
	];
</script>

<svelte:head>
	<title>Dashboard - LLM Lab</title>
</svelte:head>

<div class="space-y-8">
	<div class="page-header">
		<h1>Dashboard</h1>
		<p>
			{#if auth.isAuthenticated && auth.user}
				Welcome back, {auth.user.display || auth.user.email}.
			{:else}
				Your research platform overview.
			{/if}
		</p>
	</div>

	<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
		{#each summaryCards as card (card.title)}
			<a href={card.href} class="group block">
				<Card.Root class="relative overflow-hidden hover:border-primary/30">
					<Card.Header class="flex flex-row items-center justify-between space-y-0 pb-2">
						<Card.Title class="text-sm font-medium text-muted-foreground">{card.title}</Card.Title>
						<div class="flex h-8 w-8 items-center justify-center rounded-lg {card.color}">
							<card.icon class="h-4 w-4" />
						</div>
					</Card.Header>
					<Card.Content>
						<div class="text-2xl font-bold">{card.value}</div>
						<p class="text-xs text-muted-foreground mt-1">{card.subtitle}</p>
					</Card.Content>
					<div class="absolute bottom-3 right-4 opacity-0 transition-opacity group-hover:opacity-100">
						<ArrowRight class="h-4 w-4 text-muted-foreground" />
					</div>
				</Card.Root>
			</a>
		{/each}
	</div>

	<div class="grid gap-6 lg:grid-cols-7">
		<Card.Root class="lg:col-span-4">
			<Card.Header>
				<div class="flex items-center justify-between">
					<div>
						<Card.Title>Recent Analyses</Card.Title>
						<Card.Description>Latest analysis tasks and their status.</Card.Description>
					</div>
					<Button variant="ghost" size="sm" href="/analysis" class="text-xs">
						View all
						<ArrowRight class="ml-1 h-3 w-3" />
					</Button>
				</div>
			</Card.Header>
			<Card.Content>
				<div class="space-y-1">
					{#each Array(4) as _, i}
						<div class="flex items-center gap-3 rounded-lg px-3 py-2.5 transition-colors hover:bg-muted/50">
							<div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted">
								<Activity class="h-4 w-4 text-muted-foreground" />
							</div>
							<div class="flex-1 min-w-0">
								<Skeleton class="h-3.5 w-36" />
								<Skeleton class="mt-1.5 h-2.5 w-24" />
							</div>
							<Skeleton class="h-5 w-16 rounded-full" />
						</div>
					{/each}
				</div>
			</Card.Content>
		</Card.Root>

		<Card.Root class="lg:col-span-3">
			<Card.Header>
				<Card.Title>System Status</Card.Title>
				<Card.Description>Service health overview.</Card.Description>
			</Card.Header>
			<Card.Content>
				<div class="space-y-3">
					{#each services as svc (svc.name)}
						<div class="flex items-center justify-between">
							<div class="flex items-center gap-2.5">
								{#if svc.status === 'online'}
									<CircleCheck class="h-4 w-4 text-emerald-500" />
								{:else if svc.status === 'offline'}
									<CircleX class="h-4 w-4 text-destructive" />
								{:else}
									<Clock class="h-4 w-4 text-muted-foreground" />
								{/if}
								<span class="text-sm">{svc.name}</span>
							</div>
							<Badge variant={svc.status === 'online' ? 'secondary' : 'outline'} class="text-xs capitalize">
								{svc.status}
							</Badge>
						</div>
						{#if svc !== services[services.length - 1]}
							<Separator />
						{/if}
					{/each}
				</div>
			</Card.Content>
		</Card.Root>
	</div>
</div>
