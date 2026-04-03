<script lang="ts">
	import * as Card from '$lib/components/ui/card';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import ArrowLeft from '@lucide/svelte/icons/arrow-left';
	import Upload from '@lucide/svelte/icons/upload';
	import FileJson from '@lucide/svelte/icons/file-json';

	let fileName = $state('');
</script>

<svelte:head>
	<title>Import Models - LLM Lab</title>
</svelte:head>

<div class="space-y-6">
	<!-- Breadcrumb -->
	<div class="flex items-center gap-2 text-sm text-muted-foreground">
		<Button variant="ghost" size="sm" href="/models" class="gap-1.5 px-2">
			<ArrowLeft class="h-3.5 w-3.5" />
			Models
		</Button>
		<span>/</span>
		<span class="text-foreground font-medium">Import</span>
	</div>

	<div class="page-header">
		<h1>Import Models</h1>
		<p>Import model definitions from a JSON or ZIP file.</p>
	</div>

	<div class="mx-auto max-w-lg">
		<Card.Root>
			<Card.Header>
				<div class="flex items-center gap-2">
					<Upload class="h-4 w-4 text-muted-foreground" />
					<Card.Title>Upload File</Card.Title>
				</div>
				<Card.Description>Select a .json or .zip file containing model definitions to import.</Card.Description>
			</Card.Header>
			<Card.Content>
				<div class="space-y-4">
					<div class="flex flex-col items-center justify-center gap-3 rounded-lg border-2 border-dashed p-8 transition-colors hover:border-primary/50">
						<FileJson class="h-10 w-10 text-muted-foreground/50" />
						<div class="text-center">
							<p class="text-sm font-medium">
								{#if fileName}
									{fileName}
								{:else}
									Drop file here or click to browse
								{/if}
							</p>
							<p class="text-xs text-muted-foreground mt-1">Accepts .json and .zip files</p>
						</div>
						<Input
							type="file"
							accept=".json,.zip"
							class="max-w-xs"
							onchange={(e) => {
								const target = e.target as HTMLInputElement;
								fileName = target.files?.[0]?.name ?? '';
							}}
						/>
					</div>
					<Button class="w-full" disabled>
						<Upload class="mr-2 h-4 w-4" />
						Import Models
					</Button>
				</div>
			</Card.Content>
		</Card.Root>
	</div>
</div>
