<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Alert, AlertDescription } from '$lib/components/ui/alert';
</script>

<svelte:head>
	<title>Verify Your Email - LLM Lab</title>
</svelte:head>

<div class="flex min-h-[60vh] items-center justify-center">
	<Card.Root class="w-full max-w-md">
		<Card.Header>
			<Card.Title class="text-2xl">Check Your Email</Card.Title>
		</Card.Header>
		<Card.Content>
			<Alert>
				<AlertDescription>
					We've sent a verification link to your email address. Please check your inbox and click
					the link to verify your account.
				</AlertDescription>
			</Alert>
			<p class="mt-4 text-sm text-muted-foreground">
				Didn't receive the email? Check your spam folder, or
				<a href="/auth/signup" class="underline hover:text-foreground">try signing up again</a>.
			</p>
		</Card.Content>
	</Card.Root>
</div>
