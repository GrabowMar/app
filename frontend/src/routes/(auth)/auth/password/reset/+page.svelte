<script lang="ts">
	import { requestPasswordReset } from '$lib/api/client';
	import * as Card from '$lib/components/ui/card';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { Button } from '$lib/components/ui/button';
	import { Alert, AlertDescription } from '$lib/components/ui/alert';

	let email = $state('');
	let error = $state('');
	let success = $state(false);
	let submitting = $state(false);

	async function handleSubmit(e: Event) {
		e.preventDefault();
		error = '';
		submitting = true;

		try {
			await requestPasswordReset(email);
			success = true;
		} catch (err: unknown) {
			const e = err as { errors?: Array<{ message: string }> };
			if (e.errors?.length) {
				error = e.errors.map((e) => e.message).join('. ');
			} else {
				error = 'Failed to send password reset email.';
			}
		} finally {
			submitting = false;
		}
	}
</script>

<svelte:head>
	<title>Reset Password - LLM Lab</title>
</svelte:head>

<div class="flex min-h-[50vh] items-center justify-center sm:min-h-[60vh]">
	<Card.Root class="w-full max-w-md border-0 shadow-none sm:border sm:shadow-sm">
		<Card.Header class="px-0 sm:px-6">
			<Card.Title class="text-xl sm:text-2xl">Reset Password</Card.Title>
			<Card.Description class="text-xs sm:text-sm">Enter your email and we'll send you a reset link.</Card.Description>
		</Card.Header>
		<Card.Content class="px-0 sm:px-6">
			{#if success}
				<Alert>
					<AlertDescription>
						If an account exists with that email, we've sent a password reset link.
						Check your inbox.
					</AlertDescription>
				</Alert>
			{:else}
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
							class="h-11 sm:h-9"
						/>
					</div>
					<Button type="submit" class="h-11 w-full sm:h-9" disabled={submitting}>
						{submitting ? 'Sending...' : 'Send Reset Link'}
					</Button>
				</form>
			{/if}
		</Card.Content>
		<Card.Footer class="px-0 text-sm text-center sm:px-6">
			<a href="/auth/login" class="text-muted-foreground underline hover:text-foreground">
				Back to login
			</a>
		</Card.Footer>
	</Card.Root>
</div>
