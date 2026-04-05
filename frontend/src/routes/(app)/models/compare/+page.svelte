<script lang="ts">
	import { page } from '$app/stores';
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { Separator } from '$lib/components/ui/separator';
	import ArrowLeft from '@lucide/svelte/icons/arrow-left';
	import Cpu from '@lucide/svelte/icons/cpu';
	import Check from '@lucide/svelte/icons/check';
	import X from '@lucide/svelte/icons/x';
	import Link from '@lucide/svelte/icons/link';
	import Settings from '@lucide/svelte/icons/settings';

	interface CompareModel {
		slug: string;
		name: string;
		provider: string;
		contextWindow: string;
		inputPrice: number;
		outputPrice: number;
		appsGenerated: number;
		avgScore: number;
		successRate: string;
		capabilities: Record<string, boolean>;
	}

	const allModels: CompareModel[] = [
		{ slug: 'gpt-4o', name: 'GPT-4o', provider: 'OpenAI', contextWindow: '128K', inputPrice: 2.50, outputPrice: 10.00, appsGenerated: 24, avgScore: 78.3, successRate: '95.8%', capabilities: { 'Code': true, 'Chat': true, 'Vision': true, 'Function Calling': true, 'JSON Mode': true, 'Audio': true, 'Fine-tuning': false } },
		{ slug: 'claude-3-5-sonnet', name: 'Claude 3.5 Sonnet', provider: 'Anthropic', contextWindow: '200K', inputPrice: 3.00, outputPrice: 15.00, appsGenerated: 22, avgScore: 82.1, successRate: '93.2%', capabilities: { 'Code': true, 'Chat': true, 'Vision': true, 'Function Calling': true, 'JSON Mode': true, 'Audio': false, 'Fine-tuning': false } },
		{ slug: 'gemini-1-5-pro', name: 'Gemini 1.5 Pro', provider: 'Google', contextWindow: '2M', inputPrice: 1.25, outputPrice: 5.00, appsGenerated: 20, avgScore: 74.5, successRate: '90.1%', capabilities: { 'Code': true, 'Chat': true, 'Vision': true, 'Function Calling': true, 'JSON Mode': true, 'Audio': false, 'Fine-tuning': false } },
	];

	const queryModels = $derived($page.url.searchParams.get('models')?.split(',').filter(Boolean) ?? []);
	const compareModels = $derived(
		queryModels.length > 0
			? allModels.filter(m => queryModels.includes(m.slug))
			: allModels
	);

	let baseline = $state<'average' | 'median'>('average');
	let highlightSlug = $state('');
	let normalize = $state(false);

	const allCapabilities = $derived([...new Set(compareModels.flatMap(m => Object.keys(m.capabilities)))]);
	const avgInput = $derived(compareModels.reduce((s, m) => s + m.inputPrice, 0) / compareModels.length);
	const avgOutput = $derived(compareModels.reduce((s, m) => s + m.outputPrice, 0) / compareModels.length);
</script>

<svelte:head>
	<title>Model Comparison - LLM Lab</title>
</svelte:head>

<div class="space-y-4 sm:space-y-6">
	<!-- Breadcrumb -->
	<div class="flex items-center gap-2 text-sm text-muted-foreground">
		<Button variant="ghost" size="sm" href="/models" class="gap-1.5 px-2">
			<ArrowLeft class="h-3.5 w-3.5" />
			Models
		</Button>
		<span>/</span>
		<span class="text-foreground font-medium">Comparison</span>
	</div>

	<div class="page-header">
		<h1>Model Comparison</h1>
		<p>Side-by-side comparison of {compareModels.length} models.</p>
	</div>

	<!-- Settings -->
	<Card.Root>
		<Card.Header>
			<div class="flex items-center gap-2">
				<Settings class="h-4 w-4 text-muted-foreground" />
				<Card.Title>Comparison Settings</Card.Title>
			</div>
		</Card.Header>
		<Card.Content>
			<div class="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center sm:gap-4">
				<div class="flex items-center gap-2">
					<label class="text-sm font-medium">Baseline:</label>
					<select class="h-8 rounded-md border border-input bg-background px-2 text-sm" bind:value={baseline}>
						<option value="average">Average</option>
						<option value="median">Median</option>
					</select>
				</div>
				<div class="flex items-center gap-2">
					<label class="text-sm font-medium">Highlight:</label>
					<select class="h-8 rounded-md border border-input bg-background px-2 text-sm" bind:value={highlightSlug}>
						<option value="">None</option>
						{#each compareModels as m}
							<option value={m.slug}>{m.name}</option>
						{/each}
					</select>
				</div>
				<div class="flex items-center gap-2">
					<input type="checkbox" id="normalize" bind:checked={normalize} class="rounded" />
					<label for="normalize" class="text-sm">Normalize values</label>
				</div>
				<div class="sm:ml-auto">
					<Button variant="outline" size="sm" disabled>
						<Link class="mr-2 h-3.5 w-3.5" />
						Share Link
					</Button>
				</div>
			</div>
			<Separator class="my-3" />
			<div class="flex flex-wrap gap-1.5">
				{#each compareModels as m (m.slug)}
					<Badge variant="secondary" class="gap-1.5">
						<Cpu class="h-3 w-3" />
						{m.name}
					</Badge>
				{/each}
			</div>
		</Card.Content>
	</Card.Root>

	<!-- Core Metrics Matrix -->
	<Card.Root>
		<Card.Header>
			<Card.Title>Core Metrics</Card.Title>
		</Card.Header>
		<Card.Content class="p-0">
			<div class="hidden md:block overflow-x-auto">
				<table class="w-full">
					<thead>
						<tr class="border-b bg-muted/30">
							<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Metric</th>
							{#each compareModels as m (m.slug)}
								<th class="px-4 py-3 text-left text-xs font-medium {highlightSlug === m.slug ? 'text-primary' : 'text-muted-foreground'}">{m.name}</th>
							{/each}
						</tr>
					</thead>
					<tbody class="divide-y">
						<tr class="hover:bg-muted/30">
							<td class="px-4 py-2.5 text-sm font-medium">Provider</td>
							{#each compareModels as m}<td class="px-4 py-2.5 text-sm">{m.provider}</td>{/each}
						</tr>
						<tr class="hover:bg-muted/30">
							<td class="px-4 py-2.5 text-sm font-medium">Context Window</td>
							{#each compareModels as m}<td class="px-4 py-2.5 text-sm font-mono">{m.contextWindow}</td>{/each}
						</tr>
						<tr class="hover:bg-muted/30">
							<td class="px-4 py-2.5 text-sm font-medium">Input $/1M tokens</td>
							{#each compareModels as m}<td class="px-4 py-2.5 text-sm font-mono">${m.inputPrice.toFixed(2)}</td>{/each}
						</tr>
						<tr class="hover:bg-muted/30">
							<td class="px-4 py-2.5 text-sm font-medium">Output $/1M tokens</td>
							{#each compareModels as m}<td class="px-4 py-2.5 text-sm font-mono">${m.outputPrice.toFixed(2)}</td>{/each}
						</tr>
						<tr class="hover:bg-muted/30">
							<td class="px-4 py-2.5 text-sm font-medium">Apps Generated</td>
							{#each compareModels as m}<td class="px-4 py-2.5 text-sm font-semibold">{m.appsGenerated}</td>{/each}
						</tr>
						<tr class="hover:bg-muted/30">
							<td class="px-4 py-2.5 text-sm font-medium">Avg Score</td>
							{#each compareModels as m}<td class="px-4 py-2.5 text-sm font-semibold">{m.avgScore}</td>{/each}
						</tr>
						<tr class="hover:bg-muted/30">
							<td class="px-4 py-2.5 text-sm font-medium">Success Rate</td>
							{#each compareModels as m}<td class="px-4 py-2.5 text-sm">{m.successRate}</td>{/each}
						</tr>
					</tbody>
				</table>
			</div>
			<!-- Mobile card view -->
			<div class="md:hidden space-y-3 p-4">
				{#each compareModels as m (m.slug)}
					<div class="rounded-lg border p-4 {highlightSlug === m.slug ? 'border-primary' : ''}">
						<div class="flex items-center gap-2 mb-3">
							<Cpu class="h-4 w-4 text-primary" />
							<span class="font-medium">{m.name}</span>
							<Badge variant="secondary" class="text-xs">{m.provider}</Badge>
						</div>
						<div class="grid grid-cols-2 gap-2 text-sm">
							<div>
								<div class="text-xs text-muted-foreground">Context Window</div>
								<div class="font-mono">{m.contextWindow}</div>
							</div>
							<div>
								<div class="text-xs text-muted-foreground">Input $/1M tokens</div>
								<div class="font-mono">${m.inputPrice.toFixed(2)}</div>
							</div>
							<div>
								<div class="text-xs text-muted-foreground">Output $/1M tokens</div>
								<div class="font-mono">${m.outputPrice.toFixed(2)}</div>
							</div>
							<div>
								<div class="text-xs text-muted-foreground">Apps Generated</div>
								<div class="font-semibold">{m.appsGenerated}</div>
							</div>
							<div>
								<div class="text-xs text-muted-foreground">Avg Score</div>
								<div class="font-semibold">{m.avgScore}</div>
							</div>
							<div>
								<div class="text-xs text-muted-foreground">Success Rate</div>
								<div>{m.successRate}</div>
							</div>
						</div>
					</div>
				{/each}
			</div>
		</Card.Content>
	</Card.Root>

	<!-- Pricing Deltas -->
	<Card.Root>
		<Card.Header>
			<Card.Title>Pricing Deltas</Card.Title>
			<Card.Description>Price difference compared to {compareModels[0]?.name ?? 'first model'}.</Card.Description>
		</Card.Header>
		<Card.Content class="p-0">
			<div class="overflow-x-auto">
				<table class="w-full">
					<thead>
						<tr class="border-b bg-muted/30">
							<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Type</th>
							{#each compareModels as m (m.slug)}
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">{m.name}</th>
							{/each}
						</tr>
					</thead>
					<tbody class="divide-y">
						<tr class="hover:bg-muted/30">
							<td class="px-4 py-2.5 text-sm font-medium">Input Delta</td>
							{#each compareModels as m, i}
								<td class="px-4 py-2.5 text-sm font-mono {i === 0 ? '' : m.inputPrice > compareModels[0].inputPrice ? 'text-red-500' : 'text-emerald-500'}">
									{i === 0 ? '—' : (m.inputPrice - compareModels[0].inputPrice > 0 ? '+' : '') + (m.inputPrice - compareModels[0].inputPrice).toFixed(2)}
								</td>
							{/each}
						</tr>
						<tr class="hover:bg-muted/30">
							<td class="px-4 py-2.5 text-sm font-medium">Output Delta</td>
							{#each compareModels as m, i}
								<td class="px-4 py-2.5 text-sm font-mono {i === 0 ? '' : m.outputPrice > compareModels[0].outputPrice ? 'text-red-500' : 'text-emerald-500'}">
									{i === 0 ? '—' : (m.outputPrice - compareModels[0].outputPrice > 0 ? '+' : '') + (m.outputPrice - compareModels[0].outputPrice).toFixed(2)}
								</td>
							{/each}
						</tr>
					</tbody>
				</table>
			</div>
		</Card.Content>
	</Card.Root>

	<!-- Capabilities Comparison -->
	<Card.Root>
		<Card.Header>
			<Card.Title>Capabilities Comparison</Card.Title>
		</Card.Header>
		<Card.Content class="p-0">
			<div class="hidden md:block overflow-x-auto">
				<table class="w-full">
					<thead>
						<tr class="border-b bg-muted/30">
							<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Capability</th>
							{#each compareModels as m (m.slug)}
								<th class="px-4 py-3 text-center text-xs font-medium text-muted-foreground">{m.name}</th>
							{/each}
						</tr>
					</thead>
					<tbody class="divide-y">
						{#each allCapabilities as cap (cap)}
							<tr class="hover:bg-muted/30">
								<td class="px-4 py-2.5 text-sm font-medium">{cap}</td>
								{#each compareModels as m}
									<td class="px-4 py-2.5 text-center">
										{#if m.capabilities[cap]}
											<Check class="inline h-4 w-4 text-emerald-500" />
										{:else}
											<X class="inline h-4 w-4 text-muted-foreground/40" />
										{/if}
									</td>
								{/each}
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
			<!-- Mobile card view -->
			<div class="md:hidden space-y-3 p-4">
				{#each compareModels as m (m.slug)}
					<div class="rounded-lg border p-4">
						<div class="flex items-center gap-2 mb-3">
							<Cpu class="h-4 w-4 text-primary" />
							<span class="font-medium">{m.name}</span>
						</div>
						<div class="flex flex-wrap gap-1.5">
							{#each allCapabilities as cap (cap)}
								<Badge variant="outline" class="text-xs gap-1 {m.capabilities[cap] ? 'text-emerald-600 dark:text-emerald-400 border-emerald-500/30' : 'opacity-40'}">
									{#if m.capabilities[cap]}
										<Check class="h-2.5 w-2.5" />
									{:else}
										<X class="h-2.5 w-2.5" />
									{/if}
									{cap}
								</Badge>
							{/each}
						</div>
					</div>
				{/each}
			</div>
		</Card.Content>
	</Card.Root>
</div>
