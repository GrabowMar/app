<script lang="ts">
import { onMount } from 'svelte';
import { goto } from '$app/navigation';
import { getDocsTree } from '$lib/api/client';
import type { DocNode } from '$lib/api/client';
import { Badge } from '$lib/components/ui/badge';
import * as Card from '$lib/components/ui/card';
import FileText from '@lucide/svelte/icons/file-text';
import Folder from '@lucide/svelte/icons/folder';
import BookOpen from '@lucide/svelte/icons/book-open';
import LoaderCircle from '@lucide/svelte/icons/loader-circle';

let tree: DocNode[] = $state([]);

function flatten(nodes: DocNode[]): DocNode[] {
return nodes.flatMap((n) => (n.children.length ? [n, ...flatten(n.children)] : [n]));
}

const allDocs = $derived(flatten(tree).filter((n) => n.children.length === 0));

onMount(async () => {
tree = await getDocsTree();
});
</script>

<svelte:head>
<title>Documentation - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
<div class="page-header">
<div class="flex items-start justify-between gap-3">
<div>
<h1>Documentation</h1>
<p>Browse guides, references, and technical documentation.</p>
</div>
<Badge variant="outline" class="text-xs shrink-0">{allDocs.length} docs</Badge>
</div>
</div>

{#if tree.length === 0}
<Card.Root>
	<Card.Content class="flex items-center justify-center py-20">
		<LoaderCircle class="h-8 w-8 animate-spin text-muted-foreground" />
	</Card.Content>
</Card.Root>
{:else}
<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
{#each tree as node (node.slug)}
{#if node.children.length > 0}
<Card.Root class="cursor-default">
<Card.Header class="pb-2">
<div class="flex items-center gap-2">
<Folder class="h-4 w-4 text-muted-foreground" />
<Card.Title class="text-sm">{node.title}</Card.Title>
<Badge variant="outline" class="ml-auto text-xs">{node.children.length}</Badge>
</div>
</Card.Header>
<Card.Content class="pt-0">
<ul class="space-y-1">
{#each node.children as child (child.slug)}
<li>
<a
href="/docs/{child.slug}"
class="flex items-center gap-1.5 rounded px-2 py-1 text-xs text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
>
<FileText class="h-3.5 w-3.5 shrink-0" />
{child.title}
</a>
</li>
{/each}
</ul>
</Card.Content>
</Card.Root>
{:else}
<a href="/docs/{node.slug}">
<Card.Root class="cursor-pointer hover:border-primary/50 transition-colors h-full">
<Card.Header class="pb-2">
<div class="flex items-center gap-2">
<BookOpen class="h-4 w-4 text-muted-foreground" />
<Card.Title class="text-sm">{node.title}</Card.Title>
</div>
</Card.Header>
</Card.Root>
</a>
{/if}
{/each}
</div>
{/if}
</div>
