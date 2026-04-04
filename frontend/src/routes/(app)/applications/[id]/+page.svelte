<script lang="ts">
import { page } from '$app/stores';
import * as Card from '$lib/components/ui/card';
import { Badge } from '$lib/components/ui/badge';
import { Button } from '$lib/components/ui/button';
import {
getGenerationJob,
getJobArtifacts,
getCopilotIterations,
exportGenerationJob,
type GenerationJob,
type GenerationArtifact,
type CopilotIteration,
} from '$lib/api/client';
import { onMount } from 'svelte';
import { toast } from 'svelte-sonner';

import ArrowLeft from '@lucide/svelte/icons/arrow-left';
import Copy from '@lucide/svelte/icons/copy';
import ClipboardCheck from '@lucide/svelte/icons/clipboard-check';
import Download from '@lucide/svelte/icons/download';
import ExternalLink from '@lucide/svelte/icons/external-link';
import Eye from '@lucide/svelte/icons/eye';
import Layers from '@lucide/svelte/icons/layers';
import Bot from '@lucide/svelte/icons/bot';
import Pencil from '@lucide/svelte/icons/pencil';
import Code from '@lucide/svelte/icons/code';
import FileCode from '@lucide/svelte/icons/file-code';
import FolderTree from '@lucide/svelte/icons/folder-tree';
import Terminal from '@lucide/svelte/icons/terminal';
import Package from '@lucide/svelte/icons/package';
import Shield from '@lucide/svelte/icons/shield';
import Database from '@lucide/svelte/icons/database';
import ChevronDown from '@lucide/svelte/icons/chevron-down';
import ChevronRight from '@lucide/svelte/icons/chevron-right';
import CircleDot from '@lucide/svelte/icons/circle-dot';
import Clock from '@lucide/svelte/icons/clock';
import Timer from '@lucide/svelte/icons/timer';
import Hash from '@lucide/svelte/icons/hash';
import DollarSign from '@lucide/svelte/icons/dollar-sign';
import ChartBar from '@lucide/svelte/icons/chart-bar';
import AlertTriangle from '@lucide/svelte/icons/alert-triangle';
import CircleCheck from '@lucide/svelte/icons/circle-check';
import CircleX from '@lucide/svelte/icons/circle-x';
import LoaderCircle from '@lucide/svelte/icons/loader-circle';
import FlaskConical from '@lucide/svelte/icons/flask-conical';
import GitBranch from '@lucide/svelte/icons/git-branch';
import RefreshCw from '@lucide/svelte/icons/refresh-cw';

const jobId = $derived($page.params.id);
let loading = $state(true);
let job = $state<GenerationJob | null>(null);
let artifacts = $state<GenerationArtifact[]>([]);
let iterations = $state<CopilotIteration[]>([]);
let activeSection = $state('overview');

// Prompt explorer state
let selectedPromptIdx = $state(0);

// File explorer state
let selectedFileIdx = $state(0);

// Expanded artifact rows
let expandedArtifacts = $state<Set<number>>(new Set());

const sections = $derived(
[
{ id: 'overview', label: 'Overview', icon: Eye },
{ id: 'prompts', label: 'Prompts', icon: Terminal },
{ id: 'files', label: 'Files & Code', icon: FolderTree },
job?.mode === 'scaffolding' && job?.result_data?.backend_scan
? { id: 'scan', label: 'API Scan', icon: Shield }
: null,
{ id: 'dependencies', label: 'Dependencies', icon: Package },
{ id: 'artifacts', label: 'Artifacts', icon: Database },
job?.mode === 'copilot' ? { id: 'iterations', label: 'Copilot Iterations', icon: Bot } : null,
{ id: 'metrics', label: 'Cost & Metrics', icon: ChartBar },
].filter(Boolean) as { id: string; label: string; icon: any }[]
);

// ── Computed data ────────────────────────────────────────────────

const provider = $derived(job?.model_id_str?.split('/')[0] ?? '—');

const codeFootprint = $derived.by(() => {
if (!job?.result_data) return null;
const rd = job.result_data;
let totalLines = 0;
let totalChars = 0;
const languages: Record<string, number> = {};
const files: { name: string; code: string; lang: string }[] = [];

if (job.mode === 'scaffolding') {
if (rd.backend_code) {
const lines = rd.backend_code.split('\n').length;
totalLines += lines;
totalChars += rd.backend_code.length;
languages['Python'] = lines;
files.push({ name: 'backend/app.py', code: rd.backend_code, lang: 'python' });
}
if (rd.frontend_code) {
const lines = rd.frontend_code.split('\n').length;
totalLines += lines;
totalChars += rd.frontend_code.length;
languages['JavaScript'] = lines;
files.push({ name: 'frontend/App.jsx', code: rd.frontend_code, lang: 'javascript' });
}
} else {
const content = rd.content ?? rd.raw_response ?? '';
if (content) {
totalLines = content.split('\n').length;
totalChars = content.length;
// Detect languages from code blocks
const blocks = content.match(/```(\w+)/g) ?? [];
for (const b of blocks) {
const lang = b.replace('```', '');
const mapped = lang === 'py' ? 'Python' : lang === 'js' ? 'JavaScript' : lang === 'html' ? 'HTML' : lang === 'css' ? 'CSS' : lang.charAt(0).toUpperCase() + lang.slice(1);
languages[mapped] = (languages[mapped] ?? 0) + 1;
}
files.push({ name: 'output.txt', code: content, lang: 'text' });
}
}

return {
totalLines,
totalChars,
languages,
fileCount: (rd.backend_files ?? 0) + (rd.frontend_files ?? 0) || files.length,
files,
truncated: rd.backend_truncated || rd.frontend_truncated || rd.truncated || false,
};
});

// Build prompt entries for the two-pane explorer
const promptEntries = $derived.by(() => {
const entries: { label: string; badge: string; badgeColor: string; content: string; meta?: Record<string, string> }[] = [];

if (job?.mode === 'custom') {
if (job.custom_system_prompt)
entries.push({ label: 'System Prompt', badge: 'SYS', badgeColor: 'bg-blue-500/20 text-blue-400', content: job.custom_system_prompt });
if (job.custom_user_prompt)
entries.push({ label: 'User Prompt', badge: 'USR', badgeColor: 'bg-emerald-500/20 text-emerald-400', content: job.custom_user_prompt });
if (job.result_data?.content)
entries.push({ label: 'Response', badge: 'RES', badgeColor: 'bg-purple-500/20 text-purple-400', content: job.result_data.content.substring(0, 2000) + (job.result_data.content.length > 2000 ? '\n...(truncated for preview)' : '') });
}

// Add artifact-based prompts
for (const art of artifacts) {
const msgs = art.request_payload?.messages ?? [];
const respModel = art.response_payload?.model ?? art.request_payload?.model ?? '—';
for (const msg of msgs) {
const roleLabel = msg.role === 'system' ? 'System' : msg.role === 'user' ? 'User' : 'Assistant';
const roleBadge = msg.role === 'system' ? 'SYS' : msg.role === 'user' ? 'USR' : 'AST';
const roleColor = msg.role === 'system' ? 'bg-blue-500/20 text-blue-400' : msg.role === 'user' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-purple-500/20 text-purple-400';
entries.push({
label: `${art.stage} — ${roleLabel}`,
badge: roleBadge,
badgeColor: roleColor,
content: msg.content ?? '',
meta: { stage: art.stage, model: respModel, tokens: `${art.prompt_tokens}+${art.completion_tokens}` },
});
}
// Add response
const choices = art.response_payload?.choices ?? [];
if (choices.length > 0) {
const respContent = choices[0]?.message?.content ?? '';
entries.push({
label: `${art.stage} — Response`,
badge: 'RES',
badgeColor: 'bg-purple-500/20 text-purple-400',
content: respContent.substring(0, 3000) + (respContent.length > 3000 ? '\n...(truncated)' : ''),
meta: { stage: art.stage, model: respModel, finish: choices[0]?.finish_reason ?? '—' },
});
}
}

if (entries.length === 0 && job?.mode === 'copilot' && job.copilot_description) {
entries.push({ label: 'Copilot Description', badge: 'DESC', badgeColor: 'bg-teal-500/20 text-teal-400', content: job.copilot_description });
}

return entries;
});

// Virtual file tree
const virtualFiles = $derived.by(() => {
const fp = codeFootprint;
return codeFootprint?.files ?? [];
});

// Backend scan data
const backendScan = $derived(job?.result_data?.backend_scan ?? null);

// Dependencies
const backendDeps = $derived(job?.result_data?.backend_dependencies ?? job?.result_data?.dependencies ?? []);

// Cost calculations
const costData = $derived.by(() => {
let totalCost = 0;
let totalPrompt = 0;
let totalCompletion = 0;
const byStage: Record<string, { cost: number; prompt: number; completion: number }> = {};

for (const art of artifacts) {
totalCost += art.total_cost ?? 0;
totalPrompt += art.prompt_tokens ?? 0;
totalCompletion += art.completion_tokens ?? 0;
const s = art.stage ?? 'unknown';
if (!byStage[s]) byStage[s] = { cost: 0, prompt: 0, completion: 0 };
byStage[s].cost += art.total_cost ?? 0;
byStage[s].prompt += art.prompt_tokens ?? 0;
byStage[s].completion += art.completion_tokens ?? 0;
}

// Fall back to metrics if no artifacts
if (totalPrompt === 0 && job?.metrics) {
totalPrompt = job.metrics.prompt_tokens ?? 0;
totalCompletion = job.metrics.completion_tokens ?? 0;
}

const totalTokens = totalPrompt + totalCompletion;
const tokensPerSec = job?.duration_seconds ? totalTokens / job.duration_seconds : 0;

return { totalCost, totalPrompt, totalCompletion, totalTokens, tokensPerSec, byStage };
});

// ── Actions ──────────────────────────────────────────────────────

async function fetchData() {
try {
const [j, arts] = await Promise.all([
getGenerationJob(jobId),
getJobArtifacts(jobId),
]);
job = j;
artifacts = arts;
if (j.mode === 'copilot') {
iterations = await getCopilotIterations(jobId);
}
} catch (e: any) {
toast.error('Failed to load job details');
} finally {
loading = false;
}
}

function copyText(text: string, label = 'Copied') {
navigator.clipboard.writeText(text);
toast.success(label);
}

async function handleExport() {
try {
const data = await exportGenerationJob(jobId);
const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
const url = URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = `job-${jobId.substring(0, 8)}.json`;
a.click();
URL.revokeObjectURL(url);
toast.success('Exported JSON');
} catch {
toast.error('Export failed');
}
}

function downloadCode() {
if (!codeFootprint || codeFootprint.files.length === 0) return;
// Download as individual file(s)
for (const f of codeFootprint.files) {
const blob = new Blob([f.code], { type: 'text/plain' });
const url = URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = f.name.split('/').pop() ?? 'code.txt';
a.click();
URL.revokeObjectURL(url);
}
toast.success('Downloaded code files');
}

function toggleArtifact(id: number) {
const next = new Set(expandedArtifacts);
if (next.has(id)) next.delete(id);
else next.add(id);
expandedArtifacts = next;
}

function scrollToSection(id: string) {
activeSection = id;
document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function fmt(n: number | null | undefined, decimals = 1): string {
if (n == null) return '—';
return n.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: decimals });
}

function fmtDur(seconds: number | null): string {
if (seconds == null) return '—';
if (seconds < 60) return `${seconds.toFixed(1)}s`;
const m = Math.floor(seconds / 60);
const s = Math.round(seconds % 60);
return `${m}m ${s}s`;
}

function fmtDate(d: string | null): string {
if (!d) return '—';
return new Date(d).toLocaleString();
}

function fmtCost(c: number): string {
if (c === 0) return 'Free';
if (c < 0.01) return `$${c.toFixed(6)}`;
return `$${c.toFixed(4)}`;
}

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
const modeIcons: Record<string, any> = { custom: Pencil, scaffolding: Layers, copilot: Bot };
const httpColors: Record<string, string> = { GET: 'text-emerald-400', POST: 'text-blue-400', PUT: 'text-amber-400', DELETE: 'text-red-400', PATCH: 'text-purple-400' };

onMount(fetchData);
</script>

<svelte:head>
<title>{job?.model_name ?? 'Application'} - LLM Lab</title>
</svelte:head>

{#if loading}
<div class="flex items-center justify-center py-32">
<LoaderCircle class="h-8 w-8 animate-spin text-muted-foreground" />
<span class="ml-3 text-muted-foreground">Loading application details...</span>
</div>
{:else if !job}
<Card.Root>
<Card.Content class="py-16 text-center">
<AlertTriangle class="mx-auto h-12 w-12 text-red-400 mb-4" />
<h3 class="text-lg font-medium">Job not found</h3>
<Button variant="outline" size="sm" href="/applications" class="mt-4">Back to Applications</Button>
</Card.Content>
</Card.Root>
{:else}
<div class="space-y-5">
<!-- Breadcrumb -->
<nav aria-label="Breadcrumb" class="flex items-center gap-2 text-sm text-muted-foreground">
<a href="/applications" class="hover:text-foreground transition-colors flex items-center gap-1">
<ArrowLeft class="h-3.5 w-3.5" />
<span class="font-medium text-foreground">Applications</span>
</a>
<span>/</span>
<span class="text-muted-foreground truncate max-w-[300px]">{job.model_name ?? job.model_id_str ?? 'Unknown'}</span>
</nav>

<!-- Failed banner -->
{#if job.status === 'failed'}
<div class="flex items-center gap-3 rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3">
<AlertTriangle class="h-5 w-5 text-red-400 shrink-0" />
<div class="flex-1">
<p class="text-sm font-medium text-red-400">Generation Failed</p>
<p class="text-xs text-red-400/70 truncate">{job.error_message || 'Unknown error'}</p>
</div>
<Button variant="outline" size="sm" href="/applications/{job.id}/failure" class="border-red-500/30 text-red-400 hover:bg-red-500/10">
View Details
</Button>
</div>
{/if}

<!-- Header Card -->
<Card.Root>
<Card.Content class="p-5">
<div class="flex items-start justify-between gap-4">
<div class="flex items-start gap-4">
<div class="flex h-12 w-12 items-center justify-center rounded-xl {modeColors[job.mode] ?? 'bg-zinc-500/15'}">
{#if modeIcons[job.mode]}
<svelte:component this={modeIcons[job.mode]} class="h-6 w-6" />
{/if}
</div>
<div>
<h1 class="text-xl font-semibold">{job.model_name ?? 'Unknown Model'}</h1>
<div class="flex flex-wrap items-center gap-2 mt-1.5">
<Badge variant="outline" class="text-xs {modeColors[job.mode] ?? ''}">{job.mode}</Badge>
<Badge variant="outline" class="text-xs {statusColors[job.status] ?? ''}">
{#if job.status === 'running'}<span class="mr-1 h-1.5 w-1.5 rounded-full bg-amber-500 animate-pulse inline-block"></span>{/if}
{job.status}
</Badge>
<Badge variant="outline" class="text-xs">{provider}</Badge>
{#if job.template_name}
<Badge variant="outline" class="text-xs">{job.template_name}</Badge>
{/if}
{#if job.scaffolding_name}
<Badge variant="outline" class="text-xs bg-purple-500/10 text-purple-400 border-purple-500/30">{job.scaffolding_name}</Badge>
{/if}
{#if job.batch_name}
<Badge variant="outline" class="text-xs">
<GitBranch class="h-3 w-3 mr-1" />{job.batch_name}
</Badge>
{/if}
</div>
<p class="text-xs text-muted-foreground mt-1 font-mono">{job.model_id_str} · {job.id.substring(0, 8)}</p>
</div>
</div>
<!-- Action buttons -->
<div class="flex items-center gap-2 shrink-0">
<Button variant="outline" size="sm" onclick={() => copyText(job!.id, 'Copied Job ID')} title="Copy Job ID">
<Copy class="h-3.5 w-3.5 mr-1.5" />ID
</Button>
<Button variant="outline" size="sm" onclick={handleExport} title="Export as JSON">
<Download class="h-3.5 w-3.5 mr-1.5" />Export
</Button>
<Button variant="outline" size="sm" onclick={downloadCode} title="Download generated code">
<FileCode class="h-3.5 w-3.5 mr-1.5" />Code
</Button>
<Button size="sm" href="/sample-generator" title="Generate with same settings">
<RefreshCw class="h-3.5 w-3.5 mr-1.5" />Re-generate
</Button>
</div>
</div>
</Card.Content>
</Card.Root>

<!-- KPI Row -->
<div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
<div class="rounded-lg border bg-card p-3 text-center">
<div class="text-xs text-muted-foreground mb-1">Duration</div>
<div class="text-lg font-semibold">{fmtDur(job.duration_seconds)}</div>
</div>
<div class="rounded-lg border bg-card p-3 text-center">
<div class="text-xs text-muted-foreground mb-1">Tokens</div>
<div class="text-lg font-semibold">{fmt(costData.totalTokens, 0)}</div>
</div>
<div class="rounded-lg border bg-card p-3 text-center">
<div class="text-xs text-muted-foreground mb-1">Cost</div>
<div class="text-lg font-semibold">{fmtCost(costData.totalCost)}</div>
</div>
<div class="rounded-lg border bg-card p-3 text-center">
<div class="text-xs text-muted-foreground mb-1">Temperature</div>
<div class="text-lg font-semibold">{job.temperature}</div>
</div>
<div class="rounded-lg border bg-card p-3 text-center">
<div class="text-xs text-muted-foreground mb-1">Max Tokens</div>
<div class="text-lg font-semibold">{fmt(job.max_tokens, 0)}</div>
</div>
<div class="rounded-lg border bg-card p-3 text-center">
<div class="text-xs text-muted-foreground mb-1">Lines of Code</div>
<div class="text-lg font-semibold">{fmt(codeFootprint?.totalLines ?? 0, 0)}</div>
</div>
</div>

<!-- Sticky Section Nav -->
<div class="sticky top-0 z-20 -mx-1 px-1 py-2 bg-background/95 backdrop-blur border-b">
<div class="flex items-center gap-1 overflow-x-auto">
{#each sections as sec}
<button
class="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors whitespace-nowrap {activeSection === sec.id ? 'bg-primary/10 text-primary border border-primary/30' : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'}"
onclick={() => scrollToSection(sec.id)}
>
<svelte:component this={sec.icon} class="h-3.5 w-3.5" />
{sec.label}
</button>
{/each}
</div>
</div>

<!-- ═══════════════ OVERVIEW SECTION ═══════════════ -->
<section id="overview" class="space-y-4">
<h2 class="text-lg font-semibold flex items-center gap-2"><Eye class="h-5 w-5" /> Overview</h2>
<div class="grid md:grid-cols-2 gap-4">
<!-- Identity & Generation -->
<Card.Root>
<Card.Header class="pb-3"><Card.Title class="text-sm font-medium">Identity & Generation</Card.Title></Card.Header>
<Card.Content class="space-y-2 text-sm">
<div class="flex justify-between"><dt class="text-muted-foreground">Model</dt><dd class="font-medium">{job.model_name ?? '—'}</dd></div>
<div class="flex justify-between"><dt class="text-muted-foreground">Provider</dt><dd><Badge variant="outline" class="text-xs">{provider}</Badge></dd></div>
<div class="flex justify-between"><dt class="text-muted-foreground">Mode</dt><dd><Badge variant="outline" class="text-xs {modeColors[job.mode] ?? ''}">{job.mode}</Badge></dd></div>
<div class="flex justify-between"><dt class="text-muted-foreground">Status</dt><dd><Badge variant="outline" class="text-xs {statusColors[job.status] ?? ''}">{job.status}</Badge></dd></div>
<div class="flex justify-between"><dt class="text-muted-foreground">Job ID</dt><dd class="font-mono text-xs">{job.id.substring(0, 16)}...</dd></div>
{#if job.template_name}
<div class="flex justify-between"><dt class="text-muted-foreground">Template</dt><dd>{job.template_name}</dd></div>
{/if}
{#if job.scaffolding_name}
<div class="flex justify-between"><dt class="text-muted-foreground">Scaffolding</dt><dd>{job.scaffolding_name}</dd></div>
{/if}
{#if job.batch_name}
<div class="flex justify-between"><dt class="text-muted-foreground">Batch</dt><dd>{job.batch_name}</dd></div>
{/if}
{#if job.created_by_email}
<div class="flex justify-between"><dt class="text-muted-foreground">Created by</dt><dd>{job.created_by_email}</dd></div>
{/if}
</Card.Content>
</Card.Root>

<!-- Code Footprint -->
<Card.Root>
<Card.Header class="pb-3"><Card.Title class="text-sm font-medium">Code Footprint</Card.Title></Card.Header>
<Card.Content>
{#if codeFootprint && codeFootprint.totalLines > 0}
<div class="grid grid-cols-3 gap-4 mb-4">
<div class="text-center">
<div class="text-2xl font-bold text-blue-400">{fmt(codeFootprint.totalLines, 0)}</div>
<div class="text-xs text-muted-foreground">Lines</div>
</div>
<div class="text-center">
<div class="text-2xl font-bold text-emerald-400">{codeFootprint.fileCount}</div>
<div class="text-xs text-muted-foreground">Files</div>
</div>
<div class="text-center">
<div class="text-2xl font-bold text-purple-400">{(codeFootprint.totalChars / 1024).toFixed(1)}</div>
<div class="text-xs text-muted-foreground">KB</div>
</div>
</div>
<div class="flex flex-wrap gap-1.5">
{#each Object.entries(codeFootprint.languages) as [lang, count]}
<Badge variant="outline" class="text-xs">{lang}: {count}</Badge>
{/each}
</div>
{#if codeFootprint.truncated}
<p class="text-xs text-amber-400 mt-2">⚠ Output was truncated</p>
{/if}
{:else}
<p class="text-sm text-muted-foreground">No code generated</p>
{/if}
</Card.Content>
</Card.Root>

<!-- Timing -->
<Card.Root>
<Card.Header class="pb-3"><Card.Title class="text-sm font-medium">Timing</Card.Title></Card.Header>
<Card.Content class="space-y-2 text-sm">
<div class="flex justify-between"><dt class="text-muted-foreground">Created</dt><dd>{fmtDate(job.created_at)}</dd></div>
<div class="flex justify-between"><dt class="text-muted-foreground">Started</dt><dd>{fmtDate(job.started_at)}</dd></div>
<div class="flex justify-between"><dt class="text-muted-foreground">Completed</dt><dd>{fmtDate(job.completed_at)}</dd></div>
<div class="flex justify-between"><dt class="text-muted-foreground">Duration</dt><dd class="font-semibold">{fmtDur(job.duration_seconds)}</dd></div>
<div class="flex justify-between"><dt class="text-muted-foreground">Updated</dt><dd>{fmtDate(job.updated_at)}</dd></div>
{#if job.metrics?.backend_duration}
<div class="flex justify-between"><dt class="text-muted-foreground">Backend duration</dt><dd>{fmtDur(job.metrics.backend_duration)}</dd></div>
{/if}
{#if job.metrics?.frontend_duration}
<div class="flex justify-between"><dt class="text-muted-foreground">Frontend duration</dt><dd>{fmtDur(job.metrics.frontend_duration)}</dd></div>
{/if}
</Card.Content>
</Card.Root>

<!-- Generation Config -->
<Card.Root>
<Card.Header class="pb-3"><Card.Title class="text-sm font-medium">Generation Config</Card.Title></Card.Header>
<Card.Content class="space-y-2 text-sm">
<div class="flex justify-between"><dt class="text-muted-foreground">Temperature</dt><dd>{job.temperature}</dd></div>
<div class="flex justify-between"><dt class="text-muted-foreground">Max Tokens</dt><dd>{fmt(job.max_tokens, 0)}</dd></div>
{#if job.mode === 'copilot'}
<div class="flex justify-between"><dt class="text-muted-foreground">Max Iterations</dt><dd>{job.copilot_max_iterations}</dd></div>
<div class="flex justify-between"><dt class="text-muted-foreground">Iterations Used</dt><dd>{job.copilot_current_iteration}</dd></div>
<div class="flex justify-between"><dt class="text-muted-foreground">Open Source</dt><dd>{job.copilot_use_open_source ? 'Yes' : 'No'}</dd></div>
{/if}
{#if job.copilot_description}
<div class="pt-2 border-t"><dt class="text-muted-foreground mb-1">Description</dt><dd class="text-xs bg-muted/50 rounded p-2">{job.copilot_description}</dd></div>
{/if}
</Card.Content>
</Card.Root>
</div>
</section>

<!-- ═══════════════ PROMPTS SECTION ═══════════════ -->
<section id="prompts" class="space-y-4">
<h2 class="text-lg font-semibold flex items-center gap-2"><Terminal class="h-5 w-5" /> Prompts</h2>
{#if promptEntries.length === 0}
<Card.Root>
<Card.Content class="py-12 text-center">
<Terminal class="mx-auto h-10 w-10 text-muted-foreground/30 mb-3" />
<p class="text-sm text-muted-foreground">No prompts recorded for this job</p>
</Card.Content>
</Card.Root>
{:else}
<Card.Root>
<Card.Content class="p-0">
<div class="flex" style="height: 450px;">
<!-- Left: Prompt Tree -->
<div class="w-2/5 border-r overflow-y-auto bg-muted/20">
<div class="p-2 text-xs font-medium text-muted-foreground uppercase tracking-wider border-b px-3 py-2">
Prompt Exchange ({promptEntries.length})
</div>
{#each promptEntries as entry, i}
<button
class="w-full text-left px-3 py-2.5 text-sm border-b border-border/50 transition-colors flex items-start gap-2 {selectedPromptIdx === i ? 'bg-primary/10 border-l-2 border-l-primary' : 'hover:bg-muted/50'}"
onclick={() => (selectedPromptIdx = i)}
>
<span class="shrink-0 text-[10px] font-bold px-1.5 py-0.5 rounded {entry.badgeColor}">{entry.badge}</span>
<div class="min-w-0">
<div class="font-medium truncate">{entry.label}</div>
{#if entry.meta}
<div class="text-xs text-muted-foreground mt-0.5">{entry.meta.stage ?? ''} · {entry.meta.tokens ?? ''}</div>
{/if}
</div>
</button>
{/each}
</div>
<!-- Right: Content Preview -->
<div class="w-3/5 flex flex-col">
<div class="flex items-center justify-between px-4 py-2 border-b bg-muted/20">
<span class="text-sm font-medium">{promptEntries[selectedPromptIdx]?.label ?? ''}</span>
<Button variant="ghost" size="sm" class="h-7" onclick={() => copyText(promptEntries[selectedPromptIdx]?.content ?? '', 'Copied')}>
<Copy class="h-3.5 w-3.5 mr-1" />Copy
</Button>
</div>
{#if promptEntries[selectedPromptIdx]?.meta}
<div class="flex flex-wrap gap-3 px-4 py-1.5 border-b bg-muted/10 text-xs text-muted-foreground">
{#each Object.entries(promptEntries[selectedPromptIdx].meta ?? {}) as [k, v]}
<span><strong>{k}:</strong> {v}</span>
{/each}
</div>
{/if}
<div class="flex-1 overflow-auto p-4">
<pre class="text-xs font-mono whitespace-pre-wrap break-words text-foreground/90">{promptEntries[selectedPromptIdx]?.content ?? ''}</pre>
</div>
</div>
</div>
</Card.Content>
</Card.Root>
{/if}
</section>

<!-- ═══════════════ FILES SECTION ═══════════════ -->
<section id="files" class="space-y-4">
<h2 class="text-lg font-semibold flex items-center gap-2"><FolderTree class="h-5 w-5" /> Files & Code</h2>
{#if virtualFiles.length === 0}
<Card.Root>
<Card.Content class="py-12 text-center">
<FolderTree class="mx-auto h-10 w-10 text-muted-foreground/30 mb-3" />
<p class="text-sm text-muted-foreground">No files generated</p>
</Card.Content>
</Card.Root>
{:else}
<!-- Key Artifacts Bar -->
<div class="flex items-center gap-2 flex-wrap">
{#each virtualFiles as f, i}
<Button variant={selectedFileIdx === i ? 'default' : 'outline'} size="sm" onclick={() => (selectedFileIdx = i)}>
<FileCode class="h-3.5 w-3.5 mr-1.5" />
{f.name}
</Button>
{/each}
</div>

<Card.Root>
<Card.Content class="p-0">
<div class="flex" style="height: 500px;">
<!-- Left: File Tree -->
<div class="w-1/3 border-r overflow-y-auto bg-muted/20">
<div class="p-2 text-xs font-medium text-muted-foreground uppercase tracking-wider border-b px-3 py-2">
Files ({virtualFiles.length})
</div>
{#each virtualFiles as f, i}
<button
class="w-full text-left px-3 py-2.5 text-sm border-b border-border/50 transition-colors flex items-center gap-2 {selectedFileIdx === i ? 'bg-primary/10 border-l-2 border-l-primary' : 'hover:bg-muted/50'}"
onclick={() => (selectedFileIdx = i)}
>
<FileCode class="h-4 w-4 text-muted-foreground shrink-0" />
<div class="min-w-0 flex-1">
<div class="font-medium truncate font-mono text-xs">{f.name}</div>
<div class="text-xs text-muted-foreground">{f.code.split('\n').length} lines · {(f.code.length / 1024).toFixed(1)} KB</div>
</div>
</button>
{/each}
</div>
<!-- Right: File Preview -->
<div class="w-2/3 flex flex-col">
<div class="flex items-center justify-between px-4 py-2 border-b bg-muted/20">
<span class="text-sm font-medium font-mono">{virtualFiles[selectedFileIdx]?.name ?? ''}</span>
<div class="flex items-center gap-1">
<Badge variant="outline" class="text-xs">{virtualFiles[selectedFileIdx]?.lang}</Badge>
<Button variant="ghost" size="sm" class="h-7" onclick={() => copyText(virtualFiles[selectedFileIdx]?.code ?? '', 'Copied file')}>
<Copy class="h-3.5 w-3.5" />
</Button>
</div>
</div>
<div class="flex-1 overflow-auto bg-zinc-950">
<pre class="p-4 text-xs font-mono text-zinc-300 leading-relaxed">{#each (virtualFiles[selectedFileIdx]?.code ?? '').split('\n') as line, ln}<span class="inline-block w-10 text-right mr-4 text-zinc-600 select-none">{ln + 1}</span>{line}
{/each}</pre>
</div>
</div>
</div>
</Card.Content>
</Card.Root>
{/if}
</section>

<!-- ═══════════════ API SCAN SECTION ═══════════════ -->
{#if backendScan}
<section id="scan" class="space-y-4">
<h2 class="text-lg font-semibold flex items-center gap-2"><Shield class="h-5 w-5" /> API Scan</h2>
<div class="grid md:grid-cols-2 gap-4">
<!-- Endpoints -->
<Card.Root>
<Card.Header class="pb-3">
<Card.Title class="text-sm font-medium flex items-center gap-2">
API Endpoints
<Badge variant="outline" class="text-xs">{backendScan.endpoints?.length ?? 0}</Badge>
</Card.Title>
</Card.Header>
<Card.Content>
{#if backendScan.endpoints?.length > 0}
<div class="space-y-1.5">
{#each backendScan.endpoints as ep}
<div class="flex items-center gap-2 text-sm font-mono">
<span class="text-xs font-bold w-12 {httpColors[ep.method] ?? 'text-zinc-400'}">{ep.method}</span>
<span class="text-foreground/90">{ep.path}</span>
</div>
{/each}
</div>
{:else}
<p class="text-sm text-muted-foreground">No endpoints detected</p>
{/if}
</Card.Content>
</Card.Root>

<!-- Models -->
<Card.Root>
<Card.Header class="pb-3">
<Card.Title class="text-sm font-medium flex items-center gap-2">
Data Models
<Badge variant="outline" class="text-xs">{backendScan.models?.length ?? 0}</Badge>
</Card.Title>
</Card.Header>
<Card.Content>
{#if backendScan.models?.length > 0}
<div class="space-y-3">
{#each backendScan.models as model}
<div>
<div class="font-medium text-sm flex items-center gap-2">
<Database class="h-3.5 w-3.5 text-muted-foreground" />
{model.name}
<Badge variant="outline" class="text-[10px]">{model.fields?.length ?? 0} fields</Badge>
</div>
{#if model.fields?.length > 0}
<div class="flex flex-wrap gap-1 mt-1 ml-5">
{#each model.fields as field}
<Badge variant="outline" class="text-[10px] font-mono">{field}</Badge>
{/each}
</div>
{/if}
</div>
{/each}
</div>
{:else}
<p class="text-sm text-muted-foreground">No models detected</p>
{/if}
</Card.Content>
</Card.Root>
</div>

<!-- Detection badges -->
<div class="flex items-center gap-3">
<Badge variant="outline" class="text-xs {backendScan.has_auth ? 'bg-emerald-500/15 text-emerald-500 border-emerald-500/30' : 'bg-zinc-500/15 text-zinc-400'}">
<Shield class="h-3 w-3 mr-1" />
Auth: {backendScan.has_auth ? 'Detected' : 'None'}
</Badge>
<Badge variant="outline" class="text-xs {backendScan.has_admin ? 'bg-emerald-500/15 text-emerald-500 border-emerald-500/30' : 'bg-zinc-500/15 text-zinc-400'}">
<Shield class="h-3 w-3 mr-1" />
Admin: {backendScan.has_admin ? 'Detected' : 'None'}
</Badge>
</div>
</section>
{/if}

<!-- ═══════════════ DEPENDENCIES SECTION ═══════════════ -->
<section id="dependencies" class="space-y-4">
<h2 class="text-lg font-semibold flex items-center gap-2"><Package class="h-5 w-5" /> Dependencies</h2>
{#if backendDeps.length > 0}
<Card.Root>
<Card.Header class="pb-3">
<Card.Title class="text-sm font-medium flex items-center gap-2">
{job.mode === 'scaffolding' ? 'Backend' : ''} Dependencies
<Badge variant="outline" class="text-xs">{backendDeps.length}</Badge>
</Card.Title>
</Card.Header>
<Card.Content class="p-0">
<table class="w-full text-sm">
<thead>
<tr class="border-b bg-muted/30">
<th class="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Package</th>
<th class="px-4 py-2 text-left text-xs font-medium text-muted-foreground">Version</th>
</tr>
</thead>
<tbody class="divide-y">
{#each backendDeps as dep}
{@const parts = typeof dep === 'string' ? dep.split(/[=<>~!]+/) : [dep]}
<tr class="hover:bg-muted/30">
<td class="px-4 py-2 font-mono text-xs">{parts[0]}</td>
<td class="px-4 py-2"><Badge variant="outline" class="text-xs">{parts[1] ?? 'latest'}</Badge></td>
</tr>
{/each}
</tbody>
</table>
</Card.Content>
</Card.Root>
{:else}
<Card.Root>
<Card.Content class="py-10 text-center">
<Package class="mx-auto h-10 w-10 text-muted-foreground/30 mb-3" />
<p class="text-sm text-muted-foreground">No dependencies recorded</p>
</Card.Content>
</Card.Root>
{/if}
</section>

<!-- ═══════════════ ARTIFACTS SECTION ═══════════════ -->
<section id="artifacts" class="space-y-4">
<h2 class="text-lg font-semibold flex items-center gap-2"><Database class="h-5 w-5" /> Artifacts</h2>
{#if artifacts.length === 0}
<Card.Root>
<Card.Content class="py-10 text-center">
<Database class="mx-auto h-10 w-10 text-muted-foreground/30 mb-3" />
<p class="text-sm text-muted-foreground">No artifacts recorded</p>
</Card.Content>
</Card.Root>
{:else}
<Card.Root>
<Card.Content class="p-0">
<table class="w-full text-sm">
<thead>
<tr class="border-b bg-muted/30">
<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground w-8"></th>
<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Stage</th>
<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Model</th>
<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Prompt</th>
<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Completion</th>
<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Cost</th>
<th class="px-4 py-3 text-left text-xs font-medium text-muted-foreground">Created</th>
</tr>
</thead>
<tbody class="divide-y">
{#each artifacts as art}
<tr class="hover:bg-muted/30 cursor-pointer" onclick={() => toggleArtifact(art.id)}>
<td class="px-4 py-3">
{#if expandedArtifacts.has(art.id)}
<ChevronDown class="h-4 w-4 text-muted-foreground" />
{:else}
<ChevronRight class="h-4 w-4 text-muted-foreground" />
{/if}
</td>
<td class="px-4 py-3"><Badge variant="outline" class="text-xs">{art.stage}</Badge></td>
<td class="px-4 py-3 font-mono text-xs">{art.request_payload?.model ?? art.response_payload?.model ?? '—'}</td>
<td class="px-4 py-3">{fmt(art.prompt_tokens, 0)}</td>
<td class="px-4 py-3">{fmt(art.completion_tokens, 0)}</td>
<td class="px-4 py-3">{fmtCost(art.total_cost)}</td>
<td class="px-4 py-3 text-muted-foreground">{fmtDate(art.created_at)}</td>
</tr>
{#if expandedArtifacts.has(art.id)}
<tr>
<td colspan="7" class="px-4 py-4 bg-muted/20">
<!-- Token bar -->
{#if (art.prompt_tokens ?? 0) + (art.completion_tokens ?? 0) > 0}
{@const total = (art.prompt_tokens ?? 0) + (art.completion_tokens ?? 0)}
<div class="mb-4">
<div class="text-xs text-muted-foreground mb-1">Token Breakdown ({total} total)</div>
<div class="h-3 rounded-full overflow-hidden bg-zinc-800 flex">
<div class="bg-blue-500 h-full" style="width: {(art.prompt_tokens / total) * 100}%"></div>
<div class="bg-emerald-500 h-full" style="width: {(art.completion_tokens / total) * 100}%"></div>
</div>
<div class="flex justify-between text-[10px] text-muted-foreground mt-0.5">
<span>Prompt: {fmt(art.prompt_tokens, 0)}</span>
<span>Completion: {fmt(art.completion_tokens, 0)}</span>
</div>
</div>
{/if}
<!-- Request Messages -->
<div class="space-y-2">
<div class="text-xs font-medium text-muted-foreground uppercase">Request Messages</div>
{#each (art.request_payload?.messages ?? []) as msg}
<div class="border rounded-md">
<div class="px-3 py-1.5 border-b bg-muted/30 flex items-center gap-2">
<Badge variant="outline" class="text-[10px] {msg.role === 'system' ? 'bg-blue-500/20 text-blue-400' : msg.role === 'user' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-purple-500/20 text-purple-400'}">{msg.role}</Badge>
<span class="text-xs text-muted-foreground">{(msg.content?.length ?? 0)} chars</span>
</div>
<pre class="p-3 text-xs font-mono whitespace-pre-wrap max-h-48 overflow-auto">{msg.content ?? ''}</pre>
</div>
{/each}
</div>
<!-- Response -->
{#if art.response_payload?.choices?.length > 0}
<div class="space-y-2 mt-3">
<div class="text-xs font-medium text-muted-foreground uppercase">Response</div>
<div class="border rounded-md">
<div class="px-3 py-1.5 border-b bg-muted/30 flex items-center gap-2">
<Badge variant="outline" class="text-[10px] bg-purple-500/20 text-purple-400">assistant</Badge>
<span class="text-xs text-muted-foreground">finish: {art.response_payload.choices[0]?.finish_reason ?? '—'}</span>
</div>
<pre class="p-3 text-xs font-mono whitespace-pre-wrap max-h-48 overflow-auto">{art.response_payload.choices[0]?.message?.content ?? '(empty)'}</pre>
</div>
</div>
{/if}
</td>
</tr>
{/if}
{/each}
</tbody>
</table>
</Card.Content>
</Card.Root>
{/if}
</section>

<!-- ═══════════════ COPILOT ITERATIONS SECTION ═══════════════ -->
{#if job.mode === 'copilot' && iterations.length > 0}
<section id="iterations" class="space-y-4">
<h2 class="text-lg font-semibold flex items-center gap-2"><Bot class="h-5 w-5" /> Copilot Iterations</h2>
<div class="relative pl-6">
<!-- Timeline line -->
<div class="absolute left-2.5 top-0 bottom-0 w-px bg-border"></div>

{#each iterations as it, i}
<div class="relative mb-4">
<!-- Timeline dot -->
<div class="absolute -left-6 top-4 w-5 h-5 rounded-full border-2 flex items-center justify-center text-[10px] font-bold {it.build_success ? 'border-emerald-500 bg-emerald-500/20 text-emerald-400' : 'border-red-500 bg-red-500/20 text-red-400'}">
{it.iteration_number}
</div>

<Card.Root>
<Card.Header class="pb-2">
<div class="flex items-center justify-between">
<div class="flex items-center gap-2">
<Card.Title class="text-sm font-medium">Iteration {it.iteration_number}</Card.Title>
<Badge variant="outline" class="text-xs">{it.action}</Badge>
</div>
<Badge variant="outline" class="text-xs {it.build_success ? 'bg-emerald-500/15 text-emerald-500 border-emerald-500/30' : 'bg-red-500/15 text-red-400 border-red-500/30'}">
{it.build_success ? '✓ Build OK' : '✗ Build Failed'}
</Badge>
</div>
</Card.Header>
<Card.Content class="space-y-3">
{#if it.errors_detected && it.errors_detected.length > 0}
<div>
<div class="text-xs font-medium text-muted-foreground mb-1">Errors Detected ({it.errors_detected.length})</div>
<ul class="space-y-1">
{#each it.errors_detected as err}
<li class="flex items-start gap-2 text-xs">
<CircleX class="h-3.5 w-3.5 text-red-400 shrink-0 mt-0.5" />
<span class="text-red-400/90">{err}</span>
</li>
{/each}
</ul>
</div>
{/if}
{#if it.fix_applied}
<div>
<div class="text-xs font-medium text-muted-foreground mb-1">Fix Applied</div>
<pre class="text-xs font-mono bg-zinc-950 rounded-md p-3 max-h-32 overflow-auto text-zinc-300">{it.fix_applied}</pre>
</div>
{/if}
{#if it.build_output}
<div>
<div class="text-xs font-medium text-muted-foreground mb-1">Build Output</div>
<pre class="text-xs font-mono bg-zinc-950 rounded-md p-3 max-h-32 overflow-auto text-zinc-300">{it.build_output}</pre>
</div>
{/if}
</Card.Content>
</Card.Root>
</div>
{/each}
</div>
</section>
{/if}

<!-- ═══════════════ COST & METRICS SECTION ═══════════════ -->
<section id="metrics" class="space-y-4">
<h2 class="text-lg font-semibold flex items-center gap-2"><ChartBar class="h-5 w-5" /> Cost & Metrics</h2>

<div class="grid md:grid-cols-3 gap-4">
<!-- Cost Card -->
<Card.Root>
<Card.Header class="pb-3"><Card.Title class="text-sm font-medium flex items-center gap-2"><DollarSign class="h-4 w-4" /> Cost</Card.Title></Card.Header>
<Card.Content>
<div class="text-3xl font-bold mb-3">{fmtCost(costData.totalCost)}</div>
{#if Object.keys(costData.byStage).length > 0}
<div class="space-y-1.5 text-sm">
{#each Object.entries(costData.byStage) as [stage, data]}
<div class="flex justify-between">
<span class="text-muted-foreground">{stage}</span>
<span>{fmtCost(data.cost)}</span>
</div>
{/each}
</div>
{/if}
</Card.Content>
</Card.Root>

<!-- Token Breakdown -->
<Card.Root>
<Card.Header class="pb-3"><Card.Title class="text-sm font-medium flex items-center gap-2"><Hash class="h-4 w-4" /> Token Usage</Card.Title></Card.Header>
<Card.Content>
<div class="text-3xl font-bold mb-3">{fmt(costData.totalTokens, 0)}</div>
{#if costData.totalTokens > 0}
<div class="h-4 rounded-full overflow-hidden bg-zinc-800 flex mb-2">
<div class="bg-blue-500 h-full" style="width: {(costData.totalPrompt / costData.totalTokens) * 100}%"></div>
<div class="bg-emerald-500 h-full" style="width: {(costData.totalCompletion / costData.totalTokens) * 100}%"></div>
</div>
<div class="flex justify-between text-xs text-muted-foreground">
<span class="flex items-center gap-1"><span class="h-2 w-2 rounded-full bg-blue-500 inline-block"></span> Prompt: {fmt(costData.totalPrompt, 0)}</span>
<span class="flex items-center gap-1"><span class="h-2 w-2 rounded-full bg-emerald-500 inline-block"></span> Completion: {fmt(costData.totalCompletion, 0)}</span>
</div>
{/if}
</Card.Content>
</Card.Root>

<!-- Performance -->
<Card.Root>
<Card.Header class="pb-3"><Card.Title class="text-sm font-medium flex items-center gap-2"><Timer class="h-4 w-4" /> Performance</Card.Title></Card.Header>
<Card.Content>
<div class="text-3xl font-bold mb-3">{costData.tokensPerSec > 0 ? fmt(costData.tokensPerSec, 1) : '—'} <span class="text-sm font-normal text-muted-foreground">tok/s</span></div>
<div class="space-y-1.5 text-sm">
<div class="flex justify-between"><span class="text-muted-foreground">Total Duration</span><span>{fmtDur(job.duration_seconds)}</span></div>
<div class="flex justify-between"><span class="text-muted-foreground">Artifacts</span><span>{artifacts.length}</span></div>
{#if job.mode === 'copilot'}
<div class="flex justify-between"><span class="text-muted-foreground">Iterations</span><span>{iterations.length}</span></div>
{/if}
</div>
</Card.Content>
</Card.Root>
</div>

<!-- All Metrics (raw) -->
{#if job.metrics && Object.keys(job.metrics).length > 0}
<Card.Root>
<Card.Header class="pb-3"><Card.Title class="text-sm font-medium">All Metrics</Card.Title></Card.Header>
<Card.Content>
<div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
{#each Object.entries(job.metrics) as [key, value]}
<div class="rounded-md border p-2.5">
<dt class="text-xs text-muted-foreground">{key.replace(/_/g, ' ')}</dt>
<dd class="text-sm font-medium mt-0.5">
{typeof value === 'number'
? Number.isInteger(value)
? value.toLocaleString()
: value.toFixed(2)
: String(value)}
</dd>
</div>
{/each}
</div>
</Card.Content>
</Card.Root>
{/if}
</section>
</div>
{/if}
