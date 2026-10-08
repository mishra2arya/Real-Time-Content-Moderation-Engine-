import { describe, it, expect } from 'vitest';
import { apiClient } from '../src/api/client';

describe('ApiClient Prometheus Metric Parser', () => {
  it('parses total requests and endpoint breakdown correctly', () => {
    const samplePrometheusText = `
# HELP moderation_requests_total Total incoming moderation API requests
# TYPE moderation_requests_total counter
moderation_requests_total{endpoint="/moderate",method="POST",status="200"} 15.0
moderation_requests_total{endpoint="/moderate/batch",method="POST",status="200"} 5.0
# HELP moderation_decisions_total Moderation decisions by outcome and category
# TYPE moderation_decisions_total counter
moderation_decisions_total{decision="allow",label="non_toxic",policy_category="none"} 12.0
moderation_decisions_total{decision="flag_review",label="toxic",policy_category="none"} 3.0
moderation_decisions_total{decision="block",label="toxic",policy_category="threat"} 5.0
    `;

    // Access private parser for deterministic unit testing
    const parsed = (apiClient as any).parsePrometheusText(samplePrometheusText);

    expect(parsed.totalRequests).toBe(20.0);
    expect(parsed.requestsPerEndpoint['/moderate']).toBe(15.0);
    expect(parsed.requestsPerEndpoint['/moderate/batch']).toBe(5.0);
    expect(parsed.decisions.allow).toBe(12.0);
    expect(parsed.decisions.review).toBe(3.0);
    expect(parsed.decisions.block).toBe(5.0);
    expect(parsed.policyCategories['threat']).toBe(5.0);
  });

  it('handles empty or malformed prometheus text gracefully', () => {
    const parsed = (apiClient as any).parsePrometheusText('');
    expect(parsed.totalRequests).toBe(0);
    expect(parsed.decisions.allow).toBe(0);
    expect(parsed.decisions.review).toBe(0);
    expect(parsed.decisions.block).toBe(0);
  });
});
