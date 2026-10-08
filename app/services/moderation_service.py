"""Moderation orchestration service coordinating preprocessing, inference, and policy."""

import time
from typing import List, Optional

from app.core.config import get_settings
from app.inference.batching import AsyncBatchingEngine, get_batching_engine
from app.inference.model_manager import ModelManager, get_model_manager
from app.moderation.labels import ModerationDecision
from app.moderation.postprocessing import PolicyEngine
from app.moderation.preprocessing import clean_text


class ModerationResult:
    """Internal moderation outcome representation."""

    def __init__(
        self,
        text_id: Optional[str],
        decision: ModerationDecision,
        label: str,
        confidence: float,
        policy_categories: List[str],
        model_version: str,
        inference_ms: float,
        total_latency_ms: float,
    ):
        self.text_id = text_id
        self.decision = decision
        self.label = label
        self.confidence = confidence
        self.policy_categories = policy_categories
        self.model_version = model_version
        self.inference_ms = inference_ms
        self.total_latency_ms = total_latency_ms


class ModerationService:
    """Service layer coordinating text moderation requests."""

    def __init__(
        self,
        model_manager: Optional[ModelManager] = None,
        batching_engine: Optional[AsyncBatchingEngine] = None,
        policy_engine: Optional[PolicyEngine] = None,
    ):
        settings = get_settings()
        self.model_manager = model_manager or get_model_manager()
        self.batching_engine = batching_engine or get_batching_engine()
        self.policy_engine = policy_engine or PolicyEngine(
            block_threshold=settings.default_toxicity_threshold,
            flag_threshold=settings.flag_review_threshold,
            strict_threshold=settings.strict_toxicity_threshold,
        )

    async def moderate_text(
        self,
        text: str,
        text_id: Optional[str] = None,
        strict: bool = False,
        use_batch_queue: bool = False,
    ) -> ModerationResult:
        """Moderate a single piece of text.

        Args:
            text: Raw input text.
            text_id: Optional tracking identifier.
            strict: If True, uses lower strict threshold.
            use_batch_queue: If True, queues via dynamic micro-batcher.

        Returns:
            ModerationResult with policy decision, category tags, and latency.
        """
        t_start = time.perf_counter()

        # 1. Preprocessing
        cleaned = clean_text(text)

        # Handle empty/whitespace text safely
        if not cleaned:
            total_ms = round((time.perf_counter() - t_start) * 1000.0, 3)
            return ModerationResult(
                text_id=text_id,
                decision=ModerationDecision.ALLOW,
                label="non_toxic",
                confidence=1.0,
                policy_categories=[],
                model_version=self.model_manager.engine.model_version,
                inference_ms=0.0,
                total_latency_ms=total_ms,
            )

        # 2. Inference
        if use_batch_queue:
            logits, inf_ms = await self.batching_engine.submit(cleaned)
        else:
            logits_batch, inf_ms = self.model_manager.engine.predict([cleaned])
            logits = logits_batch[0]

        # 3. Policy Evaluation
        decision, label, confidence, categories = self.policy_engine.evaluate_logits(
            logits=logits,
            text=text,
            strict=strict,
        )

        total_ms = round((time.perf_counter() - t_start) * 1000.0, 3)

        return ModerationResult(
            text_id=text_id,
            decision=decision,
            label=label,
            confidence=confidence,
            policy_categories=categories,
            model_version=self.model_manager.engine.model_version,
            inference_ms=inf_ms,
            total_latency_ms=total_ms,
        )

    async def moderate_batch(
        self,
        items: List[dict],
        strict: bool = False,
    ) -> List[ModerationResult]:
        """Moderate a batch of items synchronously with a single vectorized tensor pass."""
        t_start = time.perf_counter()

        cleaned_items = []
        for it in items:
            raw = it.get("text", "")
            t_id = it.get("text_id")
            cleaned_items.append((t_id, raw, clean_text(raw)))

        # Separate non-empty from empty
        valid_indices = [i for i, (_, _, cl) in enumerate(cleaned_items) if cl]
        valid_texts = [cleaned_items[i][2] for i in valid_indices]

        logits_map = {}
        inf_ms = 0.0

        if valid_texts:
            logits_batch, inf_ms = self.model_manager.engine.predict(valid_texts)
            for idx, orig_pos in enumerate(valid_indices):
                logits_map[orig_pos] = logits_batch[idx]

        results = []
        for i, (t_id, raw, cl) in enumerate(cleaned_items):
            if not cl:
                results.append(
                    ModerationResult(
                        text_id=t_id,
                        decision=ModerationDecision.ALLOW,
                        label="non_toxic",
                        confidence=1.0,
                        policy_categories=[],
                        model_version=self.model_manager.engine.model_version,
                        inference_ms=0.0,
                        total_latency_ms=round(
                            (time.perf_counter() - t_start) * 1000.0, 3
                        ),
                    )
                )
            else:
                logits = logits_map[i]
                dec, lbl, conf, cats = self.policy_engine.evaluate_logits(
                    logits=logits,
                    text=raw,
                    strict=strict,
                )
                results.append(
                    ModerationResult(
                        text_id=t_id,
                        decision=dec,
                        label=lbl,
                        confidence=conf,
                        policy_categories=cats,
                        model_version=self.model_manager.engine.model_version,
                        inference_ms=inf_ms,
                        total_latency_ms=round(
                            (time.perf_counter() - t_start) * 1000.0, 3
                        ),
                    )
                )

        return results
