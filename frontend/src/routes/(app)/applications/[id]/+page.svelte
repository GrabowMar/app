<script lang="ts">
	import { page } from '$app/stores';
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { Separator } from '$lib/components/ui/separator';
	import {
		getGenerationJob,
		getJobArtifacts,
		getCopilotIterations,
		type GenerationJob,
		type GenerationArtifact,
		type CopilotIteration,
	} from '$lib/api/client';
	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import ArrowLeft from '@lucide/svelte/icons/arrow-left';
	import Cpu from '@lucide/svelte/icons/cpu';
	import Pencil from '@lucide/svelte/icons/pencil';
	import Layers from '@lucide/svelte/icons/layers';
	import Bot from '@lucide/svelte/icons/bot';
	import CircleCheck from '@lucide/svelte/icons/circle-check';
	import CircleX from '@lucide/svelte/icons/circle-x';
	import Clock from '@lucide/svelte/icons/clock';
	import Copy from '@lucide/svelte/icons/copy';
	import Code from '@lucide/svelte/icons/code';
	import MessageSquare from '@lucide/svelte/icons/message-square';
	import FileText from '@lucide/svelte/icons/file-text';
	import Settings from '@lucide/svelte/icons/settings';
	import Zap from '@lucide/svelte/icons/zap';
	import AlertTriangle from '@lucide/svelte/icons/alert-triangle';
	import LoaderCircle from '@lucide/svelte/icons/loader-circle';
	import RefreshCw from '@lucide/svelte/icons/refresh-cw';
	import ChevronRight from '@lucide/svelte/icons/chevron-right';
	import Check from '@lucide/svelte/icons/check';
	import X from '@lucide/svelte/icons/x';

	const jobId = $derived($page.params.id ?? '');

	let loading = $state(true);
	let job = $state<GenerationJob | null>(null);
	let artifacts = $state<GenerationArtifact[]>([]);
	let iterations = $state<CopilotIteration[]>([]);
	let activeSection = $state('overview');
	let codeTab = $state<'backend' | 'frontend'>('backend');

	const statusColors: Record<string, string> = {
		completed: 'bg-emerald-500/15 text-emerald-500 border-emerald-500/30',
		failed: 'bg-red-500/15 text-red-400 border-red-500/30',
		running: 'bg-amber-500/15 text-amber-500 border-amber-500/30',
		pending: 'bg-zinc-500/15 text-zinc-400 border-zinc-500/30',
	};

	const modeColors: Record<string, string> = {
		custom: 'bg-blue-500/15 text-blue-400 border-blue-500/30',
		scaffolding: 'bg-purple-500/15 text-purple-400 border-purple-500/30',
		copilot: 'bg-teal-500/15 text-teal-400 border-teal-500/30',
	};

	async function loadData() {
		try {
			const [jobData, artsData] = await Promise.all([
				getGenerationJob(jobId),
				getJobArtifacts(jobId),
			]);
			job = jobData;
			artifacts = artsData;

			if (jobData.mode === 'copilot') {
				iterations = await getCopilotIterations(jobId);
			}
		} catch (e: any) {
			toast.error('Failed to load application details');
		} finally {
			loading = false;
		}
	}

	function formatDuration(seconds: number | null): string {
		if (seconds == null) return '—';
		if (seconds < 60) return `${seconds.toFixed(1)}s`;
		const m = Math.floor(seconds / 60);
		const s = Math.round(seconds % 60);
		return `${m}m ${s}s`;
	}

	function formatDate(dateStr: string | null): string {
		if (!dateStr) return '—';
		return new Date(dateStr).toLocaleString();
	}

	function copyText(text: string) {
		navigator.clipboard.writeText(text);
		toast.success('Copied to clipboard');
	}

	const sections = $derived(
		[
			{ id: 'overview', label: 'Overview' },
			{ id: 'result', label: 'Result' },
			{ id: 'prompts', label: 'Prompts' },
			{ id: 'artifacts', label: 'Artifacts' },
			...(job?.mode === 'copilot' ? [{ id: 'iterations', label: 'Copilot Iterations' }] : []),
			{ id: 'metrics', label: 'Metrics' },
		]
	);

	const kpis = $derived(
		job
			? [
					{ label: 'Mode', value: job.mode, sub: '' },
					{ label: 'Duration', value: formatDuration(job.duration_seconds), sub: '' },
					{ label: 'Tokens', value: (job.metrics?.total_tokens ?? 0).toLocaleString(), sub: 'total' },
					{ label: 'Temperature', value: job.temperature.toString(), sub: '' },
					{ label: 'Max Tokens', value: job.max_tokens.toLocaleString(), sub: 'limit' },
					...(job.mode === 'copilot'
						? [{ label: 'Iterations', value: `${job.copilot_current_iteration}/${job.copilot_max_iterations}`, sub: '' }]
						: []),
				]
			: []
	);

	const resultContent = $derived(
		job?.result_data?.content ?? ''
	);

	const backendCode = $derived(
		job?.result_data?.backend_code ?? ''
	);

	const frontendCode = $derived(
		job?.result_data?.frontend_code ?? ''
	);

	const backendScan = $derived(
		job?.result_data?.backend_scan ?? null
	);

	const dependencies = $derived(
		job?.result_data?.backend_dependencies ?? job?.result_data?.dependencies ?? []
	);

	function scrollToSection(id: string) {
		activeSection = id;
		document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
	}

	onMount(() => {
		loadData();
	});
</script>

<svelte:head>
	<title>{job ? `${job.model_name ?? 'Application'} - LLM Lab` : 'Application - LLM Lab'}</title>
</svelte:head>

{#if loading}
	<div class="flex items-center justify-center py-20">
		<LoaderCircle class="h-6 w-6 animate-spin text-muted-foreground" />
		<span class="ml-2 text-sm text-muted-foreground">Loading application...</span>
	</div>
{:else if !job}
	<div class="text-center py-20">
		<AlertTriangle class="mx-auto h-12 w-12 text-muted-foreground/50 mb-4" />
		<h3 class="text-lg font-medium mb-1">Application not found</h3>
		<Button variant="outline" href="/applications">Back to Applications</Button>
	</div>
{:else}
	<div class="space-y-6">
		<!-- Breadcrumb -->
		<div class="flex items-center gap-2 text-sm text-muted-foreground">
			<Button variant="ghost" size="sm" href="/applications" class="gap-1.5 px-2">
				<ArrowLeft class="h-3.5 w-3.5" />
				Applications
			</Button>
			<span>/</span>
			<span class="text-foreground font-medium truncate max-w-xs">{job.model_name ?? 'Unknown Model'}</span>
		</div>

		<!-- Warning Banner (if failed) -->
		{#if job.status === 'failed'}
			<div class="flex items-center gap-3 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3">
				<AlertTriangle class="h-5 w-5 text-red-400 shrink-0" />
				<div class="min-w-0 flex-1">
					<p class="text-sm font-medium text-red-400">Generation Failed</p>
					<p class="text-xs text-muted-foreground truncate">{job.error_message || 'Unknown error'}</p>
				</div>
				<Button variant="outline" size="sm" href="/applications/{job.id}/failure">
					View Failure Details
				</Button>
			</div>
		{/if}

		<!-- Header Card -->
		<Card.Root class="border-border/60">
			<Card.Content class="p-6">
				<div class="flex items-start justify-between">
					<div class="flex items-center gap-4">
						<div class="flex h-12 w-12 items-center justify-center rounded-lg bg-muted">
							{#if job.mode === 'custom'}
								<Pencil class="h-6 w-6 text-blue-400" />
							{:else if job.mode === 'scaffolding'}
								<Layers class="h-6 w-6 text-purple-400" />
							{:else}
								<Bot class="h-6 w-6 text-teal-400" />
							{/if}
						</div>
						<div>
							<div class="flex items-center gap-3">
								<h1 class="text-xl font-semibold">{job.model_name ?? 'Unknown Model'}</h1>
								<Badge variant="outline" class="{modeColors[job.mode] ?? ''}">{job.mode}</Badge>
								<Badge variant="outline" class="{statusColors[job.status] ?? ''}">
									{#if job.status === 'running'}
										<span class="mr-1.5 h-1.5 w-1.5 rounded-full bg-amber-500 animate-pulse"></span>
									{/if}
									{#if job.status === 'completed'}
										<CircleCheck class="mr-1 h-3 w-3" />
									{:else if job.status === 'failed'}
										<CircleX class="mr-1 h-3 w-3" />
									{/if}
									{job.status}
								</Badge>
							</div>
							<p class="mt-1 text-sm text-muted-foreground">
								{job.model_id_str ?? ''} • Created {formatDate(job.created_at)}
							</p>
						</div>
					</div>
					<div class="flex items-center gap-2">
						<Button variant="ghost" size="sm" onclick={() => copyText(job!.id)} title="Copy job ID">
							<Copy class="mr-1.5 h-3.5 w-3.5" /> ID
						</Button>
					</div>
				</div>
			</Card.Content>
		</Card.Root>

		<!-- KPI Grid -->
		<div class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
			{#each kpis as kpi}
				<Card.Root>
					<Card.Content class="p-4 text-center">
						<div class="text-2xl font-bold">{kpi.value}</div>
						<div class="text-sm font-medium text-muted-foreground">{kpi.label}</div>
						{#if kpi.sub}
							<div class="text-xs text-muted-foreground/70">{kpi.sub}</div>
						{/if}
					</Card.Content>
				</Card.Root>
			{/each}
		</div>

		<!-- Section Navigation -->
		<div class="sticky top-0 z-40 -mx-4 bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/60">
			<nav class="flex gap-1 overflow-x-auto border-b py-2">
				{#each sections as section}
					<button
						class="rounded-md px-3 py-1.5 text-sm transition-colors whitespace-nowrap {activeSection === section.id ? 'bg-primary/10 text-primary font-medium' : 'text-muted-foreground hover:text-foreground'}"
						onclick={() => scrollToSection(section.id)}
					>
						{section.label}
					</button>
				{/each}
			</nav>
		</div>

		<!-- ===== SECTION: Overview ===== -->
		<div id="overview" class="scroll-mt-16 space-y-4">
			<h2 class="text-lg font-semibold">Overview</h2>
			<div class="grid gap-4 md:grid-cols-2">
				<!-- Identity -->
				<Card.Root>
					<Card.Header><Card.Title class="text-sm">Identity</Card.Title></Card.Header>
					<Card.Content>
						<dl class="grid grid-cols-2 gap-y-2 text-sm">
							<dt class="text-muted-foreground">Model</dt><dd>{job.model_name ?? '—'}</dd>
							<dt class="text-muted-foreground">Model ID</dt><dd class="font-mono text-xs">{job.model_id_str ?? '—'}</dd>
							<dt class="text-muted-foreground">Mode</dt><dd><Badge variant="outline" class="text-xs {modeColors[job.mode] ?? ''}">{job.mode}</Badge></dd>
							<dt class="text-muted-foreground">Status</dt><dd><Badge variant="outline" class="text-xs {statusColors[job.status] ?? ''}">{job.status}</Badge></dd>
							<dt class="text-muted-foreground">Job ID</dt><dd class="font-mono text-xs truncate" title={job.id}>{job.id.slice(0, 8)}…</dd>
						</dl>
					</Card.Content>
				</Card.Root>

				<!-- Generation Config -->
				<Card.Root>
					<Card.Header><Card.Title class="text-sm">Generation Config</Card.Title></Card.Header>
					<Card.Content>
						<dl class="grid grid-cols-2 gap-y-2 text-sm">
							<dt class="text-muted-foreground">Temperature</dt><dd>{job.temperature}</dd>
							<dt class="text-muted-foreground">Max Tokens</dt><dd>{job.max_tokens.toLocaleString()}</dd>
							{#if job.mode === 'copilot'}
								<dt class="text-muted-foreground">Max Iterations</dt><dd>{job.copilot_max_iterations}</dd>
								<dt class="text-muted-foreground">Open Source</dt><dd>{job.copilot_use_open_source ? 'Yes' : 'No'}</dd>
							{/if}
						</dl>
					</Card.Content>
				</Card.Root>

				<!-- Timing -->
				<Card.Root>
					<Card.Header><Card.Title class="text-sm">Timing</Card.Title></Card.Header>
					<Card.Content>
						<dl class="grid grid-cols-2 gap-y-2 text-sm">
							<dt class="text-muted-foreground">Created</dt><dd>{formatDate(job.created_at)}</dd>
							<dt class="text-muted-foreground">Started</dt><dd>{formatDate(job.started_at)}</dd>
							<dt class="text-muted-foreground">Completed</dt><dd>{formatDate(job.completed_at)}</dd>
							<dt class="text-muted-foreground">Duration</dt><dd class="font-mono">{formatDuration(job.duration_seconds)}</dd>
						</dl>
					</Card.Content>
				</Card.Root>

				<!-- Dependencies -->
				{#if dependencies.length > 0}
					<Card.Root>
						<Card.Header><Card.Title class="text-sm">Dependencies</Card.Title></Card.Header>
						<Card.Content>
							<div class="flex flex-wrap gap-1.5">
								{#each dependencies as dep}
									<Badge variant="secondary" class="text-xs">{dep}</Badge>
								{/each}
							</div>
						</Card.Content>
					</Card.Root>
				{/if}
			</div>
		</div>

		<!-- ===== SECTION: Result ===== -->
		<div id="result" class="scroll-mt-16 space-y-4">
			<div class="flex items-center justify-between">
				<h2 class="text-lg font-semibold">Generated Code</h2>
				{#if job.mode === 'scaffolding'}
					<div class="flex items-center gap-1 rounded-md border p-0.5">
						<button
							class="rounded px-3 py-1 text-sm transition-colors {codeTab === 'backend' ? 'bg-primary/10 text-primary font-medium' : 'text-muted-foreground'}"
							onclick={() => (codeTab = 'backend')}
						>
							Backend
						</button>
						<button
							class="rounded px-3 py-1 text-sm transition-colors {codeTab === 'frontend' ? 'bg-primary/10 text-primary font-medium' : 'text-muted-foreground'}"
							onclick={() => (codeTab = 'frontend')}
						>
							Frontend
						</button>
					</div>
				{/if}
			</div>

			<Card.Root>
				<Card.Content class="p-0">
					{#if job.mode === 'scaffolding'}
						<div class="relative">
							<Button
								variant="ghost"
								size="sm"
								class="absolute right-2 top-2 z-10"
								onclick={() => copyText(codeTab === 'backend' ? backendCode : frontendCode)}
							>
								<Copy class="h-3.5 w-3.5" />
							</Button>
							<div class="bg-zinc-950 p-4 font-mono text-xs leading-relaxed text-zinc-300 max-h-[600px] overflow-auto whitespace-pre-wrap">
								{codeTab === 'backend' ? backendCode || 'No backend code generated.' : frontendCode || 'No frontend code generated.'}
							</div>
						</div>
					{:else}
						<div class="relative">
							<Button
								variant="ghost"
								size="sm"
								class="absolute right-2 top-2 z-10"
								onclick={() => copyText(resultContent)}
							>
								<Copy class="h-3.5 w-3.5" />
							</Button>
							<div class="bg-zinc-950 p-4 font-mono text-xs leading-relaxed text-zinc-300 max-h-[600px] overflow-auto whitespace-pre-wrap">
								{resultContent || 'No content generated.'}
							</div>
						</div>
					{/if}
				</Card.Content>
			</Card.Root>

			<!-- Backend Scan Results -->
			{#if backendScan}
				<Card.Root>
					<Card.Header><Card.Title class="text-sm">Backend Scan</Card.Title></Card.Header>
					<Card.Content>
						<div class="grid gap-4 md:grid-cols-2">
							{#if backendScan.endpoints?.length}
								<div>
									<h4 class="text-xs font-medium text-muted-foreground mb-2">Endpoints ({backendScan.endpoints.length})</h4>
									<div class="space-y-1">
										{#each backendScan.endpoints as ep}
											<div class="flex items-center gap-2 text-xs font-mono">
												<Badge variant="secondary" class="text-[10px]">{ep.methods?.join(',') ?? 'GET'}</Badge>
												<span>{ep.path}</span>
											</div>
										{/each}
									</div>
								</div>
							{/if}
							{#if backendScan.models?.length}
								<div>
									<h4 class="text-xs font-medium text-muted-foreground mb-2">Models ({backendScan.models.length})</h4>
									<div class="space-y-1">
										{#each backendScan.models as model}
											<div class="text-xs">
												<span class="font-medium">{model.name}</span>
												{#if model.fields?.length}
													<span class="text-muted-foreground ml-1">({model.fields.length} fields)</span>
												{/if}
											</div>
										{/each}
									</div>
								</div>
							{/if}
						</div>
					</Card.Content>
				</Card.Root>
			{/if}
		</div>

		<!-- ===== SECTION: Prompts ===== -->
		<div id="prompts" class="scroll-mt-16 space-y-4">
			<h2 class="text-lg font-semibold">Prompts</h2>

			{#if job.mode === 'custom'}
				{#if job.custom_system_prompt}
					<Card.Root>
						<Card.Header>
							<div class="flex items-center justify-between">
								<Card.Title class="text-sm">System Prompt</Card.Title>
								<Button variant="ghost" size="sm" onclick={() => copyText(job!.custom_system_prompt)}>
									<Copy class="h-3.5 w-3.5" />
								</Button>
							</div>
						</Card.Header>
						<Card.Content class="p-0">
							<div class="bg-zinc-950 p-4 font-mono text-xs leading-relaxed text-zinc-300 max-h-80 overflow-auto whitespace-pre-wrap">{job.custom_system_prompt}</div>
						</Card.Content>
					</Card.Root>
				{/if}
				{#if job.custom_user_prompt}
					<Card.Root>
						<Card.Header>
							<div class="flex items-center justify-between">
								<Card.Title class="text-sm">User Prompt</Card.Title>
								<Button variant="ghost" size="sm" onclick={() => copyText(job!.custom_user_prompt)}>
									<Copy class="h-3.5 w-3.5" />
								</Button>
							</div>
						</Card.Header>
						<Card.Content class="p-0">
							<div class="bg-zinc-950 p-4 font-mono text-xs leading-relaxed text-zinc-300 max-h-80 overflow-auto whitespace-pre-wrap">{job.custom_user_prompt}</div>
						</Card.Content>
					</Card.Root>
				{/if}
			{/if}

			<!-- Show prompts from artifacts for scaffolding/copilot -->
			{#each artifacts as art}
				<Card.Root>
					<Card.Header>
						<div class="flex items-center justify-between">
							<Card.Title class="text-sm">{art.stage} Stage — Prompts</Card.Title>
							<Badge variant="outline" class="text-xs">{art.prompt_tokens + art.completion_tokens} tokens</Badge>
						</div>
					</Card.Header>
					<Card.Content>
						{#if art.request_payload?.messages}
							<div class="space-y-3">
								{#each art.request_payload.messages as msg}
									<div>
										<Badge variant="secondary" class="text-[10px] mb-1">{msg.role}</Badge>
										<div class="bg-zinc-950 rounded p-3 font-mono text-xs leading-relaxed text-zinc-300 max-h-60 overflow-auto whitespace-pre-wrap">
											{typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content, null, 2)}
										</div>
									</div>
								{/each}
							</div>
						{/if}
					</Card.Content>
				</Card.Root>
			{/each}
		</div>

		<!-- ===== SECTION: Artifacts ===== -->
		<div id="artifacts" class="scroll-mt-16 space-y-4">
			<h2 class="text-lg font-semibold">Artifacts</h2>
			{#if artifacts.length === 0}
				<Card.Root>
					<Card.Content class="py-8 text-center text-sm text-muted-foreground">
						No artifacts recorded for this job.
					</Card.Content>
				</Card.Root>
			{:else}
				<div class="overflow-x-auto">
					<table class="w-full">
						<thead>
							<tr class="border-b bg-muted/30">
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Stage</th>
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Model</th>
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Prompt Tokens</th>
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Completion Tokens</th>
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Total Cost</th>
								<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Created</th>
							</tr>
						</thead>
						<tbody class="divide-y">
							{#each artifacts as art}
								<tr class="hover:bg-muted/30">
									<td class="px-4 py-3"><Badge variant="outline" class="text-xs">{art.stage}</Badge></td>
									<td class="px-4 py-3 text-sm font-mono">{art.request_payload?.model ?? '—'}</td>
									<td class="px-4 py-3 text-sm font-mono">{art.prompt_tokens.toLocaleString()}</td>
									<td class="px-4 py-3 text-sm font-mono">{art.completion_tokens.toLocaleString()}</td>
									<td class="px-4 py-3 text-sm font-mono">${art.total_cost.toFixed(4)}</td>
									<td class="px-4 py-3 text-sm text-muted-foreground">{formatDate(art.created_at)}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		</div>

		<!-- ===== SECTION: Copilot Iterations ===== -->
		{#if job.mode === 'copilot' && iterations.length > 0}
			<div id="iterations" class="scroll-mt-16 space-y-4">
				<h2 class="text-lg font-semibold">Copilot Iterations</h2>
				<div class="space-y-3">
					{#each iterations as iter}
						<Card.Root>
							<Card.Header>
								<div class="flex items-center justify-between">
									<div class="flex items-center gap-2">
										<Card.Title class="text-sm">Iteration {iter.iteration_number}</Card.Title>
										<Badge variant="outline" class="text-xs">{iter.action}</Badge>
									</div>
									<div class="flex items-center gap-2">
										{#if iter.build_success}
											<Badge variant="outline" class="text-xs bg-emerald-500/15 text-emerald-500 border-emerald-500/30">
												<Check class="mr-1 h-3 w-3" /> Build OK
											</Badge>
										{:else}
											<Badge variant="outline" class="text-xs bg-red-500/15 text-red-400 border-red-500/30">
												<X class="mr-1 h-3 w-3" /> Build Failed
											</Badge>
										{/if}
									</div>
								</div>
							</Card.Header>
							<Card.Content>
								{#if iter.errors_detected?.length > 0}
									<div class="mb-3">
										<h4 class="text-xs font-medium text-muted-foreground mb-1">Errors Detected</h4>
										<ul class="space-y-1">
											{#each iter.errors_detected as err}
												<li class="text-xs text-red-400 flex items-start gap-1.5">
													<CircleX class="h-3 w-3 mt-0.5 shrink-0" />
													{err}
												</li>
											{/each}
										</ul>
									</div>
								{/if}
								{#if iter.fix_applied}
									<div class="mb-3">
										<h4 class="text-xs font-medium text-muted-foreground mb-1">Fix Applied</h4>
										<div class="bg-zinc-950 rounded p-2 font-mono text-xs text-zinc-300 whitespace-pre-wrap">{iter.fix_applied}</div>
									</div>
								{/if}
								{#if iter.build_output}
									<div>
										<h4 class="text-xs font-medium text-muted-foreground mb-1">Build Output</h4>
										<div class="bg-zinc-950 rounded p-2 font-mono text-xs text-zinc-300 max-h-32 overflow-auto whitespace-pre-wrap">{iter.build_output}</div>
									</div>
								{/if}
							</Card.Content>
						</Card.Root>
					{/each}
				</div>
			</div>
		{/if}

		<!-- ===== SECTION: Metrics ===== -->
		<div id="metrics" class="scroll-mt-16 space-y-4">
			<h2 class="text-lg font-semibold">Metrics</h2>
			{#if job.metrics && Object.keys(job.metrics).length > 0}
				<Card.Root>
					<Card.Content class="p-4">
						<dl class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
							{#each Object.entries(job.metrics) as [key, value]}
								<div>
									<dt class="text-xs text-muted-foreground">{key.replace(/_/g, ' ')}</dt>
									<dd class="text-sm font-mono font-medium">
										{typeof value === 'number' ? (Number.isInteger(value) ? value.toLocaleString() : value.toFixed(2)) : value}
									</dd>
								</div>
							{/each}
						</dl>
					</Card.Content>
				</Card.Root>
			{:else}
				<Card.Root>
					<Card.Content class="py-8 text-center text-sm text-muted-foreground">
						No metrics recorded.
					</Card.Content>
				</Card.Root>
			{/if}
		</div>
	</div>
{/if}
