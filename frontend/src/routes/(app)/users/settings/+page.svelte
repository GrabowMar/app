<script lang="ts">
	import { getMe, updateMe, changePassword } from '$lib/api/client';
	import { getApiTokenSafe, generateApiToken, revokeApiToken } from '$lib/api/client';
	import type { ApiUser, ApiTokenInfo, ApiTokenCreated } from '$lib/api/client';
	import { getPreferences, VALID_COLORS, VALID_ITEMS_PER_PAGE, DEFAULT_PREFERENCES } from '$lib/stores/preferences.svelte';
	import type { AccentColor } from '$lib/stores/preferences.svelte';
	import * as Card from '$lib/components/ui/card';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { Button } from '$lib/components/ui/button';
	import { Separator } from '$lib/components/ui/separator';
	import { Alert, AlertDescription } from '$lib/components/ui/alert';
	import { onMount } from 'svelte';
	import { toast } from 'svelte-sonner';
	import Sun from '@lucide/svelte/icons/sun';
	import Moon from '@lucide/svelte/icons/moon';
	import Monitor from '@lucide/svelte/icons/monitor';
	import Download from '@lucide/svelte/icons/download';
	import Upload from '@lucide/svelte/icons/upload';
	import RotateCcw from '@lucide/svelte/icons/rotate-ccw';
	import Copy from '@lucide/svelte/icons/copy';
	import Key from '@lucide/svelte/icons/key';
	import Trash2 from '@lucide/svelte/icons/trash-2';
	import Shield from '@lucide/svelte/icons/shield';
	import Cookie from '@lucide/svelte/icons/cookie';
	import AlertTriangle from '@lucide/svelte/icons/triangle-alert';

	const prefs = getPreferences();

	type TabId = 'general' | 'profile' | 'api';
	const TABS: { id: TabId; label: string }[] = [
		{ id: 'general', label: 'General' },
		{ id: 'profile', label: 'Profile' },
		{ id: 'api', label: 'API Access' },
	];

	let activeTab = $state<TabId>('general');

	// --- Profile state ---
	let profile = $state<ApiUser | null>(null);
	let name = $state('');
	let profileError = $state('');
	let profileSuccess = $state('');
	let profileSubmitting = $state(false);

	// --- Password state ---
	let currentPassword = $state('');
	let newPassword = $state('');
	let newPassword2 = $state('');
	let passwordError = $state('');
	let passwordSuccess = $state('');
	let passwordSubmitting = $state(false);

	// --- API Token state ---
	let tokenInfo = $state<ApiTokenInfo | null>(null);
	let newlyCreatedToken = $state<ApiTokenCreated | null>(null);
	let tokenLoading = $state(true);
	let tokenActionLoading = $state(false);

	// --- General tab state ---
	let showImportSection = $state(false);
	let importJson = $state('');
	let showResetConfirm = $state(false);

	let loading = $state(true);

	const avatarColorMap: Record<string, string> = {
		blue: 'bg-blue-500',
		indigo: 'bg-indigo-500',
		purple: 'bg-purple-500',
		pink: 'bg-pink-500',
		red: 'bg-red-500',
		orange: 'bg-orange-500',
		amber: 'bg-amber-500',
		green: 'bg-green-500',
		teal: 'bg-teal-500',
		cyan: 'bg-cyan-500',
	};

	const accentRingMap: Record<string, string> = {
		blue: 'ring-blue-500',
		indigo: 'ring-indigo-500',
		purple: 'ring-purple-500',
		pink: 'ring-pink-500',
		red: 'ring-red-500',
		orange: 'ring-orange-500',
		amber: 'ring-amber-500',
		green: 'ring-green-500',
		teal: 'ring-teal-500',
		cyan: 'ring-cyan-500',
	};

	function readHash(): TabId {
		if (typeof window === 'undefined') return 'general';
		const hash = window.location.hash.replace('#', '') as TabId;
		if (TABS.some((t) => t.id === hash)) return hash;
		return 'general';
	}

	function switchTab(tab: TabId) {
		activeTab = tab;
		window.location.hash = tab;
	}

	onMount(() => {
		activeTab = readHash();

		const onHashChange = () => {
			activeTab = readHash();
		};
		window.addEventListener('hashchange', onHashChange);

		// Load profile data
		getMe()
			.then((user) => {
				profile = user;
				name = user.name;
			})
			.catch(() => {})
			.finally(() => {
				loading = false;
			});

		// Load token info
		getApiTokenSafe()
			.then((info) => {
				tokenInfo = info;
			})
			.finally(() => {
				tokenLoading = false;
			});

		return () => {
			window.removeEventListener('hashchange', onHashChange);
		};
	});

	// --- Profile handlers ---
	async function handleProfileUpdate(e: Event) {
		e.preventDefault();
		profileError = '';
		profileSuccess = '';
		profileSubmitting = true;
		try {
			profile = await updateMe({ name });
			profileSuccess = 'Profile updated successfully.';
		} catch {
			profileError = 'Failed to update profile.';
		} finally {
			profileSubmitting = false;
		}
	}

	async function handlePasswordChange(e: Event) {
		e.preventDefault();
		passwordError = '';
		passwordSuccess = '';

		if (newPassword !== newPassword2) {
			passwordError = 'Passwords do not match.';
			return;
		}

		passwordSubmitting = true;
		try {
			await changePassword({ current_password: currentPassword, new_password: newPassword });
			passwordSuccess = 'Password changed successfully.';
			currentPassword = '';
			newPassword = '';
			newPassword2 = '';
		} catch (err: unknown) {
			const e = err as { errors?: Array<{ message: string }> };
			if (e.errors?.length) {
				passwordError = e.errors.map((x) => x.message).join('. ');
			} else {
				passwordError = 'Failed to change password.';
			}
		} finally {
			passwordSubmitting = false;
		}
	}

	// --- Token handlers ---
	async function handleGenerateToken() {
		tokenActionLoading = true;
		try {
			const created = await generateApiToken();
			newlyCreatedToken = created;
			tokenInfo = { key_preview: created.key.slice(-8), created_at: created.created_at };
			toast.success('API token generated');
		} catch {
			toast.error('Failed to generate token');
		} finally {
			tokenActionLoading = false;
		}
	}

	async function handleRevokeToken() {
		tokenActionLoading = true;
		try {
			await revokeApiToken();
			tokenInfo = null;
			newlyCreatedToken = null;
			toast.success('API token revoked');
		} catch {
			toast.error('Failed to revoke token');
		} finally {
			tokenActionLoading = false;
		}
	}

	async function copyToken(token: string) {
		try {
			await navigator.clipboard.writeText(token);
			toast.success('Token copied to clipboard');
		} catch {
			toast.error('Failed to copy token');
		}
	}

	// --- Data management handlers ---
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

	let userInitial = $derived.by(() => {
		if (!profile) return '?';
		const display = profile.name || profile.email;
		return display.charAt(0).toUpperCase();
	});
</script>

<svelte:head>
	<title>Settings - LLM Lab</title>
</svelte:head>

<div class="mx-auto max-w-4xl space-y-6">
	<h1 class="text-3xl font-bold tracking-tight">Settings</h1>

	<!-- Tab Navigation -->
	<div class="flex gap-6 border-b border-border">
		{#each TABS as tab}
			<button
				type="button"
				class="pb-2 text-sm transition-colors {activeTab === tab.id
					? 'border-b-2 border-primary text-foreground font-medium'
					: 'text-muted-foreground hover:text-foreground'}"
				onclick={() => switchTab(tab.id)}
			>
				{tab.label}
			</button>
		{/each}
	</div>

	<!-- ====================== TAB 1: GENERAL ====================== -->
	{#if activeTab === 'general'}
		<div class="space-y-6">
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
						<div class="flex gap-3">
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
					<div class="flex flex-wrap gap-3">
						<Button variant="outline" onclick={handleExport}>
							<Download class="h-4 w-4" />
							Export Settings
						</Button>
						<Button variant="outline" onclick={() => (showImportSection = !showImportSection)}>
							<Upload class="h-4 w-4" />
							Import Settings
						</Button>
						{#if !showResetConfirm}
							<Button variant="destructive" onclick={() => (showResetConfirm = true)}>
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
								placeholder='{"theme": "dark", "accentColor": "purple", ...}'
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
								<div class="flex items-center justify-between">
									<span>Are you sure? This will reset all preferences to defaults.</span>
									<div class="flex gap-2 ml-4">
										<Button size="sm" variant="destructive" onclick={handleReset}>Reset</Button>
										<Button size="sm" variant="ghost" onclick={() => (showResetConfirm = false)}>Cancel</Button>
									</div>
								</div>
							</AlertDescription>
						</Alert>
					{/if}
				</Card.Content>
			</Card.Root>
		</div>

	<!-- ====================== TAB 2: PROFILE ====================== -->
	{:else if activeTab === 'profile'}
		<div class="space-y-6">
			{#if loading}
				<div class="space-y-4 animate-pulse">
					<div class="h-48 rounded-lg bg-muted"></div>
				</div>
			{:else}
				<!-- Account Information -->
				<Card.Root>
					<Card.Header>
						<Card.Title>Account Information</Card.Title>
						<Card.Description>Update your personal information.</Card.Description>
					</Card.Header>
					<Card.Content>
						{#if profileSuccess}
							<Alert class="mb-4">
								<AlertDescription>{profileSuccess}</AlertDescription>
							</Alert>
						{/if}
						{#if profileError}
							<Alert variant="destructive" class="mb-4">
								<AlertDescription>{profileError}</AlertDescription>
							</Alert>
						{/if}
						<form onsubmit={handleProfileUpdate} class="space-y-4">
							<div class="space-y-2">
								<Label>Email</Label>
								<div class="inline-flex items-center rounded-md border border-border bg-muted/50 px-3 py-1.5 text-sm text-muted-foreground">
									{profile?.email ?? '—'}
								</div>
							</div>
							<div class="space-y-2">
								<Label for="name">Name</Label>
								<Input id="name" type="text" bind:value={name} placeholder="Your name" />
							</div>
							<Button type="submit" disabled={profileSubmitting}>
								{profileSubmitting ? 'Saving...' : 'Save Changes'}
							</Button>
						</form>
					</Card.Content>
				</Card.Root>

				<!-- Change Password -->
				<Card.Root>
					<Card.Header>
						<Card.Title>Change Password</Card.Title>
						<Card.Description>Update your password.</Card.Description>
					</Card.Header>
					<Card.Content>
						{#if passwordSuccess}
							<Alert class="mb-4">
								<AlertDescription>{passwordSuccess}</AlertDescription>
							</Alert>
						{/if}
						{#if passwordError}
							<Alert variant="destructive" class="mb-4">
								<AlertDescription>{passwordError}</AlertDescription>
							</Alert>
						{/if}
						<form onsubmit={handlePasswordChange} class="space-y-4">
							<div class="space-y-2">
								<Label for="current-password">Current Password</Label>
								<Input
									id="current-password"
									type="password"
									bind:value={currentPassword}
									required
									autocomplete="current-password"
								/>
							</div>
							<div class="space-y-2">
								<Label for="new-password">New Password</Label>
								<Input
									id="new-password"
									type="password"
									bind:value={newPassword}
									required
									autocomplete="new-password"
								/>
							</div>
							<div class="space-y-2">
								<Label for="new-password2">Confirm New Password</Label>
								<Input
									id="new-password2"
									type="password"
									bind:value={newPassword2}
									required
									autocomplete="new-password"
								/>
							</div>
							<Button type="submit" disabled={passwordSubmitting}>
								{passwordSubmitting ? 'Changing...' : 'Change Password'}
							</Button>
						</form>
					</Card.Content>
				</Card.Root>
			{/if}
		</div>

	<!-- ====================== TAB 3: API ACCESS ====================== -->
	{:else if activeTab === 'api'}
		<div class="space-y-6">
			<!-- API Token -->
			<Card.Root>
				<Card.Header>
					<Card.Title class="flex items-center gap-2">
						<Key class="h-5 w-5" />
						API Token
					</Card.Title>
					<Card.Description>Manage your personal API token for programmatic access.</Card.Description>
				</Card.Header>
				<Card.Content class="space-y-4">
					{#if tokenLoading}
						<div class="h-12 animate-pulse rounded-md bg-muted"></div>
					{:else if newlyCreatedToken}
						<Alert>
							<AlertTriangle class="h-4 w-4" />
							<AlertDescription>
								<p class="font-medium">Save this token! It will only be shown once.</p>
							</AlertDescription>
						</Alert>
						<div class="flex items-center gap-2 rounded-lg border border-primary/30 bg-primary/5 p-3">
							<code class="flex-1 break-all text-sm font-mono">{newlyCreatedToken.key}</code>
							<Button size="icon" variant="ghost" onclick={() => copyToken(newlyCreatedToken!.key)}>
								<Copy class="h-4 w-4" />
							</Button>
						</div>
						<Button variant="destructive" disabled={tokenActionLoading} onclick={handleRevokeToken}>
							<Trash2 class="h-4 w-4" />
							Revoke Token
						</Button>
					{:else if tokenInfo}
						<div class="flex items-center justify-between rounded-lg border border-border p-3">
							<div>
								<p class="text-sm font-medium">Active Token</p>
								<p class="text-xs text-muted-foreground font-mono">...{tokenInfo.key_preview}</p>
								<p class="text-xs text-muted-foreground">
									Created {new Date(tokenInfo.created_at).toLocaleDateString()}
								</p>
							</div>
							<Button variant="destructive" size="sm" disabled={tokenActionLoading} onclick={handleRevokeToken}>
								<Trash2 class="h-4 w-4" />
								Revoke Token
							</Button>
						</div>
					{:else}
						<div class="flex flex-col items-center gap-3 rounded-lg border border-dashed border-border p-6 text-center">
							<Key class="h-8 w-8 text-muted-foreground" />
							<p class="text-sm text-muted-foreground">No API token generated yet.</p>
							<Button disabled={tokenActionLoading} onclick={handleGenerateToken}>
								Generate New Token
							</Button>
						</div>
					{/if}
				</Card.Content>
			</Card.Root>

			<!-- Usage Guide -->
			<Card.Root>
				<Card.Header>
					<Card.Title>Usage Guide</Card.Title>
					<Card.Description>How to use the API with your token.</Card.Description>
				</Card.Header>
				<Card.Content class="space-y-4">
					<div class="space-y-2">
						<Label>Example Request</Label>
						<pre class="overflow-x-auto rounded-lg border border-border bg-muted/50 p-3 text-sm font-mono">curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://your-domain.com/api/models/</pre>
					</div>

					<Separator />

					<div class="space-y-2">
						<Label>Available Endpoints</Label>
						<div class="overflow-x-auto rounded-lg border border-border">
							<table class="w-full text-sm">
								<thead>
									<tr class="border-b border-border bg-muted/50">
										<th class="px-3 py-2 text-left font-medium">Method</th>
										<th class="px-3 py-2 text-left font-medium">Endpoint</th>
										<th class="px-3 py-2 text-left font-medium">Description</th>
									</tr>
								</thead>
								<tbody>
									<tr class="border-b border-border">
										<td class="px-3 py-2"><code class="rounded bg-muted px-1 text-xs">GET</code></td>
										<td class="px-3 py-2 font-mono text-xs">/api/models/</td>
										<td class="px-3 py-2 text-muted-foreground">List all AI models</td>
									</tr>
									<tr class="border-b border-border">
										<td class="px-3 py-2"><code class="rounded bg-muted px-1 text-xs">GET</code></td>
										<td class="px-3 py-2 font-mono text-xs">/api/models/stats/</td>
										<td class="px-3 py-2 text-muted-foreground">Model statistics</td>
									</tr>
									<tr class="border-b border-border">
										<td class="px-3 py-2"><code class="rounded bg-muted px-1 text-xs">POST</code></td>
										<td class="px-3 py-2 font-mono text-xs">/api/models/sync/</td>
										<td class="px-3 py-2 text-muted-foreground">Sync from OpenRouter</td>
									</tr>
									<tr>
										<td class="px-3 py-2"><code class="rounded bg-muted px-1 text-xs">GET</code></td>
										<td class="px-3 py-2 font-mono text-xs">/api/users/me/</td>
										<td class="px-3 py-2 text-muted-foreground">Current user profile</td>
									</tr>
								</tbody>
							</table>
						</div>
					</div>
				</Card.Content>
			</Card.Root>

			<!-- Avatar Color -->
			<Card.Root>
				<Card.Header>
					<Card.Title>Avatar Color</Card.Title>
					<Card.Description>Choose the color for your user avatar.</Card.Description>
				</Card.Header>
				<Card.Content class="space-y-4">
					<div class="flex items-center gap-6">
						<div
							class="flex h-14 w-14 items-center justify-center rounded-full text-xl font-bold text-white {avatarColorMap[prefs.avatarColor]}"
						>
							{userInitial}
						</div>
						<div class="flex flex-wrap gap-2">
							{#each VALID_COLORS as color}
								<button
									type="button"
									class="h-8 w-8 rounded-full cursor-pointer transition-all {avatarColorMap[color]} {prefs.avatarColor ===
									color
										? `ring-2 ring-offset-2 ring-offset-background ${accentRingMap[color]}`
										: 'hover:scale-110'}"
									title={color}
									onclick={() => prefs.setAvatarColor(color)}
								></button>
							{/each}
						</div>
					</div>
				</Card.Content>
			</Card.Root>

			<!-- Cookie & Data Settings -->
			<Card.Root>
				<Card.Header>
					<Card.Title class="flex items-center gap-2">
						<Cookie class="h-5 w-5" />
						Cookie &amp; Data Settings
					</Card.Title>
					<Card.Description>Manage how we use cookies and process your data.</Card.Description>
				</Card.Header>
				<Card.Content class="space-y-5">
					<!-- Essential -->
					<div class="flex items-start justify-between gap-4">
						<div class="space-y-0.5">
							<div class="flex items-center gap-2">
								<Shield class="h-4 w-4 text-muted-foreground" />
								<p class="text-sm font-medium">Essential</p>
							</div>
							<p class="text-xs text-muted-foreground">Required for basic functionality including authentication and security.</p>
						</div>
						<label class="relative inline-flex cursor-not-allowed items-center opacity-60">
							<input type="checkbox" checked={true} disabled class="peer sr-only" />
							<div
								class="h-5 w-9 rounded-full bg-primary transition-colors after:absolute after:left-0.5 after:top-0.5 after:h-4 after:w-4 after:rounded-full after:bg-white after:translate-x-4 after:content-['']"
							></div>
						</label>
					</div>

					<Separator />

					<!-- Analytics -->
					<div class="flex items-start justify-between gap-4">
						<div class="space-y-0.5">
							<p class="text-sm font-medium">Analytics &amp; Performance</p>
							<p class="text-xs text-muted-foreground">Help us understand how you use the application to improve performance.</p>
						</div>
						<label class="relative inline-flex cursor-pointer items-center">
							<input
								type="checkbox"
								checked={prefs.cookieConsent.analytics}
								onchange={(e) => prefs.setCookieConsent({ analytics: e.currentTarget.checked })}
								class="peer sr-only"
							/>
							<div
								class="h-5 w-9 rounded-full bg-muted peer-checked:bg-primary transition-colors after:absolute after:left-0.5 after:top-0.5 after:h-4 after:w-4 after:rounded-full after:bg-white after:transition-transform after:content-[''] peer-checked:after:translate-x-4"
							></div>
						</label>
					</div>

					<Separator />

					<!-- Functional -->
					<div class="flex items-start justify-between gap-4">
						<div class="space-y-0.5">
							<p class="text-sm font-medium">Functional &amp; Preferences</p>
							<p class="text-xs text-muted-foreground">Remember your preferences and settings for a personalized experience.</p>
						</div>
						<label class="relative inline-flex cursor-pointer items-center">
							<input
								type="checkbox"
								checked={prefs.cookieConsent.functional}
								onchange={(e) => prefs.setCookieConsent({ functional: e.currentTarget.checked })}
								class="peer sr-only"
							/>
							<div
								class="h-5 w-9 rounded-full bg-muted peer-checked:bg-primary transition-colors after:absolute after:left-0.5 after:top-0.5 after:h-4 after:w-4 after:rounded-full after:bg-white after:transition-transform after:content-[''] peer-checked:after:translate-x-4"
							></div>
						</label>
					</div>

					<Separator />

					<!-- AI Processing -->
					<div class="flex items-start justify-between gap-4">
						<div class="space-y-0.5">
							<p class="text-sm font-medium">AI Processing &amp; History</p>
							<p class="text-xs text-muted-foreground">Store AI analysis results and processing history for faster access.</p>
						</div>
						<label class="relative inline-flex cursor-pointer items-center">
							<input
								type="checkbox"
								checked={prefs.cookieConsent.ai}
								onchange={(e) => prefs.setCookieConsent({ ai: e.currentTarget.checked })}
								class="peer sr-only"
							/>
							<div
								class="h-5 w-9 rounded-full bg-muted peer-checked:bg-primary transition-colors after:absolute after:left-0.5 after:top-0.5 after:h-4 after:w-4 after:rounded-full after:bg-white after:transition-transform after:content-[''] peer-checked:after:translate-x-4"
							></div>
						</label>
					</div>
				</Card.Content>
			</Card.Root>
		</div>
	{/if}
</div>
