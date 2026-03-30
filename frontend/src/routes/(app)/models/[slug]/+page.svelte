<script lang="ts">
	import { page } from '$app/stores';
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { Separator } from '$lib/components/ui/separator';
	import Cpu from '@lucide/svelte/icons/cpu';
	import ArrowLeft from '@lucide/svelte/icons/arrow-left';
	import CircleCheck from '@lucide/svelte/icons/circle-check';
	import GitCompareArrows from '@lucide/svelte/icons/git-compare-arrows';
	import RefreshCw from '@lucide/svelte/icons/refresh-cw';
	import AppWindow from '@lucide/svelte/icons/app-window';
	import BarChart3 from '@lucide/svelte/icons/bar-chart-3';
	import DollarSign from '@lucide/svelte/icons/dollar-sign';
	import Layers from '@lucide/svelte/icons/layers';
	import Clock from '@lucide/svelte/icons/clock';
	import Check from '@lucide/svelte/icons/check';
	import X from '@lucide/svelte/icons/x';
	import Sparkles from '@lucide/svelte/icons/sparkles';

	const slug = $derived($page.params.slug ?? '');

	interface ModelData {
		name: string;
		provider: string;
		contextWindow: string;
		inputPrice: string;
		outputPrice: string;
		status: string;
		description: string;
		capabilities: { name: string; supported: boolean }[];
		metrics: { label: string; value: string; subtitle: string }[];
		apps: { name: string; number: number; status: string; analyses: number; created: string }[];
		metadata: Record<string, string>;
	}

	const modelMap: Record<string, ModelData> = {
		'gpt-4o': {
			name: 'GPT-4o', provider: 'OpenAI', contextWindow: '128K', inputPrice: '$2.50', outputPrice: '$10.00', status: 'active',
			description: 'GPT-4o is OpenAI\'s most capable multimodal model. It accepts text, image, and audio inputs and produces text and audio outputs. It excels at code generation, reasoning, and creative tasks.',
			capabilities: [
				{ name: 'Code Generation', supported: true }, { name: 'Chat', supported: true }, { name: 'Vision', supported: true },
				{ name: 'Function Calling', supported: true }, { name: 'JSON Mode', supported: true }, { name: 'Streaming', supported: true },
				{ name: 'System Prompts', supported: true }, { name: 'Audio', supported: true }, { name: 'Fine-tuning', supported: false },
			],
			metrics: [
				{ label: 'Total Apps', value: '24', subtitle: 'Generated' },
				{ label: 'Analyses Run', value: '67', subtitle: 'Completed' },
				{ label: 'Avg Score', value: '78.3', subtitle: 'Out of 100' },
				{ label: 'Cost Efficiency', value: 'A-', subtitle: 'Rating' },
				{ label: 'Avg Gen Time', value: '34s', subtitle: 'Per app' },
				{ label: 'Success Rate', value: '95.8%', subtitle: 'Generation' },
			],
			apps: [
				{ name: 'Task Manager', number: 1, status: 'running', analyses: 5, created: '2 days ago' },
				{ name: 'E-Commerce Store', number: 2, status: 'running', analyses: 3, created: '5 days ago' },
				{ name: 'Blog Platform', number: 3, status: 'stopped', analyses: 8, created: '1 week ago' },
				{ name: 'Chat App', number: 4, status: 'running', analyses: 2, created: '2 weeks ago' },
			],
			metadata: { 'Model ID': 'gpt-4o-2024-08-06', 'Architecture': 'Transformer (GPT-4 Turbo)', 'Training Cutoff': 'October 2023', 'Max Output Tokens': '16,384', 'API Version': '2024-08-06', 'Created': '2024-05-13' },
		},
	};

	const defaultModel: ModelData = {
		name: slug.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase()), provider: 'Unknown', contextWindow: '128K', inputPrice: '$1.00', outputPrice: '$3.00', status: 'active',
		description: 'A large language model optimized for code generation and analysis tasks.',
		capabilities: [
			{ name: 'Code Generation', supported: true }, { name: 'Chat', supported: true }, { name: 'Vision', supported: false },
			{ name: 'Function Calling', supported: true }, { name: 'JSON Mode', supported: true }, { name: 'Streaming', supported: true },
			{ name: 'System Prompts', supported: true }, { name: 'Audio', supported: false }, { name: 'Fine-tuning', supported: false },
		],
		metrics: [
			{ label: 'Total Apps', value: '12', subtitle: 'Generated' },
			{ label: 'Analyses Run', value: '34', subtitle: 'Completed' },
			{ label: 'Avg Score', value: '72.1', subtitle: 'Out of 100' },
			{ label: 'Cost Efficiency', value: 'B+', subtitle: 'Rating' },
			{ label: 'Avg Gen Time', value: '28s', subtitle: 'Per app' },
			{ label: 'Success Rate', value: '91.2%', subtitle: 'Generation' },
		],
		apps: [
			{ name: 'App 1', number: 1, status: 'running', analyses: 3, created: '3 days ago' },
			{ name: 'App 2', number: 2, status: 'stopped', analyses: 1, created: '1 week ago' },
		],
		metadata: { 'Model ID': slug, 'Architecture': 'Transformer', 'Training Cutoff': 'Unknown', 'Max Output Tokens': '8,192', 'Created': 'Unknown' },
	};

	const model = $derived(modelMap[slug] ?? defaultModel);

	const sections = ['overview', 'capabilities', 'pricing', 'applications', 'metadata'] as const;
	let activeSection = $state<string>('overview');

	function scrollToSection(id: string) {
		activeSection = id;
		document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
	}

	const statusColors: Record<string, string> = {
		running: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400',
		stopped: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400',
		building: 'bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-400',
		failed: 'bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-400',
	};
</script>

<svelte:head>
	<title>{model.name} - Models - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<!-- Breadcrumb -->
	<div class="flex items-center gap-2 text-sm text-muted-foreground">
		<Button variant="ghost" size="sm" href="/models" class="gap-1.5 px-2">
			<ArrowLeft class="h-3.5 w-3.5" />
			Models
		</Button>
		<span>/</span>
		<span class="text-foreground font-medium">{model.name}</span>
	</div>

	<!-- Header Bar -->
	<Card.Root>
		<Card.Content class="py-4">
			<div class="flex flex-wrap items-center gap-4">
				<div class="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
					<Cpu class="h-6 w-6 text-primary" />
				</div>
				<div class="flex-1 min-w-0">
					<div class="flex items-center gap-2">
						<h2 class="text-xl font-bold">{model.name}</h2>
						<Badge variant="secondary">{model.provider}</Badge>
						<Badge variant="secondary" class="gap-1 text-emerald-600 dark:text-emerald-400">
							<CircleCheck class="h-3 w-3" />
							{model.status}
						</Badge>
					</div>
				</div>
				<div class="flex items-center gap-4 text-sm">
					<div class="text-center">
						<div class="font-semibold">{model.contextWindow}</div>
						<div class="text-xs text-muted-foreground">Context</div>
					</div>
					<Separator orientation="vertical" class="h-8" />
					<div class="text-center">
						<div class="font-semibold">{model.inputPrice}</div>
						<div class="text-xs text-muted-foreground">Input/1M</div>
					</div>
					<Separator orientation="vertical" class="h-8" />
					<div class="text-center">
						<div class="font-semibold">{model.metrics[0].value}</div>
						<div class="text-xs text-muted-foreground">Apps</div>
					</div>
				</div>
				<div class="flex items-center gap-2">
					<Button variant="outline" size="sm" disabled>
						<Sparkles class="mr-2 h-3.5 w-3.5" />
						Generate App
					</Button>
					<Button variant="outline" size="sm" href="/models/compare?models={slug}">
						<GitCompareArrows class="mr-2 h-3.5 w-3.5" />
						Compare
					</Button>
					<Button variant="ghost" size="icon" class="h-8 w-8" disabled>
						<RefreshCw class="h-3.5 w-3.5" />
					</Button>
				</div>
			</div>
		</Card.Content>
	</Card.Root>

	<!-- Metric Grid -->
	<div class="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-6">
		{#each model.metrics as metric (metric.label)}
			<Card.Root>
				<Card.Content class="p-3 text-center">
					<div class="text-lg font-bold">{metric.value}</div>
					<div class="text-xs font-medium text-muted-foreground">{metric.label}</div>
					<div class="text-[10px] text-muted-foreground/70">{metric.subtitle}</div>
				</Card.Content>
			</Card.Root>
		{/each}
	</div>

	<!-- Section Navigation -->
	<div class="sticky top-0 z-10 -mx-1 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b">
		<div class="flex gap-1 px-1 py-1 overflow-x-auto">
			{#each sections as section}
				<Button
					variant={activeSection === section ? 'secondary' : 'ghost'}
					size="sm"
					class="text-xs capitalize whitespace-nowrap"
					onclick={() => scrollToSection(section)}
				>
					{section}
				</Button>
			{/each}
		</div>
	</div>

	<!-- Overview Section -->
	<div id="overview">
		<Card.Root>
			<Card.Header>
				<Card.Title>Overview</Card.Title>
			</Card.Header>
			<Card.Content>
				<p class="text-sm text-muted-foreground leading-relaxed">{model.description}</p>
			</Card.Content>
		</Card.Root>
	</div>

	<!-- Capabilities Section -->
	<div id="capabilities">
		<Card.Root>
			<Card.Header>
				<Card.Title>Capabilities</Card.Title>
				<Card.Description>Features supported by this model.</Card.Description>
			</Card.Header>
			<Card.Content>
				<div class="grid grid-cols-2 gap-2 sm:grid-cols-3">
					{#each model.capabilities as cap (cap.name)}
						<div class="flex items-center gap-2 rounded-lg border px-3 py-2 {cap.supported ? '' : 'opacity-50'}">
							{#if cap.supported}
								<Check class="h-4 w-4 text-emerald-500" />
							{:else}
								<X class="h-4 w-4 text-muted-foreground" />
							{/if}
							<span class="text-sm">{cap.name}</span>
						</div>
					{/each}
				</div>
			</Card.Content>
		</Card.Root>
	</div>

	<!-- Pricing Section -->
	<div id="pricing">
		<Card.Root>
			<Card.Header>
				<div class="flex items-center gap-2">
					<DollarSign class="h-4 w-4 text-muted-foreground" />
					<Card.Title>Pricing Information</Card.Title>
				</div>
			</Card.Header>
			<Card.Content class="p-0">
				<table class="w-full">
					<thead>
						<tr class="border-b bg-muted/30">
							<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Type</th>
							<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Price per 1M tokens</th>
							<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Price per 1K tokens</th>
						</tr>
					</thead>
					<tbody class="divide-y">
						<tr class="hover:bg-muted/30">
							<td class="px-4 py-2.5 text-sm font-medium">Input</td>
							<td class="px-4 py-2.5 text-sm font-mono">{model.inputPrice}</td>
							<td class="px-4 py-2.5 text-sm font-mono text-muted-foreground">${(parseFloat(model.inputPrice.replace('$', '')) / 1000).toFixed(6)}</td>
						</tr>
						<tr class="hover:bg-muted/30">
							<td class="px-4 py-2.5 text-sm font-medium">Output</td>
							<td class="px-4 py-2.5 text-sm font-mono">{model.outputPrice}</td>
							<td class="px-4 py-2.5 text-sm font-mono text-muted-foreground">${(parseFloat(model.outputPrice.replace('$', '')) / 1000).toFixed(6)}</td>
						</tr>
					</tbody>
				</table>
			</Card.Content>
		</Card.Root>
	</div>

	<!-- Applications Section -->
	<div id="applications">
		<Card.Root>
			<Card.Header>
				<div class="flex items-center justify-between">
					<div class="flex items-center gap-2">
						<AppWindow class="h-4 w-4 text-muted-foreground" />
						<Card.Title>Applications</Card.Title>
					</div>
					<Badge variant="outline">{model.apps.length} apps</Badge>
				</div>
			</Card.Header>
			<Card.Content class="p-0">
				<table class="w-full">
					<thead>
						<tr class="border-b bg-muted/30">
							<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Application</th>
							<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Status</th>
							<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Analyses</th>
							<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Created</th>
						</tr>
					</thead>
					<tbody class="divide-y">
						{#each model.apps as app (app.number)}
							<tr class="transition-colors hover:bg-muted/30">
								<td class="px-4 py-2.5">
									<a href="/applications/{slug}/{app.number}" class="text-sm font-medium hover:text-primary transition-colors">
										{app.name} (App #{app.number})
									</a>
								</td>
								<td class="px-4 py-2.5">
									<span class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium {statusColors[app.status] ?? ''}">
										{app.status}
									</span>
								</td>
								<td class="px-4 py-2.5 text-sm">{app.analyses}</td>
								<td class="px-4 py-2.5 text-sm text-muted-foreground">{app.created}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</Card.Content>
		</Card.Root>
	</div>

	<!-- Metadata Section -->
	<div id="metadata">
		<Card.Root>
			<Card.Header>
				<div class="flex items-center gap-2">
					<Layers class="h-4 w-4 text-muted-foreground" />
					<Card.Title>Metadata</Card.Title>
				</div>
			</Card.Header>
			<Card.Content>
				<dl class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
					{#each Object.entries(model.metadata) as [key, value]}
						<div class="rounded-lg border px-3 py-2">
							<dt class="text-xs text-muted-foreground">{key}</dt>
							<dd class="text-sm font-medium font-mono">{value}</dd>
						</div>
					{/each}
				</dl>
			</Card.Content>
		</Card.Root>
	</div>

	<!-- Usage Analytics Placeholder -->
	<Card.Root>
		<Card.Header>
			<div class="flex items-center justify-between">
				<div class="flex items-center gap-2">
					<BarChart3 class="h-4 w-4 text-muted-foreground" />
					<Card.Title>Usage Analytics</Card.Title>
				</div>
				<Badge variant="outline">Coming Soon</Badge>
			</div>
		</Card.Header>
		<Card.Content>
			<div class="flex h-48 flex-col items-center justify-center gap-2 rounded-lg border border-dashed bg-muted/20">
				<BarChart3 class="h-8 w-8 text-muted-foreground/40" />
				<p class="text-sm text-muted-foreground">Usage analytics will appear here</p>
			</div>
		</Card.Content>
	</Card.Root>
</div>
