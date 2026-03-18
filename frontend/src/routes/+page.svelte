<script lang="ts">
	import { getAuth } from '$lib/stores/auth.svelte';
	import * as Card from '$lib/components/ui/card';
	import { Button } from '$lib/components/ui/button';

	const auth = getAuth();
</script>

<svelte:head>
	<title>LLM Lab</title>
</svelte:head>

<div class="space-y-8">
	<div class="text-center space-y-4">
		<h1 class="text-4xl font-bold tracking-tight">LLM Lab</h1>
		<p class="text-xl text-muted-foreground max-w-2xl mx-auto">
			Your platform for evaluating and experimenting with large language models.
		</p>
	</div>

	{#if auth.isAuthenticated && auth.user}
		<Card.Root class="max-w-lg mx-auto">
			<Card.Header>
				<Card.Title>Welcome back, {auth.user.display || auth.user.email}!</Card.Title>
				<Card.Description>You're signed in and ready to go.</Card.Description>
			</Card.Header>
			<Card.Content>
				<div class="flex gap-2">
					<Button href="/users/{auth.user.id}">View Profile</Button>
					<Button variant="outline" href="/users/settings">Settings</Button>
				</div>
			</Card.Content>
		</Card.Root>
	{:else if !auth.loading}
		<div class="flex justify-center gap-4">
			<Button href="/auth/login" size="lg">Log In</Button>
			<Button href="/auth/signup" variant="outline" size="lg">Sign Up</Button>
		</div>
	{/if}
</div>
