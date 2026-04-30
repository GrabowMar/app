<script lang="ts">
	import { onMount } from 'svelte';
	import { getAuth } from '$lib/stores/auth.svelte';
	import {
		getAnalysisStats,
		getAnalysisTasks,
		getStatisticsOverview,
		getStatisticsRecentActivity,
		type StatisticsOverview,
		type RecentActivityItem,
	} from '$lib/api/client';
	import type { AnalysisTaskList } from '$lib/api/client';
	import * as Card from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';
	import { Separator } from '$lib/components/ui/separator';
	import BarChart3 from '@lucide/svelte/icons/bar-chart-3';
	import Boxes from '@lucide/svelte/icons/boxes';
	import AppWindow from '@lucide/svelte/icons/app-window';
	import FileText from '@lucide/svelte/icons/file-text';
	import ArrowRight from '@lucide/svelte/icons/arrow-right';
	import Activity from '@lucide/svelte/icons/activity';
	import CircleCheck from '@lucide/svelte/icons/circle-check';
	import CircleX from '@lucide/svelte/icons/circle-x';
	import Clock from '@lucide/svelte/icons/clock';
	import RefreshCw from '@lucide/svelte/icons/refresh-cw';
	import CloudDownload from '@lucide/svelte/icons/cloud-download';
	import Eraser from '@lucide/svelte/icons/eraser';
	import Download from '@lucide/svelte/icons/download';
	import Keyboard from '@lucide/svelte/icons/keyboard';
	import Settings from '@lucide/svelte/icons/settings';
	import FlaskConical from '@lucide/svelte/icons/flask-conical';
	import Cpu from '@lucide/svelte/icons/cpu';
	import type { Component } from 'svelte';

	const auth = getAuth();

	function timeAgo(dateStr: string): string {
		const seconds = Math.floor((Date.now() - new Date(dateStr).getTime()) / 1000);
		if (seconds < 60) return 'just now';
		if (seconds < 3600) return `${Math.floor(seconds / 60)} min ago`;
		if (seconds < 86400) return `${Math.floor(seconds / 3600)} hour${Math.floor(seconds / 3600) > 1 ? 's' : ''} ago`;
		return `${Math.floor(seconds / 86400)} day${Math.floor(seconds / 86400) > 1 ? 's' : ''} ago`;
	}

	const validStatuses = ['completed', 'running', 'failed', 'pending'] as const;
	type AnalysisStatus = (typeof validStatuses)[number];

	function normalizeStatus(status: string): AnalysisStatus {
		const lower = status.toLowerCase();
		if (validStatuses.includes(lower as AnalysisStatus)) return lower as AnalysisStatus;
		return 'pending';
	}

	interface RecentAnalysis {
		id: string;
		name: string;
		status: AnalysisStatus;
		time: string;
	}

	let analysisStatsValue = $state<string>('—');
	let analysisStatsSubtitle = $state<string>('Loading…');
	let analysisStatsChange = $state<string>('');
	let recentAnalyses = $state<RecentAnalysis[]>([]);
	let overview = $state<StatisticsOverview | null>(null);
	let liveActivity = $state<RecentActivityItem[]>([]);

	onMount(async () => {
		const [statsResult, tasksResult, overviewResult, activityResult] = await Promise.allSettled([
			getAnalysisStats(),
			getAnalysisTasks({ per_page: 5 }),
			getStatisticsOverview(),
			getStatisticsRecentActivity(8),
		]);

		if (statsResult.status === 'fulfilled') {
			const stats = statsResult.value;
			analysisStatsValue = String(stats.total_tasks);
			analysisStatsSubtitle = `${stats.completed_tasks} completed`;
			analysisStatsChange = `${stats.running_tasks} running`;
		} else {
			analysisStatsValue = '—';
			analysisStatsSubtitle = 'Unable to load';
			analysisStatsChange = '';
		}

		if (tasksResult.status === 'fulfilled') {
			recentAnalyses = tasksResult.value.items.map((task: AnalysisTaskList) => ({
				id: task.id,
				name: task.name,
				status: normalizeStatus(task.status),
				time: timeAgo(task.created_at),
			}));
		}

		if (overviewResult.status === 'fulfilled') {
			overview = overviewResult.value;
		}

		if (activityResult.status === 'fulfilled') {
			liveActivity = activityResult.value;
		}
	});

	interface SummaryCard {
		title: string;
		value: () => string;
		subtitle: () => string;
		change: () => string;
		icon: Component;
		href: string;
		color: string;
	}

	const summaryCards: SummaryCard[] = [
		{ title: 'Models', value: () => (overview ? String(overview.models_in_use) : '—'), subtitle: () => 'Models in use', change: () => (overview ? `${overview.total_apps} total apps` : ''), icon: Boxes, href: '/models', color: 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950/50' },
		{ title: 'Applications', value: () => (overview ? String(overview.total_apps) : '—'), subtitle: () => (overview ? `${overview.apps_completed} completed` : 'Loading…'), change: () => (overview ? `${overview.apps_success_rate}% success rate` : ''), icon: AppWindow, href: '/applications', color: 'text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/50' },
		{ title: 'Security Analyses', value: () => analysisStatsValue, subtitle: () => analysisStatsSubtitle, change: () => analysisStatsChange, icon: BarChart3, href: '/analysis', color: 'text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-950/50' },
		{ title: 'Findings', value: () => (overview ? String(overview.total_findings) : '—'), subtitle: () => (overview ? `${overview.avg_findings_per_app}/app avg` : 'Loading…'), change: () => (overview ? `${overview.analyses_completed} analyses` : ''), icon: FileText, href: '/statistics', color: 'text-violet-600 dark:text-violet-400 bg-violet-50 dark:bg-violet-950/50' },
	];

	interface ServiceStatus {
		name: string;
		status: 'online' | 'offline' | 'pending';
	}

	const services: ServiceStatus[] = [
		{ name: 'API Server', status: 'online' },
		{ name: 'Celery Worker', status: 'online' },
		{ name: 'Static Analyzer', status: 'online' },
		{ name: 'Dynamic Analyzer', status: 'online' },
		{ name: 'Performance Tester', status: 'offline' },
		{ name: 'AI Analyzer', status: 'pending' },
	];

	interface RecentApp {
		name: string;
		model: string;
		status: 'running' | 'stopped' | 'building' | 'failed';
		created: string;
	}

	const recentApps: RecentApp[] = [
		{ name: 'Task Manager', model: 'GPT-4o', status: 'running', created: '10 min ago' },
		{ name: 'E-Commerce Store', model: 'Claude 3.5 Sonnet', status: 'running', created: '1 hour ago' },
		{ name: 'Chat Application', model: 'Gemini 1.5 Pro', status: 'stopped', created: '3 hours ago' },
		{ name: 'Blog Platform', model: 'DeepSeek V3', status: 'building', created: '5 hours ago' },
		{ name: 'Portfolio Site', model: 'GPT-4o-mini', status: 'failed', created: '1 day ago' },
	];

	interface ActivityEvent {
		icon: Component;
		text: string;
		time: string;
		color: string;
	}

	const activityFeed: ActivityEvent[] = [
		{ icon: Activity, text: 'Analysis completed for GPT-4o / App #3', time: '2 min ago', color: 'text-emerald-500' },
		{ icon: AppWindow, text: 'Application generated: Task Manager', time: '10 min ago', color: 'text-blue-500' },
		{ icon: FlaskConical, text: 'Analysis started on Claude 3.5 Sonnet / App #1', time: '15 min ago', color: 'text-amber-500' },
		{ icon: Cpu, text: 'Model synced: DeepSeek V3', time: '30 min ago', color: 'text-violet-500' },
		{ icon: CircleX, text: 'Analysis failed for DeepSeek V3 / App #1', time: '1 hour ago', color: 'text-destructive' },
		{ icon: AppWindow, text: 'Application generated: E-Commerce Store', time: '1 hour ago', color: 'text-blue-500' },
		{ icon: Activity, text: 'Analysis completed for Gemini 1.5 Pro / App #2', time: '2 hours ago', color: 'text-emerald-500' },
		{ icon: FileText, text: 'Report generated: Model Analysis — GPT-4o', time: '3 hours ago', color: 'text-violet-500' },
	];

	const statusColors: Record<string, string> = {
		completed: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400',
		running: 'bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-400',
		failed: 'bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-400',
		pending: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400',
		stopped: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400',
		building: 'bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-400',
	};

	interface AdminAction {
		label: string;
		icon: Component;
		color: string;
	}

	const adminActions: AdminAction[] = [
		{ label: 'Refresh', icon: RefreshCw, color: 'text-blue-500' },
		{ label: 'Sync Models', icon: CloudDownload, color: 'text-primary' },
		{ label: 'Clear Cache', icon: Eraser, color: 'text-amber-500' },
		{ label: 'System Info', icon: Download, color: 'text-emerald-500' },
		{ label: 'Shortcuts', icon: Keyboard, color: 'text-muted-foreground' },
	];
</script>

<svelte:head>
	<title>Dashboard - LLM Lab</title>
</svelte:head>

<div class="space-y-6 sm:space-y-8">
	<div class="page-header">
		<h1>Dashboard</h1>
		<p>
			{#if auth.isAuthenticated && auth.user}
				Welcome back, {auth.user.display || auth.user.email}.
			{:else}
				Your research platform overview.
			{/if}
		</p>
	</div>

	<!-- Summary Cards -->
	<div class="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
		{#each summaryCards as card (card.title)}
			<a href={card.href} class="group block">
				<Card.Root class="relative overflow-hidden hover:border-primary/30">
					<Card.Header class="flex flex-row items-center justify-between space-y-0 px-3 pb-1 pt-3 sm:px-6 sm:pb-2 sm:pt-6">
						<Card.Title class="text-xs sm:text-sm font-medium text-muted-foreground">{card.title}</Card.Title>
						<div class="flex h-6 w-6 sm:h-8 sm:w-8 items-center justify-center rounded-lg {card.color}">
							<card.icon class="h-3 w-3 sm:h-4 sm:w-4" />
						</div>
					</Card.Header>
					<Card.Content class="px-3 pb-3 sm:px-6 sm:pb-6">
						<div class="text-xl sm:text-2xl font-bold">{card.value()}</div>
						<p class="text-[11px] sm:text-xs text-muted-foreground mt-0.5 sm:mt-1">{card.subtitle()}</p>
						<p class="text-[11px] sm:text-xs text-emerald-600 dark:text-emerald-400 mt-1 sm:mt-2">{card.change()}</p>
					</Card.Content>
					<div class="absolute bottom-3 right-4 opacity-0 transition-opacity group-hover:opacity-100">
						<ArrowRight class="h-4 w-4 text-muted-foreground" />
					</div>
				</Card.Root>
			</a>
		{/each}
	</div>

	<!-- Main Content Grid -->
	<div class="grid gap-6 lg:grid-cols-12">
		<!-- Left Column -->
		<div class="space-y-6 lg:col-span-8">
			<!-- System Status -->
			<Card.Root>
				<Card.Header>
					<div class="flex items-center justify-between">
						<div class="flex items-center gap-2">
							<Settings class="h-4 w-4 text-muted-foreground" />
							<Card.Title>System Status</Card.Title>
						</div>
						<Button variant="ghost" size="icon" class="h-8 w-8" disabled>
							<RefreshCw class="h-3.5 w-3.5" />
						</Button>
					</div>
				</Card.Header>
				<Card.Content class="p-0">
					<div class="overflow-x-auto">
						<table class="table-card-mobile w-full">
							<thead>
								<tr class="border-b bg-muted/30">
									<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Service</th>
									<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Status</th>
									<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground hide-mobile">Port</th>
								</tr>
							</thead>
							<tbody class="divide-y">
								{#each services as svc, i (svc.name)}
									<tr class="transition-colors hover:bg-muted/30">
										<td class="px-4 py-2.5" data-label="Service">
											<div class="flex items-center gap-2.5">
												{#if svc.status === 'online'}
													<CircleCheck class="h-4 w-4 text-emerald-500" />
												{:else if svc.status === 'offline'}
													<CircleX class="h-4 w-4 text-destructive" />
												{:else}
													<Clock class="h-4 w-4 text-muted-foreground" />
												{/if}
												<span class="text-sm font-medium">{svc.name}</span>
											</div>
										</td>
										<td class="px-4 py-2.5" data-label="Status">
											<Badge variant={svc.status === 'online' ? 'secondary' : 'outline'} class="text-xs capitalize">
												{svc.status}
											</Badge>
										</td>
										<td class="px-4 py-2.5 hide-mobile" data-label="Port">
											<span class="text-xs text-muted-foreground font-mono">
												{['5000', '—', '2001', '2002', '2003', '2004'][i]}
											</span>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</Card.Content>
			</Card.Root>

			<!-- Recent Analyses -->
			<Card.Root>
				<Card.Header>
					<div class="flex items-center justify-between">
						<div class="flex items-center gap-2">
							<FlaskConical class="h-4 w-4 text-muted-foreground" />
							<div>
								<Card.Title>Recent Analyses</Card.Title>
								<Card.Description>Latest analysis tasks and their status.</Card.Description>
							</div>
						</div>
						<Button variant="ghost" size="sm" href="/analysis" class="text-xs">
							View all
							<ArrowRight class="ml-1 h-3 w-3" />
						</Button>
					</div>
				</Card.Header>
				<Card.Content class="p-0">
					<div class="overflow-x-auto">
						<table class="table-card-mobile w-full">
							<thead>
								<tr class="border-b bg-muted/30">
									<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Task</th>
									<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Status</th>
									<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Time</th>
								</tr>
							</thead>
							<tbody class="divide-y">
								{#each recentAnalyses as analysis (analysis.id)}
									<tr class="transition-colors hover:bg-muted/30">
										<td class="px-4 py-2.5" data-label="Task">
											<span class="text-sm font-medium">{analysis.name}</span>
										</td>
										<td class="px-4 py-2.5" data-label="Status">
											<span class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium {statusColors[analysis.status]}">
												{analysis.status}
											</span>
										</td>
										<td class="px-4 py-2.5" data-label="Time">
											<span class="text-xs text-muted-foreground">{analysis.time}</span>
										</td>
									</tr>
								{:else}
									<tr>
										<td colspan="3" class="px-4 py-6 text-center text-sm text-muted-foreground">No recent analyses</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</Card.Content>
			</Card.Root>

			<!-- Recent Applications -->
			<Card.Root>
				<Card.Header>
					<div class="flex items-center justify-between">
						<div class="flex items-center gap-2">
							<AppWindow class="h-4 w-4 text-muted-foreground" />
							<div>
								<Card.Title>Recent Applications</Card.Title>
								<Card.Description>Latest generated applications.</Card.Description>
							</div>
						</div>
						<Button variant="ghost" size="sm" href="/applications" class="text-xs">
							View all
							<ArrowRight class="ml-1 h-3 w-3" />
						</Button>
					</div>
				</Card.Header>
				<Card.Content class="p-0">
					<div class="overflow-x-auto">
						<table class="table-card-mobile w-full">
							<thead>
								<tr class="border-b bg-muted/30">
									<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Application</th>
									<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground hide-mobile">Model</th>
									<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Status</th>
									<th class="px-4 py-2.5 text-left text-xs font-medium text-muted-foreground">Created</th>
								</tr>
							</thead>
							<tbody class="divide-y">
								{#each recentApps as app (app.name)}
									<tr class="transition-colors hover:bg-muted/30">
										<td class="px-4 py-2.5" data-label="Application">
											<span class="text-sm font-medium">{app.name}</span>
										</td>
										<td class="px-4 py-2.5 hide-mobile" data-label="Model">
											<span class="text-sm text-muted-foreground">{app.model}</span>
										</td>
										<td class="px-4 py-2.5" data-label="Status">
											<span class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium {statusColors[app.status]}">
												{app.status}
											</span>
										</td>
										<td class="px-4 py-2.5" data-label="Created">
											<span class="text-xs text-muted-foreground">{app.created}</span>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</Card.Content>
			</Card.Root>
		</div>

		<!-- Right Column -->
		<div class="space-y-6 lg:col-span-4">
			<!-- System Administration -->
			<Card.Root>
				<Card.Header>
					<div class="flex items-center gap-2">
						<Settings class="h-4 w-4 text-muted-foreground" />
						<Card.Title>System Administration</Card.Title>
					</div>
				</Card.Header>
				<Card.Content>
					<div class="grid grid-cols-2 gap-2">
						{#each adminActions as action, i (action.label)}
							<Button
								variant="outline"
								size="sm"
								class="{i === adminActions.length - 1 ? 'col-span-2' : ''} justify-start"
								disabled
							>
								<action.icon class="mr-2 h-3.5 w-3.5 {action.color}" />
								{action.label}
							</Button>
						{/each}
					</div>
				</Card.Content>
			</Card.Root>

			<!-- Activity Feed -->
			<Card.Root>
				<Card.Header>
					<div class="flex items-center justify-between">
						<div class="flex items-center gap-2">
							<Clock class="h-4 w-4 text-muted-foreground" />
							<Card.Title>Recent Activity</Card.Title>
						</div>
						<Button variant="ghost" size="icon" class="h-8 w-8" disabled>
							<RefreshCw class="h-3.5 w-3.5" />
						</Button>
					</div>
				</Card.Header>
				<Card.Content>
					<div class="space-y-1">
						{#if liveActivity.length > 0}
							{#each liveActivity as event, i (event.kind + event.id)}
								{@const EvtIcon = event.kind === 'analysis' ? Activity : AppWindow}
								{@const evtColor =
									event.status === 'completed'
										? 'text-emerald-500'
										: event.status === 'failed'
											? 'text-destructive'
											: event.status === 'running'
												? 'text-amber-500'
												: 'text-blue-500'}
								<div class="flex items-start gap-3 rounded-lg px-2 py-2 transition-colors hover:bg-muted/50">
									<div class="mt-0.5">
										<EvtIcon class="h-3.5 w-3.5 {evtColor}" />
									</div>
									<div class="flex-1 min-w-0">
										<p class="text-xs leading-relaxed break-words">
											<span class="capitalize">{event.kind}</span>: {event.title}
											<span class="text-muted-foreground">({event.status})</span>
										</p>
										<p class="text-[11px] text-muted-foreground mt-0.5">{timeAgo(event.created_at)}</p>
									</div>
								</div>
								{#if i < liveActivity.length - 1}
									<Separator />
								{/if}
							{/each}
						{:else}
							{#each activityFeed as event, i (i)}
								<div class="flex items-start gap-3 rounded-lg px-2 py-2 transition-colors hover:bg-muted/50">
									<div class="mt-0.5">
										<event.icon class="h-3.5 w-3.5 {event.color}" />
									</div>
									<div class="flex-1 min-w-0">
										<p class="text-xs leading-relaxed break-words">{event.text}</p>
										<p class="text-[11px] text-muted-foreground mt-0.5">{event.time}</p>
									</div>
								</div>
								{#if i < activityFeed.length - 1}
									<Separator />
								{/if}
							{/each}
						{/if}
					</div>
				</Card.Content>
			</Card.Root>
		</div>
	</div>
</div>
