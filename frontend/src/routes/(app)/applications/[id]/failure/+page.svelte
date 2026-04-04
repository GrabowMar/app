<script lang="ts">
	import { page } from '$app/stores';
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
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
	import Skull from '@lucide/svelte/icons/skull';
	import Check from '@lucide/svelte/icons/check';
	import X from '@lucide/svelte/icons/x';
	import Copy from '@lucide/svelte/icons/copy';
	import AlertTriangle from '@lucide/svelte/icons/alert-triangle';
	import LoaderCircle from '@lucide/svelte/icons/loader-circle';
	import CircleX from '@lucide/svelte/icons/circle-x';

	const jobId = $derived($page.params.id ?? '');

	let loading = $state(true);
	let job = $state<GenerationJob | null>(null);
	let artifacts = $state<GenerationArtifact[]>([]);
	let iterations = $state<CopilotIteration[]>([]);

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
			toast.error('Failed to load failure details');
		} finally {
			loading = false;
		}
	}

	function formatDate(dateStr: string | null): string {
		if (!dateStr) return '—';
		return new Date(dateStr).toLocaleString();
	}

	function copyText(text: string) {
		navigator.clipboard.writeText(text);
		toast.success('Copied to clipboard');
	}

	const timeline = $derived(
		job
			? [
					{ time: formatDate(job.created_at), event: 'Job created', status: 'done' as const },
					...(job.started_at
						? [{ time: formatDate(job.started_at), event: 'Generation started', status: 'done' as const }]
						: []),
					...(job.completed_at
						? [{ time: formatDate(job.completed_at), event: 'Generation failed', status: 'failed' as const }]
						: [{ time: '—', event: 'Generation failed', status: 'failed' as const }]),
				]
			: []
	);

	const failedIterations = $derived(
		iterations.filter((i) => !i.build_success)
	);

	const impact = $derived(
		job
			? [
					{ label: 'Job completed', ok: job.status === 'completed' },
					{ label: 'Result data available', ok: !!job.result_data && Object.keys(job.result_data).length > 0 },
					{ label: 'Artifacts recorded', ok: artifacts.length > 0 },
					{ label: 'Error captured', ok: !!job.error_message },
				]
			: []
	);

	onMount(() => {
		loadData();
	});
</script>

<svelte:head>
	<title>Failed: {job?.model_name ?? 'Application'} - LLM Lab</title>
</svelte:head>

{#if loading}
	<div class="flex items-center justify-center py-20">
		<LoaderCircle class="h-6 w-6 animate-spin text-muted-foreground" />
		<span class="ml-2 text-sm text-muted-foreground">Loading failure details...</span>
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
			<a href="/applications/{job.id}" class="hover:text-foreground">{job.model_name ?? 'Unknown'}</a>
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
						<h1 class="text-xl font-semibold">{job.model_name ?? 'Unknown Model'}</h1>
						<Badge variant="outline" class="bg-red-500/15 text-red-400 border-red-500/30">{job.status}</Badge>
						<Badge variant="outline" class="text-xs">{job.mode}</Badge>
					</div>
					<p class="text-sm text-muted-foreground">Generation failed • {job.model_id_str ?? ''}</p>
				</div>
			</div>
		</div>

		<!-- 2-column layout -->
		<div class="grid gap-6 lg:grid-cols-3">
			<!-- Left column (2/3) -->
			<div class="space-y-6 lg:col-span-2">
				<!-- Quick Info -->
				<div class="grid grid-cols-2 gap-3 md:grid-cols-4">
					{#each [
						{ label: 'Model', value: job.model_name ?? '—' },
						{ label: 'Mode', value: job.mode },
						{ label: 'Temperature', value: job.temperature.toString() },
						{ label: 'Max Tokens', value: job.max_tokens.toLocaleString() },
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
							<code class="text-sm text-red-400 break-all">{job.error_message || 'No error message captured'}</code>
						</div>
						<Button variant="ghost" size="sm" class="mt-2" onclick={() => copyText(job!.error_message)}>
							<Copy class="mr-1.5 h-3.5 w-3.5" /> Copy Error
						</Button>
					</Card.Content>
				</Card.Root>

				<!-- Copilot Iteration Errors -->
				{#if failedIterations.length > 0}
					<Card.Root>
						<Card.Header>
							<Card.Title>Failed Iterations</Card.Title>
							<Card.Description>{failedIterations.length} iteration(s) with errors.</Card.Description>
						</Card.Header>
						<Card.Content>
							<div class="space-y-3">
								{#each failedIterations as iter}
									<div class="rounded-md border p-3">
										<div class="flex items-center gap-2 mb-2">
											<Badge variant="outline" class="text-xs">Iteration {iter.iteration_number}</Badge>
											<Badge variant="outline" class="text-xs">{iter.action}</Badge>
										</div>
										{#if iter.errors_detected?.length > 0}
											<ul class="space-y-1">
												{#each iter.errors_detected as err}
													<li class="text-xs text-red-400 flex items-start gap-1.5">
														<CircleX class="h-3 w-3 mt-0.5 shrink-0" />
														{err}
													</li>
												{/each}
											</ul>
										{/if}
										{#if iter.build_output}
											<div class="mt-2 bg-zinc-950 rounded p-2 font-mono text-xs text-zinc-300 max-h-32 overflow-auto whitespace-pre-wrap">{iter.build_output}</div>
										{/if}
									</div>
								{/each}
							</div>
						</Card.Content>
					</Card.Root>
				{/if}

				<!-- Artifacts -->
				{#if artifacts.length > 0}
					<Card.Root>
						<Card.Header>
							<Card.Title>Request Artifacts</Card.Title>
							<Card.Description>LLM requests made during this job.</Card.Description>
						</Card.Header>
						<Card.Content>
							<div class="overflow-x-auto">
								<table class="w-full text-sm">
									<thead>
										<tr class="border-b">
											<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Stage</th>
											<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Model</th>
											<th class="px-3 py-2 text-left text-xs font-medium text-muted-foreground">Tokens</th>
										</tr>
									</thead>
									<tbody class="divide-y">
										{#each artifacts as art}
											<tr>
												<td class="px-3 py-2"><Badge variant="outline" class="text-xs">{art.stage}</Badge></td>
												<td class="px-3 py-2 font-mono text-xs">{art.request_payload?.model ?? '—'}</td>
												<td class="px-3 py-2 font-mono text-xs">{art.prompt_tokens}+{art.completion_tokens}</td>
											</tr>
										{/each}
									</tbody>
								</table>
							</div>
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
						<h3 class="text-lg font-semibold text-red-400">Failed</h3>
						<p class="mt-1 text-sm text-muted-foreground">This generation job did not complete successfully.</p>
					</Card.Content>
				</Card.Root>

				<!-- Timeline -->
				<Card.Root>
					<Card.Header><Card.Title class="text-sm">Timeline</Card.Title></Card.Header>
					<Card.Content>
						<div class="space-y-3">
							{#each timeline as event}
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
							{#each impact as item}
								<div class="flex items-center gap-2 text-sm">
									{#if item.ok}
										<Check class="h-4 w-4 text-emerald-500" />
									{:else}
										<X class="h-4 w-4 text-red-400" />
									{/if}
									<span class={item.ok ? '' : 'text-red-400'}>{item.label}</span>
								</div>
							{/each}
						</div>
					</Card.Content>
				</Card.Root>
			</div>
		</div>
	</div>
{/if}
