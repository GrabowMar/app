<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { Separator } from '$lib/components/ui/separator';
	import ArrowLeft from '@lucide/svelte/icons/arrow-left';
	import ArrowRight from '@lucide/svelte/icons/arrow-right';
	import Check from '@lucide/svelte/icons/check';
	import Search from '@lucide/svelte/icons/search';
	import Rocket from '@lucide/svelte/icons/rocket';
	import Settings from '@lucide/svelte/icons/settings';
	import RefreshCw from '@lucide/svelte/icons/refresh-cw';
	import Loader from '@lucide/svelte/icons/loader-circle';
	import FileCode from '@lucide/svelte/icons/file-code';
	import ClipboardPaste from '@lucide/svelte/icons/clipboard-paste';
	import AlertCircle from '@lucide/svelte/icons/alert-circle';
	import {
		getAnalyzers,
		getGenerationJobs,
		createAnalysisTask,
		type AnalyzerInfo,
		type GenerationJobList,
	} from '$lib/api/client';
	import { analyzerTypeLabels } from '$lib/constants/analysis';

	// -- Wizard state --
	let step = $state(1);
	const stepLabels = ['Select Source', 'Analyzers', 'Configure', 'Review'];

	// -- Step 1: Source --
	type SourceMode = 'job' | 'paste';
	let sourceMode = $state<SourceMode>('job');
	let jobsLoading = $state(true);
	let jobsError = $state('');
	let jobs = $state<GenerationJobList[]>([]);
	let selectedJobId = $state<string | null>(null);
	let jobSearch = $state('');
	let pasteBackend = $state('');
	let pasteFrontend = $state('');

	const filteredJobs = $derived(
		jobs.filter(
			(j) =>
				!jobSearch ||
				(j.model_name ?? '').toLowerCase().includes(jobSearch.toLowerCase()) ||
				(j.template_name ?? '').toLowerCase().includes(jobSearch.toLowerCase()) ||
				j.id.toLowerCase().includes(jobSearch.toLowerCase()),
		),
	);

	const selectedJob = $derived(jobs.find((j) => j.id === selectedJobId));

	const hasSource = $derived(
		sourceMode === 'job'
			? selectedJobId !== null
			: pasteBackend.trim().length > 0 || pasteFrontend.trim().length > 0,
	);

	// -- Step 2: Analyzers --
	let analyzersLoading = $state(true);
	let analyzersError = $state('');
	let analyzers = $state<AnalyzerInfo[]>([]);
	let selectedAnalyzers = $state(new Set<string>());

	const analyzerTypes = ['static', 'dynamic', 'performance', 'ai'] as const;
	const typeColors: Record<string, string> = {
		static: 'text-blue-400 border-blue-500/30 bg-blue-500/10',
		dynamic: 'text-emerald-500 border-emerald-500/30 bg-emerald-500/10',
		performance: 'text-cyan-400 border-cyan-500/30 bg-cyan-500/10',
		ai: 'text-amber-500 border-amber-500/30 bg-amber-500/10',
	};
	const typeLabels = analyzerTypeLabels;

	function analyzersByType(type: string) {
		return analyzers.filter((a) => a.type === type);
	}

	function toggleAnalyzer(name: string) {
		const next = new Set(selectedAnalyzers);
		if (next.has(name)) next.delete(name);
		else next.add(name);
		selectedAnalyzers = next;
	}

	function selectAllAnalyzers() {
		selectedAnalyzers = new Set(analyzers.filter((a) => a.available).map((a) => a.name));
	}

	function clearAllAnalyzers() {
		selectedAnalyzers = new Set();
	}

	// -- Step 3: Configure --
	let taskName = $state('');
	let autoStart = $state(true);
	let liveTarget = $state(false);
	let analyzerSettings = $state<Record<string, string>>({});

	let settingsErrors = $state<Record<string, string>>({});

	function getSettingsJson(analyzerName: string): Record<string, any> {
		const raw = analyzerSettings[analyzerName];
		if (!raw || !raw.trim()) {
			delete settingsErrors[analyzerName];
			return {};
		}
		try {
			const parsed = JSON.parse(raw);
			delete settingsErrors[analyzerName];
			return parsed;
		} catch (e: any) {
			settingsErrors[analyzerName] = e.message || 'Invalid JSON';
			return {};
		}
	}

	const selectedAnalyzersList = $derived(
		analyzers.filter((a) => selectedAnalyzers.has(a.name)),
	);

	// -- Step 4: Launch --
	let launching = $state(false);
	let launchError = $state('');

	async function handleLaunch() {
		launching = true;
		launchError = '';
		const hasErrors = Object.keys(settingsErrors).some(k => settingsErrors[k]);
		if (hasErrors) {
			launchError = 'Please fix JSON configuration errors before launching.';
			launching = false;
			return;
		}
		try {
			const settingsMap: Record<string, any> = {};
			for (const a of selectedAnalyzersList) {
				settingsMap[a.name] = getSettingsJson(a.name);
			}

			const task = await createAnalysisTask({
				name: taskName || undefined,
				generation_job_id: sourceMode === 'job' ? selectedJobId : undefined,
				source_code:
					sourceMode === 'paste'
						? { backend: pasteBackend, frontend: pasteFrontend }
						: {},
				analyzers: [...selectedAnalyzers],
				settings: settingsMap,
				auto_start: autoStart,
				live_target: sourceMode === 'job' && liveTarget ? true : undefined,
			});
			await goto(`/analysis/${task.id}`);
		} catch (err: any) {
			launchError = err?.detail ?? err?.message ?? 'Failed to create analysis task';
		} finally {
			launching = false;
		}
	}

	// -- Data fetching --
	async function loadJobs() {
		jobsLoading = true;
		jobsError = '';
		try {
			const res = await getGenerationJobs({ status: 'completed', per_page: 100 });
			jobs = res.items;
		} catch (err: any) {
			jobsError = err?.detail ?? 'Failed to load generation jobs';
		} finally {
			jobsLoading = false;
		}
	}

	async function loadAnalyzers() {
		analyzersLoading = true;
		analyzersError = '';
		try {
			analyzers = await getAnalyzers();
		} catch (err: any) {
			analyzersError = err?.detail ?? 'Failed to load analyzers';
		} finally {
			analyzersLoading = false;
		}
	}

	onMount(() => {
		loadJobs();
		loadAnalyzers();
	});

	// -- Validation --
	const canAdvance = $derived.by(() => {
		if (step === 1) return hasSource;
		if (step === 2) return selectedAnalyzers.size > 0;
		if (step === 3) return true;
		return true;
	});
</script>

<svelte:head>
	<title>New Analysis - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<!-- Breadcrumb -->
	<div class="flex items-center gap-2 text-sm text-muted-foreground">
		<Button variant="ghost" size="sm" href="/analysis" class="gap-1.5 px-2">
			<ArrowLeft class="h-3.5 w-3.5" />
			Analysis Hub
		</Button>
		<span>/</span>
		<span class="text-foreground font-medium">New Analysis</span>
	</div>

	<div class="page-header">
		<h1>New Analysis</h1>
		<p>Configure and launch an analysis pipeline.</p>
	</div>

	<!-- Layout: steps left, sidebar right -->
	<div class="grid gap-4 sm:gap-6 lg:grid-cols-4">
		<!-- Main Content (3/4) -->
		<div class="space-y-6 lg:col-span-3">
			<!-- Step Progress -->
			<div class="flex items-center gap-2 overflow-x-auto">
				{#each stepLabels as label, i}
					<button
						class="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm transition-colors {step ===
						i + 1
							? 'bg-primary/10 text-primary font-medium'
							: i + 1 < step
								? 'text-emerald-500'
								: 'text-muted-foreground'}"
						onclick={() => {
							if (i + 1 <= step) step = i + 1;
						}}
					>
						<span
							class="flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold {step ===
							i + 1
								? 'bg-primary text-primary-foreground'
								: i + 1 < step
									? 'bg-emerald-500 text-white'
									: 'bg-muted text-muted-foreground'}"
						>
							{#if i + 1 < step}
								<Check class="h-3 w-3" />
							{:else}
								{i + 1}
							{/if}
						</span>
						{label}
					</button>
					{#if i < stepLabels.length - 1}
						<div class="h-px flex-1 bg-border"></div>
					{/if}
				{/each}
			</div>

			<!-- ===== Step 1: Select Source ===== -->
			{#if step === 1}
				<Card.Root>
					<Card.Header>
						<Card.Title>Select Source</Card.Title>
						<Card.Description
							>Choose a completed generation job or paste code directly.</Card.Description
						>
					</Card.Header>
					<Card.Content>
						<!-- Mode Toggle -->
						<div class="mb-4 flex gap-2">
							<Button
								variant={sourceMode === 'job' ? 'default' : 'outline'}
								size="sm"
								onclick={() => (sourceMode = 'job')}
							>
								<FileCode class="mr-1.5 h-3.5 w-3.5" />
								Generation Job
							</Button>
							<Button
								variant={sourceMode === 'paste' ? 'default' : 'outline'}
								size="sm"
								onclick={() => (sourceMode = 'paste')}
							>
								<ClipboardPaste class="mr-1.5 h-3.5 w-3.5" />
								Paste Code
							</Button>
						</div>

						{#if sourceMode === 'job'}
							<!-- Job list -->
							<div class="mb-4">
								<div class="relative max-w-sm">
									<Search
										class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
									/>
									<input
										type="text"
										placeholder="Search jobs..."
										class="h-9 w-full rounded-md border border-input bg-background pl-9 pr-3 text-sm"
										bind:value={jobSearch}
									/>
								</div>
							</div>

							{#if jobsLoading}
								<div class="flex items-center justify-center py-12 text-muted-foreground">
									<Loader class="mr-2 h-4 w-4 animate-spin" />
									Loading jobs…
								</div>
							{:else if jobsError}
								<div
									class="flex items-center gap-2 rounded-md border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400"
								>
									<AlertCircle class="h-4 w-4 shrink-0" />
									{jobsError}
									<Button variant="outline" size="sm" class="ml-auto" onclick={loadJobs}
										>Retry</Button
									>
								</div>
							{:else if filteredJobs.length === 0}
								<div class="py-12 text-center text-sm text-muted-foreground">
									{jobs.length === 0
										? 'No completed generation jobs found.'
										: 'No jobs match your search.'}
								</div>
							{:else}
								<div class="overflow-x-auto table-scroll-wrapper">
									<table class="w-full text-sm">
										<thead>
											<tr class="border-b bg-muted/30">
												<th
													class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground"
													>Job ID</th
												>
												<th
													class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground"
													>Model</th
												>
												<th
													class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground"
													>Template</th
												>
												<th
													class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground"
													>Completed</th
												>
												<th
													class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground"
												></th>
											</tr>
										</thead>
										<tbody class="divide-y">
											{#each filteredJobs as job}
												<tr
													class="transition-colors hover:bg-muted/30 {selectedJobId ===
													job.id
														? 'bg-primary/5'
														: ''}"
												>
													<td class="px-4 py-2.5 font-mono text-xs"
														>{job.id.slice(0, 8)}…</td
													>
													<td class="px-4 py-2.5"
														>{job.model_name ?? '—'}</td
													>
													<td class="px-4 py-2.5"
														>{job.template_name ?? '—'}</td
													>
													<td class="px-4 py-2.5 text-xs text-muted-foreground">
														{job.completed_at
															? new Date(job.completed_at).toLocaleDateString()
															: '—'}
													</td>
													<td class="px-4 py-2.5">
														<Button
															variant={selectedJobId === job.id
																? 'default'
																: 'outline'}
															size="sm"
															class="h-7 text-xs"
															onclick={() => (selectedJobId = job.id)}
														>
															{selectedJobId === job.id
																? 'Selected'
																: 'Select'}
														</Button>
													</td>
												</tr>
											{/each}
										</tbody>
									</table>
								</div>
							{/if}
						{:else}
							<!-- Paste code -->
							<div class="space-y-4">
								<div>
									<label class="mb-1 block text-sm font-medium"
										>Backend Code</label
									>
									<textarea
										class="h-40 w-full rounded-md border border-input bg-background p-3 font-mono text-sm"
										placeholder="Paste backend code here…"
										bind:value={pasteBackend}
									></textarea>
								</div>
								<div>
									<label class="mb-1 block text-sm font-medium"
										>Frontend Code</label
									>
									<textarea
										class="h-40 w-full rounded-md border border-input bg-background p-3 font-mono text-sm"
										placeholder="Paste frontend code here…"
										bind:value={pasteFrontend}
									></textarea>
								</div>
							</div>
						{/if}
					</Card.Content>
				</Card.Root>
			{/if}

			<!-- ===== Step 2: Select Analyzers ===== -->
			{#if step === 2}
				<div class="space-y-4">
					<!-- Header -->
					<div
						class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between"
					>
						<div class="flex items-center gap-2">
							<Button variant="outline" size="sm" onclick={selectAllAnalyzers}
								>Select All</Button
							>
							<Button variant="outline" size="sm" onclick={clearAllAnalyzers}
								>Clear All</Button
							>
							<Button variant="outline" size="sm" onclick={loadAnalyzers}>
								<RefreshCw class="mr-1.5 h-3 w-3" /> Refresh
							</Button>
						</div>
						<Badge variant="outline"
							>{selectedAnalyzers.size} analyzer{selectedAnalyzers.size !== 1
								? 's'
								: ''} selected</Badge
						>
					</div>

					{#if analyzersLoading}
						<div
							class="flex items-center justify-center py-12 text-muted-foreground"
						>
							<Loader class="mr-2 h-4 w-4 animate-spin" />
							Loading analyzers…
						</div>
					{:else if analyzersError}
						<div
							class="flex items-center gap-2 rounded-md border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400"
						>
							<AlertCircle class="h-4 w-4 shrink-0" />
							{analyzersError}
							<Button
								variant="outline"
								size="sm"
								class="ml-auto"
								onclick={loadAnalyzers}>Retry</Button
							>
						</div>
					{:else}
						<!-- Analyzer Cards grouped by type -->
						<div class="grid grid-cols-1 gap-4 md:grid-cols-2">
							{#each analyzerTypes as type}
								{@const group = analyzersByType(type)}
								{#if group.length > 0}
									{@const colorClasses = typeColors[type] ?? ''}
									{@const borderClass = colorClasses
										.split(' ')
										.filter((c) => c.startsWith('border-'))
										.join(' ')}
									{@const textClass = colorClasses
										.split(' ')
										.filter((c) => c.startsWith('text-'))
										.join(' ')}
									<Card.Root class="border {borderClass}">
										<Card.Header>
											<div class="flex items-center justify-between">
												<Card.Title class="text-sm {textClass}"
													>{typeLabels[type] ?? type}</Card.Title
												>
												<Badge variant="outline" class="text-[10px]">
													{group.filter((a) => a.available).length}/{group.length}
													available
												</Badge>
											</div>
											<Card.Description
												>{group.length} analyzer{group.length !== 1
													? 's'
													: ''}</Card.Description
											>
										</Card.Header>
										<Card.Content>
											<div class="space-y-2">
												{#each group as analyzer}
													<label
														class="flex items-center gap-2.5 rounded-md px-2 py-1.5 transition-colors {analyzer.available
															? 'cursor-pointer hover:bg-muted/30'
															: 'cursor-not-allowed opacity-50'}"
													>
														<input
															type="checkbox"
															class="rounded"
															checked={selectedAnalyzers.has(
																analyzer.name,
															)}
															disabled={!analyzer.available}
															onchange={() =>
																toggleAnalyzer(analyzer.name)}
														/>
														<div class="min-w-0 flex-1">
															<div class="text-sm font-medium">
																{analyzer.display_name}
															</div>
															<div
																class="text-xs text-muted-foreground"
															>
																{analyzer.description}
															</div>
															{#if !analyzer.available && analyzer.availability_message}
																<div
																	class="mt-0.5 text-xs text-amber-500"
																>
																	{analyzer.availability_message}
																</div>
															{/if}
														</div>
													</label>
												{/each}
											</div>
										</Card.Content>
									</Card.Root>
								{/if}
							{/each}
						</div>
					{/if}
				</div>
			{/if}

			<!-- ===== Step 3: Configure ===== -->
			{#if step === 3}
				<div class="space-y-4">
					<!-- Task Configuration -->
					<Card.Root>
						<Card.Header>
							<div class="flex items-center gap-2">
								<Settings class="h-4 w-4 text-muted-foreground" />
								<Card.Title class="text-sm">Task Configuration</Card.Title>
							</div>
						</Card.Header>
						<Card.Content>
							<div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
								<div>
									<label class="text-sm font-medium">Task Name</label>
									<input
										type="text"
										class="mt-1 h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
										placeholder="Optional task name…"
										bind:value={taskName}
									/>
								</div>
								<div class="flex items-center gap-2 pt-6">
									<input
										type="checkbox"
										id="autoStart"
										bind:checked={autoStart}
										class="rounded"
									/>
									<label for="autoStart" class="text-sm"
										>Auto-start analysis</label
									>
								</div>
								{#if sourceMode === 'job' && selectedJobId}
									<div class="flex items-center gap-2 pt-6">
										<input
											type="checkbox"
											id="liveTarget"
											bind:checked={liveTarget}
											class="rounded"
										/>
										<label for="liveTarget" class="text-sm">
											Run against live container
											<span class="ml-1 text-xs text-muted-foreground"
												>(starts Docker container for dynamic analysis)</span
											>
										</label>
									</div>
								{/if}
							</div>
						</Card.Content>
					</Card.Root>

					<!-- Per-analyzer settings -->
					{#if selectedAnalyzersList.length > 0}
						<Card.Root>
							<Card.Header>
								<Card.Title class="text-sm">Analyzer Settings</Card.Title>
								<Card.Description
									>Override default configuration per analyzer (JSON).</Card.Description
								>
							</Card.Header>
							<Card.Content>
								<div class="space-y-4">
									{#each selectedAnalyzersList as analyzer}
										<div>
											<label class="mb-1 block text-sm font-medium"
												>{analyzer.display_name}</label
											>
											<textarea
												class="h-20 w-full rounded-md border border-input bg-background p-2 font-mono text-xs"
												placeholder={JSON.stringify(analyzer.default_config, null, 2) || '{}'}
												bind:value={analyzerSettings[analyzer.name]}
											></textarea>
											{#if settingsErrors[analyzer.name]}
												<p class="text-xs text-red-500 mt-1">{settingsErrors[analyzer.name]}</p>
											{/if}
										</div>
									{/each}
								</div>
							</Card.Content>
						</Card.Root>
					{/if}
				</div>
			{/if}

			<!-- ===== Step 4: Review & Launch ===== -->
			{#if step === 4}
				<Card.Root>
					<Card.Header>
						<Card.Title>Review & Launch</Card.Title>
						<Card.Description
							>Review your configuration before launching the analysis.</Card.Description
						>
					</Card.Header>
					<Card.Content>
						<div class="overflow-x-auto table-scroll-wrapper">
							<table class="w-full text-sm">
								<tbody class="divide-y">
									<tr>
										<td
											class="w-40 px-4 py-3 font-medium text-muted-foreground"
											>Source</td
										>
										<td class="px-4 py-3">
											{#if sourceMode === 'job' && selectedJob}
												<Badge variant="outline" class="mr-1 text-[10px]"
													>Job</Badge
												>
												{selectedJob.model_name ?? selectedJob.id.slice(0, 8)}
											{:else if sourceMode === 'paste'}
												<Badge variant="outline" class="mr-1 text-[10px]"
													>Pasted Code</Badge
												>
												{pasteBackend.trim() ? 'Backend' : ''}{pasteBackend.trim() && pasteFrontend.trim() ? ' + ' : ''}{pasteFrontend.trim() ? 'Frontend' : ''}
											{:else}
												—
											{/if}
										</td>
									</tr>
									{#if taskName}
										<tr>
											<td
												class="px-4 py-3 font-medium text-muted-foreground"
												>Name</td
											>
											<td class="px-4 py-3">{taskName}</td>
										</tr>
									{/if}
									<tr>
										<td class="px-4 py-3 font-medium text-muted-foreground"
											>Analyzers</td
										>
										<td class="px-4 py-3">
											<div class="flex flex-wrap gap-1">
												{#each selectedAnalyzersList as a}
													<Badge variant="secondary" class="text-[10px]"
														>{a.display_name}</Badge
													>
												{/each}
											</div>
										</td>
									</tr>
									<tr>
										<td class="px-4 py-3 font-medium text-muted-foreground"
											>Auto-start</td
										>
										<td class="px-4 py-3"
											>{autoStart ? 'Yes' : 'No'}</td
										>
									</tr>
									{#if sourceMode === 'job' && liveTarget}
										<tr>
											<td class="px-4 py-3 font-medium text-muted-foreground"
												>Live container</td
											>
											<td class="px-4 py-3">
												<Badge variant="outline" class="text-[10px]"
													>Enabled</Badge
												>
											</td>
										</tr>
									{/if}
								</tbody>
							</table>
						</div>

						{#if launchError}
							<div
								class="mt-4 flex items-center gap-2 rounded-md border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400"
							>
								<AlertCircle class="h-4 w-4 shrink-0" />
								{launchError}
							</div>
						{/if}
					</Card.Content>
				</Card.Root>
			{/if}
		</div>

		<!-- Sidebar (1/4) -->
		<div class="space-y-4">
			<!-- Step Navigation -->
			<Card.Root>
				<Card.Content class="p-4">
					<div class="mb-3 text-sm font-medium">
						Step {step} of {stepLabels.length}
					</div>
					<div class="mb-4 h-1.5 overflow-hidden rounded-full bg-muted">
						<div
							class="h-full rounded-full bg-primary transition-all"
							style="width: {(step / stepLabels.length) * 100}%"
						></div>
					</div>
					<div class="flex flex-col gap-2 sm:flex-row sm:justify-between">
						<Button
							variant="outline"
							size="sm"
							disabled={step === 1}
							onclick={() => step--}
						>
							<ArrowLeft class="mr-1.5 h-3.5 w-3.5" /> Back
						</Button>
						{#if step < 4}
							<Button
								size="sm"
								disabled={!canAdvance}
								onclick={() => step++}
							>
								Next <ArrowRight class="ml-1.5 h-3.5 w-3.5" />
							</Button>
						{:else}
							<Button
								size="sm"
								disabled={launching}
								onclick={handleLaunch}
							>
								{#if launching}
									<Loader class="mr-1.5 h-3.5 w-3.5 animate-spin" />
									Launching…
								{:else}
									<Rocket class="mr-1.5 h-3.5 w-3.5" /> Launch
								{/if}
							</Button>
						{/if}
					</div>
				</Card.Content>
			</Card.Root>

			<!-- Selections Summary -->
			<Card.Root>
				<Card.Header><Card.Title class="text-sm">Selections</Card.Title></Card.Header>
				<Card.Content class="space-y-3">
					<div>
						<div class="mb-1 text-xs font-medium uppercase text-muted-foreground">
							Source
						</div>
						{#if sourceMode === 'job' && selectedJob}
							<span class="text-sm"
								>{selectedJob.model_name ?? selectedJob.id.slice(0, 8)}</span
							>
						{:else if sourceMode === 'paste' && (pasteBackend.trim() || pasteFrontend.trim())}
							<span class="text-sm">Pasted code</span>
						{:else}
							<span class="text-xs italic text-muted-foreground"
								>Not selected</span
							>
						{/if}
					</div>
					<Separator />
					<div>
						<div class="mb-1 text-xs font-medium uppercase text-muted-foreground">
							Analyzers ({selectedAnalyzers.size})
						</div>
						{#if selectedAnalyzers.size > 0}
							<div class="flex flex-wrap gap-1">
								{#each selectedAnalyzersList as a}
									<Badge variant="secondary" class="text-[10px]"
										>{a.display_name}</Badge
									>
								{/each}
							</div>
						{:else}
							<span class="text-xs italic text-muted-foreground"
								>None selected</span
							>
						{/if}
					</div>
				</Card.Content>
			</Card.Root>

			<!-- Live Estimate -->
			<Card.Root>
				<Card.Header><Card.Title class="text-sm">Summary</Card.Title></Card.Header>
				<Card.Content>
					<dl class="grid grid-cols-2 gap-y-2 text-sm">
						<dt class="text-muted-foreground">Analyzers</dt>
						<dd class="font-mono">{selectedAnalyzers.size}</dd>
						<dt class="text-muted-foreground">Auto-start</dt>
						<dd class="font-mono">{autoStart ? 'Yes' : 'No'}</dd>
					</dl>
				</Card.Content>
			</Card.Root>
		</div>
	</div>
</div>
