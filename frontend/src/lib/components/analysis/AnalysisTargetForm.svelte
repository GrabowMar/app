<script lang="ts">
import * as Card from '$lib/components/ui/card';
import { Button } from '$lib/components/ui/button';
import Search from '@lucide/svelte/icons/search';
import Loader from '@lucide/svelte/icons/loader-circle';
import FileCode from '@lucide/svelte/icons/file-code';
import ClipboardPaste from '@lucide/svelte/icons/clipboard-paste';
import AlertCircle from '@lucide/svelte/icons/alert-circle';
import type { GenerationJobList } from '$lib/api/client';

type SourceMode = 'job' | 'paste';

interface Props {
	sourceMode: SourceMode;
	jobsLoading: boolean;
	jobsError: string;
	jobs: GenerationJobList[];
	filteredJobs: GenerationJobList[];
	selectedJobId: string | null;
	jobSearch: string;
	pasteBackend: string;
	pasteFrontend: string;
	onSourceModeChange: (mode: SourceMode) => void;
	onSelectJob: (id: string) => void;
	onRetryLoadJobs: () => void;
}

let {
	sourceMode,
	jobsLoading,
	jobsError,
	jobs,
	filteredJobs,
	selectedJobId,
	jobSearch = $bindable(),
	pasteBackend = $bindable(),
	pasteFrontend = $bindable(),
	onSourceModeChange,
	onSelectJob,
	onRetryLoadJobs,
}: Props = $props();

function formatCompletedDate(value: string | null | undefined): string {
	if (!value) return '—';
	return new Date(value).toLocaleDateString();
}
</script>

<Card.Root>
	<Card.Header>
		<Card.Title>Select Source</Card.Title>
		<Card.Description>Choose a completed generation job or paste code directly.</Card.Description>
	</Card.Header>
	<Card.Content>
		<div class="mb-4 flex gap-2">
			<Button
				variant={sourceMode === 'job' ? 'default' : 'outline'}
				size="sm"
				onclick={() => onSourceModeChange('job')}
			>
				<FileCode class="mr-1.5 h-3.5 w-3.5" />
				Generation Job
			</Button>
			<Button
				variant={sourceMode === 'paste' ? 'default' : 'outline'}
				size="sm"
				onclick={() => onSourceModeChange('paste')}
			>
				<ClipboardPaste class="mr-1.5 h-3.5 w-3.5" />
				Paste Code
			</Button>
		</div>

		{#if sourceMode === 'job'}
			<div class="mb-4">
				<div class="relative w-full sm:max-w-sm">
					<Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
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
				<div class="flex items-center gap-2 rounded-md border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-400">
					<AlertCircle class="h-4 w-4 shrink-0" />
					{jobsError}
					<Button variant="outline" size="sm" class="ml-auto" onclick={onRetryLoadJobs}>Retry</Button>
				</div>
			{:else if filteredJobs.length === 0}
				<div class="py-12 text-center text-sm text-muted-foreground">
					{jobs.length === 0 ? 'No completed generation jobs found.' : 'No jobs match your search.'}
				</div>
			{:else}
				<div class="space-y-3 md:hidden">
					{#each filteredJobs as job}
						<div
							class="rounded-lg border p-3 transition-colors {selectedJobId === job.id ? 'border-primary bg-primary/5 shadow-sm' : 'border-border bg-card'}"
						>
							<div class="flex items-start justify-between gap-3">
								<div class="min-w-0 flex-1 space-y-3">
									<div class="flex flex-wrap items-center gap-2">
										<div class="min-w-0 flex-1">
											<div class="truncate text-sm font-medium">{job.model_name ?? 'Untitled application'}</div>
											<div class="mt-1 font-mono text-[11px] text-muted-foreground break-all">
												{job.id}
											</div>
										</div>
										{#if selectedJobId === job.id}
											<span class="rounded-full bg-primary px-2 py-0.5 text-[10px] font-medium text-primary-foreground">
												Selected
											</span>
										{/if}
									</div>
									<dl class="grid grid-cols-2 gap-x-3 gap-y-2 text-xs">
										<div class="min-w-0">
											<dt class="text-muted-foreground">Template</dt>
											<dd class="mt-0.5 truncate text-foreground">{job.template_name ?? '—'}</dd>
										</div>
										<div class="min-w-0">
											<dt class="text-muted-foreground">Completed</dt>
											<dd class="mt-0.5 text-foreground">{formatCompletedDate(job.completed_at)}</dd>
										</div>
									</dl>
								</div>
								<Button
									variant={selectedJobId === job.id ? 'default' : 'outline'}
									size="sm"
									class="h-10 shrink-0 px-3 text-xs"
									onclick={() => onSelectJob(job.id)}
								>
									{selectedJobId === job.id ? 'Selected' : 'Select'}
								</Button>
							</div>
						</div>
					{/each}
				</div>

				<div class="hidden overflow-x-auto table-scroll-wrapper md:block">
					<table class="w-full text-sm">
						<thead>
							<tr class="border-b bg-muted/30">
								<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Job ID</th>
								<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Model</th>
								<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Template</th>
								<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Completed</th>
								<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground"></th>
							</tr>
						</thead>
						<tbody class="divide-y">
							{#each filteredJobs as job}
								<tr class="transition-colors hover:bg-muted/30 {selectedJobId === job.id ? 'bg-primary/5' : ''}">
									<td class="px-4 py-2.5 font-mono text-xs">{job.id.slice(0, 8)}…</td>
									<td class="px-4 py-2.5">{job.model_name ?? '—'}</td>
									<td class="px-4 py-2.5">{job.template_name ?? '—'}</td>
									<td class="px-4 py-2.5 text-xs text-muted-foreground">
										{formatCompletedDate(job.completed_at)}
									</td>
									<td class="px-4 py-2.5">
										<Button
											variant={selectedJobId === job.id ? 'default' : 'outline'}
											size="sm"
											class="h-7 text-xs"
											onclick={() => onSelectJob(job.id)}
										>
											{selectedJobId === job.id ? 'Selected' : 'Select'}
										</Button>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		{:else}
			<div class="space-y-4">
				<div>
					<label class="mb-1 block text-sm font-medium">Backend Code</label>
					<textarea
						class="h-40 w-full rounded-md border border-input bg-background p-3 font-mono text-sm"
						placeholder="Paste backend code here…"
						bind:value={pasteBackend}
					></textarea>
				</div>
				<div>
					<label class="mb-1 block text-sm font-medium">Frontend Code</label>
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
