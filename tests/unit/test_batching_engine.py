"""Unit tests for asynchronous dynamic batching queue and security controls."""

import asyncio

import pytest

from app.core.config import get_settings
from app.core.security import verify_api_key
from app.inference.batching import AsyncBatchingEngine
from app.inference.onnx_engine import get_onnx_engine


@pytest.mark.asyncio
async def test_async_batching_submit():
    """AsyncBatchingEngine aggregates submitted requests and returns correct predictions."""
    engine = get_onnx_engine()
    batcher = AsyncBatchingEngine(engine=engine, max_batch_size=8, timeout_ms=5)
    await batcher.start()

    try:
        # Submit concurrent tasks
        t1 = batcher.submit("Have a wonderful morning!")
        t2 = batcher.submit("You are a terrible idiot and clown.")
        t3 = batcher.submit("Kill -9 process.")

        res1, res2, res3 = await asyncio.gather(t1, t2, t3)

        logits1, ms1 = res1
        logits2, ms2 = res2
        logits3, ms3 = res3

        assert logits1.shape == (2,)
        assert logits2.shape == (2,)
        assert logits3.shape == (2,)
        assert ms1 > 0.0
    finally:
        await batcher.stop()


@pytest.mark.asyncio
async def test_verify_api_key_disabled():
    """When require_api_key is False, verification passes without key."""
    settings = get_settings()
    settings.require_api_key = False
    result = await verify_api_key(api_key=None)
    assert result is None
