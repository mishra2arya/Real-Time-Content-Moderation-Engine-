# How It Works — End-to-End Execution Flow

This walkthrough explains how an incoming message is processed from network ingress to the final policy response.

---

## 1. Request Lifecycle Step-by-Step

```text
Step 1: Network Ingress & Request Validation
  │   Client sends HTTP POST to /moderate with JSON payload: {"text": "...", "text_id": "..."}
  │   FastAPI validates input length (1 to 10,000 characters) via Pydantic v2 schemas.
  ▼
Step 2: Context Middleware & Distributed Tracing
  │   Generates or extracts 'X-Request-ID' header and binds it to request state.
  │   Initializes performance timer.
  ▼
Step 3: Text Normalization & Sanitization
  │   Normalizes Unicode NFKD representation.
  │   Removes zero-width and invisible control characters.
  │   Strips HTML tags (<p>, <div>) and resolves HTML entities (&amp; -> &).
  │   Collapses excessive character repetitions (e.g. 'stuuupid' -> 'stuupid').
  ▼
Step 4: Tokenization & Tensor Preparation
  │   DistilBERT Fast WordPiece Tokenizer encodes text into token IDs.
  │   Generates int64 numpy arrays for 'input_ids' and 'attention_mask'.
  ▼
Step 5: Optimized ONNX Inference Execution
  │   Submits tensors to ONNX Runtime InferenceSession.
  │   C++ execution provider computes parallel attention and classification heads.
  │   Returns 2-dimensional raw output logits: [score_non_toxic, score_toxic].
  ▼
Step 6: Policy Engine & Threshold Evaluation
  │   Applies numerically stable softmax: p(toxic) = exp(s_toxic) / sum(exp(s)).
  │   Compares against thresholds:
  │     - If p(toxic) >= 0.50 (or 0.35 in strict mode) -> Decision: "block", Label: "toxic"
  │     - Else if p(toxic) >= 0.40 -> Decision: "flag_review", Label: "toxic"
  │     - Else -> Decision: "allow", Label: "non_toxic"
  │   Evaluates violation categories (e.g. threats, insults, severe toxicity).
  ▼
Step 7: Telemetry & Structured Logging
  │   Records Prometheus histogram observations for request latency and inference time.
  │   Emits structured JSON log with request_id, decision, confidence, and latency.
  ▼
Step 8: Response Serialization
      Returns structured JSON response payload to client.
```

---

## 2. Policy Decisions & Status Codes

| Decision | Meaning | Action Taken |
|---|---|---|
| `allow` | Safe content; no policy breach detected. | Display to users immediately. |
| `block` | High confidence policy violation. | Block display; hide from platform. |
| `flag_review` | Borderline toxicity score ($0.40 \le p < 0.50$). | Queue for human or secondary review. |
