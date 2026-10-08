import {
  HealthResponse,
  ReadinessResponse,
  VersionResponse,
  ModerationRequest,
  ModerationResponse,
  BatchModerationRequest,
  BatchModerationResponse,
  ParsedMetrics,
} from '../types';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

class ApiClient {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${BASE_URL}${endpoint}`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000);

    try {
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...(options.headers || {}),
        },
      });

      if (!response.ok) {
        let errorDetails = `HTTP ${response.status} ${response.statusText}`;
        try {
          const body = await response.json();
          if (body.detail) {
            errorDetails = typeof body.detail === 'string' ? body.detail : JSON.stringify(body.detail);
          }
        } catch {
          // ignore parsing error
        }
        throw new Error(errorDetails);
      }

      return await response.json();
    } catch (err: unknown) {
      if (err instanceof Error) {
        if (err.name === 'AbortError') {
          throw new Error('Request timed out after 15 seconds');
        }
        throw err;
      }
      throw new Error('An unknown network error occurred');
    } finally {
      clearTimeout(timeoutId);
    }
  }

  async getHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health');
  }

  async getReadiness(): Promise<ReadinessResponse> {
    return this.request<ReadinessResponse>('/ready');
  }

  async getVersion(): Promise<VersionResponse> {
    return this.request<VersionResponse>('/version');
  }

  async moderateText(payload: ModerationRequest): Promise<ModerationResponse> {
    return this.request<ModerationResponse>('/moderate', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async moderateBatch(payload: BatchModerationRequest): Promise<BatchModerationResponse> {
    return this.request<BatchModerationResponse>('/moderate/batch', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getRawMetrics(): Promise<string> {
    const url = `${BASE_URL}/metrics`;
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to fetch metrics: HTTP ${response.status}`);
    }
    return response.text();
  }

  async getParsedMetrics(): Promise<ParsedMetrics> {
    const raw = await this.getRawMetrics();
    return this.parsePrometheusText(raw);
  }

  private parsePrometheusText(text: string): ParsedMetrics {
    const lines = text.split('\n');
    let totalRequests = 0;
    const requestsPerEndpoint: Record<string, number> = {};
    const decisions = { allow: 0, review: 0, block: 0 };
    const policyCategories: Record<string, number> = {};
    let avgInferenceSeconds = 0;
    let requestDurationSeconds = 0;

    for (const line of lines) {
      if (line.startsWith('#') || !line.trim()) continue;

      // moderation_requests_total{endpoint="/moderate",method="POST",status="200"} 12.0
      if (line.startsWith('moderation_requests_total')) {
        const valMatch = line.match(/\s+([0-9.]+)/);
        const val = valMatch ? parseFloat(valMatch[1]) : 0;
        totalRequests += val;

        const epMatch = line.match(/endpoint="([^"]+)"/);
        if (epMatch) {
          requestsPerEndpoint[epMatch[1]] = (requestsPerEndpoint[epMatch[1]] || 0) + val;
        }
      }

      // moderation_decisions_total{decision="block",label="toxic",policy_category="threat"} 3.0
      if (line.startsWith('moderation_decisions_total')) {
        const valMatch = line.match(/\s+([0-9.]+)/);
        const val = valMatch ? parseFloat(valMatch[1]) : 0;

        const decMatch = line.match(/decision="([^"]+)"/);
        if (decMatch) {
          const dec = decMatch[1];
          if (dec === 'allow') decisions.allow += val;
          else if (dec === 'flag_review') decisions.review += val;
          else if (dec === 'block') decisions.block += val;
        }

        const catMatch = line.match(/policy_category="([^"]+)"/);
        if (catMatch && catMatch[1] !== 'none') {
          const cat = catMatch[1];
          policyCategories[cat] = (policyCategories[cat] || 0) + val;
        }
      }

      // inference_latency_seconds_sum / count
      if (line.startsWith('moderation_inference_duration_seconds_sum')) {
        const match = line.match(/\s+([0-9.]+)/);
        if (match) avgInferenceSeconds = parseFloat(match[1]);
      }
      if (line.startsWith('moderation_request_duration_seconds_sum')) {
        const match = line.match(/\s+([0-9.]+)/);
        if (match) requestDurationSeconds = parseFloat(match[1]);
      }
    }

    return {
      totalRequests,
      requestsPerEndpoint,
      decisions,
      policyCategories,
      avgInferenceSeconds,
      requestDurationSeconds,
    };
  }
}

export const apiClient = new ApiClient();
