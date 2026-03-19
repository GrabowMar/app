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
	import FileText from '@lucide/svelte/icons/file-text';
	import ExternalLink from '@lucide/svelte/icons/external-link';
	import type { Component } from 'svelte';

	let searchQuery = $state('');

	interface DocFile {
		title: string;
		description: string;
	}

	interface DocCategory {
		title: string;
		description: string;
		icon: Component;
		color: string;
		docs: DocFile[];
	}

	const categories: DocCategory[] = [
		{
			title: 'Getting Started',
			description: 'Installation, setup, and quickstart guides.',
			icon: Rocket,
			color: 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/50',
			docs: [
				{ title: 'Quickstart Guide', description: 'Get the platform running in 5 minutes with Docker Compose.' },
				{ title: 'Deployment Guide', description: 'Production deployment with Caddy, HTTPS, and reverse proxy.' },
				{ title: 'Development Setup', description: 'Local development environment with hot-reload and debugging.' },
				{ title: 'Troubleshooting', description: 'Common issues, error codes, and solutions.' },
			],
		},
		{
			title: 'Architecture',
			description: 'System design, components, and data flow.',
			icon: Code,
			color: 'text-violet-600 dark:text-violet-400 bg-violet-50 dark:bg-violet-950/50',
			docs: [
				{ title: 'System Architecture', description: 'Overview of Flask, Celery, Redis, and analyzer microservices.' },
				{ title: 'Analysis Pipeline', description: 'How tasks flow through the 4-stage analysis pipeline.' },
				{ title: 'Generation Process', description: 'Code generation via LLM APIs with scaffolding and validation.' },
				{ title: 'Docker Networking', description: 'Network topology for generated app containers and analyzers.' },
				{ title: 'WebSocket Protocol', description: 'Message contract between analyzers and the gateway.' },
				{ title: 'Models Reference', description: 'Supported LLM models, providers, and capability matrix.' },
			],
		},
		{
			title: 'User Guides',
			description: 'Step-by-step guides for platform features.',
			icon: BookOpen,
			color: 'text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/50',
			docs: [
				{ title: 'Managing Models', description: 'Add, configure, and compare LLM models.' },
				{ title: 'Generating Applications', description: 'Create apps from templates with customization options.' },
				{ title: 'Running Analyses', description: 'Configure and execute security, performance, and AI analysis.' },
				{ title: 'Automation Pipelines', description: 'Set up automated generate-analyze-report workflows.' },
				{ title: 'Reports & Rankings', description: 'Generate reports and understand the MSS scoring system.' },
				{ title: 'Background Services', description: 'Monitor Celery workers, task queues, and service health.' },
				{ title: 'Analyzer Guide', description: 'Deep dive into static, dynamic, performance, and AI analyzers.' },
				{ title: 'Template Specification', description: 'Create custom application requirement templates.' },
			],
		},
		{
			title: 'Configuration',
			description: 'Settings, environment variables, and tuning.',
			icon: Settings,
			color: 'text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/50',
			docs: [
				{ title: 'Environment Variables', description: 'Complete reference for .env configuration options.' },
				{ title: 'API Keys Setup', description: 'Configure OpenAI, Anthropic, Google, and other provider keys.' },
				{ title: 'Port Configuration', description: 'Default ports, dynamic allocation, and conflict resolution.' },
				{ title: 'Analyzer Configuration', description: 'Tune analyzer settings, timeouts, and resource limits.' },
				{ title: 'API Reference', description: 'REST API endpoints for programmatic access.' },
			],
		},
	];

	const filteredCategories = $derived(
		searchQuery === '' ? categories : categories.map(cat => ({
			...cat,
			docs: cat.docs.filter(d =>
				d.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
				d.description.toLowerCase().includes(searchQuery.toLowerCase())
			),
		})).filter(cat => cat.docs.length > 0)
	);

	const totalDocs = $derived(categories.reduce((sum, c) => sum + c.docs.length, 0));
</script>

<svelte:head>
	<title>Documentation - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-bold tracking-tight">Documentation</h1>
			<p class="mt-1 text-sm text-muted-foreground">Browse guides, references, and technical documentation.</p>
		</div>
		<Badge variant="outline" class="text-xs">{totalDocs} docs</Badge>
	</div>

	<div class="relative max-w-md">
		<Search class="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
		<Input bind:value={searchQuery} placeholder="Search documentation..." class="h-9 pl-8 text-sm" />
	</div>

	<div class="grid gap-6">
		{#each filteredCategories as cat (cat.title)}
			<Card.Root>
				<Card.Header>
					<div class="flex items-center gap-3">
						<div class="flex h-10 w-10 items-center justify-center rounded-lg {cat.color} transition-colors">
							<cat.icon class="h-5 w-5" />
						</div>
						<div class="flex-1">
							<div class="flex items-center justify-between">
								<Card.Title class="text-base">{cat.title}</Card.Title>
								<Badge variant="outline" class="text-xs">{cat.docs.length} docs</Badge>
							</div>
							<p class="text-sm text-muted-foreground">{cat.description}</p>
						</div>
					</div>
				</Card.Header>
				<Card.Content class="pt-0">
					<div class="grid gap-2 sm:grid-cols-2">
						{#each cat.docs as doc}
							<div class="group flex items-start gap-2.5 rounded-lg border p-3 cursor-pointer hover:bg-muted/50 transition-colors">
								<FileText class="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
								<div class="flex-1 min-w-0">
									<div class="flex items-center gap-1">
										<span class="text-sm font-medium group-hover:underline">{doc.title}</span>
										<ArrowRight class="h-3 w-3 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
									</div>
									<p class="text-xs text-muted-foreground line-clamp-1">{doc.description}</p>
								</div>
							</div>
						{/each}
					</div>
				</Card.Content>
			</Card.Root>
		{/each}
	</div>

	{#if filteredCategories.length === 0}
		<div class="flex flex-col items-center justify-center gap-2 py-12 text-muted-foreground">
			<Search class="h-8 w-8 text-muted-foreground/40" />
			<p class="text-sm">No documentation matches "{searchQuery}"</p>
		</div>
	{/if}

	<!-- External Resources -->
	<Card.Root>
		<Card.Header>
			<Card.Title class="text-sm">External Resources</Card.Title>
		</Card.Header>
		<Card.Content>
			<div class="flex flex-wrap gap-3">
				{#each [
					{ label: 'GitHub Repository', url: '#' },
					{ label: 'API Documentation', url: '#' },
					{ label: 'Issue Tracker', url: '#' },
					{ label: 'Changelog', url: '#' },
				] as link}
					<a href={link.url} class="inline-flex items-center gap-1 rounded-md border px-3 py-1.5 text-xs font-medium hover:bg-muted transition-colors">
						{link.label}
						<ExternalLink class="h-3 w-3" />
					</a>
				{/each}
			</div>
		</Card.Content>
	</Card.Root>
</div>
