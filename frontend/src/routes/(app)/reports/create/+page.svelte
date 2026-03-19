<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { Separator } from '$lib/components/ui/separator';
	import ArrowLeft from '@lucide/svelte/icons/arrow-left';
	import ArrowRight from '@lucide/svelte/icons/arrow-right';
	import Brain from '@lucide/svelte/icons/brain';
	import GitCompareArrows from '@lucide/svelte/icons/git-compare-arrows';
	import Wrench from '@lucide/svelte/icons/wrench';
	import TrendingUp from '@lucide/svelte/icons/trending-up';
	import Layers from '@lucide/svelte/icons/layers';
	import Check from '@lucide/svelte/icons/check';
	import Play from '@lucide/svelte/icons/play';
	import type { Component } from 'svelte';

	let step = $state(1);

	// Step 1 - Report type
	const reportTypes: { id: string; label: string; description: string; icon: Component; color: string }[] = [
		{ id: 'model_analysis', label: 'Model Analysis', description: 'Analyze a single model across all its generated applications. Includes security, performance, code quality, and AI review metrics.', icon: Brain, color: 'border-blue-500/50 bg-blue-500/5 hover:bg-blue-500/10' },
		{ id: 'template_comparison', label: 'Template Comparison', description: 'Compare how different models perform on the same application template. Identifies which models excel at specific app types.', icon: GitCompareArrows, color: 'border-purple-500/50 bg-purple-500/5 hover:bg-purple-500/10' },
		{ id: 'tool_analysis', label: 'Tool Analysis', description: 'Evaluate the effectiveness of analysis tools (Bandit, ZAP, Lighthouse, etc.) across all scanned applications.', icon: Wrench, color: 'border-teal-500/50 bg-teal-500/5 hover:bg-teal-500/10' },
		{ id: 'generation_analytics', label: 'Generation Analytics', description: 'Track generation success/failure patterns, timing, and resource usage over a configurable time period.', icon: TrendingUp, color: 'border-orange-500/50 bg-orange-500/5 hover:bg-orange-500/10' },
		{ id: 'comprehensive', label: 'Comprehensive', description: 'Full platform-wide analysis combining all report types. Generates the most complete overview but takes longer to produce.', icon: Layers, color: 'border-red-500/50 bg-red-500/5 hover:bg-red-500/10' },
	];
	let selectedType = $state('');

	// Step 2 - Configuration
	let reportTitle = $state('');
	let reportDescription = $state('');
	let selectedModel = $state('');
	let selectedTemplate = $state('');
	let selectedTools: string[] = $state([]);
	let timePeriod = $state('7');
	let analyzerFilter = $state('all');

	const models = [
		{ slug: 'gpt-4o', name: 'GPT-4o' },
		{ slug: 'gpt-4o-mini', name: 'GPT-4o Mini' },
		{ slug: 'claude-3-5-sonnet', name: 'Claude 3.5 Sonnet' },
		{ slug: 'claude-3-5-haiku', name: 'Claude 3.5 Haiku' },
		{ slug: 'gemini-2-0-flash', name: 'Gemini 2.0 Flash' },
		{ slug: 'deepseek-v3', name: 'DeepSeek V3' },
	];
	const templates = [
		'Todo App', 'E-Commerce Store', 'Blog Platform', 'Chat Application',
		'Weather Dashboard', 'Portfolio Site', 'REST API', 'Social Feed',
	];
	const tools = [
		{ id: 'bandit', name: 'Bandit', category: 'Security' },
		{ id: 'semgrep', name: 'Semgrep', category: 'Security' },
		{ id: 'eslint', name: 'ESLint', category: 'Code Quality' },
		{ id: 'ruff', name: 'Ruff', category: 'Code Quality' },
		{ id: 'zap', name: 'ZAP', category: 'Dynamic' },
		{ id: 'lighthouse', name: 'Lighthouse', category: 'Performance' },
		{ id: 'load-test', name: 'Load Test', category: 'Performance' },
	];

	function toggleTool(id: string) {
		if (selectedTools.includes(id)) {
			selectedTools = selectedTools.filter(t => t !== id);
		} else {
			selectedTools = [...selectedTools, id];
		}
	}

	const typeLabel = $derived(reportTypes.find(t => t.id === selectedType)?.label ?? '');
	const canProceed = $derived(
		step === 1 ? selectedType !== '' :
		step === 2 ? reportTitle.trim() !== '' :
		true
	);
</script>

<svelte:head>
	<title>Create Report - LLM Lab</title>
</svelte:head>

<div class="grid gap-6 lg:grid-cols-[1fr_300px]">
	<!-- Main -->
	<div class="space-y-6">
		<!-- Header -->
		<div class="flex items-center gap-3">
			<Button variant="ghost" size="sm" href="/reports">
				<ArrowLeft class="mr-1.5 h-4 w-4" />
				Back
			</Button>
			<Separator orientation="vertical" class="h-6" />
			<div>
				<h1 class="text-2xl font-bold tracking-tight">Create Report</h1>
				<p class="text-sm text-muted-foreground">Step {step} of 3</p>
			</div>
		</div>

		{#if step === 1}
			<!-- Step 1: Select Type -->
			<div class="space-y-4">
				<h2 class="text-lg font-semibold">Select Report Type</h2>
				<div class="grid gap-3">
					{#each reportTypes as rt}
						<button
							class="flex items-start gap-4 rounded-lg border p-4 text-left transition-colors {selectedType === rt.id ? rt.color + ' ring-1 ring-primary' : 'hover:bg-muted/50'}"
							onclick={() => selectedType = rt.id}
						>
							<div class="mt-0.5 rounded-lg p-2 {selectedType === rt.id ? 'bg-background/50' : 'bg-muted'}">
								<rt.icon class="h-5 w-5" />
							</div>
							<div class="flex-1 space-y-1">
								<div class="flex items-center gap-2">
									<span class="font-medium">{rt.label}</span>
									{#if selectedType === rt.id}
										<Check class="h-4 w-4 text-primary" />
									{/if}
								</div>
								<p class="text-sm text-muted-foreground">{rt.description}</p>
							</div>
						</button>
					{/each}
				</div>
			</div>
		{:else if step === 2}
			<!-- Step 2: Configure -->
			<div class="space-y-6">
				<h2 class="text-lg font-semibold">Configure: {typeLabel}</h2>

				<Card.Root>
					<Card.Header>
						<Card.Title class="text-sm">General</Card.Title>
					</Card.Header>
					<Card.Content class="space-y-4">
						<div class="space-y-2">
							<Label for="title">Report Title *</Label>
							<Input id="title" bind:value={reportTitle} placeholder="e.g. GPT-4o Security Deep Dive" />
						</div>
						<div class="space-y-2">
							<Label for="desc">Description</Label>
							<textarea id="desc" bind:value={reportDescription} placeholder="Optional description..." class="flex min-h-[80px] w-full rounded-md border bg-background px-3 py-2 text-sm"></textarea>
						</div>
					</Card.Content>
				</Card.Root>

				{#if selectedType === 'model_analysis'}
					<Card.Root>
						<Card.Header><Card.Title class="text-sm">Select Model</Card.Title></Card.Header>
						<Card.Content>
							<select bind:value={selectedModel} class="h-9 w-full rounded-md border bg-background px-3 text-sm">
								<option value="">Choose a model...</option>
								{#each models as m}
									<option value={m.slug}>{m.name}</option>
								{/each}
							</select>
						</Card.Content>
					</Card.Root>
				{:else if selectedType === 'template_comparison'}
					<Card.Root>
						<Card.Header><Card.Title class="text-sm">Select Template</Card.Title></Card.Header>
						<Card.Content>
							<select bind:value={selectedTemplate} class="h-9 w-full rounded-md border bg-background px-3 text-sm">
								<option value="">Choose a template...</option>
								{#each templates as t}
									<option value={t}>{t}</option>
								{/each}
							</select>
						</Card.Content>
					</Card.Root>
				{:else if selectedType === 'tool_analysis'}
					<Card.Root>
						<Card.Header><Card.Title class="text-sm">Select Tools</Card.Title></Card.Header>
						<Card.Content>
							<div class="grid gap-2 sm:grid-cols-2">
								{#each tools as tool}
									<label class="flex items-center gap-2 rounded-md border p-2.5 text-sm cursor-pointer hover:bg-muted/50 {selectedTools.includes(tool.id) ? 'border-primary bg-primary/5' : ''}">
										<input type="checkbox" checked={selectedTools.includes(tool.id)} onchange={() => toggleTool(tool.id)} class="rounded" />
										<span>{tool.name}</span>
										<Badge variant="secondary" class="ml-auto text-[10px]">{tool.category}</Badge>
									</label>
								{/each}
							</div>
						</Card.Content>
					</Card.Root>
				{:else if selectedType === 'generation_analytics'}
					<Card.Root>
						<Card.Header><Card.Title class="text-sm">Time Period</Card.Title></Card.Header>
						<Card.Content>
							<select bind:value={timePeriod} class="h-9 w-full rounded-md border bg-background px-3 text-sm">
								<option value="1">Last 24 hours</option>
								<option value="7">Last 7 days</option>
								<option value="30">Last 30 days</option>
								<option value="90">Last 90 days</option>
								<option value="all">All time</option>
							</select>
						</Card.Content>
					</Card.Root>
				{/if}

				<Card.Root>
					<Card.Header><Card.Title class="text-sm">Analyzer Filter</Card.Title></Card.Header>
					<Card.Content>
						<select bind:value={analyzerFilter} class="h-9 w-full rounded-md border bg-background px-3 text-sm">
							<option value="all">All Analyzers</option>
							<option value="static">Static Analysis Only</option>
							<option value="dynamic">Dynamic Analysis Only</option>
							<option value="performance">Performance Only</option>
							<option value="ai">AI Review Only</option>
						</select>
					</Card.Content>
				</Card.Root>
			</div>
		{:else}
			<!-- Step 3: Review -->
			<div class="space-y-6">
				<h2 class="text-lg font-semibold">Review & Generate</h2>

				<Card.Root>
					<Card.Content class="pt-6 space-y-4">
						<div class="grid gap-4 sm:grid-cols-2">
							<div>
								<span class="text-xs text-muted-foreground">Report Type</span>
								<p class="text-sm font-medium">{typeLabel}</p>
							</div>
							<div>
								<span class="text-xs text-muted-foreground">Title</span>
								<p class="text-sm font-medium">{reportTitle}</p>
							</div>
							{#if reportDescription}
								<div class="sm:col-span-2">
									<span class="text-xs text-muted-foreground">Description</span>
									<p class="text-sm">{reportDescription}</p>
								</div>
							{/if}
							{#if selectedModel}
								<div>
									<span class="text-xs text-muted-foreground">Model</span>
									<p class="text-sm font-medium">{models.find(m => m.slug === selectedModel)?.name ?? selectedModel}</p>
								</div>
							{/if}
							{#if selectedTemplate}
								<div>
									<span class="text-xs text-muted-foreground">Template</span>
									<p class="text-sm font-medium">{selectedTemplate}</p>
								</div>
							{/if}
							{#if selectedTools.length > 0}
								<div>
									<span class="text-xs text-muted-foreground">Tools</span>
									<div class="flex flex-wrap gap-1 mt-1">
										{#each selectedTools as t}
											<Badge variant="secondary" class="text-[10px]">{t}</Badge>
										{/each}
									</div>
								</div>
							{/if}
							{#if selectedType === 'generation_analytics'}
								<div>
									<span class="text-xs text-muted-foreground">Time Period</span>
									<p class="text-sm font-medium">{timePeriod === 'all' ? 'All time' : `Last ${timePeriod} days`}</p>
								</div>
							{/if}
							<div>
								<span class="text-xs text-muted-foreground">Analyzer Filter</span>
								<p class="text-sm font-medium capitalize">{analyzerFilter === 'all' ? 'All Analyzers' : analyzerFilter}</p>
							</div>
						</div>
					</Card.Content>
				</Card.Root>

				<div class="rounded-lg border border-dashed p-4 text-center text-sm text-muted-foreground">
					Estimated generation time: 2-5 minutes
				</div>
			</div>
		{/if}
	</div>

	<!-- Sidebar -->
	<div class="space-y-4">
		<Card.Root>
			<Card.Header>
				<Card.Title class="text-sm">Progress</Card.Title>
			</Card.Header>
			<Card.Content class="space-y-3">
				{#each [{ n: 1, label: 'Select Type' }, { n: 2, label: 'Configure' }, { n: 3, label: 'Review & Generate' }] as s}
					<div class="flex items-center gap-2 text-sm {step >= s.n ? 'text-foreground' : 'text-muted-foreground'}">
						<div class="flex h-6 w-6 items-center justify-center rounded-full text-[10px] font-bold {step > s.n ? 'bg-emerald-500 text-white' : step === s.n ? 'bg-primary text-primary-foreground' : 'bg-muted'}">
							{#if step > s.n}
								<Check class="h-3 w-3" />
							{:else}
								{s.n}
							{/if}
						</div>
						<span class:font-medium={step === s.n}>{s.label}</span>
					</div>
				{/each}
			</Card.Content>
		</Card.Root>

		{#if selectedType}
			<Card.Root>
				<Card.Header>
					<Card.Title class="text-sm">Selection Summary</Card.Title>
				</Card.Header>
				<Card.Content class="text-sm space-y-2">
					<div class="flex justify-between">
						<span class="text-muted-foreground">Type</span>
						<span class="font-medium">{typeLabel}</span>
					</div>
					{#if reportTitle}
						<Separator />
						<div class="flex justify-between">
							<span class="text-muted-foreground">Title</span>
							<span class="font-medium truncate max-w-[140px]">{reportTitle}</span>
						</div>
					{/if}
				</Card.Content>
			</Card.Root>
		{/if}

		<div class="flex gap-2">
			<Button variant="outline" class="flex-1" disabled={step === 1} onclick={() => step--}>
				<ArrowLeft class="mr-1.5 h-4 w-4" />
				Back
			</Button>
			{#if step < 3}
				<Button class="flex-1" disabled={!canProceed} onclick={() => step++}>
					Next
					<ArrowRight class="ml-1.5 h-4 w-4" />
				</Button>
			{:else}
				<Button class="flex-1" disabled>
					<Play class="mr-1.5 h-4 w-4" />
					Generate
				</Button>
			{/if}
		</div>
	</div>
</div>
