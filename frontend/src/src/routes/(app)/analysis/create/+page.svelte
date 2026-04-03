<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { Separator } from '$lib/components/ui/separator';
	import ArrowLeft from '@lucide/svelte/icons/arrow-left';
	import ArrowRight from '@lucide/svelte/icons/arrow-right';
	import Cpu from '@lucide/svelte/icons/cpu';
	import Check from '@lucide/svelte/icons/check';
	import X from '@lucide/svelte/icons/x';
	import Shield from '@lucide/svelte/icons/shield';
	import Zap from '@lucide/svelte/icons/zap';
	import Search from '@lucide/svelte/icons/search';
	import Play from '@lucide/svelte/icons/play';
	import Rocket from '@lucide/svelte/icons/rocket';
	import Settings from '@lucide/svelte/icons/settings';
	import Eye from '@lucide/svelte/icons/eye';
	import RefreshCw from '@lucide/svelte/icons/refresh-cw';

	let step = $state(1);
	let selectedModel = $state<string | null>(null);
	let selectedApp = $state<number | null>(null);
	let selectedTools = $state(new Set<string>());

	const models = [
		{ slug: 'gpt-4o', name: 'GPT-4o', provider: 'OpenAI', capabilities: ['Coding', 'Analysis', 'Reasoning'], price: '$2.50', context: '128K' },
		{ slug: 'gpt-4o-mini', name: 'GPT-4o Mini', provider: 'OpenAI', capabilities: ['Coding', 'Analysis'], price: '$0.15', context: '128K' },
		{ slug: 'claude-3-5-sonnet', name: 'Claude 3.5 Sonnet', provider: 'Anthropic', capabilities: ['Coding', 'Analysis', 'Reasoning'], price: '$3.00', context: '200K' },
		{ slug: 'gemini-1-5-pro', name: 'Gemini 1.5 Pro', provider: 'Google', capabilities: ['Coding', 'Analysis', 'Multimodal'], price: '$1.25', context: '2M' },
		{ slug: 'deepseek-v3', name: 'DeepSeek V3', provider: 'DeepSeek', capabilities: ['Coding', 'Analysis'], price: '$0.27', context: '64K' },
		{ slug: 'qwen-2-5-coder', name: 'Qwen 2.5 Coder', provider: 'Alibaba', capabilities: ['Coding'], price: '$0.14', context: '128K' },
	];

	const applications = [
		{ number: 1, status: 'Running', type: 'Task Manager', backend: 'Flask', frontend: 'React', ports: { be: 5001, fe: 8001 } },
		{ number: 2, status: 'Running', type: 'Blog Platform', backend: 'Flask', frontend: 'React', ports: { be: 5002, fe: 8002 } },
		{ number: 3, status: 'Stopped', type: 'E-Commerce', backend: 'Django', frontend: 'Vue', ports: { be: null, fe: null } },
	];

	interface Analyzer {
		id: string;
		name: string;
		color: string;
		status: string;
		tools: { id: string; name: string; description: string }[];
	}

	const analyzers: Analyzer[] = [
		{
			id: 'static', name: 'Static Analysis', color: 'text-blue-400 border-blue-500/30 bg-blue-500/10',
			status: 'Online',
			tools: [
				{ id: 'bandit', name: 'Bandit', description: 'Python security linter' },
				{ id: 'eslint', name: 'ESLint', description: 'JavaScript linter' },
				{ id: 'ruff', name: 'Ruff', description: 'Python linter' },
				{ id: 'stylelint', name: 'Stylelint', description: 'CSS linter' },
				{ id: 'htmlhint', name: 'HTMLHint', description: 'HTML linter' },
			],
		},
		{
			id: 'dynamic', name: 'Dynamic Analysis', color: 'text-emerald-500 border-emerald-500/30 bg-emerald-500/10',
			status: 'Online',
			tools: [
				{ id: 'zap', name: 'OWASP ZAP', description: 'Web security scanner' },
				{ id: 'port-scan', name: 'Port Scanner', description: 'Network port discovery' },
				{ id: 'connectivity', name: 'Connectivity', description: 'Endpoint reachability test' },
			],
		},
		{
			id: 'performance', name: 'Performance', color: 'text-cyan-400 border-cyan-500/30 bg-cyan-500/10',
			status: 'Offline',
			tools: [
				{ id: 'lighthouse', name: 'Lighthouse', description: 'Web performance audit' },
				{ id: 'load-test', name: 'Load Test', description: 'Stress testing' },
				{ id: 'response-time', name: 'Response Time', description: 'API response timing' },
			],
		},
		{
			id: 'ai', name: 'AI Review', color: 'text-amber-500 border-amber-500/30 bg-amber-500/10',
			status: 'Online',
			tools: [
				{ id: 'requirements-scanner', name: 'Requirements Scanner', description: 'Check app requirements' },
				{ id: 'code-quality', name: 'Code Quality', description: 'AI code review' },
			],
		},
	];

	let priority = $state('normal');
	let autoStart = $state(true);
	let buildIfMissing = $state(true);
	let stopAfter = $state(false);
	let searchQuery = $state('');

	const selectedModelData = $derived(models.find(m => m.slug === selectedModel));
	const selectedAppData = $derived(applications.find(a => a.number === selectedApp));

	function toggleTool(id: string) {
		const next = new Set(selectedTools);
		if (next.has(id)) next.delete(id); else next.add(id);
		selectedTools = next;
	}

	function selectAllTools() {
		selectedTools = new Set(analyzers.flatMap(a => a.tools.map(t => t.id)));
	}

	function clearAllTools() {
		selectedTools = new Set();
	}

	const stepLabels = ['Select Model', 'Choose App', 'Configure', 'Review'];
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
	<div class="grid gap-6 lg:grid-cols-4">
		<!-- Main Content (3/4) -->
		<div class="space-y-6 lg:col-span-3">
			<!-- Step Progress -->
			<div class="flex items-center gap-2">
				{#each stepLabels as label, i}
					<button
						class="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm transition-colors {step === i + 1 ? 'bg-primary/10 text-primary font-medium' : i + 1 < step ? 'text-emerald-500' : 'text-muted-foreground'}"
						onclick={() => { if (i + 1 <= step) step = i + 1; }}
					>
						<span class="flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold {step === i + 1 ? 'bg-primary text-primary-foreground' : i + 1 < step ? 'bg-emerald-500 text-white' : 'bg-muted text-muted-foreground'}">
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

			<!-- ===== Step 1: Select Model ===== -->
			{#if step === 1}
				<Card.Root>
					<Card.Header>
						<Card.Title>Select AI Model</Card.Title>
						<Card.Description>Choose which model's application to analyze.</Card.Description>
					</Card.Header>
					<Card.Content>
						<div class="mb-4">
							<div class="relative max-w-sm">
								<Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
								<input
									type="text"
									placeholder="Search models..."
									class="h-9 w-full rounded-md border border-input bg-background pl-9 pr-3 text-sm"
									bind:value={searchQuery}
								/>
							</div>
						</div>
						<div class="overflow-x-auto">
							<table class="w-full text-sm">
								<thead>
									<tr class="border-b bg-muted/30">
										<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Model</th>
										<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Provider</th>
										<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Capabilities</th>
										<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Price/1K</th>
										<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Context</th>
										<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground"></th>
									</tr>
								</thead>
								<tbody class="divide-y">
									{#each models.filter(m => !searchQuery || m.name.toLowerCase().includes(searchQuery.toLowerCase())) as model}
										<tr class="transition-colors hover:bg-muted/30 {selectedModel === model.slug ? 'bg-primary/5' : ''}">
											<td class="px-4 py-2.5 font-medium">{model.name}</td>
											<td class="px-4 py-2.5"><Badge variant="outline" class="text-[10px]">{model.provider}</Badge></td>
											<td class="px-4 py-2.5">
												<div class="flex gap-1">
													{#each model.capabilities as cap}
														<Badge variant="secondary" class="text-[10px]">{cap}</Badge>
													{/each}
												</div>
											</td>
											<td class="px-4 py-2.5 font-mono text-xs">{model.price}</td>
											<td class="px-4 py-2.5 font-mono text-xs">{model.context}</td>
											<td class="px-4 py-2.5">
												<Button variant={selectedModel === model.slug ? 'default' : 'outline'} size="sm" class="h-7 text-xs" onclick={() => selectedModel = model.slug}>
													{selectedModel === model.slug ? 'Selected' : 'Select'}
												</Button>
											</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					</Card.Content>
				</Card.Root>
			{/if}

			<!-- ===== Step 2: Choose Application ===== -->
			{#if step === 2}
				<Card.Root>
					<Card.Header>
						<Card.Title>Choose Application</Card.Title>
						<Card.Description>Select the application to analyze from {selectedModelData?.name ?? 'the selected model'}.</Card.Description>
					</Card.Header>
					<Card.Content>
						<div class="overflow-x-auto">
							<table class="w-full text-sm">
								<thead>
									<tr class="border-b bg-muted/30">
										<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">App #</th>
										<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Status</th>
										<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Type</th>
										<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Stack</th>
										<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Ports</th>
										<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground"></th>
									</tr>
								</thead>
								<tbody class="divide-y">
									{#each applications as app}
										<tr class="transition-colors hover:bg-muted/30 {selectedApp === app.number ? 'bg-primary/5' : ''}">
											<td class="px-4 py-2.5 font-medium">#{app.number}</td>
											<td class="px-4 py-2.5">
												<Badge variant="outline" class="text-[10px] {app.status === 'Running' ? 'bg-emerald-500/15 text-emerald-500 border-emerald-500/30' : 'bg-amber-500/15 text-amber-500 border-amber-500/30'}">
													{app.status}
												</Badge>
											</td>
											<td class="px-4 py-2.5">{app.type}</td>
											<td class="px-4 py-2.5">
												<div class="flex gap-1">
													<Badge variant="secondary" class="text-[10px]">{app.backend}</Badge>
													<Badge variant="secondary" class="text-[10px]">{app.frontend}</Badge>
												</div>
											</td>
											<td class="px-4 py-2.5 font-mono text-xs">
												{#if app.ports.be}
													BE:{app.ports.be} FE:{app.ports.fe}
												{:else}
													—
												{/if}
											</td>
											<td class="px-4 py-2.5">
												<Button variant={selectedApp === app.number ? 'default' : 'outline'} size="sm" class="h-7 text-xs" onclick={() => selectedApp = app.number}>
													{selectedApp === app.number ? 'Selected' : 'Select'}
												</Button>
											</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					</Card.Content>
				</Card.Root>
			{/if}

			<!-- ===== Step 3: Configure Analysis ===== -->
			{#if step === 3}
				<div class="space-y-4">
					<!-- Tool Selection Header -->
					<div class="flex items-center justify-between">
						<div class="flex items-center gap-2">
							<Button variant="outline" size="sm" onclick={selectAllTools}>Select All</Button>
							<Button variant="outline" size="sm" onclick={clearAllTools}>Clear All</Button>
							<Button variant="outline" size="sm" disabled>
								<RefreshCw class="mr-1.5 h-3 w-3" /> Refresh
							</Button>
						</div>
						<Badge variant="outline">{selectedTools.size} tools selected</Badge>
					</div>

					<!-- Analyzer Cards -->
					<div class="grid gap-4 md:grid-cols-2">
						{#each analyzers as analyzer}
							<Card.Root class="border {analyzer.color.split(' ').filter(c => c.startsWith('border-')).join(' ')}">
								<Card.Header>
									<div class="flex items-center justify-between">
										<Card.Title class="text-sm {analyzer.color.split(' ').filter(c => c.startsWith('text-')).join(' ')}">{analyzer.name}</Card.Title>
										<Badge variant="outline" class="text-[10px] {analyzer.status === 'Online' ? 'bg-emerald-500/15 text-emerald-500 border-emerald-500/30' : 'bg-red-500/15 text-red-400 border-red-500/30'}">
											{analyzer.status}
										</Badge>
									</div>
									<Card.Description>{analyzer.tools.length} tools available</Card.Description>
								</Card.Header>
								<Card.Content>
									<div class="space-y-2">
										{#each analyzer.tools as tool}
											<label class="flex items-center gap-2.5 rounded-md px-2 py-1.5 hover:bg-muted/30 cursor-pointer transition-colors">
												<input
													type="checkbox"
													class="rounded"
													checked={selectedTools.has(tool.id)}
													onchange={() => toggleTool(tool.id)}
												/>
												<div class="min-w-0 flex-1">
													<div class="text-sm font-medium">{tool.name}</div>
													<div class="text-xs text-muted-foreground">{tool.description}</div>
												</div>
											</label>
										{/each}
									</div>
								</Card.Content>
							</Card.Root>
						{/each}
					</div>

					<!-- Configuration Section -->
					<Card.Root>
						<Card.Header>
							<div class="flex items-center gap-2">
								<Settings class="h-4 w-4 text-muted-foreground" />
								<Card.Title class="text-sm">Configuration</Card.Title>
							</div>
						</Card.Header>
						<Card.Content>
							<div class="grid gap-4 md:grid-cols-3">
								<div>
									<label class="text-sm font-medium">Priority</label>
									<select class="mt-1 h-9 w-full rounded-md border border-input bg-background px-3 text-sm" bind:value={priority}>
										<option value="low">Low</option>
										<option value="normal">Normal</option>
										<option value="high">High</option>
									</select>
								</div>
								<div class="flex items-center gap-2 pt-6">
									<input type="checkbox" id="autoStart" bind:checked={autoStart} class="rounded" />
									<label for="autoStart" class="text-sm">Auto-start containers</label>
								</div>
								<div class="flex items-center gap-2 pt-6">
									<input type="checkbox" id="buildMissing" bind:checked={buildIfMissing} class="rounded" />
									<label for="buildMissing" class="text-sm">Build if missing</label>
								</div>
							</div>
						</Card.Content>
					</Card.Root>
				</div>
			{/if}

			<!-- ===== Step 4: Review ===== -->
			{#if step === 4}
				<Card.Root>
					<Card.Header>
						<Card.Title>Review & Launch</Card.Title>
						<Card.Description>Review your configuration before launching the analysis.</Card.Description>
					</Card.Header>
					<Card.Content>
						<div class="overflow-x-auto">
							<table class="w-full text-sm">
								<tbody class="divide-y">
									<tr>
										<td class="px-4 py-3 font-medium text-muted-foreground w-40">Model</td>
										<td class="px-4 py-3">{selectedModelData?.name ?? '—'} <Badge variant="outline" class="ml-1 text-[10px]">{selectedModelData?.provider ?? ''}</Badge></td>
									</tr>
									<tr>
										<td class="px-4 py-3 font-medium text-muted-foreground">Application</td>
										<td class="px-4 py-3">#{selectedApp ?? '—'} ({selectedAppData?.type ?? ''})</td>
									</tr>
									<tr>
										<td class="px-4 py-3 font-medium text-muted-foreground">Type</td>
										<td class="px-4 py-3">{selectedTools.size >= 10 ? 'Full Analysis' : 'Partial Analysis'}</td>
									</tr>
									<tr>
										<td class="px-4 py-3 font-medium text-muted-foreground">Tools</td>
										<td class="px-4 py-3">
											<div class="flex flex-wrap gap-1">
												{#each [...selectedTools] as tool}
													<Badge variant="secondary" class="text-[10px]">{tool}</Badge>
												{/each}
											</div>
										</td>
									</tr>
									<tr>
										<td class="px-4 py-3 font-medium text-muted-foreground">Priority</td>
										<td class="px-4 py-3 capitalize">{priority}</td>
									</tr>
									<tr>
										<td class="px-4 py-3 font-medium text-muted-foreground">Est. Time</td>
										<td class="px-4 py-3">~{Math.max(1, selectedTools.size * 0.5).toFixed(0)} minutes</td>
									</tr>
									<tr>
										<td class="px-4 py-3 font-medium text-muted-foreground">Container</td>
										<td class="px-4 py-3">{autoStart ? 'Auto-start enabled' : 'Manual start'}{buildIfMissing ? ', build if missing' : ''}</td>
									</tr>
								</tbody>
							</table>
						</div>
					</Card.Content>
				</Card.Root>
			{/if}
		</div>

		<!-- Sidebar (1/4) -->
		<div class="space-y-4">
			<!-- Step Navigation -->
			<Card.Root>
				<Card.Content class="p-4">
					<div class="text-sm font-medium mb-3">Step {step} of {stepLabels.length}</div>
					<div class="h-1.5 rounded-full bg-muted overflow-hidden mb-4">
						<div class="h-full rounded-full bg-primary transition-all" style="width: {(step / stepLabels.length) * 100}%"></div>
					</div>
					<div class="flex justify-between">
						<Button variant="outline" size="sm" disabled={step === 1} onclick={() => step--}>
							<ArrowLeft class="mr-1.5 h-3.5 w-3.5" /> Back
						</Button>
						{#if step < 4}
							<Button size="sm" disabled={(step === 1 && !selectedModel) || (step === 2 && !selectedApp) || (step === 3 && selectedTools.size === 0)} onclick={() => step++}>
								Next <ArrowRight class="ml-1.5 h-3.5 w-3.5" />
							</Button>
						{:else}
							<Button size="sm" disabled>
								<Rocket class="mr-1.5 h-3.5 w-3.5" /> Launch
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
						<div class="text-xs font-medium text-muted-foreground uppercase mb-1">Model</div>
						{#if selectedModelData}
							<div class="flex items-center gap-2">
								<Cpu class="h-3.5 w-3.5 text-muted-foreground" />
								<span class="text-sm">{selectedModelData.name}</span>
							</div>
						{:else}
							<span class="text-xs text-muted-foreground italic">Not selected</span>
						{/if}
					</div>
					<Separator />
					<div>
						<div class="text-xs font-medium text-muted-foreground uppercase mb-1">Application</div>
						{#if selectedAppData}
							<span class="text-sm">#{selectedAppData.number} — {selectedAppData.type}</span>
						{:else}
							<span class="text-xs text-muted-foreground italic">Not selected</span>
						{/if}
					</div>
					<Separator />
					<div>
						<div class="text-xs font-medium text-muted-foreground uppercase mb-1">Tools ({selectedTools.size})</div>
						{#if selectedTools.size > 0}
							<div class="flex flex-wrap gap-1">
								{#each [...selectedTools] as tool}
									<Badge variant="secondary" class="text-[10px]">{tool}</Badge>
								{/each}
							</div>
						{:else}
							<span class="text-xs text-muted-foreground italic">None selected</span>
						{/if}
					</div>
				</Card.Content>
			</Card.Root>

			<!-- Live Estimate -->
			<Card.Root>
				<Card.Header><Card.Title class="text-sm">Estimate</Card.Title></Card.Header>
				<Card.Content>
					<dl class="grid grid-cols-2 gap-y-2 text-sm">
						<dt class="text-muted-foreground">Time</dt>
						<dd class="font-mono">~{Math.max(1, selectedTools.size * 0.5).toFixed(0)}m</dd>
						<dt class="text-muted-foreground">Tools</dt>
						<dd class="font-mono">{selectedTools.size}</dd>
						<dt class="text-muted-foreground">Services</dt>
						<dd class="font-mono">{analyzers.filter(a => a.tools.some(t => selectedTools.has(t.id))).length}</dd>
					</dl>
				</Card.Content>
			</Card.Root>
		</div>
	</div>
</div>
