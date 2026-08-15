from __future__ import annotations

import asyncio

import pytest

from local_llm_server.async_scheduler import AsyncRuntimeGate
from local_llm_server.core.contracts import ErrorCode, InferenceError, InferenceRequest, TaskType
from local_llm_server.scheduler import QueueState


def _request(model: str = "demo") -> InferenceRequest:
    return InferenceRequest(task=TaskType.CHAT, model=model, input_text="hello")


def test_gate_queues_fifo_until_running_slot_is_released():
    async def scenario():
        gate = AsyncRuntimeGate(capacity=4, max_running=1)
        first = await gate.acquire("r1", _request())
        assert first.state is QueueState.RUNNING

        second_task = asyncio.create_task(gate.acquire("r2", _request()))
        third_task = asyncio.create_task(gate.acquire("r3", _request()))
        await asyncio.sleep(0)
        assert gate.scheduler.get("r2").state is QueueState.QUEUED
        assert gate.scheduler.get("r3").state is QueueState.QUEUED

        await gate.release("r1")
        second = await asyncio.wait_for(second_task, timeout=0.5)
        assert second.request_id == "r2"
        assert second.state is QueueState.RUNNING
        assert gate.scheduler.get("r3").state is QueueState.QUEUED

        await gate.release("r2")
        third = await asyncio.wait_for(third_task, timeout=0.5)
        assert third.request_id == "r3"
        await gate.release("r3")

    asyncio.run(scenario())


def test_queue_capacity_rejects_before_runtime_execution():
    async def scenario():
        gate = AsyncRuntimeGate(capacity=1, max_running=1)
        await gate.acquire("running", _request())
        queued_task = asyncio.create_task(gate.acquire("queued", _request()))
        await asyncio.sleep(0)
        assert gate.scheduler.get("queued").state is QueueState.QUEUED

        with pytest.raises(InferenceError) as exc_info:
            await gate.acquire("overflow", _request())
        assert exc_info.value.code is ErrorCode.RESOURCE_EXHAUSTED
        assert exc_info.value.retryable is True

        queued_task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await queued_task
        await gate.release("running")

    asyncio.run(scenario())


def test_deadline_expires_while_waiting_for_runtime_slot():
    async def scenario():
        gate = AsyncRuntimeGate(capacity=2, max_running=1)
        await gate.acquire("running", _request())

        with pytest.raises(InferenceError) as exc_info:
            await gate.acquire("deadline", _request(), timeout_seconds=0.01)
        assert exc_info.value.code is ErrorCode.TIMEOUT
        assert gate.scheduler.get("deadline").state is QueueState.EXPIRED

        await gate.release("running")

    asyncio.run(scenario())


def test_cancelling_queued_request_does_not_consume_future_slot():
    async def scenario():
        gate = AsyncRuntimeGate(capacity=2, max_running=1)
        await gate.acquire("running", _request())
        waiting = asyncio.create_task(gate.acquire("cancel-me", _request()))
        await asyncio.sleep(0)
        waiting.cancel()
        with pytest.raises(asyncio.CancelledError):
            await waiting
        assert gate.scheduler.get("cancel-me").state is QueueState.CANCELLED

        await gate.release("running")
        next_request = await gate.acquire("next", _request())
        assert next_request.state is QueueState.RUNNING
        snapshot = await gate.snapshot()
        assert snapshot.inflight == 1
        await gate.release("next")

    asyncio.run(scenario())


def test_running_cancel_sets_token_without_freeing_slot_until_release():
    async def scenario():
        gate = AsyncRuntimeGate(capacity=2, max_running=1)
        running = await gate.acquire("running", _request())
        assert running.state is QueueState.RUNNING

        cancelled = await gate.cancel("running")
        assert cancelled.state is QueueState.RUNNING
        assert cancelled.cancellation.cancelled is True
        assert (await gate.snapshot()).inflight == 1

        await gate.release("running", cancel_requested=True)
        assert gate.scheduler.get("running").state is QueueState.COMPLETED
        assert (await gate.snapshot()).inflight == 0

    asyncio.run(scenario())


def test_public_snapshot_contains_no_request_content():
    async def scenario():
        gate = AsyncRuntimeGate(capacity=2, max_running=1)
        await gate.acquire("r1", _request())
        rendered = str((await gate.snapshot()).to_public_dict())
        assert "hello" not in rendered
        assert "messages" not in rendered
        assert "input_text" not in rendered
        await gate.release("r1")

    asyncio.run(scenario())
