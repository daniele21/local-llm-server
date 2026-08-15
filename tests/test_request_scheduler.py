from __future__ import annotations

import asyncio

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from local_llm_server.async_scheduler import AsyncRuntimeGate
from local_llm_server.core.contracts import InferenceRequest, TaskType
from local_llm_server.request_middleware import install_request_policy
from local_llm_server.request_scheduler import (
    _hold_gate_for_stream,
    install_request_scheduler,
)
from local_llm_server.runtime import ModelRuntimeManager
from local_llm_server.scheduler_policy import RequestSchedulerSettings


class _Engine:
    backend = "fake"

    def close(self):
        pass


def _cfg(model: str):
    return {
        "model": model,
        "model_id": f"org/{model}",
        "backend": "fake",
        "modalities": ["text"],
        "max_concurrent_requests": 1,
    }


def _request_payload(model: str):
    return {
        "model": model,
        "messages": [{"role": "user", "content": "hello"}],
        "stream": False,
    }


def _app(*, models=("demo",), capacity=1):
    manager = ModelRuntimeManager(default_model=models[0])
    for model in models:
        manager.add(_cfg(model), _Engine())
    app = FastAPI()
    app.state.runtime_manager = manager
    install_request_scheduler(
        app,
        settings=RequestSchedulerSettings(queue_capacity=capacity),
    )
    # Last-added middleware executes outermost, so policy prepares the request
    # before the scheduler middleware runs.
    install_request_policy(app)
    return app, manager


def test_queue_overflow_returns_429_before_backend_route_is_invoked():
    async def scenario():
        app, manager = _app(capacity=1)
        started = asyncio.Event()
        release = asyncio.Event()
        route_calls = 0

        @app.post("/v1/chat/completions")
        async def chat(request: Request):
            nonlocal route_calls
            route_calls += 1
            started.set()
            await release.wait()
            return JSONResponse({"ok": True})

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            first = asyncio.create_task(client.post("/v1/chat/completions", json=_request_payload("demo")))
            await asyncio.wait_for(started.wait(), timeout=1)
            second = asyncio.create_task(client.post("/v1/chat/completions", json=_request_payload("demo")))
            await asyncio.sleep(0.02)

            overflow = await client.post("/v1/chat/completions", json=_request_payload("demo"))
            assert overflow.status_code == 429
            assert overflow.json()["detail"]["code"] == "resource_exhausted"
            assert route_calls == 1

            release.set()
            first_response, second_response = await asyncio.gather(first, second)
            assert first_response.status_code == 200
            assert second_response.status_code == 200
            assert route_calls == 2
            assert float(second_response.headers["x-local-llm-queue-wait-ms"]) > 0

        runtime = manager.resolve("demo")
        metrics = runtime.latest_inference_metrics
        assert metrics.durations.queue_wait_ms is not None
        assert metrics.durations.queue_wait_ms > 0
        gate = app.state.runtime_gate_registry.gate_for(runtime)
        assert (await gate.snapshot()).requests == ()

    asyncio.run(scenario())


def test_explicit_queue_timeout_returns_408_without_invoking_route():
    async def scenario():
        app, _ = _app(capacity=1)
        started = asyncio.Event()
        release = asyncio.Event()
        route_calls = 0

        @app.post("/v1/chat/completions")
        async def chat(request: Request):
            nonlocal route_calls
            route_calls += 1
            started.set()
            await release.wait()
            return JSONResponse({"ok": True})

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            first = asyncio.create_task(client.post("/v1/chat/completions", json=_request_payload("demo")))
            await asyncio.wait_for(started.wait(), timeout=1)
            timed_out = await client.post(
                "/v1/chat/completions",
                json=_request_payload("demo"),
                headers={"x-local-llm-queue-timeout-ms": "10"},
            )
            assert timed_out.status_code == 408
            assert timed_out.json()["detail"]["code"] == "timeout"
            assert route_calls == 1
            release.set()
            assert (await first).status_code == 200

    asyncio.run(scenario())


def test_runtime_gates_are_isolated_per_resident_model():
    async def scenario():
        app, _ = _app(models=("a", "b"), capacity=1)
        a_started = asyncio.Event()
        a_release = asyncio.Event()
        route_calls = {"a": 0, "b": 0}

        @app.post("/v1/chat/completions")
        async def chat(request: Request):
            model = request.state.prepared_inference_request.canonical.model
            route_calls[model] += 1
            if model == "a":
                a_started.set()
                await a_release.wait()
            return JSONResponse({"model": model})

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            a_request = asyncio.create_task(client.post("/v1/chat/completions", json=_request_payload("a")))
            await asyncio.wait_for(a_started.wait(), timeout=1)
            b_response = await asyncio.wait_for(
                client.post("/v1/chat/completions", json=_request_payload("b")),
                timeout=1,
            )
            assert b_response.status_code == 200
            assert route_calls == {"a": 1, "b": 1}
            a_release.set()
            assert (await a_request).status_code == 200

    asyncio.run(scenario())


def test_invalid_timeout_header_fails_before_route():
    async def scenario():
        app, _ = _app(capacity=1)
        route_calls = 0

        @app.post("/v1/chat/completions")
        async def chat():
            nonlocal route_calls
            route_calls += 1
            return JSONResponse({"ok": True})

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/v1/chat/completions",
                json=_request_payload("demo"),
                headers={"x-local-llm-queue-timeout-ms": "never"},
            )
            assert response.status_code == 400
            assert response.json()["detail"]["code"] == "invalid_request"
            assert route_calls == 0

    asyncio.run(scenario())


def test_streaming_body_holds_gate_until_iterator_finishes_and_then_prunes():
    async def scenario():
        gate = AsyncRuntimeGate(capacity=1, max_running=1)
        request = InferenceRequest(task=TaskType.CHAT, model="demo", input_text="hello", stream=True)
        await gate.acquire("stream", request)
        continue_stream = asyncio.Event()

        async def source():
            yield b"first"
            await continue_stream.wait()
            yield b"second"

        wrapped = _hold_gate_for_stream(source(), gate=gate, request_id="stream")
        assert await wrapped.__anext__() == b"first"
        assert (await gate.snapshot()).inflight == 1
        continue_stream.set()
        assert await wrapped.__anext__() == b"second"
        try:
            await wrapped.__anext__()
        except StopAsyncIteration:
            pass
        snapshot = await gate.snapshot()
        assert snapshot.inflight == 0
        assert snapshot.requests == ()

    asyncio.run(scenario())
