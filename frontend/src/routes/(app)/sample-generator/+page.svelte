<script lang="ts">
	import { onMount } from 'svelte';
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { Separator } from '$lib/components/ui/separator';
	import {
		getModels,
		getScaffoldingTemplates,
		getAppTemplates,
		createCustomJob,
		createScaffoldingBatch,
		createCopilotJob,
		getGenerationJobs,
		getGenerationJob,
		getJobArtifacts,
		cancelGenerationJob,
		type LLMModelSummary,
		type ScaffoldingTemplate,
		type AppRequirementTemplate,
		type GenerationJob,
		type GenerationJobList,
		type GenerationArtifact,
		type PaginatedJobs,
	} from '$lib/api/client';
	import Play from '@lucide/svelte/icons/play';
	import Search from '@lucide/svelte/icons/search';
	import Check from '@lucide/svelte/icons/check';
	import X from '@lucide/svelte/icons/x';
	import LoaderCircle from '@lucide/svelte/icons/loader-circle';
	import Clock from '@lucide/svelte/icons/clock';
	import Code from '@lucide/svelte/icons/code';
	import Layers from '@lucide/svelte/icons/layers';
	import Bot from '@lucide/svelte/icons/bot';
	import ChevronDown from '@lucide/svelte/icons/chevron-down';
	import RefreshCw from '@lucide/svelte/icons/refresh-cw';
	import Square from '@lucide/svelte/icons/square';
	import FileCode from '@lucide/svelte/icons/file-code';

	// --- Shared state ---
	type TabId = 'custom' | 'scaffolding' | 'copilot';
	let activeTab = $state<TabId>('custom');
	let models = $state<LLMModelSummary[]>([]);
	let modelsLoading = $state(true);

	// --- Custom mode ---
	let customSystemPrompt = $state('You are an expert full-stack developer. Write clean, well-structured code with proper error handling, type safety, and following best practices.');
	let customUserPrompt = $state('');
	let customModelId = $state<number | ''>('');
	let customTemperature = $state(0.3);
	let customMaxTokens = $state(32000);
	let customSubmitting = $state(false);
	let customError = $state('');
	let customJob = $state<GenerationJob | null>(null);
	let customPolling = $state(false);

	// --- Scaffolding mode ---
	let scaffoldingTemplates = $state<ScaffoldingTemplate[]>([]);
	let appTemplates = $state<AppRequirementTemplate[]>([]);
	let scaffoldingLoading = $state(true);
	let selectedScaffoldId = $state<number | ''>('');
	let selectedAppIds = $state<Set<number>>(new Set());
	let selectedModelIds = $state<Set<number>>(new Set());
	let scaffoldingTemperature = $state(0.3);
	let scaffoldingMaxTokens = $state(32000);
	let scaffoldingSubmitting = $state(false);
	let scaffoldingError = $state('');
	let scaffoldingResult = $state<{ batch_id: string; job_count: number; status: string } | null>(null);
	let appSearch = $state('');
	let modelSearch = $state('');

	// --- Copilot mode ---
	let copilotDescription = $state('');
	let copilotModelId = $state<number | ''>('');
	let copilotMaxIterations = $state(5);
	let copilotUseOpenSource = $state(true);
	let copilotSubmitting = $state(false);
	let copilotError = $state('');
	let copilotJob = $state<GenerationJob | null>(null);
	let copilotPolling = $state(false);

	// --- History ---
	let historyData = $state<PaginatedJobs | null>(null);
	let historyLoading = $state(true);
	let historyPage = $state(1);
	let historyModeFilter = $state('');
	let historyStatusFilter = $state('');
	let expandedJobId = $state<string | null>(null);
	let expandedJob = $state<GenerationJob | null>(null);
	let expandedArtifacts = $state<GenerationArtifact[]>([]);
	let expandedLoading = $state(false);
	let resultTab = $state<'backend' | 'frontend' | 'scan'>('backend');

	const statusColors: Record<string, string> = {
		completed: 'bg-emerald-500/15 text-emerald-500 border-emerald-500/30',
		running: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
		failed: 'bg-red-500/15 text-red-400 border-red-500/30',
		pending: 'bg-amber-500/15 text-amber-500 border-amber-500/30',
		cancelled: 'bg-zinc-500/15 text-zinc-400 border-zinc-500/30',
	};

	const modeLabels: Record<string, string> = {
		custom: 'Custom',
		scaffolding: 'Scaffolding',
		copilot: 'Copilot',
	};

	const filteredAppTemplates = $derived(
		appTemplates.filter(t =>
			t.name.toLowerCase().includes(appSearch.toLowerCase()) ||
			t.description.toLowerCase().includes(appSearch.toLowerCase())
		)
	);

	const filteredModels = $derived(
		models.filter(m =>
			m.model_name.toLowerCase().includes(modelSearch.toLowerCase()) ||
			m.provider.toLowerCase().includes(modelSearch.toLowerCase())
		)
	);

	const modelProviders = $derived([...new Set(filteredModels.map(m => m.provider))].sort());

	// --- Data loading ---
	onMount(async () => {
		const [modelsRes] = await Promise.all([
			getModels({ per_page: 100 }),
			loadScaffoldingData(),
			loadHistory(),
		]);
		models = modelsRes.items;
		modelsLoading = false;
	});

	async function loadScaffoldingData() {
		try {
			const [scaffolds, apps] = await Promise.all([
				getScaffoldingTemplates(),
				getAppTemplates(),
			]);
			scaffoldingTemplates = scaffolds;
			appTemplates = apps;
			if (scaffolds.length > 0) {
				const def = scaffolds.find(s => s.is_default);
				selectedScaffoldId = def ? def.id : scaffolds[0].id;
			}
		} finally {
			scaffoldingLoading = false;
		}
	}

	async function loadHistory() {
		historyLoading = true;
		try {
			historyData = await getGenerationJobs({
				page: historyPage,
				per_page: 15,
				mode: historyModeFilter || undefined,
				status: historyStatusFilter || undefined,
			});
		} catch {
			historyData = null;
		} finally {
			historyLoading = false;
		}
	}

	// --- Custom mode actions ---
	async function submitCustomJob() {
		if (!customModelId || !customUserPrompt.trim()) return;
		customSubmitting = true;
		customError = '';
		customJob = null;
		try {
			const job = await createCustomJob({
				model_id: customModelId as number,
				system_prompt: customSystemPrompt,
				user_prompt: customUserPrompt,
				temperature: customTemperature,
				max_tokens: customMaxTokens,
			});
			customJob = job;
			pollCustomJob(job.id);
			loadHistory();
		} catch (err: any) {
			customError = err?.detail ?? err?.message ?? 'Failed to create job';
		} finally {
			customSubmitting = false;
		}
	}

	async function pollCustomJob(id: string) {
		customPolling = true;
		try {
			while (true) {
				await new Promise(r => setTimeout(r, 2000));
				const job = await getGenerationJob(id);
				customJob = job;
				if (job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled') {
					loadHistory();
					break;
				}
			}
		} catch {
			// polling stopped
		} finally {
			customPolling = false;
		}
	}

	// --- Scaffolding mode actions ---
	function toggleAppTemplate(id: number) {
		const s = new Set(selectedAppIds);
		s.has(id) ? s.delete(id) : s.add(id);
		selectedAppIds = s;
	}

	function toggleModelSelection(id: number) {
		const s = new Set(selectedModelIds);
		s.has(id) ? s.delete(id) : s.add(id);
		selectedModelIds = s;
	}

	function selectAllApps() {
		selectedAppIds = new Set(filteredAppTemplates.map(t => t.id));
	}

	function clearApps() {
		selectedAppIds = new Set();
	}

	function selectAllModelIds() {
		selectedModelIds = new Set(filteredModels.map(m => m.id));
	}

	function clearModelIds() {
		selectedModelIds = new Set();
	}

	async function submitScaffoldingBatch() {
		if (!selectedScaffoldId || selectedAppIds.size === 0 || selectedModelIds.size === 0) return;
		scaffoldingSubmitting = true;
		scaffoldingError = '';
		scaffoldingResult = null;
		try {
			const result = await createScaffoldingBatch({
				scaffolding_template_id: selectedScaffoldId as number,
				app_requirement_ids: [...selectedAppIds],
				model_ids: [...selectedModelIds],
				temperature: scaffoldingTemperature,
				max_tokens: scaffoldingMaxTokens,
			});
			scaffoldingResult = result;
			loadHistory();
		} catch (err: any) {
			scaffoldingError = err?.detail ?? err?.message ?? 'Failed to create batch';
		} finally {
			scaffoldingSubmitting = false;
		}
	}

	// --- Copilot mode actions ---
	async function submitCopilotJob() {
		if (!copilotDescription.trim()) return;
		copilotSubmitting = true;
		copilotError = '';
		copilotJob = null;
		try {
			const job = await createCopilotJob({
				description: copilotDescription,
				model_id: copilotModelId ? (copilotModelId as number) : undefined,
				max_iterations: copilotMaxIterations,
				use_open_source: copilotUseOpenSource,
			});
			copilotJob = job;
			pollCopilotJob(job.id);
			loadHistory();
		} catch (err: any) {
			copilotError = err?.detail ?? err?.message ?? 'Failed to create copilot job';
		} finally {
			copilotSubmitting = false;
		}
	}

	async function pollCopilotJob(id: string) {
		copilotPolling = true;
		try {
			while (true) {
				await new Promise(r => setTimeout(r, 3000));
				const job = await getGenerationJob(id);
				copilotJob = job;
				if (job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled') {
					loadHistory();
					break;
				}
			}
		} catch {
			// polling stopped
		} finally {
			copilotPolling = false;
		}
	}

	// --- History actions ---
	async function toggleExpandJob(id: string) {
		if (expandedJobId === id) {
			expandedJobId = null;
			expandedJob = null;
			expandedArtifacts = [];
			return;
		}
		expandedJobId = id;
		expandedLoading = true;
		try {
			const [job, artifacts] = await Promise.all([
				getGenerationJob(id),
				getJobArtifacts(id),
			]);
			expandedJob = job;
			expandedArtifacts = artifacts;
		} catch {
			expandedJob = null;
			expandedArtifacts = [];
		} finally {
			expandedLoading = false;
		}
	}

	async function cancelJob(id: string) {
		try {
			await cancelGenerationJob(id);
			loadHistory();
		} catch {
			// ignore
		}
	}

	function formatDuration(seconds: number | null): string {
		if (seconds === null || seconds === undefined) return '—';
		if (seconds < 60) return `${seconds.toFixed(0)}s`;
		const m = Math.floor(seconds / 60);
		const s = Math.round(seconds % 60);
		return `${m}m ${s}s`;
	}

	function formatDate(dateStr: string | null): string {
		if (!dateStr) return '—';
		return new Date(dateStr).toLocaleString();
	}
</script>

<svelte:head>
	<title>Sample Generator - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div>
		<div class="flex items-center justify-between">
			<div class="flex items-center gap-3">
				<h1 class="text-2xl font-bold tracking-tight">Sample Generator</h1>
				<Badge variant="outline" class="text-xs">AI-Powered</Badge>
			</div>
			<a href="/sample-generator/templates" class="inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-colors">
				<Layers class="h-3.5 w-3.5" /> Manage Templates
			</a>
		</div>
		<p class="mt-1 text-sm text-muted-foreground">Generate code samples using LLMs with custom prompts, scaffolding templates, or AI copilot.</p>
	</div>

	<!-- Tabs -->
	<div class="flex gap-1 rounded-lg bg-muted p-1 overflow-x-auto flex-nowrap">
		<button
			class="flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors whitespace-nowrap {activeTab === 'custom' ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'}"
			onclick={() => activeTab = 'custom'}
		>
			<Code class="h-4 w-4" />
			Custom
		</button>
		<button
			class="flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors whitespace-nowrap {activeTab === 'scaffolding' ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'}"
			onclick={() => activeTab = 'scaffolding'}
		>
			<Layers class="h-4 w-4" />
			Scaffolding
		</button>
		<button
			class="flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors whitespace-nowrap {activeTab === 'copilot' ? 'bg-background text-foreground shadow-sm' : 'text-muted-foreground hover:text-foreground'}"
			onclick={() => activeTab = 'copilot'}
		>
			<Bot class="h-4 w-4" />
			Copilot
		</button>
	</div>

	<!-- ==================== CUSTOM TAB ==================== -->
	{#if activeTab === 'custom'}
		<div class="grid gap-6 lg:grid-cols-[1fr_360px]">
			<div class="space-y-4">
				<Card.Root>
					<Card.Header>
						<Card.Title>Custom Generation</Card.Title>
						<Card.Description>Send a custom prompt to any model and get a generated response.</Card.Description>
					</Card.Header>
					<Card.Content>
						<div class="space-y-4">
							<div class="space-y-2">
								<Label>System Prompt</Label>
								<textarea
									bind:value={customSystemPrompt}
									rows={3}
									class="flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
									placeholder="Set the AI's behavior and role..."
								></textarea>
							</div>

							<div class="space-y-2">
								<Label>User Prompt</Label>
								<textarea
									bind:value={customUserPrompt}
									rows={6}
									class="flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
									placeholder="Describe what you want the AI to generate..."
								></textarea>
							</div>

							<div class="grid gap-4 grid-cols-1 sm:grid-cols-3">
								<div class="space-y-2">
									<Label>Model</Label>
									{#if modelsLoading}
										<div class="flex h-9 items-center gap-2 rounded-md border px-3 text-sm text-muted-foreground">
											<LoaderCircle class="h-3.5 w-3.5 animate-spin" /> Loading…
										</div>
									{:else}
										<select
											bind:value={customModelId}
											class="flex h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm shadow-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
										>
											<option value="">Select a model</option>
											{#each models as m}
												<option value={m.id}>{m.model_name} ({m.provider})</option>
											{/each}
										</select>
									{/if}
								</div>
								<div class="space-y-2">
									<Label>Temperature: {customTemperature.toFixed(1)}</Label>
									<input
										type="range"
										min="0"
										max="2"
										step="0.1"
										bind:value={customTemperature}
										class="w-full accent-primary"
									/>
									<div class="flex justify-between text-[10px] text-muted-foreground">
										<span>Precise</span>
										<span>Creative</span>
									</div>
								</div>
								<div class="space-y-2">
									<Label>Max Tokens</Label>
									<input
										type="number"
										bind:value={customMaxTokens}
										min={1}
										max={200000}
										class="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
									/>
								</div>
							</div>

							{#if customError}
								<div class="rounded-md bg-red-500/10 border border-red-500/30 px-4 py-3 text-sm text-red-400">
									{customError}
								</div>
							{/if}

							<Button
								onclick={submitCustomJob}
								disabled={customSubmitting || !customModelId || !customUserPrompt.trim()}
							>
								{#if customSubmitting}
									<LoaderCircle class="mr-2 h-4 w-4 animate-spin" /> Submitting…
								{:else}
									<Play class="mr-2 h-4 w-4" /> Generate
								{/if}
							</Button>
						</div>
					</Card.Content>
				</Card.Root>
			</div>

			<!-- Custom Result Panel -->
			<div class="space-y-4">
				{#if customJob}
					<Card.Root>
						<Card.Header class="pb-2">
							<div class="flex items-center justify-between">
								<Card.Title class="text-sm">Job Status</Card.Title>
								<Badge variant="outline" class="text-[10px] {statusColors[customJob.status] ?? ''}">
									{#if customJob.status === 'running' || customJob.status === 'pending'}
										<LoaderCircle class="mr-1 h-3 w-3 animate-spin" />
									{/if}
									{customJob.status}
								</Badge>
							</div>
						</Card.Header>
						<Card.Content>
							<div class="space-y-2 text-sm">
								<div class="flex justify-between">
									<span class="text-muted-foreground">Job ID</span>
									<span class="font-mono text-xs">{customJob.id.slice(0, 8)}…</span>
								</div>
								{#if customJob.model_name}
									<div class="flex justify-between">
										<span class="text-muted-foreground">Model</span>
										<span>{customJob.model_name}</span>
									</div>
								{/if}
								<div class="flex justify-between">
									<span class="text-muted-foreground">Temperature</span>
									<span class="font-mono">{customJob.temperature}</span>
								</div>
								{#if customJob.duration_seconds !== null}
									<div class="flex justify-between">
										<span class="text-muted-foreground">Duration</span>
										<span class="font-mono">{formatDuration(customJob.duration_seconds)}</span>
									</div>
								{/if}
								{#if customJob.error_message}
									<div class="rounded-md bg-red-500/10 border border-red-500/30 px-3 py-2 text-xs text-red-400 mt-2">
										{customJob.error_message}
									</div>
								{/if}
							</div>
						</Card.Content>
					</Card.Root>

					{#if customJob.status === 'completed' && customJob.result_data?.content}
						<Card.Root>
							<Card.Header class="pb-2">
								<Card.Title class="text-sm">Result</Card.Title>
							</Card.Header>
							<Card.Content class="p-0">
								<pre class="max-h-[500px] overflow-x-auto overflow-y-auto rounded-b-xl bg-muted/50 p-4 text-xs font-mono leading-relaxed">{customJob.result_data.content}</pre>
							</Card.Content>
						</Card.Root>
					{/if}
				{:else}
					<Card.Root>
						<Card.Content class="py-12 text-center">
							<Code class="mx-auto h-10 w-10 text-muted-foreground/30" />
							<p class="mt-3 text-sm text-muted-foreground">Submit a prompt to see generation results here.</p>
						</Card.Content>
					</Card.Root>
				{/if}
			</div>
		</div>
	{/if}

	<!-- ==================== SCAFFOLDING TAB ==================== -->
	{#if activeTab === 'scaffolding'}
		<div class="space-y-4">
			<Card.Root>
				<Card.Header>
					<Card.Title>Scaffolding Batch Generation</Card.Title>
					<Card.Description>Select a scaffolding template, app requirements, and models to generate in batch.</Card.Description>
				</Card.Header>
				<Card.Content>
					<div class="space-y-6">
						<!-- Scaffolding Template -->
						<div class="space-y-2">
							<Label>Scaffolding Template</Label>
							{#if scaffoldingLoading}
								<div class="flex h-9 items-center gap-2 rounded-md border px-3 text-sm text-muted-foreground">
									<LoaderCircle class="h-3.5 w-3.5 animate-spin" /> Loading templates…
								</div>
							{:else}
								<div class="grid gap-3 grid-cols-1 sm:grid-cols-2 lg:grid-cols-3">
									{#each scaffoldingTemplates as tpl}
										<button
											class="rounded-lg border p-4 text-left transition-colors {selectedScaffoldId === tpl.id ? 'ring-2 ring-primary bg-primary/5' : 'hover:bg-muted/50'}"
											onclick={() => selectedScaffoldId = tpl.id}
										>
											<div class="flex items-center gap-2">
												<Layers class="h-4 w-4 {selectedScaffoldId === tpl.id ? 'text-primary' : 'text-muted-foreground'}" />
												<span class="text-sm font-medium">{tpl.name}</span>
												{#if tpl.is_default}
													<Badge variant="secondary" class="text-[10px]">Default</Badge>
												{/if}
											</div>
											<p class="mt-1 text-xs text-muted-foreground line-clamp-2">{tpl.description}</p>
											{#if Object.keys(tpl.tech_stack).length > 0}
												<div class="mt-2 flex flex-wrap gap-1">
													{#each Object.entries(tpl.tech_stack) as [key, val]}
														<Badge variant="outline" class="text-[10px]">{key}: {val}</Badge>
													{/each}
												</div>
											{/if}
										</button>
									{/each}
								</div>
								{#if scaffoldingTemplates.length === 0}
									<p class="text-sm text-muted-foreground">No scaffolding templates found. Create one in the admin.</p>
								{/if}
							{/if}
						</div>

						<Separator />

						<!-- App Requirements + Models side by side -->
						<div class="grid gap-4 md:grid-cols-2">
							<!-- App Requirements -->
							<div class="space-y-3">
								<div class="flex items-center justify-between">
									<Label>App Requirements</Label>
									<div class="flex gap-1 text-[10px]">
										<button class="text-primary hover:underline" onclick={selectAllApps}>Select All</button>
										<span class="text-muted-foreground">|</span>
										<button class="text-muted-foreground hover:underline" onclick={clearApps}>Clear</button>
										<span class="ml-1 text-muted-foreground">({selectedAppIds.size})</span>
									</div>
								</div>
								<div class="relative">
									<Search class="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
									<Input bind:value={appSearch} placeholder="Search apps…" class="h-8 pl-8 text-xs" />
								</div>
								<div class="max-h-64 space-y-1 overflow-y-auto rounded-md border p-1">
									{#if scaffoldingLoading}
										<div class="flex items-center justify-center py-6 text-sm text-muted-foreground">
											<LoaderCircle class="mr-2 h-4 w-4 animate-spin" /> Loading…
										</div>
									{:else}
										{#each filteredAppTemplates as app}
											<button
												class="flex w-full items-start gap-2 rounded-md px-2.5 py-2 text-left text-sm transition-colors hover:bg-muted/50 {selectedAppIds.has(app.id) ? 'bg-primary/5 ring-1 ring-primary/20' : ''}"
												onclick={() => toggleAppTemplate(app.id)}
											>
												<div class="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded border {selectedAppIds.has(app.id) ? 'bg-primary border-primary text-primary-foreground' : 'border-border'}">
													{#if selectedAppIds.has(app.id)}<Check class="h-3 w-3" />{/if}
												</div>
												<div class="min-w-0">
													<div class="font-medium">{app.name}</div>
													<div class="text-xs text-muted-foreground line-clamp-1">{app.description}</div>
												</div>
												<Badge variant="secondary" class="ml-auto shrink-0 text-[10px]">{app.category}</Badge>
											</button>
										{/each}
										{#if filteredAppTemplates.length === 0}
											<p class="py-4 text-center text-xs text-muted-foreground">No templates found.</p>
										{/if}
									{/if}
								</div>
							</div>

							<!-- Models -->
							<div class="space-y-3">
								<div class="flex items-center justify-between">
									<Label>Models</Label>
									<div class="flex gap-1 text-[10px]">
										<button class="text-primary hover:underline" onclick={selectAllModelIds}>Select All</button>
										<span class="text-muted-foreground">|</span>
										<button class="text-muted-foreground hover:underline" onclick={clearModelIds}>Clear</button>
										<span class="ml-1 text-muted-foreground">({selectedModelIds.size})</span>
									</div>
								</div>
								<div class="relative">
									<Search class="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
									<Input bind:value={modelSearch} placeholder="Search models…" class="h-8 pl-8 text-xs" />
								</div>
								<div class="max-h-64 space-y-1 overflow-y-auto rounded-md border p-1">
									{#if modelsLoading}
										<div class="flex items-center justify-center py-6 text-sm text-muted-foreground">
											<LoaderCircle class="mr-2 h-4 w-4 animate-spin" /> Loading…
										</div>
									{:else}
										{#each modelProviders as provider}
											<div class="px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">{provider}</div>
											{#each filteredModels.filter(m => m.provider === provider) as m}
												<button
													class="flex w-full items-center gap-2 rounded-md px-2.5 py-2 text-left text-sm transition-colors hover:bg-muted/50 {selectedModelIds.has(m.id) ? 'bg-primary/5 ring-1 ring-primary/20' : ''}"
													onclick={() => toggleModelSelection(m.id)}
												>
													<div class="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded border {selectedModelIds.has(m.id) ? 'bg-primary border-primary text-primary-foreground' : 'border-border'}">
														{#if selectedModelIds.has(m.id)}<Check class="h-3 w-3" />{/if}
													</div>
													<span class="font-medium">{m.model_name}</span>
													{#if m.is_free}
														<Badge variant="secondary" class="ml-auto text-[10px]">Free</Badge>
													{:else}
														<span class="ml-auto font-mono text-xs text-muted-foreground">${m.input_price_per_million}</span>
													{/if}
												</button>
											{/each}
										{/each}
										{#if filteredModels.length === 0}
											<p class="py-4 text-center text-xs text-muted-foreground">No models found.</p>
										{/if}
									{/if}
								</div>
							</div>
						</div>

						<Separator />

						<!-- Controls row -->
						<div class="flex flex-col gap-4 sm:flex-row sm:flex-wrap sm:items-end">
							<div class="space-y-2">
								<Label>Temperature: {scaffoldingTemperature.toFixed(1)}</Label>
								<input
									type="range"
									min="0"
									max="2"
									step="0.1"
									bind:value={scaffoldingTemperature}
									class="w-40 accent-primary"
								/>
							</div>
							<div class="space-y-2">
								<Label>Max Tokens</Label>
								<input
									type="number"
									bind:value={scaffoldingMaxTokens}
									min={1}
									max={200000}
									class="flex h-9 w-32 rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
								/>
							</div>
							<div class="ml-auto flex items-center gap-3">
								{#if selectedAppIds.size > 0 && selectedModelIds.size > 0}
									<span class="text-sm text-muted-foreground">
										{selectedAppIds.size} apps × {selectedModelIds.size} models = <span class="font-bold text-primary">{selectedAppIds.size * selectedModelIds.size}</span> jobs
									</span>
								{/if}
								<Button
									onclick={submitScaffoldingBatch}
									disabled={scaffoldingSubmitting || !selectedScaffoldId || selectedAppIds.size === 0 || selectedModelIds.size === 0}
								>
									{#if scaffoldingSubmitting}
										<LoaderCircle class="mr-2 h-4 w-4 animate-spin" /> Creating…
									{:else}
										<Play class="mr-2 h-4 w-4" /> Generate Batch
									{/if}
								</Button>
							</div>
						</div>

						{#if scaffoldingError}
							<div class="rounded-md bg-red-500/10 border border-red-500/30 px-4 py-3 text-sm text-red-400">
								{scaffoldingError}
							</div>
						{/if}

						{#if scaffoldingResult}
							<div class="rounded-md bg-emerald-500/10 border border-emerald-500/30 px-4 py-3 text-sm text-emerald-400">
								<div class="flex items-center gap-2">
									<Check class="h-4 w-4" />
									Batch created with {scaffoldingResult.job_count} jobs.
								</div>
								<div class="mt-1 text-xs text-muted-foreground">
									Batch ID: <span class="font-mono">{scaffoldingResult.batch_id}</span> · Status: {scaffoldingResult.status}
								</div>
							</div>
						{/if}
					</div>
				</Card.Content>
			</Card.Root>
		</div>
	{/if}

	<!-- ==================== COPILOT TAB ==================== -->
	{#if activeTab === 'copilot'}
		<div class="grid gap-6 lg:grid-cols-[1fr_360px]">
			<Card.Root>
				<Card.Header>
					<Card.Title>Copilot Generation</Card.Title>
					<Card.Description>Describe what you want to build and let the AI copilot iterate to produce it.</Card.Description>
				</Card.Header>
				<Card.Content>
					<div class="space-y-4">
						<div class="space-y-2">
							<Label>Description</Label>
							<textarea
								bind:value={copilotDescription}
								rows={5}
								class="flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
								placeholder="Describe what you want to build. Be specific about features, tech stack, and requirements…"
							></textarea>
						</div>

						<div class="grid gap-4 grid-cols-1 sm:grid-cols-2">
							<div class="space-y-2">
								<Label>Model (optional)</Label>
								{#if modelsLoading}
									<div class="flex h-9 items-center gap-2 rounded-md border px-3 text-sm text-muted-foreground">
										<LoaderCircle class="h-3.5 w-3.5 animate-spin" /> Loading…
									</div>
								{:else}
									<select
										bind:value={copilotModelId}
										class="flex h-9 w-full rounded-md border border-input bg-transparent px-3 text-sm shadow-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
									>
										<option value="">Auto-select</option>
										{#each models as m}
											<option value={m.id}>{m.model_name} ({m.provider})</option>
										{/each}
									</select>
								{/if}
							</div>
							<div class="space-y-2">
								<Label>Max Iterations: {copilotMaxIterations}</Label>
								<input
									type="range"
									min="1"
									max="10"
									step="1"
									bind:value={copilotMaxIterations}
									class="w-full accent-primary"
								/>
								<div class="flex justify-between text-[10px] text-muted-foreground">
									<span>1</span>
									<span>10</span>
								</div>
							</div>
						</div>

						<label class="flex items-center gap-2 text-sm cursor-pointer">
							<div class="relative">
								<input
									type="checkbox"
									bind:checked={copilotUseOpenSource}
									class="peer sr-only"
								/>
								<div class="h-5 w-9 rounded-full bg-muted transition-colors peer-checked:bg-primary"></div>
								<div class="absolute left-0.5 top-0.5 h-4 w-4 rounded-full bg-background shadow-sm transition-transform peer-checked:translate-x-4"></div>
							</div>
							Use open-source models
						</label>

						{#if copilotError}
							<div class="rounded-md bg-red-500/10 border border-red-500/30 px-4 py-3 text-sm text-red-400">
								{copilotError}
							</div>
						{/if}

						<Button
							onclick={submitCopilotJob}
							disabled={copilotSubmitting || !copilotDescription.trim()}
						>
							{#if copilotSubmitting}
								<LoaderCircle class="mr-2 h-4 w-4 animate-spin" /> Starting…
							{:else}
								<Bot class="mr-2 h-4 w-4" /> Start Copilot
							{/if}
						</Button>
					</div>
				</Card.Content>
			</Card.Root>

			<!-- Copilot Result Panel -->
			<div class="space-y-4">
				{#if copilotJob}
					<Card.Root>
						<Card.Header class="pb-2">
							<div class="flex items-center justify-between">
								<Card.Title class="text-sm">Copilot Progress</Card.Title>
								<Badge variant="outline" class="text-[10px] {statusColors[copilotJob.status] ?? ''}">
									{#if copilotJob.status === 'running' || copilotJob.status === 'pending'}
										<LoaderCircle class="mr-1 h-3 w-3 animate-spin" />
									{/if}
									{copilotJob.status}
								</Badge>
							</div>
						</Card.Header>
						<Card.Content>
							<div class="space-y-3">
								<div class="text-sm">
									<div class="flex justify-between mb-1">
										<span class="text-muted-foreground">Iteration</span>
										<span class="font-mono">{copilotJob.copilot_current_iteration} / {copilotJob.copilot_max_iterations}</span>
									</div>
									<div class="h-1.5 rounded-full bg-muted overflow-hidden">
										<div
											class="h-full rounded-full bg-primary transition-all"
											style="width: {copilotJob.copilot_max_iterations > 0 ? (copilotJob.copilot_current_iteration / copilotJob.copilot_max_iterations) * 100 : 0}%"
										></div>
									</div>
								</div>
								{#if copilotJob.model_name}
									<div class="flex justify-between text-sm">
										<span class="text-muted-foreground">Model</span>
										<span>{copilotJob.model_name}</span>
									</div>
								{/if}
								{#if copilotJob.duration_seconds !== null}
									<div class="flex justify-between text-sm">
										<span class="text-muted-foreground">Duration</span>
										<span class="font-mono">{formatDuration(copilotJob.duration_seconds)}</span>
									</div>
								{/if}
								{#if copilotJob.app_directory}
									<div class="flex justify-between text-sm">
										<span class="text-muted-foreground">Directory</span>
										<span class="font-mono text-xs truncate max-w-[180px]">{copilotJob.app_directory}</span>
									</div>
								{/if}
								{#if copilotJob.error_message}
									<div class="rounded-md bg-red-500/10 border border-red-500/30 px-3 py-2 text-xs text-red-400">
										{copilotJob.error_message}
									</div>
								{/if}
								{#if (copilotJob.status === 'running' || copilotJob.status === 'pending')}
									<Button variant="outline" size="sm" onclick={() => cancelJob(copilotJob!.id)}>
										<Square class="mr-1.5 h-3.5 w-3.5" /> Cancel
									</Button>
								{/if}
							</div>
						</Card.Content>
					</Card.Root>

					{#if copilotJob.status === 'completed' && copilotJob.result_data && Object.keys(copilotJob.result_data).length > 0}
						<Card.Root>
							<Card.Header class="pb-2">
								<Card.Title class="text-sm">Result</Card.Title>
							</Card.Header>
							<Card.Content class="p-0">
								<pre class="max-h-[400px] overflow-auto rounded-b-xl bg-muted/50 p-4 text-xs font-mono leading-relaxed">{JSON.stringify(copilotJob.result_data, null, 2)}</pre>
							</Card.Content>
						</Card.Root>
					{/if}
				{:else}
					<Card.Root>
						<Card.Content class="py-12 text-center">
							<Bot class="mx-auto h-10 w-10 text-muted-foreground/30" />
							<p class="mt-3 text-sm text-muted-foreground">Start the copilot to see progress here.</p>
						</Card.Content>
					</Card.Root>
				{/if}
			</div>
		</div>
	{/if}

	<!-- ==================== HISTORY SECTION ==================== -->
	<Separator />

	<Card.Root>
		<Card.Header>
			<div class="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
				<div>
					<Card.Title>Generation History</Card.Title>
					<Card.Description>Past generation jobs and their results.</Card.Description>
				</div>
				<div class="flex flex-wrap items-center gap-2">
					<select
						bind:value={historyModeFilter}
						onchange={() => { historyPage = 1; loadHistory(); }}
						class="h-8 rounded-md border bg-transparent px-2 text-xs"
					>
						<option value="">All modes</option>
						<option value="custom">Custom</option>
						<option value="scaffolding">Scaffolding</option>
						<option value="copilot">Copilot</option>
					</select>
					<select
						bind:value={historyStatusFilter}
						onchange={() => { historyPage = 1; loadHistory(); }}
						class="h-8 rounded-md border bg-transparent px-2 text-xs"
					>
						<option value="">All statuses</option>
						<option value="pending">Pending</option>
						<option value="running">Running</option>
						<option value="completed">Completed</option>
						<option value="failed">Failed</option>
						<option value="cancelled">Cancelled</option>
					</select>
					<Button variant="outline" size="sm" onclick={loadHistory} disabled={historyLoading}>
						<RefreshCw class="h-3.5 w-3.5 {historyLoading ? 'animate-spin' : ''}" />
					</Button>
				</div>
			</div>
		</Card.Header>
		<Card.Content class="p-0">
			{#if historyLoading && !historyData}
				<div class="flex items-center justify-center py-12 text-sm text-muted-foreground">
					<LoaderCircle class="mr-2 h-4 w-4 animate-spin" /> Loading history…
				</div>
			{:else if historyData && historyData.items.length > 0}
				<div class="overflow-x-auto">
				<table class="w-full text-sm">
					<thead>
						<tr class="border-b bg-muted/30">
							<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Mode</th>
							<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Status</th>
							<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Model</th>
							<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Template</th>
							<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Duration</th>
							<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Created</th>
						</tr>
					</thead>
					<tbody class="divide-y">
						{#each historyData.items as job}
							<tr
								class="hover:bg-muted/30 cursor-pointer transition-colors {expandedJobId === job.id ? 'bg-muted/20' : ''}"
								onclick={() => toggleExpandJob(job.id)}
							>
								<td class="px-3 py-2">
									<Badge variant="secondary" class="text-[10px]">{modeLabels[job.mode] ?? job.mode}</Badge>
								</td>
								<td class="px-3 py-2">
									<Badge variant="outline" class="text-[10px] {statusColors[job.status] ?? ''}">
										{#if job.status === 'running' || job.status === 'pending'}
											<LoaderCircle class="mr-1 h-3 w-3 animate-spin" />
										{/if}
										{job.status}
									</Badge>
								</td>
								<td class="px-3 py-2 text-xs">{job.model_name ?? '—'}</td>
								<td class="px-3 py-2 text-xs">{job.template_name ?? job.scaffolding_name ?? '—'}</td>
								<td class="px-3 py-2 text-xs font-mono text-muted-foreground">{formatDuration(job.duration_seconds)}</td>
								<td class="px-3 py-2 text-xs text-muted-foreground">{formatDate(job.created_at)}</td>
							</tr>

							<!-- Expanded row -->
							{#if expandedJobId === job.id}
								<tr>
									<td colspan="6" class="bg-muted/10 px-4 py-4">
										{#if expandedLoading}
											<div class="flex items-center gap-2 text-sm text-muted-foreground">
												<LoaderCircle class="h-4 w-4 animate-spin" /> Loading details…
											</div>
										{:else if expandedJob}
											<div class="space-y-3">
												<div class="grid gap-4 grid-cols-1 sm:grid-cols-3 text-sm">
													<div>
														<span class="text-muted-foreground">Job ID:</span>
														<span class="ml-1 font-mono text-xs">{expandedJob.id}</span>
													</div>
													{#if expandedJob.error_message}
														<div class="md:col-span-2">
															<span class="text-muted-foreground">Error:</span>
															<span class="ml-1 text-red-400">{expandedJob.error_message}</span>
														</div>
													{/if}
													{#if expandedJob.temperature}
														<div>
															<span class="text-muted-foreground">Temperature:</span>
															<span class="ml-1 font-mono">{expandedJob.temperature}</span>
														</div>
													{/if}
													{#if expandedJob.max_tokens}
														<div>
															<span class="text-muted-foreground">Max Tokens:</span>
															<span class="ml-1 font-mono">{expandedJob.max_tokens}</span>
														</div>
													{/if}
												</div>

												{#if expandedJob.result_data && Object.keys(expandedJob.result_data).length > 0}
													<div>
														<h4 class="text-xs font-medium text-muted-foreground mb-1">Result</h4>
														{#if expandedJob.mode === 'scaffolding' && expandedJob.result_data.backend_code}
															<!-- Scaffolding: show backend + frontend tabs -->
															<div class="space-y-2">
																<div class="flex gap-1">
																	<button
																		class="rounded-md px-2 py-1 text-xs {resultTab === 'backend' ? 'bg-primary text-primary-foreground' : 'bg-muted/50 text-muted-foreground hover:text-foreground'}"
																		onclick={() => resultTab = 'backend'}
																	>Backend ({expandedJob.result_data.backend_code?.length ?? 0} chars)</button>
																	<button
																		class="rounded-md px-2 py-1 text-xs {resultTab === 'frontend' ? 'bg-primary text-primary-foreground' : 'bg-muted/50 text-muted-foreground hover:text-foreground'}"
																		onclick={() => resultTab = 'frontend'}
																	>Frontend ({expandedJob.result_data.frontend_code?.length ?? 0} chars)</button>
																	{#if expandedJob.result_data.backend_scan}
																		<button
																			class="rounded-md px-2 py-1 text-xs {resultTab === 'scan' ? 'bg-primary text-primary-foreground' : 'bg-muted/50 text-muted-foreground hover:text-foreground'}"
																			onclick={() => resultTab = 'scan'}
																		>API Scan</button>
																	{/if}
																</div>
																{#if resultTab === 'backend'}
																	<pre class="max-h-64 overflow-auto rounded-md bg-muted/50 p-3 text-xs font-mono">{expandedJob.result_data.backend_code}</pre>
																{:else if resultTab === 'frontend'}
																	<pre class="max-h-64 overflow-auto rounded-md bg-muted/50 p-3 text-xs font-mono">{expandedJob.result_data.frontend_code}</pre>
																{:else if resultTab === 'scan'}
																	<div class="rounded-md bg-muted/50 p-3 text-xs space-y-2">
																		<div><span class="text-muted-foreground">Endpoints:</span> {expandedJob.result_data.backend_scan?.endpoints?.length ?? 0}</div>
																		<div><span class="text-muted-foreground">Models:</span> {expandedJob.result_data.backend_scan?.models?.length ?? 0}</div>
																		{#if expandedJob.result_data.backend_dependencies?.length}
																			<div><span class="text-muted-foreground">Dependencies:</span> {expandedJob.result_data.backend_dependencies.join(', ')}</div>
																		{/if}
																		{#if expandedJob.result_data.backend_scan?.endpoints}
																			<div class="mt-2">
																				<span class="font-medium">Endpoints:</span>
																				{#each expandedJob.result_data.backend_scan.endpoints as ep}
																					<div class="ml-2 font-mono">{ep.method} {ep.path} {ep.requires_auth ? '🔒' : ''}</div>
																				{/each}
																			</div>
																		{/if}
																	</div>
																{/if}
																{#if expandedJob.result_data.backend_truncated || expandedJob.result_data.frontend_truncated}
																	<div class="text-xs text-amber-400">⚠ Output was truncated ({expandedJob.result_data.backend_truncated ? 'backend' : ''}{expandedJob.result_data.backend_truncated && expandedJob.result_data.frontend_truncated ? ' + ' : ''}{expandedJob.result_data.frontend_truncated ? 'frontend' : ''})</div>
																{/if}
															</div>
														{:else if expandedJob.mode === 'copilot' && expandedJob.result_data.content}
															<!-- Copilot: show result with iteration info -->
															<div class="space-y-2">
																{#if expandedJob.result_data.iterations_completed}
																	<div class="flex items-center gap-3 text-xs">
																		<span class="text-muted-foreground">Iterations: {expandedJob.result_data.iterations_completed}</span>
																		{#if expandedJob.result_data.dependencies?.length}
																			<span class="text-muted-foreground">Deps: {expandedJob.result_data.dependencies.join(', ')}</span>
																		{/if}
																		{#if expandedJob.result_data.final_errors?.length}
																			<span class="text-amber-400">⚠ {expandedJob.result_data.final_errors.length} remaining errors</span>
																		{/if}
																	</div>
																{/if}
																<pre class="max-h-64 overflow-auto rounded-md bg-muted/50 p-3 text-xs font-mono">{expandedJob.result_data.content}</pre>
															</div>
														{:else}
															<!-- Custom/other: show content or JSON -->
															<pre class="max-h-48 overflow-auto rounded-md bg-muted/50 p-3 text-xs font-mono">{expandedJob.result_data.content ?? JSON.stringify(expandedJob.result_data, null, 2)}</pre>
														{/if}
													</div>
												{/if}

												{#if expandedArtifacts.length > 0}
													<div>
														<h4 class="text-xs font-medium text-muted-foreground mb-1">Artifacts ({expandedArtifacts.length})</h4>
														<div class="space-y-2">
															{#each expandedArtifacts as artifact}
																<div class="rounded-md border p-3 text-xs">
																	<div class="flex items-center gap-3 mb-1">
																		<Badge variant="outline" class="text-[10px]">{artifact.stage}</Badge>
																		<span class="text-muted-foreground">Tokens: {artifact.prompt_tokens} + {artifact.completion_tokens}</span>
																		{#if artifact.total_cost > 0}
																			<span class="text-muted-foreground">Cost: ${artifact.total_cost.toFixed(4)}</span>
																		{/if}
																	</div>
																</div>
															{/each}
														</div>
													</div>
												{/if}

												<div class="flex gap-2">
													{#if expandedJob.status === 'running' || expandedJob.status === 'pending'}
														<Button variant="destructive" size="sm" onclick={() => cancelJob(expandedJob!.id)}>
															<Square class="mr-1.5 h-3.5 w-3.5" /> Cancel Job
														</Button>
													{/if}
												</div>
											</div>
										{/if}
									</td>
								</tr>
							{/if}
						{/each}
					</tbody>
				</table>
				</div>

				<!-- Pagination -->
				{#if historyData.pages > 1}
					<div class="flex items-center justify-between border-t px-4 py-3">
						<span class="text-xs text-muted-foreground">
							Page {historyData.page} of {historyData.pages} ({historyData.total} total)
						</span>
						<div class="flex gap-1">
							<Button
								variant="outline"
								size="sm"
								disabled={historyData.page <= 1}
								onclick={() => { historyPage = historyData!.page - 1; loadHistory(); }}
							>
								Previous
							</Button>
							<Button
								variant="outline"
								size="sm"
								disabled={historyData.page >= historyData.pages}
								onclick={() => { historyPage = historyData!.page + 1; loadHistory(); }}
							>
								Next
							</Button>
						</div>
					</div>
				{/if}
			{:else}
				<div class="flex flex-col items-center justify-center py-12 text-sm text-muted-foreground">
					<FileCode class="mb-3 h-10 w-10 text-muted-foreground/30" />
					<p>No generation jobs yet.</p>
					<p class="text-xs mt-1">Create your first job using any of the tabs above.</p>
				</div>
			{/if}
		</Card.Content>
	</Card.Root>
</div>
