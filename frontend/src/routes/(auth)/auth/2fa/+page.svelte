<script lang="ts">
	import { goto } from '$app/navigation';
	import { authenticate2FA } from '$lib/api/client';
	import * as Card from '$lib/components/ui/card';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { Button } from '$lib/components/ui/button';
	import { Alert, AlertDescription } from '$lib/components/ui/alert';

	let code = $state('');
	let error = $state('');
	let submitting = $state(false);

	async function handleSubmit(e: Event) {
		e.preventDefault();
		error = '';
		submitting = true;

		try {
			await authenticate2FA(code);
			goto('/');
		} catch (err: unknown) {
			const e = err as { errors?: Array<{ message: string }> };
			if (e.errors?.length) {
				error = e.errors.map((e) => e.message).join('. ');
			} else {
				error = 'Invalid code. Please try again.';
			}
		} finally {
			submitting = false;
		}
	}
</script>

<svelte:head>
	<title>Two-Factor Authentication - LLM Lab</title>
</svelte:head>

<div class="flex min-h-[50vh] items-center justify-center sm:min-h-[60vh]">
	<Card.Root class="w-full max-w-md border-0 shadow-none sm:border sm:shadow-sm">
		<Card.Header class="px-0 sm:px-6">
			<Card.Title class="text-xl sm:text-2xl">Two-Factor Authentication</Card.Title>
			<Card.Description class="text-xs sm:text-sm">Enter the code from your authenticator app.</Card.Description>
		</Card.Header>
		<Card.Content class="px-0 sm:px-6">
			{#if error}
				<Alert variant="destructive" class="mb-4">
					<AlertDescription>{error}</AlertDescription>
				</Alert>
			{/if}
			<form onsubmit={handleSubmit} class="space-y-4">
				<div class="space-y-2">
					<Label for="code">Authentication Code</Label>
					<Input
						id="code"
						type="text"
						inputmode="numeric"
						pattern="[0-9]*"
						placeholder="000000"
						bind:value={code}
						required
						autocomplete="one-time-code"
						class="h-11 text-center text-lg tracking-[0.3em] sm:h-9 sm:text-base sm:tracking-normal sm:text-left"
					/>
				</div>
				<Button type="submit" class="h-11 w-full sm:h-9" disabled={submitting}>
					{submitting ? 'Verifying...' : 'Verify'}
				</Button>
			</form>
		</Card.Content>
	</Card.Root>
</div>
