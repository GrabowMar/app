<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import Trophy from '@lucide/svelte/icons/trophy';
	import Medal from '@lucide/svelte/icons/medal';
	import Search from '@lucide/svelte/icons/search';
	import Download from '@lucide/svelte/icons/download';
	import Info from '@lucide/svelte/icons/info';
	import ArrowUpDown from '@lucide/svelte/icons/arrow-up-down';
	import ExternalLink from '@lucide/svelte/icons/external-link';

	let searchQuery = $state('');
	let providerFilter = $state('all');
	let sortBy = $state<'mss' | 'security' | 'performance' | 'quality' | 'ai'>('mss');
	let sortAsc = $state(false);
	let showMethodology = $state(false);
	let selectedModels = $state<Set<string>>(new Set());

	interface ModelRanking {
		slug: string;
		name: string;
		provider: string;
		mss: number;
		security: number;
		performance: number;
		quality: number;
		ai: number;
		apps: number;
		humaneval: number | null;
		mbpp: number | null;
		swebench: number | null;
	}

	const models: ModelRanking[] = [
		{ slug: 'gpt-4o', name: 'GPT-4o', provider: 'OpenAI', mss: 82.4, security: 7.8, performance: 85, quality: 8.1, ai: 7.8, apps: 8, humaneval: 90.2, mbpp: 87.6, swebench: 33.2 },
		{ slug: 'claude-3-5-sonnet', name: 'Claude 3.5 Sonnet', provider: 'Anthropic', mss: 85.1, security: 8.4, performance: 82, quality: 8.6, ai: 8.2, apps: 8, humaneval: 92.0, mbpp: 89.4, swebench: 49.0 },
		{ slug: 'gemini-2-0-flash', name: 'Gemini 2.0 Flash', provider: 'Google', mss: 78.3, security: 7.2, performance: 88, quality: 7.4, ai: 7.0, apps: 8, humaneval: 85.7, mbpp: 82.1, swebench: 28.4 },
		{ slug: 'gpt-4o-mini', name: 'GPT-4o Mini', provider: 'OpenAI', mss: 71.6, security: 6.5, performance: 80, quality: 7.0, ai: 6.8, apps: 8, humaneval: 87.0, mbpp: 84.3, swebench: null },
		{ slug: 'claude-3-5-haiku', name: 'Claude 3.5 Haiku', provider: 'Anthropic', mss: 73.9, security: 7.0, performance: 78, quality: 7.2, ai: 7.1, apps: 8, humaneval: 88.1, mbpp: 85.2, swebench: null },
		{ slug: 'deepseek-v3', name: 'DeepSeek V3', provider: 'DeepSeek', mss: 76.8, security: 7.1, performance: 79, quality: 7.8, ai: 7.5, apps: 8, humaneval: 82.6, mbpp: 80.4, swebench: 42.0 },
		{ slug: 'llama-3-1-70b', name: 'Llama 3.1 70B', provider: 'Meta', mss: 68.2, security: 5.9, performance: 74, quality: 6.8, ai: 6.4, apps: 6, humaneval: 80.5, mbpp: 78.3, swebench: null },
		{ slug: 'mistral-large', name: 'Mistral Large', provider: 'Mistral', mss: 72.1, security: 6.6, performance: 76, quality: 7.1, ai: 6.9, apps: 7, humaneval: 84.0, mbpp: 81.0, swebench: null },
	];

	const providers = [...new Set(models.map(m => m.provider))];

	const filteredModels = $derived(() => {
		let list = models.filter(m =>
			(providerFilter === 'all' || m.provider === providerFilter) &&
			(searchQuery === '' || m.name.toLowerCase().includes(searchQuery.toLowerCase()))
		);
		list.sort((a, b) => {
			const diff = (a[sortBy] ?? 0) - (b[sortBy] ?? 0);
			return sortAsc ? diff : -diff;
		});
		return list;
	});

	function toggleSort(col: typeof sortBy) {
		if (sortBy === col) sortAsc = !sortAsc;
		else { sortBy = col; sortAsc = false; }
	}

	function toggleSelect(slug: string) {
		const next = new Set(selectedModels);
		if (next.has(slug)) next.delete(slug);
		else if (next.size < 10) next.add(slug);
		selectedModels = next;
	}

	function scoreColor(val: number, max: number = 10): string {
		const pct = max === 100 ? val : (val / max) * 100;
		if (pct >= 80) return 'text-emerald-500';
		if (pct >= 60) return 'text-amber-500';
		return 'text-red-400';
	}
</script>

<svelte:head>
	<title>Rankings - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
		<div>
			<h1 class="text-2xl font-bold tracking-tight">Model Rankings</h1>
			<p class="mt-1 text-xs sm:text-sm text-muted-foreground">Compare model performance using the Model Scoring System (MSS).</p>
		</div>
		<div class="flex gap-2">
			<Button variant="outline" size="sm" disabled>
				<Download class="mr-1.5 h-3.5 w-3.5" />
				Export
			</Button>
		</div>
	</div>

	<!-- Methodology Panel -->
	<Card.Root class="border-blue-500/20 bg-blue-500/5">
		<button class="flex w-full items-center gap-3 p-4 text-left text-sm" onclick={() => showMethodology = !showMethodology}>
			<Info class="h-4 w-4 text-blue-500 shrink-0" />
			<span class="font-medium">MSS Methodology</span>
			<Badge variant="outline" class="ml-auto text-[10px]">{showMethodology ? 'Hide' : 'Show'}</Badge>
		</button>
		{#if showMethodology}
			<Card.Content class="pt-0 text-sm text-muted-foreground space-y-2">
				<p>The <strong>Model Scoring System (MSS)</strong> is a weighted composite score (0–100) derived from four dimensions:</p>
				<div class="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
					{#each [
						{ label: 'Security (30%)', desc: 'Static + dynamic analysis findings severity-weighted' },
						{ label: 'Performance (25%)', desc: 'Lighthouse scores + load test response times' },
						{ label: 'Code Quality (25%)', desc: 'Linting issues, complexity, duplication rate' },
						{ label: 'AI Review (20%)', desc: 'Requirements compliance + quality assessment' },
					] as dim}
						<div class="rounded-lg border p-2.5">
							<span class="text-xs font-medium text-foreground">{dim.label}</span>
							<p class="text-[11px] text-muted-foreground">{dim.desc}</p>
						</div>
					{/each}
				</div>
				<div class="flex flex-wrap gap-2 pt-1">
					<a href="https://www.swebench.com" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1 text-xs text-blue-500 hover:underline">
						SWE-bench <ExternalLink class="h-3 w-3" />
					</a>
					<a href="https://evalplus.github.io/leaderboard.html" target="_blank" rel="noopener noreferrer" class="inline-flex items-center gap-1 text-xs text-blue-500 hover:underline">
						EvalPlus (HumanEval/MBPP+) <ExternalLink class="h-3 w-3" />
					</a>
				</div>
			</Card.Content>
		{/if}
	</Card.Root>

	<!-- Filters -->
	<div class="flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-center">
		<div class="relative w-full sm:flex-1 sm:max-w-sm">
			<Search class="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
			<Input bind:value={searchQuery} placeholder="Search models..." class="h-9 pl-8 text-sm" />
		</div>
		<select bind:value={providerFilter} class="h-9 w-full sm:w-auto rounded-md border bg-background px-3 text-sm">
			<option value="all">All Providers</option>
			{#each providers as p}
				<option value={p}>{p}</option>
			{/each}
		</select>
		{#if selectedModels.size > 0}
			<Badge variant="outline" class="text-xs">{selectedModels.size}/10 selected</Badge>
		{/if}
	</div>

	<!-- Leaderboard -->
	<Card.Root>
		<Card.Header class="pb-0">
			<div class="flex items-center gap-2">
				<Trophy class="h-4 w-4 text-amber-500" />
				<Card.Title>Leaderboard</Card.Title>
			</div>
		</Card.Header>
		<Card.Content class="p-0 pt-4">
			<!-- Desktop table (768px+) -->
			<div class="hidden md:block overflow-x-auto">
				<table class="w-full text-sm">
					<thead>
						<tr class="border-b bg-muted/30">
							<th class="w-10 px-3 py-2"></th>
							<th class="w-14 px-3 py-2 text-left text-xs font-medium text-muted-foreground">Rank</th>
							<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Model</th>
							{#each [
								{ key: 'mss' as const, label: 'MSS' },
								{ key: 'security' as const, label: 'Security' },
								{ key: 'performance' as const, label: 'Perf.' },
								{ key: 'quality' as const, label: 'Quality' },
								{ key: 'ai' as const, label: 'AI Rev.' },
							] as col}
								<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">
									<button class="inline-flex items-center gap-1 hover:text-foreground" onclick={() => toggleSort(col.key)}>
										{col.label}
										<ArrowUpDown class="h-3 w-3 {sortBy === col.key ? 'text-foreground' : ''}" />
									</button>
								</th>
							{/each}
							<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">HumanEval</th>
							<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">MBPP+</th>
							<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">SWE-bench</th>
							<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Apps</th>
						</tr>
					</thead>
					<tbody class="divide-y">
						{#each filteredModels() as model, i}
							<tr class="hover:bg-muted/30 {i < 3 ? 'bg-amber-500/5' : ''} {selectedModels.has(model.slug) ? 'ring-1 ring-inset ring-primary/40' : ''}">
								<td class="px-3 py-2">
									<input type="checkbox" checked={selectedModels.has(model.slug)} onchange={() => toggleSelect(model.slug)} class="rounded" />
								</td>
								<td class="px-3 py-2">
									<div class="flex items-center gap-1.5">
										{#if i < 3}
											<Medal class="h-4 w-4 {i === 0 ? 'text-amber-500' : i === 1 ? 'text-slate-400' : 'text-amber-700'}" />
										{/if}
										<span class="text-xs font-semibold">#{i + 1}</span>
									</div>
								</td>
								<td class="px-3 py-2">
									<div>
										<a href="/models/{model.slug}" class="font-medium hover:underline">{model.name}</a>
										<div class="text-[10px] text-muted-foreground">{model.provider}</div>
									</div>
								</td>
								<td class="px-3 py-2 font-mono font-bold {scoreColor(model.mss, 100)}">{model.mss.toFixed(1)}</td>
								<td class="px-3 py-2 font-mono text-xs {scoreColor(model.security)}">{model.security.toFixed(1)}</td>
								<td class="px-3 py-2 font-mono text-xs {scoreColor(model.performance, 100)}">{model.performance}</td>
								<td class="px-3 py-2 font-mono text-xs {scoreColor(model.quality)}">{model.quality.toFixed(1)}</td>
								<td class="px-3 py-2 font-mono text-xs {scoreColor(model.ai)}">{model.ai.toFixed(1)}</td>
								<td class="px-3 py-2 font-mono text-xs">{model.humaneval?.toFixed(1) ?? '—'}</td>
								<td class="px-3 py-2 font-mono text-xs">{model.mbpp?.toFixed(1) ?? '—'}</td>
								<td class="px-3 py-2 font-mono text-xs">{model.swebench?.toFixed(1) ?? '—'}</td>
								<td class="px-3 py-2 text-xs text-muted-foreground">{model.apps}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>

			<!-- Mobile card view (below 768px) -->
			<div class="md:hidden space-y-3 px-4 pb-4">
				{#each filteredModels() as model, i}
					<div class="bg-card border rounded-lg p-4 {i < 3 ? 'border-amber-500/30' : ''} {selectedModels.has(model.slug) ? 'ring-1 ring-inset ring-primary/40' : ''}">
						<!-- Card header: rank, model, provider -->
						<div class="flex items-center gap-3">
							<input type="checkbox" checked={selectedModels.has(model.slug)} onchange={() => toggleSelect(model.slug)} class="rounded shrink-0" />
							<div class="flex items-center gap-1.5 shrink-0">
								{#if i < 3}
									<Medal class="h-5 w-5 {i === 0 ? 'text-amber-500' : i === 1 ? 'text-slate-400' : 'text-amber-700'}" />
								{:else}
									<span class="flex h-5 w-5 items-center justify-center text-xs font-bold text-muted-foreground">#{i + 1}</span>
								{/if}
							</div>
							<div class="min-w-0 flex-1">
								<a href="/models/{model.slug}" class="font-medium text-sm hover:underline truncate block">{model.name}</a>
								<Badge variant="outline" class="mt-0.5 text-[10px]">{model.provider}</Badge>
							</div>
							<div class="text-right shrink-0">
								<div class="text-[10px] font-medium text-muted-foreground">MSS</div>
								<div class="text-lg font-bold font-mono {scoreColor(model.mss, 100)}">{model.mss.toFixed(1)}</div>
							</div>
						</div>

						<!-- Card body: score grid -->
						<div class="mt-3 grid grid-cols-2 gap-x-4 gap-y-1.5">
							<div class="flex items-center justify-between">
								<span class="text-[10px] text-muted-foreground">Security</span>
								<span class="text-xs font-mono font-medium {scoreColor(model.security)}">{model.security.toFixed(1)}</span>
							</div>
							<div class="flex items-center justify-between">
								<span class="text-[10px] text-muted-foreground">Performance</span>
								<span class="text-xs font-mono font-medium {scoreColor(model.performance, 100)}">{model.performance}</span>
							</div>
							<div class="flex items-center justify-between">
								<span class="text-[10px] text-muted-foreground">Quality</span>
								<span class="text-xs font-mono font-medium {scoreColor(model.quality)}">{model.quality.toFixed(1)}</span>
							</div>
							<div class="flex items-center justify-between">
								<span class="text-[10px] text-muted-foreground">AI Review</span>
								<span class="text-xs font-mono font-medium {scoreColor(model.ai)}">{model.ai.toFixed(1)}</span>
							</div>
							<div class="flex items-center justify-between">
								<span class="text-[10px] text-muted-foreground">HumanEval</span>
								<span class="text-xs font-mono font-medium">{model.humaneval?.toFixed(1) ?? '—'}</span>
							</div>
							<div class="flex items-center justify-between">
								<span class="text-[10px] text-muted-foreground">MBPP+</span>
								<span class="text-xs font-mono font-medium">{model.mbpp?.toFixed(1) ?? '—'}</span>
							</div>
							<div class="flex items-center justify-between">
								<span class="text-[10px] text-muted-foreground">SWE-bench</span>
								<span class="text-xs font-mono font-medium">{model.swebench?.toFixed(1) ?? '—'}</span>
							</div>
							<div class="flex items-center justify-between">
								<span class="text-[10px] text-muted-foreground">Apps</span>
								<span class="text-xs font-mono font-medium text-muted-foreground">{model.apps}</span>
							</div>
						</div>
					</div>
				{/each}
			</div>
		</Card.Content>
	</Card.Root>

	<div class="text-xs text-muted-foreground">
		Showing {filteredModels().length} of {models.length} models &middot; MSS scores computed from platform analysis data &middot; External benchmarks sourced from public leaderboards
	</div>
</div>
