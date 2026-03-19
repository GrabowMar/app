<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Separator } from '$lib/components/ui/separator';
	import Code from '@lucide/svelte/icons/code';
	import Check from '@lucide/svelte/icons/check';
	import Search from '@lucide/svelte/icons/search';
	import ChevronLeft from '@lucide/svelte/icons/chevron-left';
	import ChevronRight from '@lucide/svelte/icons/chevron-right';
	import Play from '@lucide/svelte/icons/play';
	import Box from '@lucide/svelte/icons/box';
	import FileCode from '@lucide/svelte/icons/file-code';
	import Layers from '@lucide/svelte/icons/layers';
	import X from '@lucide/svelte/icons/x';
	import LoaderCircle from '@lucide/svelte/icons/loader-circle';
	import Clock from '@lucide/svelte/icons/clock';

	let step = $state(1);
	let templateSearch = $state('');
	let modelSearch = $state('');
	let rerunOnFailure = $state(true);
	let maxRetries = $state(2);
	let pastLimit = $state(10);

	const scaffolds = [
		{ id: 'default', name: 'Default React + Flask', description: 'React Vite frontend with Flask backend, Docker compose, analyzer wiring', active: true, details: ['Docker + docker-compose', 'Port allocation (5001+/8001+)', 'React Vite frontend', 'Flask REST backend', 'Analyzer wiring'] },
		{ id: 'vue-fastapi', name: 'Vue + FastAPI', description: 'Vue.js frontend with FastAPI backend', active: false },
		{ id: 'angular-django', name: 'Angular + Django', description: 'Angular frontend with Django REST backend', active: false },
	];

	const templates = [
		{ slug: 'todo-app', name: 'Todo Application', description: 'A full-featured task management app with CRUD operations and user authentication', category: 'Productivity' },
		{ slug: 'blog-platform', name: 'Blog Platform', description: 'Content management system with posts, comments, and user profiles', category: 'Content' },
		{ slug: 'ecommerce', name: 'E-Commerce Store', description: 'Online store with product catalog, cart, and checkout flow', category: 'Commerce' },
		{ slug: 'dashboard', name: 'Analytics Dashboard', description: 'Data visualization dashboard with charts and real-time metrics', category: 'Analytics' },
		{ slug: 'chat-app', name: 'Chat Application', description: 'Real-time messaging app with rooms and direct messages', category: 'Communication' },
		{ slug: 'weather-app', name: 'Weather App', description: 'Weather forecast application with location search and maps', category: 'Utility' },
		{ slug: 'recipe-manager', name: 'Recipe Manager', description: 'Recipe collection app with search, categories, and meal planning', category: 'Lifestyle' },
		{ slug: 'project-tracker', name: 'Project Tracker', description: 'Project management tool with kanban boards and team collaboration', category: 'Productivity' },
	];

	const models = [
		{ slug: 'gpt-4o', name: 'GPT-4o', provider: 'OpenAI', inputPrice: 2.50, outputPrice: 10.00 },
		{ slug: 'gpt-4o-mini', name: 'GPT-4o Mini', provider: 'OpenAI', inputPrice: 0.15, outputPrice: 0.60 },
		{ slug: 'claude-3-5-sonnet', name: 'Claude 3.5 Sonnet', provider: 'Anthropic', inputPrice: 3.00, outputPrice: 15.00 },
		{ slug: 'claude-3-haiku', name: 'Claude 3 Haiku', provider: 'Anthropic', inputPrice: 0.25, outputPrice: 1.25 },
		{ slug: 'gemini-1-5-pro', name: 'Gemini 1.5 Pro', provider: 'Google', inputPrice: 1.25, outputPrice: 5.00 },
		{ slug: 'gemini-1-5-flash', name: 'Gemini 1.5 Flash', provider: 'Google', inputPrice: 0.075, outputPrice: 0.30 },
	];

	const pastGenerations = [
		{ timestamp: '2025-03-19 14:32', appName: 'todo-app', model: 'GPT-4o', status: 'completed', message: 'Successfully generated and deployed', duration: '1m 45s' },
		{ timestamp: '2025-03-19 14:15', appName: 'blog-platform', model: 'Claude 3.5 Sonnet', status: 'completed', message: 'Generated with 2 retries', duration: '3m 12s' },
		{ timestamp: '2025-03-19 13:50', appName: 'ecommerce', model: 'GPT-4o Mini', status: 'failed', message: 'Build failed: Missing dependency in requirements.txt', duration: '2m 08s' },
		{ timestamp: '2025-03-18 16:20', appName: 'chat-app', model: 'Gemini 1.5 Pro', status: 'completed', message: 'Successfully generated', duration: '1m 30s' },
		{ timestamp: '2025-03-18 15:45', appName: 'dashboard', model: 'GPT-4o', status: 'running', message: 'Building Docker containers...', duration: '0m 42s' },
		{ timestamp: '2025-03-18 14:00', appName: 'todo-app', model: 'Claude 3 Haiku', status: 'completed', message: 'Successfully generated', duration: '0m 58s' },
		{ timestamp: '2025-03-17 11:30', appName: 'weather-app', model: 'Gemini 1.5 Flash', status: 'pending', message: 'Queued for generation', duration: '—' },
	];

	let selectedScaffold = $state('default');
	let selectedTemplates = $state<Set<string>>(new Set());
	let selectedModels = $state<Set<string>>(new Set());

	const filteredTemplates = $derived(templates.filter(t =>
		t.name.toLowerCase().includes(templateSearch.toLowerCase()) ||
		t.description.toLowerCase().includes(templateSearch.toLowerCase())
	));
	const filteredModels = $derived(models.filter(m =>
		m.name.toLowerCase().includes(modelSearch.toLowerCase())
	));
	const totalPairs = $derived(selectedTemplates.size * selectedModels.size);
	const avgCost = $derived(() => {
		if (selectedModels.size === 0) return '0.00';
		const avg = [...selectedModels].reduce((sum, slug) => {
			const m = models.find(m => m.slug === slug);
			return sum + (m ? m.inputPrice : 0);
		}, 0) / selectedModels.size;
		return avg.toFixed(2);
	});

	const statusColors: Record<string, string> = {
		completed: 'bg-emerald-500/15 text-emerald-500 border-emerald-500/30',
		running: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
		failed: 'bg-red-500/15 text-red-400 border-red-500/30',
		pending: 'bg-amber-500/15 text-amber-500 border-amber-500/30',
	};

	function toggleTemplate(slug: string) {
		const s = new Set(selectedTemplates);
		s.has(slug) ? s.delete(slug) : s.add(slug);
		selectedTemplates = s;
	}
	function toggleModel(slug: string) {
		const s = new Set(selectedModels);
		s.has(slug) ? s.delete(slug) : s.add(slug);
		selectedModels = s;
	}
	function selectAllTemplates() { selectedTemplates = new Set(filteredTemplates.map(t => t.slug)); }
	function clearTemplates() { selectedTemplates = new Set(); }
	function selectAllModels() { selectedModels = new Set(filteredModels.map(m => m.slug)); }
	function clearModels() { selectedModels = new Set(); }

	const providers = $derived([...new Set(models.map(m => m.provider))]);

	// Mock review progress data
	const reviewResults = [
		{ template: 'todo-app', model: 'GPT-4o', status: 'completed', message: 'Success' },
		{ template: 'blog-platform', model: 'GPT-4o', status: 'completed', message: 'Success' },
		{ template: 'todo-app', model: 'Claude 3.5 Sonnet', status: 'failed', message: 'Build timeout' },
	];
</script>

<svelte:head>
	<title>Sample Generator - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<div>
			<div class="flex items-center gap-3">
				<h1 class="text-2xl font-bold tracking-tight">Sample Generator</h1>
				<Badge variant="outline" class="text-xs">AI-Powered</Badge>
			</div>
			<p class="mt-1 text-sm text-muted-foreground">Generate AI-powered applications with scaffolding templates.</p>
		</div>
	</div>

	<div class="grid gap-6 lg:grid-cols-[1fr_300px]">
		<!-- Left Column: Wizard -->
		<div class="space-y-6">
			<!-- Step Indicator -->
			<div class="flex items-center gap-2">
				{#each [{ n: 1, label: 'Scaffold' }, { n: 2, label: 'Selections' }, { n: 3, label: 'Review' }] as s}
					<button
						class="flex items-center gap-2 rounded-full px-4 py-1.5 text-sm transition-colors {step === s.n ? 'bg-primary text-primary-foreground font-medium' : step > s.n ? 'bg-emerald-500/15 text-emerald-500' : 'bg-muted text-muted-foreground'}"
						onclick={() => { if (s.n <= step) step = s.n; }}
					>
						{#if step > s.n}<Check class="h-3.5 w-3.5" />{:else}<span class="font-mono text-xs">{s.n}</span>{/if}
						{s.label}
					</button>
					{#if s.n < 3}<div class="h-px flex-1 bg-border"></div>{/if}
				{/each}
			</div>

			<!-- Step 1: Select Scaffolding -->
			{#if step === 1}
				<div class="space-y-4">
					<Card.Root>
						<Card.Header>
							<Card.Title>Select Scaffolding</Card.Title>
							<Card.Description>Choose the application stack for generation.</Card.Description>
						</Card.Header>
						<Card.Content>
							<div class="grid gap-3 md:grid-cols-3">
								{#each scaffolds as scaffold}
									<button
										class="rounded-lg border p-4 text-left transition-colors {selectedScaffold === scaffold.id ? 'ring-2 ring-primary bg-primary/5' : ''} {!scaffold.active ? 'opacity-50 cursor-not-allowed' : 'hover:bg-muted/50'}"
										onclick={() => { if (scaffold.active) selectedScaffold = scaffold.id; }}
										disabled={!scaffold.active}
									>
										<div class="flex items-center gap-2">
											<Box class="h-5 w-5 {selectedScaffold === scaffold.id ? 'text-primary' : 'text-muted-foreground'}" />
											<span class="text-sm font-medium">{scaffold.name}</span>
										</div>
										<p class="mt-1 text-xs text-muted-foreground">{scaffold.description}</p>
										{#if !scaffold.active}
											<Badge variant="outline" class="mt-2 text-[10px]">Coming Soon</Badge>
										{/if}
									</button>
								{/each}
							</div>

							{#if selectedScaffold === 'default'}
								<div class="mt-4 rounded-lg bg-muted/50 p-4">
									<h4 class="text-sm font-medium mb-2">Stack Preview</h4>
									<div class="flex flex-wrap gap-2">
										{#each scaffolds[0].details ?? [] as detail}
											<Badge variant="secondary" class="text-xs">{detail}</Badge>
										{/each}
									</div>
								</div>
							{/if}
						</Card.Content>
					</Card.Root>

					<!-- Advanced Options -->
					<Card.Root>
						<Card.Header class="pb-2">
							<Card.Title class="text-sm">Advanced Options</Card.Title>
						</Card.Header>
						<Card.Content>
							<div class="flex flex-wrap items-center gap-4 text-sm">
								<label class="flex items-center gap-1.5">
									<input type="checkbox" bind:checked={rerunOnFailure} class="rounded" />
									Re-run on failure
								</label>
								<label class="flex items-center gap-1.5">
									Max retries:
									<select bind:value={maxRetries} class="h-7 rounded-md border bg-background px-2 text-xs">
										<option value={1}>1</option>
										<option value={2}>2</option>
										<option value={3}>3</option>
									</select>
								</label>
							</div>
						</Card.Content>
					</Card.Root>

					<!-- Past Generations -->
					<Card.Root>
						<Card.Header class="pb-2">
							<div class="flex items-center justify-between">
								<Card.Title class="text-sm">Past Generations</Card.Title>
								<select bind:value={pastLimit} class="h-7 rounded-md border bg-background px-2 text-xs">
									<option value={10}>10</option>
									<option value={25}>25</option>
									<option value={50}>50</option>
								</select>
							</div>
						</Card.Header>
						<Card.Content class="p-0">
							<table class="w-full text-sm">
								<thead>
									<tr class="border-b bg-muted/30">
										<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Timestamp</th>
										<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">App</th>
										<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Model</th>
										<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Status</th>
										<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Message</th>
										<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Duration</th>
									</tr>
								</thead>
								<tbody class="divide-y">
									{#each pastGenerations.slice(0, pastLimit) as gen}
										<tr class="hover:bg-muted/30">
											<td class="px-3 py-2 text-xs text-muted-foreground font-mono">{gen.timestamp}</td>
											<td class="px-3 py-2 font-medium">{gen.appName}</td>
											<td class="px-3 py-2"><Badge variant="secondary" class="text-[10px]">{gen.model}</Badge></td>
											<td class="px-3 py-2">
												<Badge variant="outline" class="text-[10px] {statusColors[gen.status] ?? ''}">
													{#if gen.status === 'running'}<LoaderCircle class="mr-1 h-3 w-3 animate-spin" />{/if}
													{gen.status}
												</Badge>
											</td>
											<td class="px-3 py-2 text-xs text-muted-foreground max-w-[200px] truncate">{gen.message}</td>
											<td class="px-3 py-2 text-xs font-mono text-muted-foreground">{gen.duration}</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</Card.Content>
					</Card.Root>
				</div>
			{/if}

			<!-- Step 2: Select Templates & Models -->
			{#if step === 2}
				<Card.Root>
					<Card.Header>
						<Card.Title>Select Templates & Models</Card.Title>
						<Card.Description>Choose which templates and models to use for generation.</Card.Description>
					</Card.Header>
					<Card.Content>
						<div class="grid gap-4 md:grid-cols-2">
							<!-- Templates -->
							<div class="space-y-3">
								<div class="flex items-center justify-between">
									<h3 class="text-sm font-medium">Templates</h3>
									<div class="flex gap-1">
										<button class="text-[10px] text-primary hover:underline" onclick={selectAllTemplates}>Select All</button>
										<span class="text-muted-foreground">|</span>
										<button class="text-[10px] text-muted-foreground hover:underline" onclick={clearTemplates}>Clear</button>
									</div>
								</div>
								<div class="relative">
									<Search class="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
									<Input bind:value={templateSearch} placeholder="Search templates..." class="h-8 pl-8 text-xs" />
								</div>
								<div class="max-h-72 space-y-1 overflow-y-auto">
									{#each filteredTemplates as t}
										<button
											class="flex w-full items-start gap-2 rounded-md px-2.5 py-2 text-left text-sm transition-colors hover:bg-muted/50 {selectedTemplates.has(t.slug) ? 'bg-primary/5 ring-1 ring-primary/20' : ''}"
											onclick={() => toggleTemplate(t.slug)}
										>
											<div class="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded border {selectedTemplates.has(t.slug) ? 'bg-primary border-primary text-primary-foreground' : 'border-border'}">
												{#if selectedTemplates.has(t.slug)}<Check class="h-3 w-3" />{/if}
											</div>
											<div class="min-w-0">
												<div class="font-medium">{t.name}</div>
												<div class="text-xs text-muted-foreground line-clamp-1">{t.description}</div>
											</div>
											<Badge variant="secondary" class="ml-auto shrink-0 text-[10px]">{t.category}</Badge>
										</button>
									{/each}
								</div>
							</div>

							<!-- Models -->
							<div class="space-y-3">
								<div class="flex items-center justify-between">
									<h3 class="text-sm font-medium">Models</h3>
									<div class="flex gap-1">
										<button class="text-[10px] text-primary hover:underline" onclick={selectAllModels}>Select All</button>
										<span class="text-muted-foreground">|</span>
										<button class="text-[10px] text-muted-foreground hover:underline" onclick={clearModels}>Clear</button>
									</div>
								</div>
								<div class="relative">
									<Search class="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
									<Input bind:value={modelSearch} placeholder="Search models..." class="h-8 pl-8 text-xs" />
								</div>
								<div class="max-h-72 space-y-1 overflow-y-auto">
									{#each providers as provider}
										<div class="px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">{provider}</div>
										{#each filteredModels.filter(m => m.provider === provider) as m}
											<button
												class="flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-left text-sm transition-colors hover:bg-muted/50 {selectedModels.has(m.slug) ? 'bg-primary/5 ring-1 ring-primary/20' : ''}"
												onclick={() => toggleModel(m.slug)}
											>
												<div class="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded border {selectedModels.has(m.slug) ? 'bg-primary border-primary text-primary-foreground' : 'border-border'}">
													{#if selectedModels.has(m.slug)}<Check class="h-3 w-3" />{/if}
												</div>
												<span class="font-medium">{m.name}</span>
												<span class="ml-auto font-mono text-xs text-muted-foreground">${m.inputPrice} / ${m.outputPrice}</span>
											</button>
										{/each}
									{/each}
								</div>
							</div>
						</div>
					</Card.Content>
				</Card.Root>
			{/if}

			<!-- Step 3: Review & Generate -->
			{#if step === 3}
				<div class="space-y-4">
					<!-- Summary Bar -->
					<Card.Root>
						<Card.Content class="py-3">
							<div class="flex flex-wrap items-center gap-6 text-sm">
								<div><span class="text-muted-foreground">Combinations:</span> <span class="font-mono font-bold text-primary">{totalPairs}</span></div>
								<div><span class="text-muted-foreground">Scaffolding:</span> <span class="font-medium">{scaffolds.find(s => s.id === selectedScaffold)?.name}</span></div>
								<div><span class="text-muted-foreground">Templates:</span> <span class="font-mono">{selectedTemplates.size}</span></div>
								<div><span class="text-muted-foreground">Models:</span> <span class="font-mono">{selectedModels.size}</span></div>
								<div><span class="text-muted-foreground">Avg $/1K:</span> <span class="font-mono">${avgCost()}</span></div>
							</div>
						</Card.Content>
					</Card.Root>

					<!-- Progress (mock) -->
					<Card.Root>
						<Card.Content class="py-3">
							<div class="flex items-center gap-4">
								<div class="h-1.5 flex-1 rounded-full bg-muted overflow-hidden">
									<div class="h-full rounded-full bg-primary" style="width: 0%"></div>
								</div>
								<span class="text-xs text-muted-foreground font-mono">0 / {totalPairs}</span>
							</div>
							<div class="mt-2 flex gap-4 text-xs">
								<span class="text-emerald-500">0 succeeded</span>
								<span class="text-red-400">0 failed</span>
								<span class="text-muted-foreground">0 in progress</span>
							</div>
						</Card.Content>
					</Card.Root>

					<!-- Results Preview -->
					{#if totalPairs > 0}
						<Card.Root>
							<Card.Header><Card.Title class="text-sm">Job Queue</Card.Title></Card.Header>
							<Card.Content class="p-0">
								<table class="w-full text-sm">
									<thead>
										<tr class="border-b bg-muted/30">
											<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">#</th>
											<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Template</th>
											<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Model</th>
											<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Status</th>
											<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Message</th>
										</tr>
									</thead>
									<tbody class="divide-y">
										{#each [...selectedTemplates].flatMap(t => [...selectedModels].map(m => ({ t, m }))).slice(0, 15) as job, i}
											<tr class="hover:bg-muted/30">
												<td class="px-3 py-2 font-mono text-xs text-muted-foreground">{i + 1}</td>
												<td class="px-3 py-2">{templates.find(t => t.slug === job.t)?.name ?? job.t}</td>
												<td class="px-3 py-2">{models.find(m => m.slug === job.m)?.name ?? job.m}</td>
												<td class="px-3 py-2"><Badge variant="outline" class="text-[10px] bg-zinc-500/15 text-zinc-400">Pending</Badge></td>
												<td class="px-3 py-2 text-xs text-muted-foreground">Queued</td>
											</tr>
										{/each}
										{#if totalPairs > 15}
											<tr><td colspan="5" class="px-3 py-2 text-center text-xs text-muted-foreground">...and {totalPairs - 15} more</td></tr>
										{/if}
									</tbody>
								</table>
							</Card.Content>
						</Card.Root>
					{/if}
				</div>
			{/if}
		</div>

		<!-- Right Column: Sidebar -->
		<div class="space-y-4">
			<!-- Wizard Nav -->
			<Card.Root>
				<Card.Content class="p-4 space-y-4">
					<div class="flex h-1.5 rounded-full bg-muted overflow-hidden">
						<div class="rounded-full bg-primary transition-all" style="width: {(step / 3) * 100}%"></div>
					</div>
					<div class="text-center text-sm text-muted-foreground">Step {step} of 3</div>

					{#if totalPairs > 0}
						<div class="rounded-lg bg-muted/50 p-3 text-center">
							<div class="text-2xl font-bold text-primary">{totalPairs}</div>
							<div class="text-xs text-muted-foreground">{selectedTemplates.size} T × {selectedModels.size} M = {totalPairs} pairs</div>
						</div>
					{/if}

					<div class="flex gap-2">
						<Button variant="outline" size="sm" class="flex-1" disabled={step === 1} onclick={() => step--}>
							<ChevronLeft class="mr-1 h-3.5 w-3.5" /> Back
						</Button>
						{#if step < 3}
							<Button size="sm" class="flex-1" onclick={() => step++}>
								Next <ChevronRight class="ml-1 h-3.5 w-3.5" />
							</Button>
						{:else}
							<Button size="sm" class="flex-1" disabled>
								<Play class="mr-1 h-3.5 w-3.5" /> Start
							</Button>
						{/if}
					</div>
				</Card.Content>
			</Card.Root>

			<!-- Copilot Mode -->
			<Card.Root>
				<Card.Content class="p-4">
					<div class="flex items-center gap-2">
						<h3 class="text-sm font-medium">Copilot Mode</h3>
						<Badge variant="outline" class="text-[10px]">Coming Soon</Badge>
					</div>
					<p class="mt-1 text-xs text-muted-foreground">AI-assisted generation with intelligent defaults and optimization.</p>
				</Card.Content>
			</Card.Root>

			<!-- Selection Summary -->
			<Card.Root>
				<Card.Content class="p-4 space-y-3">
					<h3 class="text-sm font-medium">Summary</h3>
					<div class="space-y-2 text-sm">
						<div class="flex items-center gap-2">
							<Layers class="h-3.5 w-3.5 text-muted-foreground" />
							<span class="text-muted-foreground">Scaffolding:</span>
							<Badge variant="secondary" class="text-[10px]">{scaffolds.find(s => s.id === selectedScaffold)?.name}</Badge>
						</div>

						{#if selectedTemplates.size > 0}
							<div>
								<div class="flex items-center justify-between mb-1">
									<span class="text-xs text-muted-foreground">Templates ({selectedTemplates.size})</span>
									<button class="text-[10px] text-muted-foreground hover:underline" onclick={clearTemplates}>clear</button>
								</div>
								<div class="max-h-24 overflow-y-auto space-y-0.5">
									{#each [...selectedTemplates] as slug}
										<div class="text-xs">{templates.find(t => t.slug === slug)?.name ?? slug}</div>
									{/each}
								</div>
							</div>
						{/if}

						{#if selectedModels.size > 0}
							<div>
								<div class="flex items-center justify-between mb-1">
									<span class="text-xs text-muted-foreground">Models ({selectedModels.size})</span>
									<button class="text-[10px] text-muted-foreground hover:underline" onclick={clearModels}>clear</button>
								</div>
								<div class="max-h-24 overflow-y-auto space-y-0.5">
									{#each [...selectedModels] as slug}
										<div class="text-xs">{models.find(m => m.slug === slug)?.name ?? slug}</div>
									{/each}
								</div>
							</div>
						{/if}

						<Separator />
						<div class="flex justify-between text-xs">
							<span class="text-muted-foreground">Avg $/1K</span>
							<span class="font-mono">${avgCost()}</span>
						</div>
					</div>
				</Card.Content>
			</Card.Root>
		</div>
	</div>
</div>
