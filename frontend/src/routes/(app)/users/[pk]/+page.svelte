<script lang="ts">
	import { page } from '$app/state';
	import { getUser, type ApiUser } from '$lib/api/client';
	import { getAuth } from '$lib/stores/auth.svelte';
	import * as Card from '$lib/components/ui/card';
	import * as Avatar from '$lib/components/ui/avatar';
	import { Button } from '$lib/components/ui/button';
	import { Badge } from '$lib/components/ui/badge';
	import { Separator } from '$lib/components/ui/separator';
	import { onMount } from 'svelte';

	const auth = getAuth();
	let profile = $state<ApiUser | null>(null);
	let error = $state('');
	let loading = $state(true);

	onMount(async () => {
		const pk = Number(page.params.pk);
		try {
			profile = await getUser(pk);
		} catch {
			error = 'User not found.';
		} finally {
			loading = false;
		}
	});

	function getInitials(name: string): string {
		return name
			.split(/\s+/)
			.map((w) => w[0])
			.join('')
			.toUpperCase()
			.slice(0, 2);
	}
</script>

<svelte:head>
	<title>{profile?.name || 'User'} - LLM Lab</title>
</svelte:head>

<div class="max-w-2xl mx-auto">
	{#if loading}
		<div class="space-y-4 animate-pulse">
			<div class="h-32 rounded-lg bg-muted"></div>
		</div>
	{:else if error}
		<Card.Root>
			<Card.Content class="pt-6 text-center">
				<p class="text-muted-foreground">{error}</p>
			</Card.Content>
		</Card.Root>
	{:else if profile}
		<Card.Root>
			<Card.Header>
				<div class="flex items-center space-x-4">
					<Avatar.Root class="h-16 w-16">
						<Avatar.Fallback class="text-lg">
							{getInitials(profile.name || profile.email)}
						</Avatar.Fallback>
					</Avatar.Root>
					<div>
						<Card.Title class="text-2xl">{profile.name || 'Unnamed User'}</Card.Title>
						<Card.Description>{profile.email}</Card.Description>
					</div>
				</div>
			</Card.Header>
			<Separator />
			<Card.Content class="pt-4">
				<div class="flex flex-wrap gap-2">
					<Badge variant="secondary">Member</Badge>
				</div>
			</Card.Content>
			{#if auth.user && auth.user.id === Number(page.params.pk)}
				<Card.Footer>
					<div class="flex gap-2">
						<Button href="/users/settings">Edit Profile</Button>
					</div>
				</Card.Footer>
			{/if}
		</Card.Root>
	{/if}
</div>
