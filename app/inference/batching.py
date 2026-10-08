"""Dynamic asynchronous micro-batching queue for high-throughput stream moderation."""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Tuple

import numpy as np

from app.core.config import get_settings
from app.core.logging import logger
from app.inference.onnx_engine import ONNXInferenceEngine, get_onnx_engine


class BatchItem:
    """Represents a single request inside the micro-batch queue."""

    def __init__(self, text: str, future: asyncio.Future):
        self.text = text
        self.future = future
        self.enqueued_time = time.perf_counter()


class AsyncBatchingEngine:
    """Asynchronous dynamic batcher that aggregates requests across a time window."""

    _instance: Optional["AsyncBatchingEngine"] = None

    def __init__(
        self,
        engine: Optional[ONNXInferenceEngine] = None,
        max_batch_size: Optional[int] = None,
        timeout_ms: Optional[int] = None,
        max_queue_size: int = 2000,
    ):
        settings = get_settings()
        self.engine = engine or get_onnx_engine()
        self.max_batch_size = max_batch_size or settings.batch_max_size
        self.timeout_sec = (timeout_ms or settings.batch_timeout_ms) / 1000.0
        self.max_queue_size = max_queue_size

        self.queue: asyncio.Queue[BatchItem] = asyncio.Queue(maxsize=max_queue_size)
        self.worker_task: Optional[asyncio.Task] = None
        self.running = False
        self.thread_pool = ThreadPoolExecutor(
            max_workers=4, thread_name_prefix="ort-batch"
        )

    async def start(self) -> None:
        """Start the background consumer loop."""
        if not self.running:
            self.running = True
            self.worker_task = asyncio.create_task(self._process_queue_loop())
            logger.info("Dynamic micro-batching worker started.")

    async def stop(self) -> None:
        """Gracefully stop the background consumer loop and thread pool."""
        self.running = False
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        self.thread_pool.shutdown(wait=False)
        logger.info("Dynamic micro-batching worker stopped.")

    async def submit(self, text: str) -> Tuple[np.ndarray, float]:
        """Submit a single text for batch inference.

        Returns:
            Tuple of (logits ndarray [2], inference_time_ms float).
        """
        loop = asyncio.get_running_loop()
        future: asyncio.Future = loop.create_future()
        item = BatchItem(text, future)

        try:
            # Backpressure guard
            self.queue.put_nowait(item)
        except asyncio.QueueFull:
            logger.warning("Micro-batch queue full. Shedding load.")
            raise RuntimeError(
                "Moderation queue capacity exceeded (backpressure)."
            ) from None

        return await future

    async def _process_queue_loop(self) -> None:
        """Continuously drain queue, aggregating items up to max_batch_size or timeout."""
        loop = asyncio.get_running_loop()

        while self.running:
            try:
                # Wait for the first item
                item = await self.queue.get()
                batch = [item]

                # Collect subsequent items within the time budget
                deadline = time.perf_counter() + self.timeout_sec
                while len(batch) < self.max_batch_size:
                    time_remaining = deadline - time.perf_counter()
                    if time_remaining <= 0:
                        break
                    try:
                        next_item = await asyncio.wait_for(
                            self.queue.get(),
                            timeout=time_remaining,
                        )
                        batch.append(next_item)
                    except asyncio.TimeoutError:
                        break

                # Execute batch inference in thread pool
                texts = [b.text for b in batch]

                logits, inf_ms = await loop.run_in_executor(
                    self.thread_pool,
                    self.engine.predict,
                    texts,
                )

                # Resolve each future in the batch
                for i, b in enumerate(batch):
                    if not b.future.done():
                        b.future.set_result((logits[i], inf_ms))
                    self.queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in batch processing loop: {e}", exc_info=True)
                for b in batch:
                    if not b.future.done():
                        b.future.set_exception(e)
                    self.queue.task_done()


def get_batching_engine() -> AsyncBatchingEngine:
    """Retrieve or initialize singleton async batching engine."""
    if AsyncBatchingEngine._instance is None:
        AsyncBatchingEngine._instance = AsyncBatchingEngine()
    return AsyncBatchingEngine._instance
