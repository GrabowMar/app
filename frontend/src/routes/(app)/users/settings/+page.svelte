<script lang="ts">
	import { goto } from '$app/navigation';
	import { getAuth } from '$lib/stores/auth.svelte';
	import { getMe, updateMe, changePassword, type ApiUser } from '$lib/api/client';
	import * as Card from '$lib/components/ui/card';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { Button } from '$lib/components/ui/button';
	import { Separator } from '$lib/components/ui/separator';
	import { Alert, AlertDescription } from '$lib/components/ui/alert';
	import { onMount } from 'svelte';

	const auth = getAuth();

	let profile = $state<ApiUser | null>(null);
	let name = $state('');
	let profileError = $state('');
	let profileSuccess = $state('');
	let profileSubmitting = $state(false);

	let currentPassword = $state('');
	let newPassword = $state('');
	let newPassword2 = $state('');
	let passwordError = $state('');
	let passwordSuccess = $state('');
	let passwordSubmitting = $state(false);

	let loading = $state(true);

	onMount(async () => {
		if (!auth.isAuthenticated && !auth.isLoading) {
			goto('/auth/login');
			return;
		}
		try {
			profile = await getMe();
			name = profile.name;
		} catch {
			goto('/auth/login');
		} finally {
			loading = false;
		}
	});

	async function handleProfileUpdate(e: Event) {
		e.preventDefault();
		profileError = '';
		profileSuccess = '';
		profileSubmitting = true;

		try {
			profile = await updateMe({ name });
			profileSuccess = 'Profile updated successfully.';
		} catch (err: unknown) {
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
				passwordError = e.errors.map((e) => e.message).join('. ');
			} else {
				passwordError = 'Failed to change password.';
			}
		} finally {
			passwordSubmitting = false;
		}
	}
</script>

<svelte:head>
	<title>Settings - LLM Lab</title>
</svelte:head>

<div class="max-w-2xl mx-auto space-y-6">
	<h1 class="text-3xl font-bold tracking-tight">Settings</h1>

	{#if loading}
		<div class="space-y-4 animate-pulse">
			<div class="h-48 rounded-lg bg-muted"></div>
		</div>
	{:else}
		<!-- Profile Section -->
		<Card.Root>
			<Card.Header>
				<Card.Title>Profile</Card.Title>
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
						<Label for="name">Name</Label>
						<Input id="name" type="text" bind:value={name} placeholder="Your name" />
					</div>
					<Button type="submit" disabled={profileSubmitting}>
						{profileSubmitting ? 'Saving...' : 'Update Profile'}
					</Button>
				</form>
			</Card.Content>
		</Card.Root>

		<Separator />

		<!-- Password Section -->
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
