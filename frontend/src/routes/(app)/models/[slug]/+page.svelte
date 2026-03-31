<script lang="ts">
	import { page } from '$app/stores';
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { Separator } from '$lib/components/ui/separator';
	import { getModel, type LLMModelDetail } from '$lib/api/client';
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

	const slug = $derived($page.params.slug ?? '');

	let model = $state<LLMModelDetail | null>(null);
	let loading = $state(true);
	let error = $state('');

	const sections = ['overview', 'capabilities', 'pricing', 'metadata'] as const;
	let activeSection = $state<string>('overview');

	function scrollToSection(id: string) {
		activeSection = id;
		document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
	}

	function formatPrice(price: number): string {
		if (price === 0) return 'Free';
		if (price < 0.01) return `$${price.toFixed(4)}`;
		return `$${price.toFixed(2)}`;
	}

	function formatTokens(n: number): string {
		if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(0)}M`;
		if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
		return String(n);
	}

	function costEfficiencyGrade(score: number): string {
		if (score >= 0.9) return 'A+';
		if (score >= 0.8) return 'A';
		if (score >= 0.7) return 'A-';
		if (score >= 0.6) return 'B+';
		if (score >= 0.5) return 'B';
		if (score >= 0.4) return 'B-';
		if (score >= 0.3) return 'C+';
		if (score >= 0.2) return 'C';
		return 'D';
	}

	interface CapEntry { name: string; supported: boolean }

	function buildCapabilities(m: LLMModelDetail): CapEntry[] {
		return [
			{ name: 'Code Generation', supported: true },
			{ name: 'Function Calling', supported: m.supports_function_calling },
			{ name: 'Vision', supported: m.supports_vision },
			{ name: 'JSON Mode', supported: m.supports_json_mode },
			{ name: 'Streaming', supported: m.supports_streaming },
		];
	}

	interface CachePricing {
		label: string;
		perMillionTokens: number;
	}

	function getCachePricing(m: LLMModelDetail): CachePricing[] {
		const meta = m.metadata || {};
		const pricing = (meta.openrouter_pricing as Record<string, string>) || {};
		const tiers: CachePricing[] = [];
		if (pricing.input_cache_read) {
			const val = parseFloat(pricing.input_cache_read);
			if (val > 0) tiers.push({ label: 'Cache Read', perMillionTokens: val * 1_000_000 });
		}
		if (pricing.input_cache_write) {
			const val = parseFloat(pricing.input_cache_write);
			if (val > 0) tiers.push({ label: 'Cache Write', perMillionTokens: val * 1_000_000 });
		}
		if (pricing.web_search) {
			const val = parseFloat(pricing.web_search);
			if (val > 0) tiers.push({ label: 'Web Search', perMillionTokens: val * 1_000_000 });
		}
		return tiers;
	}

	function buildMetadata(m: LLMModelDetail): Record<string, string> {
		const meta = m.metadata || {};
		const entries: Record<string, string> = {
			'Model ID': m.model_id,
			'Provider': m.provider,
			'Context Window': formatTokens(m.context_window),
			'Max Output': m.max_output_tokens ? formatTokens(m.max_output_tokens) : 'N/A',
		};
		if (meta.architecture_modality) entries['Modality'] = String(meta.architecture_modality);
		if (meta.architecture_tokenizer) entries['Tokenizer'] = String(meta.architecture_tokenizer);
		if (meta.architecture_instruct_type) entries['Instruct Type'] = String(meta.architecture_instruct_type);

		const inputMods = meta.architecture_input_modalities as string[] | undefined;
		if (inputMods?.length) entries['Input Modalities'] = inputMods.join(', ');
		const outputMods = meta.architecture_output_modalities as string[] | undefined;
		if (outputMods?.length) entries['Output Modalities'] = outputMods.join(', ');

		if (meta.openrouter_created) {
			const ts = Number(meta.openrouter_created);
			if (ts > 0) entries['Created'] = new Date(ts * 1000).toLocaleDateString();
		}
		if (m.created_at) entries['Added to Lab'] = new Date(m.created_at).toLocaleDateString();
		if (m.updated_at) entries['Last Updated'] = new Date(m.updated_at).toLocaleDateString();
		return entries;
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

<div class="space-y-6">
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
									<CircleCheck class="h-3 w-3" /> Free
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
							<div class="font-semibold">{costEfficiencyGrade(model.cost_efficiency)}</div>
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
					<div class="text-lg font-bold">{costEfficiencyGrade(model.cost_efficiency)}</div>
					<div class="text-xs font-medium text-muted-foreground">Cost Efficiency</div>
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
						variant={activeSection === section ? 'secondary' : 'ghost'}
						size="sm"
						class="text-xs capitalize whitespace-nowrap"
						onclick={() => scrollToSection(section)}
					>
						{section}
					</Button>
				{/each}
			</div>
		</div>

		<!-- Overview Section -->
		<div id="overview">
			<Card.Root>
				<Card.Header>
					<Card.Title>Overview</Card.Title>
				</Card.Header>
				<Card.Content>
					<p class="text-sm text-muted-foreground leading-relaxed">
						{model.description || `${model.model_name} by ${model.provider}. A large language model available via OpenRouter.`}
					</p>
				</Card.Content>
			</Card.Root>
		</div>

		<!-- Capabilities Section -->
		<div id="capabilities">
			<Card.Root>
				<Card.Header>
					<Card.Title>Capabilities</Card.Title>
					<Card.Description>Features supported by this model.</Card.Description>
				</Card.Header>
				<Card.Content>
					<div class="grid grid-cols-2 gap-2 sm:grid-cols-3">
						{#each buildCapabilities(model) as cap (cap.name)}
							<div class="flex items-center gap-2 rounded-lg border px-3 py-2 {cap.supported ? '' : 'opacity-50'}">
								{#if cap.supported}
									<Check class="h-4 w-4 text-emerald-500" />
								{:else}
									<X class="h-4 w-4 text-muted-foreground" />
								{/if}
								<span class="text-sm">{cap.name}</span>
							</div>
						{/each}
					</div>
				</Card.Content>
			</Card.Root>
		</div>

		<!-- Pricing Section -->
		<div id="pricing">
			<Card.Root>
				<Card.Header>
					<div class="flex items-center gap-2">
						<DollarSign class="h-4 w-4 text-muted-foreground" />
						<Card.Title>Pricing Information</Card.Title>
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
							{#each getCachePricing(model) as tier}
								<tr class="hover:bg-muted/30">
									<td class="px-4 py-2.5 text-sm font-medium">{tier.label}</td>
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

		<!-- Metadata Section -->
		<div id="metadata">
			<Card.Root>
				<Card.Header>
					<div class="flex items-center gap-2">
						<Layers class="h-4 w-4 text-muted-foreground" />
						<Card.Title>Metadata</Card.Title>
					</div>
				</Card.Header>
				<Card.Content>
					<dl class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
						{#each Object.entries(buildMetadata(model)) as [key, value]}
							<div class="rounded-lg border px-3 py-2">
								<dt class="text-xs text-muted-foreground">{key}</dt>
								<dd class="text-sm font-medium font-mono">{value}</dd>
							</div>
						{/each}
					</dl>
				</Card.Content>
			</Card.Root>
		</div>

		<!-- Usage Analytics Placeholder -->
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
				<div class="flex h-48 flex-col items-center justify-center gap-2 rounded-lg border border-dashed bg-muted/20">
					<BarChart3 class="h-8 w-8 text-muted-foreground/40" />
					<p class="text-sm text-muted-foreground">Usage analytics will appear here</p>
				</div>
			</Card.Content>
		</Card.Root>
	{/if}
</div>
