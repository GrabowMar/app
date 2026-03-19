<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import Cpu from '@lucide/svelte/icons/cpu';
	import Search from '@lucide/svelte/icons/search';
	import GitCompareArrows from '@lucide/svelte/icons/git-compare-arrows';
	import CloudDownload from '@lucide/svelte/icons/cloud-download';
	import Download from '@lucide/svelte/icons/download';
	import Upload from '@lucide/svelte/icons/upload';
	import CircleCheck from '@lucide/svelte/icons/circle-check';
	import CircleX from '@lucide/svelte/icons/circle-x';
	import Trophy from '@lucide/svelte/icons/trophy';
	import ChevronLeft from '@lucide/svelte/icons/chevron-left';
	import ChevronRight from '@lucide/svelte/icons/chevron-right';

	let searchQuery = $state('');
	let selectedProvider = $state('all');
	let selectedModels = $state<Set<string>>(new Set());

	interface Model {
		slug: string;
		name: string;
		provider: string;
		contextWindow: string;
		inputPrice: string;
		outputPrice: string;
		status: 'active' | 'inactive';
		capabilities: string[];
		appsGenerated: number;
	}

	const models: Model[] = [
		{ slug: 'gpt-4o', name: 'GPT-4o', provider: 'OpenAI', contextWindow: '128K', inputPrice: '$2.50', outputPrice: '$10.00', status: 'active', capabilities: ['Code', 'Chat', 'Vision'], appsGenerated: 24 },
		{ slug: 'gpt-4o-mini', name: 'GPT-4o Mini', provider: 'OpenAI', contextWindow: '128K', inputPrice: '$0.15', outputPrice: '$0.60', status: 'active', capabilities: ['Code', 'Chat'], appsGenerated: 18 },
		{ slug: 'claude-3-5-sonnet', name: 'Claude 3.5 Sonnet', provider: 'Anthropic', contextWindow: '200K', inputPrice: '$3.00', outputPrice: '$15.00', status: 'active', capabilities: ['Code', 'Chat', 'Vision'], appsGenerated: 22 },
		{ slug: 'claude-3-5-haiku', name: 'Claude 3.5 Haiku', provider: 'Anthropic', contextWindow: '200K', inputPrice: '$0.80', outputPrice: '$4.00', status: 'active', capabilities: ['Code', 'Chat'], appsGenerated: 15 },
		{ slug: 'gemini-1-5-pro', name: 'Gemini 1.5 Pro', provider: 'Google', contextWindow: '2M', inputPrice: '$1.25', outputPrice: '$5.00', status: 'active', capabilities: ['Code', 'Chat', 'Vision'], appsGenerated: 20 },
		{ slug: 'gemini-2-0-flash', name: 'Gemini 2.0 Flash', provider: 'Google', contextWindow: '1M', inputPrice: '$0.10', outputPrice: '$0.40', status: 'active', capabilities: ['Code', 'Chat'], appsGenerated: 12 },
		{ slug: 'deepseek-v3', name: 'DeepSeek V3', provider: 'DeepSeek', contextWindow: '64K', inputPrice: '$0.27', outputPrice: '$1.10', status: 'active', capabilities: ['Code', 'Chat'], appsGenerated: 16 },
		{ slug: 'deepseek-r1', name: 'DeepSeek R1', provider: 'DeepSeek', contextWindow: '64K', inputPrice: '$0.55', outputPrice: '$2.19', status: 'active', capabilities: ['Code', 'Reasoning'], appsGenerated: 10 },
		{ slug: 'qwen-2-5-coder', name: 'Qwen 2.5 Coder', provider: 'Alibaba', contextWindow: '128K', inputPrice: '$0.30', outputPrice: '$1.20', status: 'active', capabilities: ['Code'], appsGenerated: 8 },
		{ slug: 'llama-3-1-405b', name: 'Llama 3.1 405B', provider: 'Meta', contextWindow: '128K', inputPrice: '$3.00', outputPrice: '$3.00', status: 'inactive', capabilities: ['Code', 'Chat'], appsGenerated: 5 },
	];

	const providers = ['all', ...new Set(models.map(m => m.provider))];

	const filteredModels = $derived(
		models.filter(m => {
			const matchSearch = !searchQuery || m.name.toLowerCase().includes(searchQuery.toLowerCase()) || m.provider.toLowerCase().includes(searchQuery.toLowerCase());
			const matchProvider = selectedProvider === 'all' || m.provider === selectedProvider;
			return matchSearch && matchProvider;
		})
	);

	const stats = {
		total: models.length,
		active: models.filter(m => m.status === 'active').length,
		providers: new Set(models.map(m => m.provider)).size,
		avgCost: '$1.29',
	};

	function toggleModel(slug: string) {
		const next = new Set(selectedModels);
		if (next.has(slug)) next.delete(slug); else next.add(slug);
		selectedModels = next;
	}
</script>

<svelte:head>
	<title>Models - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<div class="flex items-center justify-between">
		<div class="page-header">
			<h1>Models</h1>
			<p>Browse and manage AI models available for research.</p>
		</div>
		<div class="flex items-center gap-2">
			<Button variant="outline" size="sm" href="/rankings">
				<Trophy class="mr-2 h-3.5 w-3.5" />
				Rankings
			</Button>
			<Button variant="outline" size="sm" href="/models/import">
				<Upload class="mr-2 h-3.5 w-3.5" />
				Import
			</Button>
		</div>
	</div>

	<!-- Stats -->
	<div class="flex flex-wrap items-center gap-2">
		<Badge variant="secondary" class="gap-1.5">
			<Cpu class="h-3 w-3" />
			{stats.total} models
		</Badge>
		<Badge variant="secondary" class="gap-1.5">
			<CircleCheck class="h-3 w-3 text-emerald-500" />
			{stats.active} active
		</Badge>
		<Badge variant="outline">{stats.providers} providers</Badge>
		<Badge variant="outline">Avg {stats.avgCost}/1K tokens</Badge>
	</div>

	<!-- Filters & Actions -->
	<div class="flex flex-wrap items-center gap-3">
		<div class="relative flex-1 max-w-sm">
			<Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
			<Input placeholder="Search models..." class="pl-9" bind:value={searchQuery} />
		</div>
		<select
			class="h-9 rounded-md border border-input bg-background px-3 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring"
			bind:value={selectedProvider}
		>
			{#each providers as p}
				<option value={p}>{p === 'all' ? 'All Providers' : p}</option>
			{/each}
		</select>
		<div class="ml-auto flex items-center gap-2">
			{#if selectedModels.size >= 2}
				<Button size="sm" href="/models/compare?models={[...selectedModels].join(',')}">
					<GitCompareArrows class="mr-2 h-3.5 w-3.5" />
					Compare ({selectedModels.size})
				</Button>
			{/if}
			<Button variant="outline" size="sm" disabled>
				<CloudDownload class="mr-2 h-3.5 w-3.5" />
				Sync from OpenRouter
			</Button>
			<Button variant="outline" size="sm" disabled>
				<Download class="mr-2 h-3.5 w-3.5" />
				Export JSON
			</Button>
		</div>
	</div>

	<!-- Models Table -->
	<Card.Root>
		<Card.Content class="p-0">
			<div class="overflow-x-auto">
				<table class="w-full">
					<thead>
						<tr class="border-b bg-muted/30">
							<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground w-10">
								<input type="checkbox" class="rounded" disabled />
							</th>
							<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Model</th>
							<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Provider</th>
							<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Context</th>
							<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Input $/1M</th>
							<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Output $/1M</th>
							<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Status</th>
							<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Capabilities</th>
							<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Apps</th>
						</tr>
					</thead>
					<tbody class="divide-y">
						{#each filteredModels as model (model.slug)}
							<tr class="transition-colors hover:bg-muted/30 {selectedModels.has(model.slug) ? 'bg-primary/5' : ''}">
								<td class="px-4 py-3">
									<input
										type="checkbox"
										class="rounded"
										checked={selectedModels.has(model.slug)}
										onchange={() => toggleModel(model.slug)}
									/>
								</td>
								<td class="px-4 py-3">
									<a href="/models/{model.slug}" class="flex items-center gap-2.5 group/link">
										<div class="flex h-8 w-8 items-center justify-center rounded-lg bg-muted group-hover/link:bg-primary/10 transition-colors">
											<Cpu class="h-3.5 w-3.5 text-muted-foreground group-hover/link:text-primary transition-colors" />
										</div>
										<span class="text-sm font-medium group-hover/link:text-primary transition-colors">{model.name}</span>
									</a>
								</td>
								<td class="px-4 py-3">
									<span class="text-sm text-muted-foreground">{model.provider}</span>
								</td>
								<td class="px-4 py-3">
									<span class="text-sm font-mono">{model.contextWindow}</span>
								</td>
								<td class="px-4 py-3">
									<span class="text-sm font-mono">{model.inputPrice}</span>
								</td>
								<td class="px-4 py-3">
									<span class="text-sm font-mono">{model.outputPrice}</span>
								</td>
								<td class="px-4 py-3">
									{#if model.status === 'active'}
										<Badge variant="secondary" class="text-xs gap-1">
											<CircleCheck class="h-3 w-3 text-emerald-500" />
											Active
										</Badge>
									{:else}
										<Badge variant="outline" class="text-xs gap-1">
											<CircleX class="h-3 w-3" />
											Inactive
										</Badge>
									{/if}
								</td>
								<td class="px-4 py-3">
									<div class="flex flex-wrap gap-1">
										{#each model.capabilities as cap}
											<Badge variant="outline" class="text-[10px] px-1.5 py-0">{cap}</Badge>
										{/each}
									</div>
								</td>
								<td class="px-4 py-3">
									<span class="text-sm font-medium">{model.appsGenerated}</span>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</Card.Content>
	</Card.Root>

	<!-- Pagination -->
	<div class="flex items-center justify-between">
		<p class="text-sm text-muted-foreground">Showing 1–{filteredModels.length} of {filteredModels.length} models</p>
		<div class="flex items-center gap-1">
			<Button variant="outline" size="icon" class="h-8 w-8" disabled>
				<ChevronLeft class="h-4 w-4" />
			</Button>
			<Button variant="outline" size="sm" class="h-8 min-w-8 bg-primary text-primary-foreground">1</Button>
			<Button variant="outline" size="icon" class="h-8 w-8" disabled>
				<ChevronRight class="h-4 w-4" />
			</Button>
		</div>
	</div>
</div>
