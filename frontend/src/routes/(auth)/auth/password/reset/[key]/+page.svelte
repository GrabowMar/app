<script lang="ts">
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { resetPassword } from '$lib/api/client';
	import * as Card from '$lib/components/ui/card';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { Button } from '$lib/components/ui/button';
	import { Alert, AlertDescription } from '$lib/components/ui/alert';

	let password = $state('');
	let password2 = $state('');
	let error = $state('');
	let success = $state(false);
	let submitting = $state(false);

	async function handleSubmit(e: Event) {
		e.preventDefault();
		error = '';

		if (password !== password2) {
			error = 'Passwords do not match.';
			return;
		}

		submitting = true;
		const key = page.params.key ?? '';

		try {
			await resetPassword(key, password);
			success = true;
		} catch (err: unknown) {
			const e = err as { errors?: Array<{ message: string }> };
			if (e.errors?.length) {
				error = e.errors.map((e) => e.message).join('. ');
			} else {
				error = 'Password reset failed. The link may be expired or invalid.';
			}
		} finally {
			submitting = false;
		}
	}
</script>

<svelte:head>
	<title>Set New Password - LLM Lab</title>
</svelte:head>

<div class="flex min-h-[60vh] items-center justify-center">
	<Card.Root class="w-full max-w-md">
		<Card.Header>
			<Card.Title class="text-2xl">Set New Password</Card.Title>
			<Card.Description>Choose a new password for your account.</Card.Description>
		</Card.Header>
		<Card.Content>
			{#if success}
				<Alert class="mb-4">
					<AlertDescription>Your password has been reset successfully!</AlertDescription>
				</Alert>
				<Button class="w-full" onclick={() => goto('/auth/login')}>Continue to Login</Button>
			{:else}
				{#if error}
					<Alert variant="destructive" class="mb-4">
						<AlertDescription>{error}</AlertDescription>
					</Alert>
				{/if}
				<form onsubmit={handleSubmit} class="space-y-4">
					<div class="space-y-2">
						<Label for="password">New Password</Label>
						<Input
							id="password"
							type="password"
							bind:value={password}
							required
							autocomplete="new-password"
						/>
					</div>
					<div class="space-y-2">
						<Label for="password2">Confirm New Password</Label>
						<Input
							id="password2"
							type="password"
							bind:value={password2}
							required
							autocomplete="new-password"
						/>
					</div>
					<Button type="submit" class="w-full" disabled={submitting}>
						{submitting ? 'Resetting...' : 'Reset Password'}
					</Button>
				</form>
			{/if}
		</Card.Content>
	</Card.Root>
</div>
