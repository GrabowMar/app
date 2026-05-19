<script lang="ts">
	import { getPreferences, VALID_COLORS, VALID_ITEMS_PER_PAGE } from '$lib/stores/preferences.svelte';
	import * as Card from '$lib/components/ui/card';
	import { Label } from '$lib/components/ui/label';
	import { Button } from '$lib/components/ui/button';
	import { Separator } from '$lib/components/ui/separator';
	import { Alert, AlertDescription } from '$lib/components/ui/alert';
	import { toast } from 'svelte-sonner';
	import Sun from '@lucide/svelte/icons/sun';
	import Moon from '@lucide/svelte/icons/moon';
	import Monitor from '@lucide/svelte/icons/monitor';
	import Download from '@lucide/svelte/icons/download';
	import Upload from '@lucide/svelte/icons/upload';
	import RotateCcw from '@lucide/svelte/icons/rotate-ccw';
	import AlertTriangle from '@lucide/svelte/icons/triangle-alert';

	interface Props {
		avatarColorMap: Record<string, string>;
		accentRingMap: Record<string, string>;
	}

	let { avatarColorMap, accentRingMap }: Props = $props();

	const prefs = getPreferences();

	let showImportSection = $state(false);
	let importJson = $state('');
	let showResetConfirm = $state(false);

	function handleExport() {
		const json = prefs.exportPreferences();
		const blob = new Blob([json], { type: 'application/json' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = 'llm-lab-settings.json';
		a.click();
		URL.revokeObjectURL(url);
		toast.success('Settings exported');
	}

	function handleImport() {
		if (!importJson.trim()) {
			toast.error('Please paste JSON settings');
			return;
		}
		const ok = prefs.importPreferences(importJson);
		if (ok) {
			toast.success('Settings imported successfully');
			importJson = '';
			showImportSection = false;
		} else {
			toast.error('Invalid settings JSON');
		}
	}

	function handleReset() {
		prefs.resetPreferences();
		showResetConfirm = false;
		toast.success('Settings reset to defaults');
	}
</script>

<!-- Appearance -->
<Card.Root>
	<Card.Header>
		<Card.Title>Appearance</Card.Title>
		<Card.Description>Customize the look and feel of the application.</Card.Description>
	</Card.Header>
	<Card.Content class="space-y-6">
		<!-- Theme -->
		<div class="space-y-2">
			<Label>Theme</Label>
			<div class="flex flex-col gap-2 sm:flex-row sm:gap-3">
				{#each [
					{ value: 'light', label: 'Light', Icon: Sun },
					{ value: 'dark', label: 'Dark', Icon: Moon },
					{ value: 'system', label: 'System', Icon: Monitor },
				] as { value, label, Icon }}
					<button
						type="button"
						class="flex flex-1 items-center gap-2 rounded-lg border p-3 cursor-pointer transition-colors {prefs.theme ===
						value
							? 'border-primary bg-primary/5'
							: 'border-border hover:border-muted-foreground/50'}"
						onclick={() => prefs.setTheme(value as 'light' | 'dark' | 'system')}
					>
						<Icon class="h-4 w-4" />
						<span class="text-sm font-medium">{label}</span>
					</button>
				{/each}
			</div>
		</div>

		<Separator />

		<!-- Accent Color -->
		<div class="space-y-2">
			<Label>Accent Color</Label>
			<div class="flex flex-wrap gap-2">
				{#each VALID_COLORS as color}
					<button
						type="button"
						class="h-8 w-8 rounded-full cursor-pointer transition-all {avatarColorMap[color]} {prefs.accentColor ===
						color
							? `ring-2 ring-offset-2 ring-offset-background ${accentRingMap[color]}`
							: 'hover:scale-110'}"
						title={color}
						onclick={() => prefs.setAccentColor(color)}
					></button>
				{/each}
			</div>
		</div>
	</Card.Content>
</Card.Root>

<!-- Sidebar -->
<Card.Root>
	<Card.Header>
		<Card.Title>Sidebar</Card.Title>
		<Card.Description>Configure sidebar behavior.</Card.Description>
	</Card.Header>
	<Card.Content>
		<div class="flex items-center justify-between">
			<div>
				<p class="text-sm font-medium">Start collapsed</p>
				<p class="text-xs text-muted-foreground">Sidebar starts in collapsed state on page load.</p>
			</div>
			<label class="relative inline-flex cursor-pointer items-center">
				<input
					type="checkbox"
					checked={prefs.sidebarCollapsed}
					onchange={(e) => prefs.setSidebarCollapsed(e.currentTarget.checked)}
					class="peer sr-only"
				/>
				<div
					class="h-5 w-9 rounded-full bg-muted peer-checked:bg-primary transition-colors after:absolute after:left-0.5 after:top-0.5 after:h-4 after:w-4 after:rounded-full after:bg-white after:transition-transform after:content-[''] peer-checked:after:translate-x-4"
				></div>
			</label>
		</div>
	</Card.Content>
</Card.Root>

<!-- Display Preferences -->
<Card.Root>
	<Card.Header>
		<Card.Title>Display Preferences</Card.Title>
		<Card.Description>Configure how data is displayed throughout the application.</Card.Description>
	</Card.Header>
	<Card.Content class="space-y-5">
		<!-- Items per page -->
		<div class="flex items-center justify-between">
			<div>
				<p class="text-sm font-medium">Items per page</p>
				<p class="text-xs text-muted-foreground">Number of items shown in tables and lists.</p>
			</div>
			<select
				class="h-9 rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
				value={prefs.itemsPerPage}
				onchange={(e) => prefs.setItemsPerPage(Number(e.currentTarget.value) as 10 | 25 | 50 | 100)}
			>
				{#each VALID_ITEMS_PER_PAGE as count}
					<option value={count}>{count}</option>
				{/each}
			</select>
		</div>

		<Separator />

		<!-- Date format -->
		<div class="flex items-center justify-between">
			<div>
				<p class="text-sm font-medium">Date format</p>
				<p class="text-xs text-muted-foreground">How dates are displayed in the application.</p>
			</div>
			<select
				class="h-9 rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
				value={prefs.dateFormat}
				onchange={(e) => prefs.setDateFormat(e.currentTarget.value as 'relative' | 'absolute' | 'iso')}
			>
				<option value="relative">Relative</option>
				<option value="absolute">Absolute</option>
				<option value="iso">ISO</option>
			</select>
		</div>

		<Separator />

		<!-- Compact tables -->
		<div class="flex items-center justify-between">
			<div>
				<p class="text-sm font-medium">Compact tables</p>
				<p class="text-xs text-muted-foreground">Reduce padding in table rows for a denser layout.</p>
			</div>
			<label class="relative inline-flex cursor-pointer items-center">
				<input
					type="checkbox"
					checked={prefs.compactTables}
					onchange={(e) => prefs.setCompactTables(e.currentTarget.checked)}
					class="peer sr-only"
				/>
				<div
					class="h-5 w-9 rounded-full bg-muted peer-checked:bg-primary transition-colors after:absolute after:left-0.5 after:top-0.5 after:h-4 after:w-4 after:rounded-full after:bg-white after:transition-transform after:content-[''] peer-checked:after:translate-x-4"
				></div>
			</label>
		</div>

		<Separator />

		<!-- Show advanced options -->
		<div class="flex items-center justify-between">
			<div>
				<p class="text-sm font-medium">Show advanced options</p>
				<p class="text-xs text-muted-foreground">Display additional configuration options for power users.</p>
			</div>
			<label class="relative inline-flex cursor-pointer items-center">
				<input
					type="checkbox"
					checked={prefs.showAdvancedOptions}
					onchange={(e) => prefs.setShowAdvancedOptions(e.currentTarget.checked)}
					class="peer sr-only"
				/>
				<div
					class="h-5 w-9 rounded-full bg-muted peer-checked:bg-primary transition-colors after:absolute after:left-0.5 after:top-0.5 after:h-4 after:w-4 after:rounded-full after:bg-white after:transition-transform after:content-[''] peer-checked:after:translate-x-4"
				></div>
			</label>
		</div>

		<Separator />

		<!-- Auto-refresh dashboards -->
		<div class="flex items-center justify-between">
			<div>
				<p class="text-sm font-medium">Auto-refresh dashboards</p>
				<p class="text-xs text-muted-foreground">Automatically refresh dashboard data at regular intervals.</p>
			</div>
			<label class="relative inline-flex cursor-pointer items-center">
				<input
					type="checkbox"
					checked={prefs.autoRefresh}
					onchange={(e) => prefs.setAutoRefresh(e.currentTarget.checked)}
					class="peer sr-only"
				/>
				<div
					class="h-5 w-9 rounded-full bg-muted peer-checked:bg-primary transition-colors after:absolute after:left-0.5 after:top-0.5 after:h-4 after:w-4 after:rounded-full after:bg-white after:transition-transform after:content-[''] peer-checked:after:translate-x-4"
				></div>
			</label>
		</div>
	</Card.Content>
</Card.Root>

<!-- Data Management -->
<Card.Root>
	<Card.Header>
		<Card.Title>Data Management</Card.Title>
		<Card.Description>Export, import, or reset your settings.</Card.Description>
	</Card.Header>
	<Card.Content class="space-y-4">
		<div class="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:gap-3">
			<Button variant="outline" class="w-full sm:w-auto" onclick={handleExport}>
				<Download class="h-4 w-4" />
				Export Settings
			</Button>
			<Button variant="outline" class="w-full sm:w-auto" onclick={() => (showImportSection = !showImportSection)}>
				<Upload class="h-4 w-4" />
				Import Settings
			</Button>
			{#if !showResetConfirm}
				<Button variant="destructive" class="w-full sm:w-auto" onclick={() => (showResetConfirm = true)}>
					<RotateCcw class="h-4 w-4" />
					Reset to Defaults
				</Button>
			{/if}
		</div>

		{#if showImportSection}
			<div class="space-y-3 rounded-lg border border-border p-4">
				<Label for="import-json">Paste settings JSON</Label>
				<textarea
					id="import-json"
					class="flex min-h-[100px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
					placeholder={'{"theme": "dark", "accentColor": "purple", ...}'}
					bind:value={importJson}
				></textarea>
				<div class="flex gap-2">
					<Button size="sm" onclick={handleImport}>Confirm Import</Button>
					<Button
						size="sm"
						variant="ghost"
						onclick={() => {
							showImportSection = false;
							importJson = '';
						}}
					>
						Cancel
					</Button>
				</div>
			</div>
		{/if}

		{#if showResetConfirm}
			<Alert variant="destructive">
				<AlertTriangle class="h-4 w-4" />
				<AlertDescription>
					<div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
						<span>Are you sure? This will reset all preferences to defaults.</span>
						<div class="flex gap-2 sm:ml-4">
							<Button size="sm" variant="destructive" onclick={handleReset}>Reset</Button>
							<Button size="sm" variant="ghost" onclick={() => (showResetConfirm = false)}>Cancel</Button>
						</div>
					</div>
				</AlertDescription>
			</Alert>
		{/if}
	</Card.Content>
</Card.Root>
