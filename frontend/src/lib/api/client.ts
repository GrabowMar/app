const ALLAUTH_BASE = '/_allauth/browser/v1';
const API_BASE = '/api';

export interface ApiUser {
	email: string;
	name: string;
	url: string;
}

async function allauthFetch(path: string, options: RequestInit = {}): Promise<Response> {
	const headers: Record<string, string> = {
		'Content-Type': 'application/json',
		...(options.headers as Record<string, string>),
	};
	const method = (options.method || 'GET').toUpperCase();
	if (method !== 'GET' && method !== 'HEAD') {
		headers['X-CSRFToken'] = getCsrfToken();
	}
	const res = await fetch(`${ALLAUTH_BASE}${path}`, {
		...options,
		headers,
		credentials: 'include',
	});
	return res;
}

function getCsrfToken(): string {
	const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]*)/);
	return match ? decodeURIComponent(match[1]) : '';
}

async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
	const headers: Record<string, string> = {
		'Content-Type': 'application/json',
		...(options.headers as Record<string, string>),
	};
	const method = (options.method || 'GET').toUpperCase();
	if (method !== 'GET' && method !== 'HEAD') {
		headers['X-CSRFToken'] = getCsrfToken();
	}
	const res = await fetch(`${API_BASE}${path}`, {
		...options,
		headers,
		credentials: 'include',
	});
	if (!res.ok) {
		if (res.status === 401) {
			window.location.href = '/auth/login';
			return new Promise<Response>(() => {});
		}
		const body = await res.json().catch(() => ({}));
		throw body;
	}
	return res;
}

export async function authenticate2FA(code: string): Promise<void> {
	const res = await allauthFetch('/auth/2fa/authenticate', {
		method: 'POST',
		body: JSON.stringify({ code }),
	});
	if (!res.ok) {
		const body = await res.json().catch(() => ({}));
		throw body;
	}
}

export async function verifyEmail(key: string): Promise<void> {
	const res = await allauthFetch('/auth/email/verify', {
		method: 'POST',
		body: JSON.stringify({ key }),
	});
	if (!res.ok) {
		const body = await res.json().catch(() => ({}));
		throw body;
	}
}

export async function requestPasswordReset(email: string): Promise<void> {
	const res = await allauthFetch('/auth/password/request', {
		method: 'POST',
		body: JSON.stringify({ email }),
	});
	if (!res.ok) {
		const body = await res.json().catch(() => ({}));
		throw body;
	}
}

export async function resetPassword(key: string, password: string): Promise<void> {
	const res = await allauthFetch('/auth/password/reset', {
		method: 'POST',
		body: JSON.stringify({ key, password }),
	});
	if (!res.ok) {
		const body = await res.json().catch(() => ({}));
		throw body;
	}
}

export async function getMe(): Promise<ApiUser> {
	const res = await apiFetch('/users/me/');
	return res.json();
}

export async function getUser(pk: number): Promise<ApiUser> {
	const res = await apiFetch(`/users/${pk}/`);
	return res.json();
}

export async function updateMe(data: { name: string }): Promise<ApiUser> {
	const res = await apiFetch('/users/me/', {
		method: 'PATCH',
		body: JSON.stringify(data),
	});
	return res.json();
}

export async function changePassword(data: {
	current_password: string;
	new_password: string;
}): Promise<void> {
	const res = await allauthFetch('/account/password/change', {
		method: 'POST',
		body: JSON.stringify(data),
	});
	if (!res.ok) {
		const body = await res.json().catch(() => ({}));
		throw body;
	}
}

export async function logout(): Promise<void> {
	const res = await allauthFetch('/auth/session', {
		method: 'DELETE',
	});
	if (!res.ok) {
		const body = await res.json().catch(() => ({}));
		throw body;
	}
}

// ---------------------------------------------------------------------------
// API Token Management (multi-token)
// ---------------------------------------------------------------------------

export interface ApiTokenSummary {
	id: string;
	name: string;
	prefix: string;
	scopes: string[];
	expires_at: string | null;
	last_used_at: string | null;
	last_used_ip: string;
	revoked_at: string | null;
	created_at: string;
}

export interface ApiTokenCreatedResponse extends ApiTokenSummary {
	token: string;
}

export interface CreateApiTokenPayload {
	name: string;
	scopes?: string[];
	expires_at?: string | null;
}

export async function listApiTokens(): Promise<ApiTokenSummary[]> {
	const res = await apiFetch('/tokens/');
	return res.json();
}

export async function createApiToken(payload: CreateApiTokenPayload): Promise<ApiTokenCreatedResponse> {
	const res = await apiFetch('/tokens/', {
		method: 'POST',
		body: JSON.stringify(payload),
	});
	return res.json();
}

export async function revokeApiToken(id: string): Promise<void> {
	await apiFetch(`/tokens/${id}/`, { method: 'DELETE' });
}

// ---------------------------------------------------------------------------
// LLM Models
// ---------------------------------------------------------------------------

export interface LLMModelSummary {
	id: number;
	model_id: string;
	canonical_slug: string;
	provider: string;
	model_name: string;
	description: string;
	is_free: boolean;
	context_window: number;
	max_output_tokens: number;
	context_window_display: string;
	input_price_per_million: number;
	output_price_per_million: number;
	capabilities: string[];
	cost_efficiency: number;
	supports_vision: boolean;
	supports_function_calling: boolean;
	supports_streaming: boolean;
	supports_json_mode: boolean;
}

export interface LLMModelDetail extends LLMModelSummary {
	description: string;
	max_output_tokens: number;
	input_price_per_token: number;
	output_price_per_token: number;
	metadata: Record<string, unknown>;
	capabilities_json: Record<string, unknown>;
	created_at: string;
	updated_at: string;
}

export interface PaginatedModels {
	items: LLMModelSummary[];
	total: number;
	page: number;
	per_page: number;
	pages: number;
}

export interface ModelsStats {
	total: number;
	providers: number;
	free: number;
	avg_input_price: number;
	avg_output_price: number;
}

export interface SyncResult {
	fetched: number;
	upserted: number;
}

export async function getModels(params: {
	page?: number;
	per_page?: number;
	search?: string;
	provider?: string;
	capability?: string;
	free_only?: boolean;
	sort_by?: string;
	sort_dir?: 'asc' | 'desc';
	price_range?: string;
	context_range?: string;
} = {}): Promise<PaginatedModels> {
	const q = new URLSearchParams();
	if (params.page) q.set('page', String(params.page));
	if (params.per_page) q.set('per_page', String(params.per_page));
	if (params.search) q.set('search', params.search);
	if (params.provider) q.set('provider', params.provider);
	if (params.capability) q.set('capability', params.capability);
	if (params.free_only) q.set('free_only', 'true');
	if (params.sort_by) q.set('sort_by', params.sort_by);
	if (params.sort_dir) q.set('sort_dir', params.sort_dir);
	if (params.price_range) q.set('price_range', params.price_range);
	if (params.context_range) q.set('context_range', params.context_range);
	const qs = q.toString();
	const res = await apiFetch(`/models/${qs ? '?' + qs : ''}`);
	return res.json();
}

export async function getModel(slug: string): Promise<LLMModelDetail> {
	const res = await apiFetch(`/models/detail/${slug}/`);
	return res.json();
}

export async function getModelsStats(): Promise<ModelsStats> {
	const res = await apiFetch('/models/stats/');
	return res.json();
}

export async function getProviders(): Promise<string[]> {
	const res = await apiFetch('/models/providers/');
	return res.json();
}

export async function syncModelsFromOpenRouter(): Promise<SyncResult> {
	const res = await apiFetch('/models/sync/', { method: 'POST' });
	return res.json();
}

export async function deleteModel(slug: string): Promise<void> {
	await apiFetch(`/models/detail/${slug}/`, { method: 'DELETE' });
}

export async function getRelatedModels(slug: string, limit = 10): Promise<LLMModelSummary[]> {
	const res = await apiFetch(`/models/detail/${slug}/related/?limit=${limit}`);
	return res.json();
}

// ---------------------------------------------------------------------------
// Generation
// ---------------------------------------------------------------------------

export interface ScaffoldingTemplate {
	id: number;
	name: string;
	slug: string;
	description: string;
	tech_stack: Record<string, string>;
	substitution_vars: string[];
	is_default: boolean;
	created_at: string;
	updated_at: string;
}

export interface AppRequirementTemplate {
	id: number;
	name: string;
	slug: string;
	category: string;
	description: string;
	backend_requirements: string[];
	frontend_requirements: string[];
	admin_requirements: string[];
	api_endpoints: any[];
	data_model: Record<string, any>;
	is_default: boolean;
	created_at: string;
	updated_at: string;
}

export interface PromptTemplate {
	id: number;
	name: string;
	slug: string;
	stage: string;
	role: string;
	content: string;
	description: string;
	is_default: boolean;
	version: number;
	created_at: string;
	updated_at: string;
}

export interface GenerationJob {
	id: string;
	mode: string;
	status: string;
	model_name: string | null;
	model_id_str: string | null;
	batch_id: string | null;
	batch_name: string | null;
	template_name: string | null;
	scaffolding_name: string | null;
	created_by_email: string | null;
	temperature: number;
	max_tokens: number;
	custom_system_prompt: string;
	custom_user_prompt: string;
	copilot_description: string;
	copilot_max_iterations: number;
	copilot_current_iteration: number;
	copilot_use_open_source: boolean;
	app_directory: string;
	started_at: string | null;
	completed_at: string | null;
	duration_seconds: number | null;
	error_message: string;
	result_data: Record<string, any>;
	metrics: Record<string, any>;
	created_at: string;
	updated_at: string;
}

export interface GenerationJobList {
	id: string;
	mode: string;
	status: string;
	model_name: string | null;
	model_id_str: string | null;
	template_name: string | null;
	scaffolding_name: string | null;
	started_at: string | null;
	completed_at: string | null;
	duration_seconds: number | null;
	error_message: string;
	created_at: string;
}

export interface PaginatedJobs {
	items: GenerationJobList[];
	total: number;
	page: number;
	per_page: number;
	pages: number;
}

export interface GenerationArtifact {
	id: number;
	stage: string;
	request_payload: Record<string, any>;
	response_payload: Record<string, any>;
	prompt_tokens: number;
	completion_tokens: number;
	total_cost: number;
	created_at: string;
}

export interface CopilotIteration {
	id: number;
	iteration_number: number;
	action: string;
	llm_request: Record<string, any>;
	llm_response: Record<string, any>;
	build_output: string;
	build_success: boolean;
	errors_detected: string[];
	fix_applied: string;
	created_at: string;
}

export interface GenerationBatch {
	id: string;
	name: string;
	mode: string;
	status: string;
	total_jobs: number;
	completed_jobs: number;
	failed_jobs: number;
	created_at: string;
	updated_at: string;
}

export interface BatchCreateResponse {
	batch_id: string;
	job_count: number;
	status: string;
}

export async function getScaffoldingTemplates(): Promise<ScaffoldingTemplate[]> {
	const res = await apiFetch('/generation/scaffolding-templates/');
	return res.json();
}

export async function getAppTemplates(): Promise<AppRequirementTemplate[]> {
	const res = await apiFetch('/generation/app-templates/');
	return res.json();
}

export async function getPromptTemplates(stage?: string, role?: string): Promise<PromptTemplate[]> {
	const params = new URLSearchParams();
	if (stage) params.set('stage', stage);
	if (role) params.set('role', role);
	const qs = params.toString();
	const res = await apiFetch(`/generation/prompt-templates/${qs ? '?' + qs : ''}`);
	return res.json();
}

export async function createCustomJob(data: {
	model_id: number;
	system_prompt: string;
	user_prompt: string;
	temperature?: number;
	max_tokens?: number;
}): Promise<GenerationJob> {
	const res = await apiFetch('/generation/jobs/custom/', {
		method: 'POST',
		body: JSON.stringify(data),
	});
	return res.json();
}

export async function createScaffoldingBatch(data: {
	scaffolding_template_id: number;
	app_requirement_ids: number[];
	model_ids: number[];
	temperature?: number;
	max_tokens?: number;
}): Promise<BatchCreateResponse> {
	const res = await apiFetch('/generation/jobs/scaffolding/', {
		method: 'POST',
		body: JSON.stringify(data),
	});
	return res.json();
}

export async function createCopilotJob(data: {
	description: string;
	model_id?: number;
	scaffolding_template_id?: number;
	max_iterations?: number;
	use_open_source?: boolean;
}): Promise<GenerationJob> {
	const res = await apiFetch('/generation/jobs/copilot/', {
		method: 'POST',
		body: JSON.stringify(data),
	});
	return res.json();
}

export async function getGenerationJobs(params?: {
	page?: number;
	per_page?: number;
	mode?: string;
	status?: string;
}): Promise<PaginatedJobs> {
	const q = new URLSearchParams();
	if (params?.page) q.set('page', String(params.page));
	if (params?.per_page) q.set('per_page', String(params.per_page));
	if (params?.mode) q.set('mode', params.mode);
	if (params?.status) q.set('status', params.status);
	const qs = q.toString();
	const res = await apiFetch(`/generation/jobs/${qs ? '?' + qs : ''}`);
	return res.json();
}

export async function getGenerationJob(id: string): Promise<GenerationJob> {
	const res = await apiFetch(`/generation/jobs/${id}/`);
	return res.json();
}

export async function cancelGenerationJob(id: string): Promise<{ success: boolean }> {
	const res = await apiFetch(`/generation/jobs/${id}/cancel/`, { method: 'POST' });
	return res.json();
}

export async function deleteGenerationJob(id: string): Promise<{ success: boolean }> {
	const res = await apiFetch(`/generation/jobs/${id}/`, { method: 'DELETE' });
	return res.json();
}

export async function retryGenerationJob(id: string): Promise<GenerationJob> {
	const res = await apiFetch(`/generation/jobs/${id}/retry/`, { method: 'POST' });
	return res.json();
}

export async function getJobArtifacts(id: string): Promise<GenerationArtifact[]> {
	const res = await apiFetch(`/generation/jobs/${id}/artifacts/`);
	return res.json();
}

export async function getCopilotIterations(id: string): Promise<CopilotIteration[]> {
	const res = await apiFetch(`/generation/jobs/${id}/copilot-iterations/`);
	return res.json();
}

export async function exportGenerationJob(id: string): Promise<Record<string, any>> {
	const res = await apiFetch(`/generation/jobs/${id}/export/`);
	return res.json();
}

export async function getGenerationBatches(): Promise<GenerationBatch[]> {
	const res = await apiFetch('/generation/batches/');
	return res.json();
}

export async function getGenerationBatch(id: string): Promise<GenerationBatch> {
	const res = await apiFetch(`/generation/batches/${id}/`);
	return res.json();
}

// ── Template CRUD ──────────────────────────────────────────────────

export async function createScaffoldingTemplate(data: {
	name: string;
	slug: string;
	description?: string;
	tech_stack?: Record<string, string>;
	substitution_vars?: string[];
}): Promise<ScaffoldingTemplate> {
	const res = await apiFetch('/generation/scaffolding-templates/', {
		method: 'POST',
		body: JSON.stringify(data),
	});
	return res.json();
}

export async function updateScaffoldingTemplate(
	slug: string,
	data: Partial<{
		name: string;
		description: string;
		tech_stack: Record<string, string>;
		substitution_vars: string[];
	}>
): Promise<ScaffoldingTemplate> {
	const res = await apiFetch(`/generation/scaffolding-templates/${slug}/`, {
		method: 'PUT',
		body: JSON.stringify(data),
	});
	return res.json();
}

export async function deleteScaffoldingTemplate(slug: string): Promise<void> {
	await apiFetch(`/generation/scaffolding-templates/${slug}/`, { method: 'DELETE' });
}

export async function createAppTemplate(data: {
	name: string;
	slug: string;
	description?: string;
	backend_requirements?: string[];
	frontend_requirements?: string[];
	admin_requirements?: string[];
	api_endpoints?: Record<string, unknown>;
	data_model?: Record<string, unknown>;
}): Promise<AppRequirementTemplate> {
	const res = await apiFetch('/generation/app-templates/', {
		method: 'POST',
		body: JSON.stringify(data),
	});
	return res.json();
}

export async function updateAppTemplate(
	slug: string,
	data: Partial<{
		name: string;
		description: string;
		backend_requirements: string[];
		frontend_requirements: string[];
		admin_requirements: string[];
		api_endpoints: Record<string, unknown>;
		data_model: Record<string, unknown>;
	}>
): Promise<AppRequirementTemplate> {
	const res = await apiFetch(`/generation/app-templates/${slug}/`, {
		method: 'PUT',
		body: JSON.stringify(data),
	});
	return res.json();
}

export async function deleteAppTemplate(slug: string): Promise<void> {
	await apiFetch(`/generation/app-templates/${slug}/`, { method: 'DELETE' });
}

export async function createPromptTemplate(data: {
	name: string;
	slug: string;
	stage: string;
	role: string;
	content: string;
}): Promise<PromptTemplate> {
	const res = await apiFetch('/generation/prompt-templates/', {
		method: 'POST',
		body: JSON.stringify(data),
	});
	return res.json();
}

export async function updatePromptTemplate(
	slug: string,
	data: Partial<{
		name: string;
		stage: string;
		role: string;
		content: string;
	}>
): Promise<PromptTemplate> {
	const res = await apiFetch(`/generation/prompt-templates/${slug}/`, {
		method: 'PUT',
		body: JSON.stringify(data),
	});
	return res.json();
}

export async function deletePromptTemplate(slug: string): Promise<void> {
	await apiFetch(`/generation/prompt-templates/${slug}/`, { method: 'DELETE' });
}

// ── Analysis types ────────────────────────────────────

export interface AnalysisTask {
	id: string;
	name: string;
	status: string;
	generation_job_id: string | null;
	source_code: Record<string, string>;
	configuration: Record<string, any>;
	results_summary: Record<string, any>;
	generation_job_name: string | null;
	created_by_email: string;
	results_count: number;
	findings_count: number;
	started_at: string | null;
	completed_at: string | null;
	duration_seconds: number | null;
	error_message: string;
	created_at: string;
	updated_at: string;
}

export interface AnalysisTaskList {
	id: string;
	name: string;
	status: string;
	created_at: string;
	updated_at: string;
	generation_job_id: string | null;
	created_by_email: string;
	results_summary: Record<string, any>;
	started_at: string | null;
	completed_at: string | null;
	duration_seconds: number | null;
}

export interface PaginatedAnalysisTasks {
	items: AnalysisTaskList[];
	total: number;
	page: number;
	per_page: number;
	pages: number;
}

export interface AnalysisResult {
	id: number;
	task_id: string;
	analyzer_type: string;
	analyzer_name: string;
	status: string;
	raw_output: Record<string, any>;
	summary: Record<string, any>;
	error_message: string;
	started_at: string | null;
	completed_at: string | null;
	duration_seconds: number | null;
	findings_count: number;
	finding_summary: Record<string, number>;
	created_at: string;
}

export interface AnalysisFinding {
	id: number;
	result_id: number;
	severity: string;
	category: string;
	confidence: string;
	title: string;
	description: string;
	suggestion: string;
	file_path: string;
	line_number: number | null;
	column_number: number | null;
	code_snippet: string;
	rule_id: string;
	tool_specific_data: Record<string, any>;
	analyzer_name: string;
	created_at: string;
}

export interface PaginatedFindings {
	items: AnalysisFinding[];
	total: number;
	page: number;
	per_page: number;
	pages: number;
}

export interface AnalyzerInfo {
	name: string;
	type: string;
	display_name: string;
	description: string;
	available: boolean;
	availability_message: string;
	default_config: Record<string, any>;
}

export interface AnalysisStats {
	total_tasks: number;
	completed_tasks: number;
	failed_tasks: number;
	running_tasks: number;
	total_findings: number;
	findings_by_severity: Record<string, number>;
	findings_by_category: Record<string, number>;
	most_common_issues: Array<{ title: string; count: number }>;
}

// ── Analysis ──────────────────────────────────────────

export async function createAnalysisTask(data: {
	name?: string;
	generation_job_id?: string;
	source_code?: Record<string, string>;
	analyzers: string[];
	settings?: Record<string, any>;
	auto_start?: boolean;
}): Promise<AnalysisTask> {
	const res = await apiFetch('/analysis/tasks/', {
		method: 'POST',
		body: JSON.stringify(data),
	});
	return res.json();
}

export async function getAnalysisTasks(params?: {
	page?: number;
	per_page?: number;
	status?: string;
	search?: string;
}): Promise<PaginatedAnalysisTasks> {
	const searchParams = new URLSearchParams();
	if (params?.page) searchParams.set('page', String(params.page));
	if (params?.per_page) searchParams.set('per_page', String(params.per_page));
	if (params?.status) searchParams.set('status', params.status);
	if (params?.search) searchParams.set('search', params.search);
	const qs = searchParams.toString();
	const res = await apiFetch(`/analysis/tasks/${qs ? '?' + qs : ''}`);
	return res.json();
}

export async function getAnalysisTask(taskId: string): Promise<AnalysisTask> {
	const res = await apiFetch(`/analysis/tasks/${taskId}/`);
	return res.json();
}

export async function cancelAnalysisTask(
	taskId: string,
): Promise<{ success: boolean; status: string; message?: string }> {
	const res = await apiFetch(`/analysis/tasks/${taskId}/cancel/`, { method: 'POST' });
	return res.json();
}

export async function deleteAnalysisTask(taskId: string): Promise<{ success: boolean }> {
	const res = await apiFetch(`/analysis/tasks/${taskId}/`, { method: 'DELETE' });
	return res.json();
}

export async function getAnalysisResults(taskId: string): Promise<AnalysisResult[]> {
	const res = await apiFetch(`/analysis/tasks/${taskId}/results/`);
	return res.json();
}

export async function getAnalysisResult(taskId: string, resultId: number): Promise<AnalysisResult> {
	const res = await apiFetch(`/analysis/tasks/${taskId}/results/${resultId}/`);
	return res.json();
}

export async function getAnalysisFindings(
	taskId: string,
	params?: {
		page?: number;
		per_page?: number;
		severity?: string;
		category?: string;
		analyzer?: string;
	},
): Promise<PaginatedFindings> {
	const searchParams = new URLSearchParams();
	if (params?.page) searchParams.set('page', String(params.page));
	if (params?.per_page) searchParams.set('per_page', String(params.per_page));
	if (params?.severity) searchParams.set('severity', params.severity);
	if (params?.category) searchParams.set('category', params.category);
	if (params?.analyzer) searchParams.set('analyzer', params.analyzer);
	const qs = searchParams.toString();
	const res = await apiFetch(`/analysis/tasks/${taskId}/findings/${qs ? '?' + qs : ''}`);
	return res.json();
}

export async function getAnalyzers(): Promise<AnalyzerInfo[]> {
	const res = await apiFetch('/analysis/analyzers/');
	return res.json();
}

export async function getAnalysisStats(): Promise<AnalysisStats> {
	const res = await apiFetch('/analysis/stats/');
	return res.json();
}

// ---------------------------------------------------------------------------
// Statistics (cross-app aggregates)
// ---------------------------------------------------------------------------

export interface StatisticsOverview {
	total_apps: number;
	apps_completed: number;
	apps_failed: number;
	apps_running: number;
	apps_success_rate: number;
	total_analyses: number;
	analyses_completed: number;
	analyses_failed: number;
	analyses_running: number;
	analyses_success_rate: number;
	total_findings: number;
	avg_findings_per_app: number;
	models_in_use: number;
	avg_analysis_seconds: number;
}

export interface SeverityBucket {
	severity: string;
	count: number;
	percent: number;
}

export interface SeverityDistribution {
	total: number;
	distribution: SeverityBucket[];
}

export interface TrendPoint {
	date: string;
	total: number;
	completed: number;
	failed: number;
}

export interface AnalysisTrends {
	days: number;
	total: number;
	series: TrendPoint[];
}

export interface ModelComparisonRow {
	model_id: string;
	name: string;
	provider: string;
	apps: number;
	apps_completed: number;
	success_rate: number;
	avg_duration_seconds: number;
	cost_efficiency: number;
	security: number;
	quality: number;
	performance: number;
	mss: number;
	findings: { critical: number; high: number; medium: number; low: number; info: number };
}

export interface ToolEffectivenessRow {
	name: string;
	type: string;
	scans: number;
	findings: number;
	avg_per_scan: number;
	top_rule: string;
}

export interface TopFindingRow {
	title: string;
	severity: string;
	rule_id: string;
	count: number;
}

export interface RecentActivityItem {
	kind: string;
	id: string;
	title: string;
	status: string;
	created_at: string;
}

export interface CodeGenerationStats {
	total_apps: number;
	completed: number;
	failed: number;
	running: number;
	success_rate: number;
	avg_duration_seconds: number;
	total_tokens: number;
	total_cost_usd: number;
	total_lines_of_code: number;
	by_provider: { provider: string; apps: number }[];
}

export interface AnalyzerHealth {
	total: number;
	online: number;
	offline: number;
	analyzers: {
		name: string;
		type: string;
		display_name: string;
		available: boolean;
		availability_message: string;
	}[];
}

export interface StatisticsDashboard {
	overview: StatisticsOverview;
	severity: SeverityDistribution;
	trends: AnalysisTrends;
	models: ModelComparisonRow[];
	tools: ToolEffectivenessRow[];
	top_findings: TopFindingRow[];
	code_generation: CodeGenerationStats;
	analyzer_health: AnalyzerHealth;
	recent_activity: RecentActivityItem[];
}

export async function getStatisticsDashboard(): Promise<StatisticsDashboard> {
	const res = await apiFetch('/statistics/dashboard/');
	return res.json();
}

export async function getStatisticsOverview(): Promise<StatisticsOverview> {
	const res = await apiFetch('/statistics/overview/');
	return res.json();
}

export async function getStatisticsSeverity(): Promise<SeverityDistribution> {
	const res = await apiFetch('/statistics/severity/');
	return res.json();
}

export async function getStatisticsTrends(days = 14): Promise<AnalysisTrends> {
	const res = await apiFetch(`/statistics/trends/?days=${days}`);
	return res.json();
}

export async function getStatisticsModels(limit = 25): Promise<ModelComparisonRow[]> {
	const res = await apiFetch(`/statistics/models/?limit=${limit}`);
	return res.json();
}

export async function getStatisticsTools(): Promise<ToolEffectivenessRow[]> {
	const res = await apiFetch('/statistics/tools/');
	return res.json();
}

export async function getStatisticsTopFindings(limit = 10): Promise<TopFindingRow[]> {
	const res = await apiFetch(`/statistics/top-findings/?limit=${limit}`);
	return res.json();
}

export async function getStatisticsRecentActivity(limit = 20): Promise<RecentActivityItem[]> {
	const res = await apiFetch(`/statistics/recent-activity/?limit=${limit}`);
	return res.json();
}

export async function getStatisticsCodeGeneration(): Promise<CodeGenerationStats> {
	const res = await apiFetch('/statistics/code-generation/');
	return res.json();
}

export async function getStatisticsAnalyzerHealth(): Promise<AnalyzerHealth> {
	const res = await apiFetch('/statistics/analyzer-health/');
	return res.json();
}

// ---------------------------------------------------------------------------
// Rankings
// ---------------------------------------------------------------------------

export interface RankingFindings {
critical: number;
high: number;
medium: number;
low: number;
info: number;
}

export interface RankingRow {
model_id: string;
model_name: string;
provider: string;
is_free: boolean;
context_length: number | null;
price_per_million_input: number | null;
price_per_million_output: number | null;
apps: number;
apps_completed: number;
avg_duration: number;
findings: RankingFindings;
benchmark_score: number;
cost_efficiency_score: number;
accessibility_score: number;
adoption_score: number;
mss_score: number;
composite_score: number;
[key: string]: unknown;
}

export interface RankingsPagination {
page: number;
per_page: number;
total: number;
pages: number;
}

export interface RankingsStatistics {
total_models: number;
with_benchmarks: number;
free_models: number;
avg_mss: number;
unique_providers: number;
}

export interface RankingsResponse {
rankings: RankingRow[];
pagination: RankingsPagination;
statistics: RankingsStatistics;
filters_applied: Record<string, unknown>;
}

export interface RankingsTopResponse {
models: RankingRow[];
count: number;
weights: Record<string, number> | null;
}

export interface RankingsStatus {
total_models: number;
models_with_benchmarks: number;
total_benchmark_rows: number;
benchmarks: Record<string, number>;
}

export interface RankingsListParams {
page?: number;
per_page?: number;
sort_by?: string;
sort_dir?: 'asc' | 'desc';
search?: string;
provider?: string;
max_price?: number;
min_context?: number;
min_composite?: number;
include_free?: boolean;
has_benchmarks?: boolean;
}

function _qs(params: Record<string, unknown>): string {
const usp = new URLSearchParams();
for (const [k, v] of Object.entries(params)) {
if (v === undefined || v === null || v === '') continue;
usp.set(k, String(v));
}
const s = usp.toString();
return s ? `?${s}` : '';
}

export async function getRankings(params: RankingsListParams = {}): Promise<RankingsResponse> {
const res = await apiFetch(`/rankings/${_qs(params as Record<string, unknown>)}`);
return res.json();
}

export async function getTopModels(count = 10): Promise<RankingsTopResponse> {
const res = await apiFetch(`/rankings/top/?count=${count}`);
return res.json();
}

export async function getRankingsStatus(): Promise<RankingsStatus> {
const res = await apiFetch('/rankings/status/');
return res.json();
}

export async function refreshRankings(): Promise<RankingsStatus> {
const res = await apiFetch('/rankings/refresh/', { method: 'POST' });
return res.json();
}

export function exportRankingsUrl(): string {
return '/api/rankings/export/';
}

// ============================================================
// Reports
// ============================================================

export type ReportType =
        | 'model_analysis'
        | 'template_comparison'
        | 'tool_analysis'
        | 'generation_analytics'
        | 'comprehensive';

export type ReportStatus = 'pending' | 'generating' | 'completed' | 'failed';

export interface ReportSummary {
        id: string;
        report_id: string;
        report_type: ReportType;
        title: string;
        description: string;
        status: ReportStatus;
        progress_percent: number;
        summary: Record<string, unknown>;
        error_message: string;
        created_at: string;
        completed_at: string | null;
        expires_at: string | null;
        generation_job_id: string | null;
        analysis_task_id: string | null;
}

export interface ReportDetail extends ReportSummary {
        config: Record<string, unknown>;
        report_data: Record<string, unknown>;
}

export interface ReportListResponse {
        reports: ReportSummary[];
        pagination: { total: number; limit: number; offset: number };
}

export interface GenerateReportPayload {
        report_type: ReportType;
        config?: Record<string, unknown>;
        title?: string;
        description?: string;
        expires_in_days?: number | null;
}

export interface ReportListParams {
        report_type?: ReportType;
        status?: ReportStatus;
        limit?: number;
        offset?: number;
}

export async function getReports(params: ReportListParams = {}): Promise<ReportListResponse> {
        const query = new URLSearchParams();
        if (params.report_type) query.set('report_type', params.report_type);
        if (params.status) query.set('status', params.status);
        if (params.limit !== undefined) query.set('limit', String(params.limit));
        if (params.offset !== undefined) query.set('offset', String(params.offset));
        const qs = query.toString();
        const res = await apiFetch(`/reports/${qs ? `?${qs}` : ''}`);
        return res.json();
}

export async function generateReport(payload: GenerateReportPayload): Promise<ReportSummary> {
        const res = await apiFetch('/reports/generate/', {
                method: 'POST',
                body: JSON.stringify({ config: {}, ...payload })
        });
        return res.json();
}

export async function getReport(reportId: string): Promise<ReportDetail> {
        const res = await apiFetch(`/reports/${reportId}/`);
        return res.json();
}

export async function getReportData(reportId: string): Promise<{
        report_id: string;
        report_type: ReportType;
        title: string;
        status: ReportStatus;
        progress: number;
        data: Record<string, unknown>;
}> {
        const res = await apiFetch(`/reports/${reportId}/data/`);
        return res.json();
}

export async function deleteReport(reportId: string): Promise<{ success: boolean; message: string }> {
        const res = await apiFetch(`/reports/${reportId}/`, { method: 'DELETE' });
        return res.json();
}

// ---------------------------------------------------------------------------
// Runtime — Docker container management
// ---------------------------------------------------------------------------

export type ContainerStatus = 'pending' | 'building' | 'running' | 'stopped' | 'failed' | 'removed';
export type ActionType = 'build' | 'start' | 'stop' | 'restart' | 'remove';
export type ActionStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface ContainerInstance {
	id: string;
	job_id: string | null;
	container_name: string;
	image_tag: string;
	status: ContainerStatus;
	backend_port: number | null;
	frontend_port: number | null;
	error_message: string;
	created_at: string;
	updated_at: string;
}

export interface ContainerAction {
	id: string;
	container_id: string;
	action_type: ActionType;
	status: ActionStatus;
	progress_percent: number;
	log_output: string;
	error_message: string;
	created_at: string;
	updated_at: string;
}

export interface DockerInfo {
	daemon_available: boolean;
	version: string | null;
	containers_running: number | null;
	containers_stopped: number | null;
	images: number | null;
	os: string | null;
}

export interface ContainerHealthResponse {
	container_id: string;
	health: string;
	status: ContainerStatus;
}

export interface PaginatedContainers {
	containers: ContainerInstance[];
	pagination: { total: number; page: number; per_page: number; pages: number };
}

export interface GenericResponse {
	success: boolean;
	message: string;
	action_id: string | null;
}

export async function getContainers(params: {
	page?: number;
	per_page?: number;
	status?: ContainerStatus;
} = {}): Promise<PaginatedContainers> {
	const q = new URLSearchParams();
	if (params.page) q.set('page', String(params.page));
	if (params.per_page) q.set('per_page', String(params.per_page));
	if (params.status) q.set('status', params.status);
	const qs = q.toString();
	const res = await apiFetch(`/runtime/containers/${qs ? '?' + qs : ''}`);
	return res.json();
}

export async function getContainer(id: string): Promise<ContainerInstance> {
	const res = await apiFetch(`/runtime/containers/${id}/`);
	return res.json();
}

export async function startContainer(id: string): Promise<GenericResponse> {
	const res = await apiFetch(`/runtime/containers/${id}/start/`, { method: 'POST' });
	return res.json();
}

export async function stopContainer(id: string): Promise<GenericResponse> {
	const res = await apiFetch(`/runtime/containers/${id}/stop/`, { method: 'POST' });
	return res.json();
}

export async function restartContainer(id: string): Promise<GenericResponse> {
	const res = await apiFetch(`/runtime/containers/${id}/restart/`, { method: 'POST' });
	return res.json();
}

export async function removeContainer(id: string): Promise<GenericResponse> {
	const res = await apiFetch(`/runtime/containers/${id}/remove/`, { method: 'POST' });
	return res.json();
}

export async function getContainerLogs(id: string, tail = 200): Promise<{ logs: string }> {
	const res = await apiFetch(`/runtime/containers/${id}/logs/?tail=${tail}`);
	return res.json();
}

export async function getContainerHealth(id: string): Promise<ContainerHealthResponse> {
	const res = await apiFetch(`/runtime/containers/${id}/health/`);
	return res.json();
}

export async function getContainerActions(id: string): Promise<ContainerAction[]> {
	const res = await apiFetch(`/runtime/actions/?container_id=${id}`);
	return res.json();
}

export async function getAction(actionId: string): Promise<ContainerAction> {
	const res = await apiFetch(`/runtime/actions/${actionId}/`);
	return res.json();
}

export async function buildContainerForJob(jobId: string): Promise<GenericResponse> {
	const res = await apiFetch(`/runtime/jobs/${jobId}/build/`, { method: 'POST' });
	return res.json();
}

export async function getDockerInfo(): Promise<DockerInfo> {
	const res = await apiFetch('/runtime/docker/info/');
	return res.json();
}
