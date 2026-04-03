<script lang="ts">
	import { goto } from '$app/navigation';
	import { getAuth } from '$lib/stores/auth.svelte';
	import * as Card from '$lib/components/ui/card';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { Button } from '$lib/components/ui/button';
	import { Alert, AlertDescription } from '$lib/components/ui/alert';

	const auth = getAuth();

	let email = $state('');
	let password = $state('');
	let password2 = $state('');
	let error = $state('');
	let submitting = $state(false);

	async function handleSubmit(e: Event) {
		e.preventDefault();
		error = '';

		if (password !== password2) {
			error = 'Passwords do not match.';
			return;
		}

		submitting = true;
		try {
			const res = await auth.signup(email, password, password2);
			if (!res.ok) {
				error = res.error || 'Sign up failed. Please try again.';
				return;
			}
			goto('/auth/verify-email');
		} catch (err: unknown) {
			const e = err as { errors?: Array<{ message: string }> };
			if (e.errors?.length) {
				error = e.errors.map((e) => e.message).join('. ');
			} else {
				error = 'Sign up failed. Please try again.';
			}
		} finally {
			submitting = false;
		}
	}
</script>

<svelte:head>
	<title>Sign Up - LLM Lab</title>
</svelte:head>

<Card.Root class="w-full">
		<Card.Header>
			<Card.Title class="text-2xl">Create Account</Card.Title>
			<Card.Description>Enter your email and choose a password.</Card.Description>
		</Card.Header>
		<Card.Content>
			{#if error}
				<Alert variant="destructive" class="mb-4">
					<AlertDescription>{error}</AlertDescription>
				</Alert>
			{/if}
			<form onsubmit={handleSubmit} class="space-y-4">
				<div class="space-y-2">
					<Label for="email">Email</Label>
					<Input
						id="email"
						type="email"
						placeholder="you@example.com"
						bind:value={email}
						required
						autocomplete="email"
					/>
				</div>
				<div class="space-y-2">
					<Label for="password">Password</Label>
					<Input
						id="password"
						type="password"
						bind:value={password}
						required
						autocomplete="new-password"
					/>
				</div>
				<div class="space-y-2">
					<Label for="password2">Confirm Password</Label>
					<Input
						id="password2"
						type="password"
						bind:value={password2}
						required
						autocomplete="new-password"
					/>
				</div>
				<Button type="submit" class="w-full" disabled={submitting}>
					{submitting ? 'Creating account...' : 'Sign Up'}
				</Button>
			</form>
		</Card.Content>
		<Card.Footer class="text-sm text-center">
			<p class="text-muted-foreground">
				Already have an account?
				<a href="/auth/login" class="underline hover:text-foreground">Log in</a>
			</p>
		</Card.Footer>
	</Card.Root>
