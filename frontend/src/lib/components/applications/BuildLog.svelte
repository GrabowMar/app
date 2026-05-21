<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { Button } from '$lib/components/ui/button';
	import { toast } from 'svelte-sonner';
	import Copy from '@lucide/svelte/icons/copy';
	import ChevronDown from '@lucide/svelte/icons/chevron-down';
	import ChevronRight from '@lucide/svelte/icons/chevron-right';
	import RefreshCw from '@lucide/svelte/icons/refresh-cw';
	import { getContainerActions, type ContainerAction } from '$lib/api/runtime';

	interface Props {
		containerId: string;
		/** Auto-expand on mount (e.g. when status is `failed`). */
		startOpen?: boolean;
		/** Poll while the latest build action is still running. */
		live?: boolean;
	}

	let { containerId, startOpen = false, live = true }: Props = $props();

	let action = $state<ContainerAction | null>(null);
	let open = $state(startOpen);
	let loading = $state(false);
	let poll: ReturnType<typeof setInterval> | null = null;

	async function refresh() {
		loading = true;
		try {
			const items = await getContainerActions(containerId, { per_page: 5 });
			// Pick most recent build action; fall back to most recent action.
			const builds = items.filter((a) => a.action_type === 'build');
			action = builds[0] ?? items[0] ?? null;
		} catch {
			action = null;
		} finally {
			loading = false;
		}
	}

	function startPolling() {
		stopPolling();
		if (!live) return;
		poll = setInterval(() => {
			if (action && (action.status === 'running' || action.status === 'pending')) {
				refresh();
			}
		}, 1500);
	}

	function stopPolling() {
		if (poll) {
			clearInterval(poll);
			poll = null;
		}
	}

	onMount(() => {
		refresh().then(startPolling);
	});
	onDestroy(stopPolling);

	async function copyToClipboard() {
		if (!action?.output) return;
		try {
			await navigator.clipboard.writeText(action.output);
			toast.success('Build log copied');
		} catch {
			toast.error('Copy failed');
		}
	}

	const statusClass = $derived(
		action?.status === 'failed'
			? 'text-red-400'
			: action?.status === 'running'
				? 'text-amber-400'
				: action?.status === 'completed'
					? 'text-emerald-400'
					: 'text-muted-foreground',
	);
</script>

<div class="rounded border border-border bg-muted/10">
	<button
		type="button"
		class="flex w-full items-center justify-between px-3 py-2 text-left text-sm hover:bg-muted/20"
		onclick={() => (open = !open)}
	>
		<span class="flex items-center gap-2">
			{#if open}<ChevronDown class="h-4 w-4" />{:else}<ChevronRight class="h-4 w-4" />{/if}
			<span class="font-medium">Build log</span>
			{#if action}
				<span class="text-xs {statusClass}">
					· {action.action_type} · {action.status}
					{#if action.exit_code != null && action.status !== 'running'}
						· exit {action.exit_code}
					{/if}
				</span>
			{:else if loading}
				<span class="text-xs text-muted-foreground">· loading…</span>
			{:else}
				<span class="text-xs text-muted-foreground">· no builds yet</span>
			{/if}
		</span>
		<span class="flex items-center gap-1" onclick={(e) => e.stopPropagation()} role="presentation">
			<Button
				variant="ghost"
				size="sm"
				onclick={(e) => {
					e.stopPropagation();
					refresh();
				}}
				title="Refresh"
			>
				<RefreshCw class="h-3.5 w-3.5 {loading ? 'animate-spin' : ''}" />
			</Button>
			{#if action?.output}
				<Button
					variant="ghost"
					size="sm"
					onclick={(e) => {
						e.stopPropagation();
						copyToClipboard();
					}}
					title="Copy log"
				>
					<Copy class="h-3.5 w-3.5" />
				</Button>
			{/if}
		</span>
	</button>

	{#if open}
		<div class="border-t border-border p-3 space-y-2">
			{#if action?.error_message && action.status === 'failed'}
				<div class="text-xs text-red-400 font-mono bg-red-500/5 border border-red-500/20 rounded p-2 whitespace-pre-wrap break-words">
					{action.error_message}
				</div>
			{/if}
			{#if action?.output}
				<pre class="max-h-96 overflow-auto text-[11px] leading-snug font-mono whitespace-pre-wrap break-words bg-background/60 rounded p-2">{action.output}</pre>
			{:else if !loading}
				<p class="text-xs text-muted-foreground">No output captured for this action.</p>
			{/if}
		</div>
	{/if}
</div>
