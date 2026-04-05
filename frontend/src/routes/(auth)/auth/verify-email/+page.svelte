<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Alert, AlertDescription } from '$lib/components/ui/alert';
</script>

<svelte:head>
	<title>Verify Your Email - LLM Lab</title>
</svelte:head>

<div class="flex min-h-[50vh] items-center justify-center sm:min-h-[60vh]">
	<Card.Root class="w-full max-w-md border-0 shadow-none sm:border sm:shadow-sm">
		<Card.Header class="px-0 sm:px-6">
			<Card.Title class="text-xl sm:text-2xl">Check Your Email</Card.Title>
		</Card.Header>
		<Card.Content class="px-0 sm:px-6">
			<Alert>
				<AlertDescription>
					We've sent a verification link to your email address. Please check your inbox and click
					the link to verify your account.
				</AlertDescription>
			</Alert>
			<p class="mt-4 text-xs text-muted-foreground sm:text-sm">
				Didn't receive the email? Check your spam folder, or
				<a href="/auth/signup" class="underline hover:text-foreground">try signing up again</a>.
			</p>
		</Card.Content>
	</Card.Root>
</div>
