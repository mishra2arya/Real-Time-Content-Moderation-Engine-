"""Post-processing and policy enforcement logic for moderation predictions."""

from typing import List, Tuple

import numpy as np

from app.moderation.labels import (
    POLICY_KEYWORDS,
    ContentLabel,
    ModerationDecision,
    PolicyCategory,
)


class PolicyEngine:
    """Evaluates raw model probabilities against business and safety policy rules."""

    def __init__(
        self,
        block_threshold: float = 0.50,
        flag_threshold: float = 0.40,
        strict_threshold: float = 0.35,
    ):
        self.block_threshold = block_threshold
        self.flag_threshold = flag_threshold
        self.strict_threshold = strict_threshold

    def evaluate_logits(
        self,
        logits: np.ndarray,
        text: str = "",
        strict: bool = False,
    ) -> Tuple[ModerationDecision, str, float, List[str]]:
        """Convert model logits to a policy decision and violation categories.

        Args:
            logits: 1D array of logits [score_non_toxic, score_toxic].
            text: Original or cleaned text for subcategory tagging.
            strict: If True, uses lower strict threshold for elevated safety environments.

        Returns:
            Tuple of (decision, label, confidence, policy_categories).
        """
        # Numerically stable softmax
        exp_logits = np.exp(logits - np.max(logits))
        probs = exp_logits / np.sum(exp_logits)
        prob_non_toxic = float(probs[0])
        prob_toxic = float(probs[1])

        effective_block_threshold = (
            self.strict_threshold if strict else self.block_threshold
        )

        categories: List[str] = []

        if prob_toxic >= effective_block_threshold:
            decision = ModerationDecision.BLOCK
            label = ContentLabel.TOXIC.value
            confidence = round(prob_toxic, 4)
            categories = self._identify_categories(text, prob_toxic)
        elif prob_toxic >= self.flag_threshold:
            decision = ModerationDecision.FLAG_REVIEW
            label = ContentLabel.TOXIC.value
            confidence = round(prob_toxic, 4)
            categories = self._identify_categories(text, prob_toxic)
        else:
            decision = ModerationDecision.ALLOW
            label = ContentLabel.NON_TOXIC.value
            confidence = round(prob_non_toxic, 4)

        return decision, label, confidence, categories

    def _identify_categories(self, text: str, prob_toxic: float) -> List[str]:
        """Detect granular policy violation categories based on text markers and probability."""
        matched: List[str] = []
        lower_text = text.lower()

        for category, keywords in POLICY_KEYWORDS.items():
            for kw in keywords:
                if kw in lower_text:
                    matched.append(category.value)
                    break

        # If high toxicity probability but no specific keyword matched, default to general toxicity
        if not matched and prob_toxic >= self.block_threshold:
            matched.append(PolicyCategory.TOXICITY.value)

        return matched
