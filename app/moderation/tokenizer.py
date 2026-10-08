"""Tokenizer wrapper for tokenizing single and batched inputs."""

from typing import Dict, List, Union

import numpy as np
from transformers import AutoTokenizer


class ModerationTokenizer:
    """Wrapper around HuggingFace AutoTokenizer for ONNX-ready numpy input tensors."""

    def __init__(
        self,
        model_name_or_path: str = "distilbert-base-uncased",
        max_length: int = 128,
    ):
        self.model_name_or_path = model_name_or_path
        self.max_length = max_length
        self.tokenizer = AutoTokenizer.from_pretrained(model_name_or_path)  # nosec B615

    def tokenize(
        self,
        texts: Union[str, List[str]],
        padding: Union[bool, str] = True,
        truncation: bool = True,
    ) -> Dict[str, np.ndarray]:
        """Tokenize one or multiple texts and return int64 numpy arrays for ONNX runtime.

        Args:
            texts: Single text string or list of text strings.
            padding: Padding strategy ('max_length', True, or False).
            truncation: Whether to truncate to max_length.

        Returns:
            Dict containing 'input_ids' and 'attention_mask' as int64 numpy arrays.
        """
        if isinstance(texts, str):
            texts = [texts]

        encoded = self.tokenizer(
            texts,
            padding=padding,
            truncation=truncation,
            max_length=self.max_length,
            return_tensors="np",
        )

        return {
            "input_ids": encoded["input_ids"].astype(np.int64),
            "attention_mask": encoded["attention_mask"].astype(np.int64),
        }
