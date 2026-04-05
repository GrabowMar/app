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
// API Token Management
// ---------------------------------------------------------------------------

export interface ApiTokenInfo {
	key_preview: string;
	created_at: string;
}

export interface ApiTokenCreated {
	key: string;
	created_at: string;
}

export async function getApiToken(): Promise<ApiTokenInfo | null> {
	const res = await apiFetch('/users/me/token/');
	return res.json();
}

export async function getApiTokenSafe(): Promise<ApiTokenInfo | null> {
	try {
		const headers: Record<string, string> = { 'Content-Type': 'application/json' };
		const res = await fetch(`${API_BASE}/users/me/token/`, {
			headers,
			credentials: 'include',
		});
		if (res.status === 404) return null;
		if (res.status === 401) {
			window.location.href = '/auth/login';
			return new Promise<null>(() => {});
		}
		if (!res.ok) throw new Error('Failed to check token');
		return res.json();
	} catch {
		return null;
	}
}

export async function generateApiToken(): Promise<ApiTokenCreated> {
	const res = await apiFetch('/users/me/token/', { method: 'POST' });
	return res.json();
}

export async function revokeApiToken(): Promise<void> {
	await apiFetch('/users/me/token/', { method: 'DELETE' });
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
