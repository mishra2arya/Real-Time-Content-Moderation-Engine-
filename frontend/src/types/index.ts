export type ModerationDecision = 'allow' | 'flag_review' | 'block';
export type ContentLabel = 'non_toxic' | 'toxic';
export type PolicyCategory = 'threat' | 'insult' | 'severe_toxicity' | 'identity_attack' | 'toxicity';

export interface ModerationRequest {
  text: string;
  text_id?: string;
  strict?: boolean;
  use_batch_queue?: boolean;
}

export interface ModerationResponse {
  text_id: string | null;
  request_id: string;
  decision: ModerationDecision;
  label: ContentLabel;
  confidence: number;
  policy_category: PolicyCategory | null;
  policy_categories: PolicyCategory[];
  model_version: string;
  inference_ms: number;
  total_latency_ms: number;
}

export interface BatchItem {
  text: string;
  text_id?: string;
}

export interface BatchModerationRequest {
  items: BatchItem[];
  strict?: boolean;
}

export interface BatchModerationResponse {
  results: ModerationResponse[];
  batch_size: number;
  total_latency_ms: number;
}

export interface HealthResponse {
  status: string;
  app_name: string;
  version: string;
  environment: string;
}

export interface ModelInfo {
  model_version: string;
  engine: string;
  execution_provider: string;
  max_sequence_length: number;
  threads: number;
  ready: boolean;
}

export interface SystemTelemetry {
  memory_rss_mb: number;
  cpu_percent: number;
  num_threads: number;
}

export interface ReadinessResponse {
  status: string;
  model_ready: boolean;
  model_info: ModelInfo;
  system: SystemTelemetry;
}

export interface VersionResponse {
  app_name: string;
  app_version: string;
  model_version: string;
  inference_engine: string;
  python_version: string;
  status: string;
}

export interface ParsedMetrics {
  totalRequests: number;
  requestsPerEndpoint: Record<string, number>;
  decisions: {
    allow: number;
    review: number;
    block: number;
  };
  policyCategories: Record<string, number>;
  avgInferenceSeconds: number;
  requestDurationSeconds: number;
}

export interface ModerationEvent {
  id: string;
  timestamp: string;
  text: string;
  decision: ModerationDecision;
  label: ContentLabel;
  confidence: number;
  category: string | null;
  latencyMs: number;
  model: string;
}
