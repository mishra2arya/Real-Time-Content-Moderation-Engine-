"""Unit tests for policy evaluation engine and thresholds."""

import numpy as np

from app.moderation.labels import ContentLabel, ModerationDecision, PolicyCategory
from app.moderation.postprocessing import PolicyEngine


def test_policy_engine_allow(policy_engine: PolicyEngine):
    """Low toxicity probability should yield ALLOW decision."""
    # logits [score_nontoxic, score_toxic] -> high nontoxic
    logits = np.array([3.0, -3.0])
    decision, label, confidence, categories = policy_engine.evaluate_logits(
        logits, "A nice message."
    )
    assert decision == ModerationDecision.ALLOW
    assert label == ContentLabel.NON_TOXIC.value
    assert confidence > 0.95
    assert categories == []


def test_policy_engine_block(policy_engine: PolicyEngine):
    """High toxicity probability should yield BLOCK decision."""
    logits = np.array([-3.0, 3.0])
    decision, label, confidence, categories = policy_engine.evaluate_logits(
        logits, "You are an idiot and a moron."
    )
    assert decision == ModerationDecision.BLOCK
    assert label == ContentLabel.TOXIC.value
    assert confidence > 0.95
    assert PolicyCategory.INSULT.value in categories


def test_policy_engine_flag_review(policy_engine: PolicyEngine):
    """Borderline toxicity between flag_threshold (0.40) and block_threshold (0.50) yields FLAG_REVIEW."""
    # equal logits give prob 0.50. Let's make prob toxic ~0.45: logits [0.2, 0.0] -> probs [0.55, 0.45]
    logits = np.array([0.2, 0.0])
    decision, label, confidence, _ = policy_engine.evaluate_logits(
        logits, "Somewhat suspicious text"
    )
    assert decision == ModerationDecision.FLAG_REVIEW
    assert label == ContentLabel.TOXIC.value
    assert 0.40 <= confidence < 0.50


def test_policy_engine_strict_mode(policy_engine: PolicyEngine):
    """Strict mode uses strict_threshold (0.35) instead of standard (0.50)."""
    # prob toxic ~0.38: logits [0.5, 0.0] -> probs [0.62, 0.38]
    logits = np.array([0.5, 0.0])
    decision_normal, _, _, _ = policy_engine.evaluate_logits(
        logits, "Text", strict=False
    )
    decision_strict, _, _, _ = policy_engine.evaluate_logits(
        logits, "Text", strict=True
    )

    assert decision_normal != ModerationDecision.BLOCK
    assert decision_strict == ModerationDecision.BLOCK


def test_policy_engine_threat_category(policy_engine: PolicyEngine):
    """Specific threat keywords should tag threat category."""
    logits = np.array([-2.0, 2.0])
    _, _, _, categories = policy_engine.evaluate_logits(
        logits, "I will hunt you and destroy you."
    )
    assert PolicyCategory.THREAT.value in categories


def test_module_aliases_and_exceptions():
    """Verify alias re-exports and custom domain exceptions."""
    from app.core.exceptions import (
        InferenceTimeoutException,
        InvalidPayloadException,
        ModelNotReadyException,
        ModerationEngineException,
        QueueCapacityExceededException,
    )
    from app.moderation.policy import PolicyEngine as AliasedPolicyEngine
    from app.moderation.service import ModerationResult, ModerationService

    assert AliasedPolicyEngine is not None
    assert ModerationService is not None
    assert ModerationResult is not None

    ex1 = ModerationEngineException("Custom err", 500)
    assert ex1.status_code == 500 and ex1.message == "Custom err"

    ex2 = ModelNotReadyException()
    assert ex2.status_code == 503

    ex3 = InvalidPayloadException("Invalid")
    assert ex3.status_code == 422

    ex4 = QueueCapacityExceededException()
    assert ex4.status_code == 429

    ex5 = InferenceTimeoutException()
    assert ex5.status_code == 504
