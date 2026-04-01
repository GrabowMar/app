<script lang="ts">
	import { page } from '$app/stores';
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { Separator } from '$lib/components/ui/separator';
	import { getModel, type LLMModelDetail } from '$lib/api/client';
	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import Cpu from '@lucide/svelte/icons/cpu';
	import ArrowLeft from '@lucide/svelte/icons/arrow-left';
	import CircleCheck from '@lucide/svelte/icons/circle-check';
	import GitCompareArrows from '@lucide/svelte/icons/git-compare-arrows';
	import RefreshCw from '@lucide/svelte/icons/refresh-cw';
	import DollarSign from '@lucide/svelte/icons/dollar-sign';
	import Layers from '@lucide/svelte/icons/layers';
	import Check from '@lucide/svelte/icons/check';
	import X from '@lucide/svelte/icons/x';
	import Sparkles from '@lucide/svelte/icons/sparkles';
	import BarChart3 from '@lucide/svelte/icons/bar-chart-3';
	import LoaderCircle from '@lucide/svelte/icons/loader-circle';
	import Info from '@lucide/svelte/icons/info';
	import ExternalLink from '@lucide/svelte/icons/external-link';
	import Copy from '@lucide/svelte/icons/copy';
	import Download from '@lucide/svelte/icons/download';
	import ChevronDown from '@lucide/svelte/icons/chevron-down';
	import Zap from '@lucide/svelte/icons/zap';
	import Eye from '@lucide/svelte/icons/eye';
	import MessageSquare from '@lucide/svelte/icons/message-square';
	import Wrench from '@lucide/svelte/icons/wrench';
	import Braces from '@lucide/svelte/icons/braces';
	import Radio from '@lucide/svelte/icons/radio';
	import Mic from '@lucide/svelte/icons/mic';
	import Box from '@lucide/svelte/icons/box';
	import Settings from '@lucide/svelte/icons/settings';
	import Gauge from '@lucide/svelte/icons/gauge';
	import Shield from '@lucide/svelte/icons/shield';
	import Code from '@lucide/svelte/icons/code';
	import ArrowDownToLine from '@lucide/svelte/icons/arrow-down-to-line';
	import ArrowUpFromLine from '@lucide/svelte/icons/arrow-up-from-line';
	import Gift from '@lucide/svelte/icons/gift';
	import GraduationCap from '@lucide/svelte/icons/graduation-cap';

	const slug = $derived($page.params.slug ?? '');

	let model = $state<LLMModelDetail | null>(null);
	let loading = $state(true);
	let error = $state('');
	let rawJsonOpen = $state(false);

	// Derived data from model (safe to use in templates without @const)
	const meta = $derived(model ? (model.metadata || {}) as Record<string, unknown> : {} as Record<string, unknown>);
	const caps = $derived(model ? (model.capabilities_json || {}) as Record<string, unknown> : {} as Record<string, unknown>);
	const arch = $derived(model ? getArchitecture(model) : {} as Record<string, unknown>);
	const efficiency = $derived(model ? costEfficiencyGrade(model.cost_efficiency) : { grade: 'D', color: 'text-red-500' });
	const inputMods = $derived((arch.input_modalities || meta.architecture_input_modalities || []) as string[]);
	const outputMods = $derived((arch.output_modalities || meta.architecture_output_modalities || []) as string[]);
	const supportedParams = $derived(model ? getSupportedParameters(model) : [] as string[]);
	const perRequestLimits = $derived(model ? getPerRequestLimits(model) : {} as Record<string, unknown>);
	const capMatrix = $derived(model ? getCapabilityMatrix(model) : {} as Record<string, boolean>);
	const instructType = $derived((arch.instruct_type || meta.architecture_instruct_type || '') as string);
	const defaultParams = $derived(model ? getDefaultParameters(model) : {} as Record<string, unknown>);
	const hfId = $derived(model ? getHuggingFaceId(model) : '');

	const sections = [
		{ id: 'overview', label: 'Overview', icon: Info },
		{ id: 'capabilities', label: 'Capabilities', icon: Zap },
		{ id: 'pricing', label: 'Pricing', icon: DollarSign },
		{ id: 'metadata', label: 'Metadata', icon: Layers },
	] as const;
	let activeSection = $state<string>('overview');

	function scrollToSection(id: string) {
		activeSection = id;
		document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
	}

	// Scroll-spy
	onMount(() => {
		const observer = new IntersectionObserver(
			(entries) => {
				for (const entry of entries) {
					if (entry.isIntersecting) {
						activeSection = entry.target.id;
					}
				}
			},
			{ rootMargin: '-20% 0px -70% 0px' },
		);
		for (const s of sections) {
			const el = document.getElementById(s.id);
			if (el) observer.observe(el);
		}
		return () => observer.disconnect();
	});

	function formatPrice(price: number): string {
		if (price === 0) return 'Free';
		if (price < 0.01) return `$${price.toFixed(4)}`;
		return `$${price.toFixed(2)}`;
	}

	function formatTokens(n: number): string {
		if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
		if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
		return String(n);
	}

	function formatNumber(n: number): string {
		return n.toLocaleString();
	}

	function costEfficiencyGrade(score: number): { grade: string; color: string } {
		if (score >= 0.9) return { grade: 'A+', color: 'text-emerald-500' };
		if (score >= 0.8) return { grade: 'A', color: 'text-emerald-500' };
		if (score >= 0.7) return { grade: 'A-', color: 'text-emerald-400' };
		if (score >= 0.6) return { grade: 'B+', color: 'text-blue-500' };
		if (score >= 0.5) return { grade: 'B', color: 'text-blue-500' };
		if (score >= 0.4) return { grade: 'B-', color: 'text-blue-400' };
		if (score >= 0.3) return { grade: 'C+', color: 'text-amber-500' };
		if (score >= 0.2) return { grade: 'C', color: 'text-amber-500' };
		return { grade: 'D', color: 'text-red-500' };
	}

	// Extract data helpers
	function getMeta(m: LLMModelDetail) {
		return (m.metadata || {}) as Record<string, unknown>;
	}

	function getCaps(m: LLMModelDetail) {
		return (m.capabilities_json || {}) as Record<string, unknown>;
	}

	function getArchitecture(m: LLMModelDetail) {
		const caps = getCaps(m);
		return (caps.architecture || {}) as Record<string, unknown>;
	}

	function getHuggingFaceId(m: LLMModelDetail): string | null {
		const caps = getCaps(m);
		const hfId = caps.hugging_face_id as string | undefined;
		return hfId || null;
	}

	function getSupportedParameters(m: LLMModelDetail): string[] {
		const caps = getCaps(m);
		const meta = getMeta(m);
		const params = (caps.supported_parameters as string[]) || (meta.openrouter_supported_parameters as string[]) || [];
		return params;
	}

	function getPerRequestLimits(m: LLMModelDetail): Record<string, number> {
		const caps = getCaps(m);
		return (caps.per_request_limits || {}) as Record<string, number>;
	}

	function getDefaultParameters(m: LLMModelDetail): Record<string, unknown> {
		const caps = getCaps(m);
		return (caps.default_parameters || {}) as Record<string, unknown>;
	}

	interface SkillBadge {
		name: string;
		icon: typeof Zap;
		active: boolean;
	}

	function getCoreSkills(m: LLMModelDetail): SkillBadge[] {
		const caps = getCaps(m);
		const arch = getArchitecture(m);
		const inputMods = (arch.input_modalities || []) as string[];
		const outputMods = (arch.output_modalities || []) as string[];
		return [
			{ name: 'Text/Chat', icon: MessageSquare, active: true },
			{ name: 'Vision', icon: Eye, active: m.supports_vision || inputMods.includes('image') },
			{ name: 'Functions', icon: Wrench, active: m.supports_function_calling },
			{ name: 'Streaming', icon: Radio, active: m.supports_streaming },
			{ name: 'JSON Mode', icon: Braces, active: m.supports_json_mode },
			{ name: 'Audio', icon: Mic, active: inputMods.includes('audio') || outputMods.includes('audio') },
			{ name: 'Multimodal', icon: Box, active: inputMods.length > 1 || (caps.multimodal as boolean) || false },
		];
	}

	function getCapabilityMatrix(m: LLMModelDetail): Record<string, boolean> {
		const caps = getCaps(m);
		const result: Record<string, boolean> = {};
		for (const [key, value] of Object.entries(caps)) {
			if (typeof value === 'boolean') {
				result[key] = value;
			}
		}
		// Add model-level capabilities
		result['function_calling'] = m.supports_function_calling;
		result['vision'] = m.supports_vision;
		result['streaming'] = m.supports_streaming;
		result['json_mode'] = m.supports_json_mode;
		return result;
	}

	interface PricingTier {
		label: string;
		perMillionTokens: number;
	}

	function getAllPricingTiers(m: LLMModelDetail): PricingTier[] {
		const meta = getMeta(m);
		const caps = getCaps(m);
		const pricing = (meta.openrouter_pricing || (caps.pricing as Record<string, string>) || {}) as Record<string, string>;
		const tiers: PricingTier[] = [];
		const tierMap: Record<string, string> = {
			input_cache_read: 'Cache Read',
			input_cache_write: 'Cache Write',
			web_search: 'Web Search',
			internal_reasoning: 'Internal Reasoning',
			request: 'Per Request',
			image: 'Per Image',
		};
		for (const [key, label] of Object.entries(tierMap)) {
			const raw = pricing[key];
			if (raw) {
				const val = parseFloat(raw);
				if (val > 0) tiers.push({ label, perMillionTokens: val * 1_000_000 });
			}
		}
		return tiers;
	}

	function formatMetaValue(value: unknown): string {
		if (value === null || value === undefined) return '—';
		if (typeof value === 'object') {
			if (Array.isArray(value)) {
				if (value.length === 0) return '—';
				if (value.length > 3) return `${value.slice(0, 3).join(', ')} (+${value.length - 3})`;
				return value.join(', ');
			}
			return `${Object.keys(value).length} keys`;
		}
		if (typeof value === 'number') {
			return value > 1000 ? formatNumber(value) : String(value);
		}
		const sv = String(value);
		return sv.length > 80 ? sv.slice(0, 77) + '...' : sv;
	}

	async function copyToClipboard(text: string) {
		await navigator.clipboard.writeText(text);
		toast.success('Copied to clipboard');
	}

	function exportJson(m: LLMModelDetail) {
		const data = { model: m, capabilities_json: m.capabilities_json, metadata: m.metadata };
		const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `${m.canonical_slug}.json`;
		a.click();
		URL.revokeObjectURL(url);
	}

	async function load() {
		loading = true;
		error = '';
		try {
			model = await getModel(slug);
		} catch {
			error = 'Model not found.';
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		if (slug) load();
	});
</script>

<svelte:head>
	<title>{model?.model_name ?? slug} - Models - LLM Lab</title>
</svelte:head>

<div class="space-y-4">
	<!-- Breadcrumb -->
	<div class="flex items-center gap-2 text-sm text-muted-foreground">
		<Button variant="ghost" size="sm" href="/models" class="gap-1.5 px-2">
			<ArrowLeft class="h-3.5 w-3.5" />
			Models
		</Button>
		<span>/</span>
		<span class="text-foreground font-medium">{model?.model_name ?? slug}</span>
	</div>

	{#if loading}
		<div class="flex items-center justify-center py-20">
			<LoaderCircle class="h-8 w-8 animate-spin text-muted-foreground" />
		</div>
	{:else if error}
		<div class="rounded-lg border border-destructive bg-destructive/10 p-4 text-sm text-destructive">
			{error}
		</div>
	{:else if model}

		<!-- Header Bar -->
		<Card.Root>
			<Card.Content class="py-4">
				<div class="flex flex-wrap items-center gap-4">
					<div class="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
						<Cpu class="h-6 w-6 text-primary" />
					</div>
					<div class="flex-1 min-w-0">
						<div class="flex items-center gap-2 flex-wrap">
							<h2 class="text-xl font-bold">{model.model_name}</h2>
							<Badge variant="secondary">{model.provider}</Badge>
							{#if model.is_free}
								<Badge variant="secondary" class="gap-1 text-emerald-600 dark:text-emerald-400">
									<Gift class="h-3 w-3" /> Free
								</Badge>
							{/if}
						</div>
						{#if model.description}
							<p class="text-sm text-muted-foreground mt-1 line-clamp-2">{model.description}</p>
						{/if}
					</div>
					<div class="flex items-center gap-4 text-sm">
						<div class="text-center">
							<div class="font-semibold">{model.context_window_display}</div>
							<div class="text-xs text-muted-foreground">Context</div>
						</div>
						<Separator orientation="vertical" class="h-8" />
						<div class="text-center">
							<div class="font-semibold">{formatPrice(model.input_price_per_million)}</div>
							<div class="text-xs text-muted-foreground">Input/1M</div>
						</div>
						<Separator orientation="vertical" class="h-8" />
						<div class="text-center">
							<div class="font-semibold {efficiency.color}">{efficiency.grade}</div>
							<div class="text-xs text-muted-foreground">Efficiency</div>
						</div>
					</div>
					<div class="flex items-center gap-2">
						<Button variant="outline" size="sm" disabled>
							<Sparkles class="mr-2 h-3.5 w-3.5" />
							Generate App
						</Button>
						<Button variant="outline" size="sm" href="/models/compare?models={slug}">
							<GitCompareArrows class="mr-2 h-3.5 w-3.5" />
							Compare
						</Button>
						<Button variant="ghost" size="icon" class="h-8 w-8" onclick={load}>
							<RefreshCw class="h-3.5 w-3.5" />
						</Button>
					</div>
				</div>
			</Card.Content>
		</Card.Root>

		<!-- Metric Grid -->
		<div class="grid grid-cols-2 gap-3 md:grid-cols-3 lg:grid-cols-5">
			<Card.Root>
				<Card.Content class="p-3 text-center">
					<div class="text-lg font-bold">{model.context_window_display}</div>
					<div class="text-xs font-medium text-muted-foreground">Context Window</div>
				</Card.Content>
			</Card.Root>
			<Card.Root>
				<Card.Content class="p-3 text-center">
					<div class="text-lg font-bold">{formatPrice(model.input_price_per_million)}</div>
					<div class="text-xs font-medium text-muted-foreground">Input $/1M</div>
				</Card.Content>
			</Card.Root>
			<Card.Root>
				<Card.Content class="p-3 text-center">
					<div class="text-lg font-bold">{formatPrice(model.output_price_per_million)}</div>
					<div class="text-xs font-medium text-muted-foreground">Output $/1M</div>
				</Card.Content>
			</Card.Root>
			<Card.Root>
				<Card.Content class="p-3 text-center">
					<div class="text-lg font-bold {efficiency.color}" title="Score: {model.cost_efficiency.toFixed(2)} — Based on context window size and pricing">{efficiency.grade}</div>
					<div class="text-xs font-medium text-muted-foreground">Efficiency ({model.cost_efficiency.toFixed(2)})</div>
				</Card.Content>
			</Card.Root>
			<Card.Root>
				<Card.Content class="p-3 text-center">
					<div class="text-lg font-bold">{model.max_output_tokens ? formatTokens(model.max_output_tokens) : 'N/A'}</div>
					<div class="text-xs font-medium text-muted-foreground">Max Output</div>
				</Card.Content>
			</Card.Root>
		</div>

		<!-- Section Navigation -->
		<div class="sticky top-0 z-10 -mx-1 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b">
			<div class="flex gap-1 px-1 py-1 overflow-x-auto">
				{#each sections as section}
					<Button
						variant={activeSection === section.id ? 'secondary' : 'ghost'}
						size="sm"
						class="text-xs whitespace-nowrap gap-1.5"
						onclick={() => scrollToSection(section.id)}
					>
						<section.icon class="h-3 w-3" />
						{section.label}
					</Button>
				{/each}
			</div>
		</div>

		<!-- ==================== OVERVIEW SECTION ==================== -->
		<div id="overview" class="space-y-3">
			<div class="grid gap-3 lg:grid-cols-2">
				<!-- Identity Card -->
				<Card.Root>
					<Card.Content class="p-4">
						<div class="flex items-center gap-2 mb-3">
							<Info class="h-4 w-4 text-primary" />
							<span class="text-xs font-bold uppercase text-muted-foreground">Identity</span>
						</div>
						<div class="grid grid-cols-2 gap-3">
							<div>
								<div class="text-xs text-muted-foreground">Display Name</div>
								<div class="text-sm font-medium truncate" title={model.model_name}>{model.model_name}</div>
							</div>
							<div>
								<div class="text-xs text-muted-foreground">Provider</div>
								<Badge variant="secondary" class="mt-0.5">{model.provider}</Badge>
							</div>
							<div>
								<div class="text-xs text-muted-foreground">Model ID</div>
								<code class="text-xs truncate block" title={model.model_id}>{model.model_id}</code>
							</div>
							<div>
								<div class="text-xs text-muted-foreground">Canonical Slug</div>
								<code class="text-xs truncate block" title={model.canonical_slug}>{model.canonical_slug}</code>
							</div>
							<div>
								<div class="text-xs text-muted-foreground">Database ID</div>
								<div class="text-sm font-medium">#{model.id}</div>
							</div>
							<div>
								<div class="text-xs text-muted-foreground">Last Updated</div>
								<div class="text-sm font-medium">{new Date(model.updated_at).toLocaleDateString()}</div>
							</div>
						</div>
					</Card.Content>
				</Card.Root>

				<!-- Capacity Card -->
				<Card.Root>
					<Card.Content class="p-4">
						<div class="flex items-center gap-2 mb-3">
							<Gauge class="h-4 w-4 text-blue-500" />
							<span class="text-xs font-bold uppercase text-muted-foreground">Capacity</span>
						</div>
						<div class="flex items-center justify-center gap-8 mb-3">
							<div class="text-center">
								<div class="text-3xl font-bold text-primary">{model.context_window_display}</div>
								<div class="text-xs text-muted-foreground">Context Window</div>
							</div>
							<Separator orientation="vertical" class="h-12" />
							<div class="text-center">
								<div class="text-3xl font-bold text-emerald-500">{model.max_output_tokens ? formatTokens(model.max_output_tokens) : '—'}</div>
								<div class="text-xs text-muted-foreground">Max Output</div>
							</div>
						</div>
						<div class="flex flex-wrap gap-1.5 justify-center">
							{#if model.is_free}
								<Badge variant="secondary" class="gap-1 text-emerald-600 dark:text-emerald-400"><Gift class="h-3 w-3" /> Free</Badge>
							{/if}
							{#if (meta.openrouter_top_provider as Record<string, unknown>)?.is_moderated}
								<Badge variant="secondary" class="gap-1 text-blue-600 dark:text-blue-400"><Shield class="h-3 w-3" /> Moderated</Badge>
							{/if}
							{#if meta.openrouter_created}
								<Badge variant="outline" class="gap-1 text-muted-foreground">
									Created {new Date(Number(meta.openrouter_created) * 1000).toLocaleDateString()}
								</Badge>
							{/if}
						</div>
					</Card.Content>
				</Card.Root>
			</div>

			<!-- External Links -->
			{#if hfId || model.description}
				<Card.Root>
					<Card.Content class="p-4">
						{#if hfId}
							<div class="flex items-center gap-2 mb-2">
								<span class="text-xs text-muted-foreground">🤗 HuggingFace:</span>
								<a href="https://huggingface.co/{hfId}" target="_blank" rel="noopener noreferrer" class="text-sm text-primary hover:underline inline-flex items-center gap-1">
									<code class="text-xs">{hfId}</code>
									<ExternalLink class="h-3 w-3" />
								</a>
							</div>
						{/if}
						{#if model.description}
							<p class="text-sm text-muted-foreground leading-relaxed">
								{model.description}
							</p>
						{:else}
							<p class="text-sm text-muted-foreground leading-relaxed">
								{model.model_name} by {model.provider}. A large language model available via OpenRouter.
							</p>
						{/if}
					</Card.Content>
				</Card.Root>
			{/if}
		</div>

		<!-- ==================== CAPABILITIES SECTION ==================== -->
		<div id="capabilities" class="space-y-3">
			<Card.Root>
				<Card.Header class="pb-3">
					<div class="flex items-center gap-2">
						<Zap class="h-4 w-4 text-amber-500" />
						<Card.Title>Capabilities</Card.Title>
					</div>
				</Card.Header>
				<Card.Content class="space-y-4">
					<!-- Core Skills -->
					<div>
						<div class="flex items-center gap-2 mb-2">
							<Sparkles class="h-3.5 w-3.5 text-amber-500" />
							<span class="text-xs font-bold uppercase text-muted-foreground">Skills</span>
						</div>
						<div class="flex flex-wrap gap-1.5">
							{#each getCoreSkills(model) as skill}
								<Badge variant={skill.active ? 'default' : 'outline'} class="{skill.active ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border-emerald-500/20' : 'opacity-50'} gap-1">
									<skill.icon class="h-3 w-3" />
									{skill.name}
								</Badge>
							{/each}
						</div>
					</div>

					<Separator />

					<div class="grid gap-3 md:grid-cols-2">
						<!-- Architecture -->
						<div>
							<div class="flex items-center gap-2 mb-2">
								<Box class="h-3.5 w-3.5 text-primary" />
								<span class="text-xs font-bold uppercase text-muted-foreground">Architecture</span>
							</div>
							<div class="grid grid-cols-2 gap-2 text-sm mb-2">
								<div>
									<span class="text-xs text-muted-foreground">Modality:</span>
									<span class="ml-1 font-medium">{arch.modality || meta.architecture_modality || '—'}</span>
								</div>
								<div>
									<span class="text-xs text-muted-foreground">Tokenizer:</span>
									<span class="ml-1 font-medium">{arch.tokenizer || meta.architecture_tokenizer || '—'}</span>
								</div>
							</div>
							{#if inputMods.length || outputMods.length}
								<div class="flex flex-wrap gap-1">
									{#each inputMods as mod}
										<Badge variant="outline" class="text-xs gap-1"><ArrowDownToLine class="h-2.5 w-2.5" />{mod}</Badge>
									{/each}
									{#each outputMods as mod}
										<Badge variant="outline" class="text-xs gap-1"><ArrowUpFromLine class="h-2.5 w-2.5" />{mod}</Badge>
									{/each}
								</div>
							{/if}
						</div>

						<!-- Supported Parameters -->
						<div>
							<div class="flex items-center gap-2 mb-2">
								<Settings class="h-3.5 w-3.5 text-blue-500" />
								<span class="text-xs font-bold uppercase text-muted-foreground">Supported Parameters</span>
							</div>
							{#if supportedParams.length}
								<div class="flex flex-wrap gap-1">
									{#each supportedParams.slice(0, 8) as param}
										<Badge variant="outline" class="text-xs">{param}</Badge>
									{/each}
									{#if supportedParams.length > 8}
										<Badge variant="outline" class="text-xs text-muted-foreground">+{supportedParams.length - 8} more</Badge>
									{/if}
								</div>
							{:else}
								<span class="text-xs text-muted-foreground">Not published</span>
							{/if}
						</div>
					</div>

					<Separator />

					<div class="grid gap-3 md:grid-cols-3">
						<!-- Per-Request Limits -->
						<div>
							<div class="flex items-center gap-2 mb-2">
								<Gauge class="h-3.5 w-3.5 text-red-500" />
								<span class="text-xs font-bold uppercase text-muted-foreground">Per-Request Limits</span>
							</div>
							{#if Object.keys(perRequestLimits).length}
								<div class="space-y-1 text-sm">
									{#if perRequestLimits.prompt_tokens}
										<div class="flex justify-between">
											<span class="text-xs text-muted-foreground">Prompt:</span>
											<Badge variant="outline" class="text-xs">{formatNumber(perRequestLimits.prompt_tokens)}</Badge>
										</div>
									{/if}
									{#if perRequestLimits.completion_tokens}
										<div class="flex justify-between">
											<span class="text-xs text-muted-foreground">Completion:</span>
											<Badge variant="outline" class="text-xs">{formatNumber(perRequestLimits.completion_tokens)}</Badge>
										</div>
									{/if}
								</div>
							{:else}
								<span class="text-xs text-muted-foreground">Not specified</span>
							{/if}
						</div>

						<!-- Capability Matrix -->
						{#if Object.keys(capMatrix).length}
							<div class="md:col-span-2">
								<div class="flex items-center gap-2 mb-2">
									<CircleCheck class="h-3.5 w-3.5 text-emerald-500" />
									<span class="text-xs font-bold uppercase text-muted-foreground">Capability Matrix</span>
								</div>
								<div class="flex flex-wrap gap-1">
									{#each Object.entries(capMatrix).sort(([a], [b]) => a.localeCompare(b)) as [key, value]}
										<Badge variant="outline" class="{value ? 'text-emerald-600 dark:text-emerald-400 border-emerald-500/30' : 'opacity-40'} text-xs gap-1">
											{#if value}<Check class="h-2.5 w-2.5" />{:else}<X class="h-2.5 w-2.5" />{/if}
											{key.replace(/_/g, ' ')}
										</Badge>
									{/each}
								</div>
							</div>
						{/if}
					</div>

					<!-- Instruct Type & Default Parameters -->
					{#if instructType || Object.keys(defaultParams).length}
						<Separator />
						<div class="grid gap-3 md:grid-cols-2">
							{#if instructType}
								<div>
									<div class="flex items-center gap-2 mb-2">
										<GraduationCap class="h-3.5 w-3.5 text-purple-500" />
										<span class="text-xs font-bold uppercase text-muted-foreground">Instruct Type</span>
									</div>
									<Badge variant="secondary">{instructType}</Badge>
								</div>
							{/if}
							{#if Object.keys(defaultParams).length}
								<div>
									<div class="flex items-center gap-2 mb-2">
										<Settings class="h-3.5 w-3.5 text-purple-500" />
										<span class="text-xs font-bold uppercase text-muted-foreground">Default Parameters</span>
									</div>
									<div class="space-y-1 text-sm">
										{#each Object.entries(defaultParams) as [key, value]}
											<div class="flex justify-between">
												<span class="text-xs text-muted-foreground">{key}</span>
												<code class="text-xs">{String(value)}</code>
											</div>
										{/each}
									</div>
								</div>
							{/if}
						</div>
					{/if}
				</Card.Content>
			</Card.Root>
		</div>

		<!-- ==================== PRICING SECTION ==================== -->
		<div id="pricing" class="space-y-3">
			<!-- Pricing Stat Cards -->
			<div class="grid grid-cols-2 gap-3 lg:grid-cols-4">
				<Card.Root>
					<Card.Content class="p-3">
						<div class="flex items-center gap-2">
							<div class="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10">
								<ArrowDownToLine class="h-4 w-4 text-emerald-500" />
							</div>
							<div>
								<div class="text-xs text-muted-foreground">Input</div>
								<div class="text-sm font-bold">{formatPrice(model.input_price_per_million)}/1M</div>
							</div>
						</div>
					</Card.Content>
				</Card.Root>
				<Card.Root>
					<Card.Content class="p-3">
						<div class="flex items-center gap-2">
							<div class="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/10">
								<ArrowUpFromLine class="h-4 w-4 text-blue-500" />
							</div>
							<div>
								<div class="text-xs text-muted-foreground">Output</div>
								<div class="text-sm font-bold">{formatPrice(model.output_price_per_million)}/1M</div>
							</div>
						</div>
					</Card.Content>
				</Card.Root>
				<Card.Root>
					<Card.Content class="p-3">
						<div class="flex items-center gap-2">
							<div class="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-500/10">
								<BarChart3 class="h-4 w-4 text-amber-500" />
							</div>
							<div>
								<div class="text-xs text-muted-foreground">Efficiency</div>
								<div class="text-sm font-bold {efficiency.color}">{efficiency.grade} ({model.cost_efficiency.toFixed(2)})</div>
							</div>
						</div>
					</Card.Content>
				</Card.Root>
				<Card.Root>
					<Card.Content class="p-3">
						<div class="flex items-center gap-2">
							<div class="flex h-8 w-8 items-center justify-center rounded-lg {model.is_free ? 'bg-emerald-500/10' : 'bg-muted'}">
								{#if model.is_free}
									<Gift class="h-4 w-4 text-emerald-500" />
								{:else}
									<DollarSign class="h-4 w-4 text-muted-foreground" />
								{/if}
							</div>
							<div>
								<div class="text-xs text-muted-foreground">Tier</div>
								<div class="text-sm font-bold">{model.is_free ? 'Free' : 'Paid'}</div>
							</div>
						</div>
					</Card.Content>
				</Card.Root>
			</div>

			<!-- Pricing Table -->
			<Card.Root>
				<Card.Header class="pb-3">
					<div class="flex items-center gap-2">
						<DollarSign class="h-4 w-4 text-muted-foreground" />
						<Card.Title>Pricing Breakdown</Card.Title>
					</div>
				</Card.Header>
				<Card.Content class="p-0">
					<table class="w-full">
						<thead>
							<tr class="border-b bg-muted/30">
								<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Type</th>
								<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Per 1M tokens</th>
								<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Per 1K tokens</th>
								<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Per token</th>
							</tr>
						</thead>
						<tbody class="divide-y">
							<tr class="hover:bg-muted/30">
								<td class="px-4 py-2.5 text-sm font-medium">Input</td>
								<td class="px-4 py-2.5 text-sm font-mono">{formatPrice(model.input_price_per_million)}</td>
								<td class="px-4 py-2.5 text-sm font-mono text-muted-foreground">{formatPrice(model.input_price_per_million / 1000)}</td>
								<td class="px-4 py-2.5 text-sm font-mono text-muted-foreground">{model.input_price_per_token === 0 ? 'Free' : `$${model.input_price_per_token.toExponential(2)}`}</td>
							</tr>
							<tr class="hover:bg-muted/30">
								<td class="px-4 py-2.5 text-sm font-medium">Output</td>
								<td class="px-4 py-2.5 text-sm font-mono">{formatPrice(model.output_price_per_million)}</td>
								<td class="px-4 py-2.5 text-sm font-mono text-muted-foreground">{formatPrice(model.output_price_per_million / 1000)}</td>
								<td class="px-4 py-2.5 text-sm font-mono text-muted-foreground">{model.output_price_per_token === 0 ? 'Free' : `$${model.output_price_per_token.toExponential(2)}`}</td>
							</tr>
							{#each getAllPricingTiers(model) as tier}
								<tr class="hover:bg-muted/30 bg-muted/10">
									<td class="px-4 py-2.5 text-sm font-medium text-muted-foreground">{tier.label}</td>
									<td class="px-4 py-2.5 text-sm font-mono">{formatPrice(tier.perMillionTokens)}</td>
									<td class="px-4 py-2.5 text-sm font-mono text-muted-foreground">{formatPrice(tier.perMillionTokens / 1000)}</td>
									<td class="px-4 py-2.5 text-sm font-mono text-muted-foreground">${(tier.perMillionTokens / 1_000_000).toExponential(2)}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</Card.Content>
			</Card.Root>
		</div>

		<!-- ==================== METADATA SECTION ==================== -->
		<div id="metadata" class="space-y-3">
			<!-- Quick Reference Bar -->
			<Card.Root>
				<Card.Content class="p-3">
					<div class="flex flex-wrap items-center gap-3 text-sm">
						<div class="flex items-center gap-1">
							<span class="text-xs text-muted-foreground">Model ID:</span>
							<code class="text-xs">{model.model_id}</code>
						</div>
						<Separator orientation="vertical" class="h-4" />
						<div class="flex items-center gap-1">
							<span class="text-xs text-muted-foreground">DB:</span>
							<span class="text-xs font-bold">#{model.id}</span>
						</div>
						<Separator orientation="vertical" class="h-4" />
						<div class="flex items-center gap-1">
							<span class="text-xs text-muted-foreground">Provider:</span>
							<Badge variant="secondary" class="text-xs">{model.provider}</Badge>
						</div>
						{#if model.canonical_slug}
							<Separator orientation="vertical" class="h-4" />
							<div class="flex items-center gap-1">
								<span class="text-xs text-muted-foreground">Slug:</span>
								<code class="text-xs">{model.canonical_slug}</code>
							</div>
						{/if}
						<div class="ml-auto flex gap-1">
							<Button variant="ghost" size="sm" class="h-7 text-xs gap-1" onclick={() => exportJson(model!)}>
								<Download class="h-3 w-3" />
								Export JSON
							</Button>
							<Button variant="ghost" size="sm" class="h-7 text-xs gap-1" onclick={() => copyToClipboard(JSON.stringify({ ...model, capabilities_json: model!.capabilities_json }, null, 2))}>
								<Copy class="h-3 w-3" />
								Copy
							</Button>
						</div>
					</div>
				</Card.Content>
			</Card.Root>

			<!-- Data Tables -->
			<div class="grid gap-3 lg:grid-cols-2">
				<!-- OpenRouter Metadata -->
				{#if Object.keys(caps).length}
					<Card.Root>
						<Card.Header class="py-3 px-4">
							<div class="flex items-center gap-2">
								<Code class="h-4 w-4 text-purple-500" />
								<span class="text-sm font-bold">OpenRouter Metadata</span>
								<Badge variant="outline" class="text-xs">{Object.keys(caps).length} keys</Badge>
							</div>
						</Card.Header>
						<Card.Content class="p-0">
							<div class="max-h-[300px] overflow-y-auto">
								<table class="w-full">
									<tbody class="divide-y">
										{#each Object.entries(caps).filter(([, v]) => v !== null && v !== '') as [key, value]}
											<tr class="hover:bg-muted/30">
												<td class="px-3 py-1.5 text-xs text-muted-foreground w-2/5"><code>{key}</code></td>
												<td class="px-3 py-1.5 text-xs">{formatMetaValue(value)}</td>
											</tr>
										{/each}
									</tbody>
								</table>
							</div>
						</Card.Content>
					</Card.Root>
				{/if}

				<!-- Enriched Metadata -->
				{#if Object.keys(meta).length}
					<Card.Root>
						<Card.Header class="py-3 px-4">
							<div class="flex items-center gap-2">
								<Layers class="h-4 w-4 text-emerald-500" />
								<span class="text-sm font-bold">Enriched Dataset</span>
								<Badge variant="outline" class="text-xs">{Object.keys(meta).length} keys</Badge>
							</div>
						</Card.Header>
						<Card.Content class="p-0">
							<div class="max-h-[300px] overflow-y-auto">
								<table class="w-full">
									<tbody class="divide-y">
										{#each Object.entries(meta).filter(([, v]) => v !== null && v !== '') as [key, value]}
											<tr class="hover:bg-muted/30">
												<td class="px-3 py-1.5 text-xs text-muted-foreground w-2/5"><code>{key}</code></td>
												<td class="px-3 py-1.5 text-xs">{formatMetaValue(value)}</td>
											</tr>
										{/each}
									</tbody>
								</table>
							</div>
						</Card.Content>
					</Card.Root>
				{/if}
			</div>

			<!-- Raw JSON Payload -->
			<Card.Root>
				<Card.Content class="p-3">
					<button
						class="flex w-full items-center gap-2 text-left"
						onclick={() => rawJsonOpen = !rawJsonOpen}
					>
						<Code class="h-4 w-4 text-muted-foreground" />
						<span class="text-sm font-bold">Raw JSON Payload</span>
						<ChevronDown class="h-4 w-4 text-muted-foreground ml-auto transition-transform {rawJsonOpen ? 'rotate-180' : ''}" />
					</button>
					{#if rawJsonOpen}
						<div class="mt-3 relative">
							<Button
								variant="ghost"
								size="sm"
								class="absolute top-2 right-2 h-7 text-xs gap-1 bg-background/80 backdrop-blur"
								onclick={() => copyToClipboard(JSON.stringify(caps, null, 2))}
							>
								<Copy class="h-3 w-3" />
								Copy
							</Button>
							<pre class="rounded-lg bg-zinc-950 dark:bg-zinc-900 text-zinc-300 p-4 text-xs overflow-auto max-h-[400px]">{JSON.stringify(caps, null, 2)}</pre>
						</div>
					{/if}
				</Card.Content>
			</Card.Root>
		</div>

		<!-- ==================== USAGE ANALYTICS PLACEHOLDER ==================== -->
		<Card.Root>
			<Card.Header>
				<div class="flex items-center justify-between">
					<div class="flex items-center gap-2">
						<BarChart3 class="h-4 w-4 text-muted-foreground" />
						<Card.Title>Usage Analytics</Card.Title>
					</div>
					<Badge variant="outline">Coming Soon</Badge>
				</div>
			</Card.Header>
			<Card.Content>
				<div class="flex h-32 flex-col items-center justify-center gap-2 rounded-lg border border-dashed bg-muted/20">
					<BarChart3 class="h-8 w-8 text-muted-foreground/40" />
					<p class="text-sm text-muted-foreground">Usage analytics will appear here</p>
				</div>
			</Card.Content>
		</Card.Root>
	{/if}
</div>
