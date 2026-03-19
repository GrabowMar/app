<script lang="ts">
	import { page } from '$app/stores';
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import ArrowLeft from '@lucide/svelte/icons/arrow-left';
	import Skull from '@lucide/svelte/icons/skull';
	import RotateCw from '@lucide/svelte/icons/rotate-cw';
	import Check from '@lucide/svelte/icons/check';
	import X from '@lucide/svelte/icons/x';
	import Clock from '@lucide/svelte/icons/clock';
	import Copy from '@lucide/svelte/icons/copy';
	import AlertTriangle from '@lucide/svelte/icons/alert-triangle';
	import FileText from '@lucide/svelte/icons/file-text';

	const slug = $derived($page.params.slug);
	const appNum = $derived(Number($page.params.appNum));

	const modelName = $derived(
		slug === 'gpt-4o' ? 'GPT-4o' :
		slug === 'claude-3-5-sonnet' ? 'Claude 3.5 Sonnet' :
		slug === 'deepseek-v3' ? 'DeepSeek V3' :
		slug.replace(/-/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase())
	);

	const failure = {
		failureStage: 'Docker Build',
		generationAttempts: 3,
		templateName: 'E-Commerce',
		templateSlug: 'e-commerce',
		createdAt: '2025-03-18 17:45:00',
		failedAt: '2025-03-18 17:48:32',
		errorMessage: 'ERROR: failed to solve: process "/bin/sh -c pip install --no-cache-dir -r requirements.txt" did not complete successfully: exit code: 1',
		errorLog: `Step 1/8 : FROM python:3.11-slim
 ---> a1b2c3d4e5f6
Step 5/8 : RUN pip install --no-cache-dir -r requirements.txt
 ---> Running in g7h8i9j0k1l2
Collecting flask==3.0.0
  Downloading Flask-3.0.0-py3-none-any.whl
Collecting nonexistent-package==99.0.0
  ERROR: Could not find a version that satisfies the requirement nonexistent-package==99.0.0
  ERROR: No matching distribution found for nonexistent-package==99.0.0
The command '/bin/sh -c pip install --no-cache-dir -r requirements.txt' returned a non-zero code: 1`,
		generationErrors: [
			'Invalid package "nonexistent-package" in requirements.txt',
			'Missing CORS configuration in app.py',
			'Database migration script references undefined model',
		],
		filesGenerated: 'partial',
		timeline: [
			{ time: '17:45:00', event: 'Generation started', status: 'done' },
			{ time: '17:46:12', event: 'Code generated (attempt 1)', status: 'done' },
			{ time: '17:46:30', event: 'Build started', status: 'done' },
			{ time: '17:47:15', event: 'Build failed - retry 1', status: 'failed' },
			{ time: '17:47:30', event: 'Auto-fix applied', status: 'done' },
			{ time: '17:47:45', event: 'Build started (attempt 2)', status: 'done' },
			{ time: '17:48:20', event: 'Build failed - retry 2', status: 'failed' },
			{ time: '17:48:32', event: 'Max retries exceeded', status: 'failed' },
		],
		impact: [
			{ label: 'Container running', ok: false },
			{ label: 'Backend accessible', ok: false },
			{ label: 'Frontend accessible', ok: false },
			{ label: 'Source code generated', ok: true },
			{ label: 'Prompts recorded', ok: true },
		],
	};
</script>

<svelte:head>
	<title>Failed: {modelName} #{appNum} - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<!-- Breadcrumb -->
	<div class="flex items-center gap-2 text-sm text-muted-foreground">
		<Button variant="ghost" size="sm" href="/applications" class="gap-1.5 px-2">
			<ArrowLeft class="h-3.5 w-3.5" />
			Applications
		</Button>
		<span>/</span>
		<a href="/applications/{slug}/{appNum}" class="hover:text-foreground">{modelName} #{appNum}</a>
		<span>/</span>
		<span class="text-red-400 font-medium">Failure Details</span>
	</div>

	<!-- Header -->
	<div class="flex items-center justify-between">
		<div class="flex items-center gap-3">
			<div class="flex h-10 w-10 items-center justify-center rounded-lg bg-red-500/10">
				<Skull class="h-5 w-5 text-red-400" />
			</div>
			<div>
				<div class="flex items-center gap-2">
					<h1 class="text-xl font-semibold">{modelName} #{appNum}</h1>
					<Badge variant="outline" class="bg-red-500/15 text-red-400 border-red-500/30">Dead</Badge>
				</div>
				<p class="text-sm text-muted-foreground">Failed at {failure.failureStage} stage</p>
			</div>
		</div>
		<Button disabled>
			<RotateCw class="mr-2 h-4 w-4" />
			Retry Generation
		</Button>
	</div>

	<!-- 2-column layout -->
	<div class="grid gap-6 lg:grid-cols-3">
		<!-- Left column (2/3) -->
		<div class="space-y-6 lg:col-span-2">
			<!-- Quick Info -->
			<div class="grid grid-cols-2 gap-3 md:grid-cols-4">
				{#each [
					{ label: 'Model', value: modelName },
					{ label: 'Template', value: failure.templateName },
					{ label: 'Failure Stage', value: failure.failureStage },
					{ label: 'Attempts', value: failure.generationAttempts.toString() },
				] as info}
					<Card.Root>
						<Card.Content class="p-3">
							<div class="text-xs text-muted-foreground">{info.label}</div>
							<div class="text-sm font-medium mt-0.5">{info.value}</div>
						</Card.Content>
					</Card.Root>
				{/each}
			</div>

			<!-- Error Message -->
			<Card.Root class="border-red-500/20">
				<Card.Header>
					<div class="flex items-center gap-2">
						<AlertTriangle class="h-4 w-4 text-red-400" />
						<Card.Title>Error Message</Card.Title>
					</div>
				</Card.Header>
				<Card.Content>
					<div class="rounded-md bg-red-500/5 border border-red-500/20 p-4">
						<code class="text-sm text-red-400 break-all">{failure.errorMessage}</code>
					</div>
				</Card.Content>
			</Card.Root>

			<!-- Error Log -->
			<Card.Root>
				<Card.Header>
					<div class="flex items-center justify-between">
						<Card.Title>Error Log</Card.Title>
						<Button variant="ghost" size="sm" disabled>
							<Copy class="mr-1.5 h-3.5 w-3.5" /> Copy
						</Button>
					</div>
				</Card.Header>
				<Card.Content class="p-0">
					<div class="bg-zinc-950 p-4 font-mono text-xs leading-relaxed text-zinc-300 max-h-64 overflow-y-auto whitespace-pre">{failure.errorLog}</div>
				</Card.Content>
			</Card.Root>

			<!-- Generation Errors -->
			{#if failure.generationErrors.length > 0}
				<Card.Root>
					<Card.Header>
						<Card.Title>Generation Errors</Card.Title>
						<Card.Description>{failure.generationErrors.length} issues detected during generation.</Card.Description>
					</Card.Header>
					<Card.Content>
						<ul class="space-y-2">
							{#each failure.generationErrors as error, i}
								<li class="flex items-start gap-2 text-sm">
									<span class="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-red-500/10 text-[10px] font-medium text-red-400">{i + 1}</span>
									<span>{error}</span>
								</li>
							{/each}
						</ul>
					</Card.Content>
				</Card.Root>
			{/if}
		</div>

		<!-- Right column (1/3) -->
		<div class="space-y-6">
			<!-- Status Card -->
			<Card.Root class="border-red-500/20">
				<Card.Content class="p-6 text-center">
					<Skull class="mx-auto h-12 w-12 text-red-400 mb-3" />
					<h3 class="text-lg font-semibold text-red-400">Dead</h3>
					<p class="mt-1 text-sm text-muted-foreground">This application failed to build successfully.</p>
					<Button class="mt-4 w-full" disabled>
						<RotateCw class="mr-2 h-4 w-4" />
						Retry Generation
					</Button>
				</Card.Content>
			</Card.Root>

			<!-- Timeline -->
			<Card.Root>
				<Card.Header><Card.Title class="text-sm">Timeline</Card.Title></Card.Header>
				<Card.Content>
					<div class="space-y-3">
						{#each failure.timeline as event}
							<div class="flex items-start gap-3">
								<div class="mt-0.5">
									{#if event.status === 'done'}
										<div class="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500/15">
											<Check class="h-3 w-3 text-emerald-500" />
										</div>
									{:else}
										<div class="flex h-5 w-5 items-center justify-center rounded-full bg-red-500/15">
											<X class="h-3 w-3 text-red-400" />
										</div>
									{/if}
								</div>
								<div class="min-w-0 flex-1">
									<p class="text-sm {event.status === 'failed' ? 'text-red-400' : ''}">{event.event}</p>
									<p class="text-xs text-muted-foreground">{event.time}</p>
								</div>
							</div>
						{/each}
					</div>
				</Card.Content>
			</Card.Root>

			<!-- Impact -->
			<Card.Root>
				<Card.Header><Card.Title class="text-sm">Impact Assessment</Card.Title></Card.Header>
				<Card.Content>
					<div class="space-y-2">
						{#each failure.impact as item}
							<div class="flex items-center gap-2 text-sm">
								{#if item.ok}
									<Check class="h-4 w-4 text-emerald-500" />
								{:else}
									<X class="h-4 w-4 text-red-400" />
								{/if}
								<span class="{item.ok ? '' : 'text-red-400'}">{item.label}</span>
							</div>
						{/each}
					</div>
				</Card.Content>
			</Card.Root>
		</div>
	</div>
</div>
