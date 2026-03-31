<script lang="ts">
	import Cookie from '@lucide/svelte/icons/cookie';
	import X from '@lucide/svelte/icons/x';
	import { Button } from '$lib/components/ui/button';

	let visible = $state(false);

	function checkCookie() {
		if (typeof document !== 'undefined') {
			visible = !document.cookie.includes('cookie_consent=accepted');
		}
	}

	function accept() {
		document.cookie = 'cookie_consent=accepted; path=/; max-age=31536000; SameSite=Lax';
		visible = false;
	}

	function dismiss() {
		visible = false;
	}

	$effect(() => {
		checkCookie();
	});
</script>

{#if visible}
	<div class="fixed bottom-4 left-4 right-4 z-50 mx-auto max-w-lg rounded-lg border bg-card p-4 shadow-lg md:left-auto md:right-6 md:max-w-md">
		<div class="flex items-start gap-3">
			<Cookie class="mt-0.5 h-5 w-5 shrink-0 text-muted-foreground" />
			<div class="flex-1 space-y-2">
				<p class="text-sm">
					We use cookies for essential functionality. By continuing, you agree to our use of cookies.
				</p>
				<div class="flex gap-2">
					<Button size="sm" onclick={accept}>Accept</Button>
					<Button variant="ghost" size="sm" onclick={dismiss}>
						Dismiss
					</Button>
				</div>
			</div>
			<button class="text-muted-foreground hover:text-foreground" onclick={dismiss}>
				<X class="h-4 w-4" />
				<span class="sr-only">Close</span>
			</button>
		</div>
	</div>
{/if}
