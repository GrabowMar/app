<script lang="ts">
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { verifyEmail } from '$lib/api/client';
	import * as Card from '$lib/components/ui/card';
	import { Button } from '$lib/components/ui/button';
	import { Alert, AlertDescription } from '$lib/components/ui/alert';
	import { onMount } from 'svelte';

	let verifying = $state(true);
	let success = $state(false);
	let error = $state('');

	onMount(async () => {
		const key = page.params.key ?? '';
		try {
			await verifyEmail(key);
			success = true;
		} catch (err: unknown) {
			const e = err as { errors?: Array<{ message: string }> };
			if (e.errors?.length) {
				error = e.errors.map((e) => e.message).join('. ');
			} else {
				error = 'Email verification failed. The link may be expired or invalid.';
			}
		} finally {
			verifying = false;
		}
	});
</script>

<svelte:head>
	<title>Email Verification - LLM Lab</title>
</svelte:head>

<div class="flex min-h-[50vh] items-center justify-center sm:min-h-[60vh]">
	<Card.Root class="w-full max-w-md border-0 shadow-none sm:border sm:shadow-sm">
		<Card.Header class="px-0 sm:px-6">
			<Card.Title class="text-xl sm:text-2xl">Email Verification</Card.Title>
		</Card.Header>
		<Card.Content class="px-0 sm:px-6">
			{#if verifying}
				<p class="text-muted-foreground">Verifying your email...</p>
			{:else if success}
				<Alert class="mb-4">
					<AlertDescription>Your email has been verified successfully!</AlertDescription>
				</Alert>
				<Button class="h-11 w-full sm:h-9" onclick={() => goto('/auth/login')}>Continue to Login</Button>
			{:else}
				<Alert variant="destructive" class="mb-4">
					<AlertDescription>{error}</AlertDescription>
				</Alert>
				<Button variant="outline" class="h-11 w-full sm:h-9" onclick={() => goto('/auth/signup')}>
					Back to Sign Up
				</Button>
			{/if}
		</Card.Content>
	</Card.Root>
</div>
