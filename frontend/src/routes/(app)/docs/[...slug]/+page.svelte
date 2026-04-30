<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { getDoc } from '$lib/api/client';
	import type { DocPage } from '$lib/api/client';
	import { Badge } from '$lib/components/ui/badge';
	import FileText from '@lucide/svelte/icons/file-text';
	import AlertCircle from '@lucide/svelte/icons/alert-circle';

	let doc: DocPage | null = $state(null);
	let loading = $state(true);
	let notFound = $state(false);

	async function loadDoc(slug: string) {
		loading = true;
		notFound = false;
		doc = null;
		const result = await getDoc(slug);
		if (!result) {
			notFound = true;
		} else {
			doc = result;
		}
		loading = false;
	}

	onMount(() => {
		loadDoc($page.params.slug);
	});

	$effect(() => {
		const slug = $page.params.slug;
		loadDoc(slug);
	});

	function formatDate(ts: number) {
		return new Date(ts * 1000).toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'short',
			day: 'numeric',
		});
	}
</script>

<svelte:head>
	<title>{doc?.title ?? 'Docs'} - LLM Lab</title>
</svelte:head>

{#if loading}
	<div class="flex items-center gap-2 text-sm text-muted-foreground py-8">
		<span>Loading…</span>
	</div>
{:else if notFound}
	<div class="flex flex-col items-center gap-3 py-16 text-center">
		<AlertCircle class="h-10 w-10 text-muted-foreground/40" />
		<h2 class="text-lg font-semibold">Page not found</h2>
		<p class="text-sm text-muted-foreground">The document <code class="font-mono">{$page.params.slug}</code> does not exist.</p>
		<a href="/docs" class="text-sm text-primary hover:underline">← Back to docs</a>
	</div>
{:else if doc}
	<div class="flex gap-8">
		<!-- Article -->
		<article class="min-w-0 flex-1">
			<div class="mb-4 flex items-center justify-between gap-2">
				<div class="flex items-center gap-2 text-xs text-muted-foreground">
					<FileText class="h-3.5 w-3.5" />
					<a href="/docs" class="hover:underline">Docs</a>
					<span>/</span>
					<span class="font-medium text-foreground">{doc.title}</span>
				</div>
				<Badge variant="outline" class="text-xs">Updated {formatDate(doc.last_modified)}</Badge>
			</div>

			<!-- Rendered markdown -->
			<div class="prose prose-sm max-w-none dark:prose-invert
				prose-headings:scroll-mt-20
				prose-code:before:content-none prose-code:after:content-none
				prose-code:rounded prose-code:bg-muted prose-code:px-1 prose-code:py-0.5 prose-code:text-xs
				prose-pre:p-0 prose-pre:bg-transparent">
				{@html doc.html}
			</div>
		</article>

		<!-- TOC sidebar -->
		{#if doc.toc}
			<aside class="hidden w-52 shrink-0 xl:block">
				<div class="sticky top-6">
					<p class="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">On this page</p>
					<div class="toc-nav text-xs [&_a]:text-muted-foreground [&_a:hover]:text-foreground [&_a]:no-underline [&_li]:list-none [&_ul]:pl-3 [&_ul]:space-y-1 [&_a]:block [&_a]:py-0.5 [&_a:hover]:underline">
						{@html doc.toc}
					</div>
				</div>
			</aside>
		{/if}
	</div>
{/if}
