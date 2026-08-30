from __future__ import annotations

import asyncio

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from local_llm_server.request_middleware import install_request_policy
from local_llm_server.request_resource_admission import (
    _hold_reservation_for_stream,
    install_request_resource_admission,
)
from local_llm_server.resource_manager import ReservationKind, ResourceManager
from local_llm_server.resources import ResourceBudget
from local_llm_server.runtime import ModelRuntimeManager


class _Engine:
    backend = "fake"

    def close(self):
        pass


def _cfg(*, request_bytes: int | None = 60):
    return {
        "model": "demo",
        "model_id": "org/demo",
        "backend": "fake",
        "modalities": ["text"],
        "max_concurrent_requests": 2,
        "resource_request_estimate_bytes": request_bytes,
    }


def _payload():
    return {
        "model": "demo",
        "messages": [{"role": "user", "content": "hello"}],
        "stream": False,
    }


def _app(*, limit: int = 100, request_bytes: int | None = 60):
    resources = ResourceManager(ResourceBudget(limit_bytes=limit))
    manager = ModelRuntimeManager(default_model="demo", resource_manager=resources)
    manager.add(_cfg(request_bytes=request_bytes), _Engine())
    app = FastAPI()
    app.state.runtime_manager = manager
    # Last-added middleware runs outermost: canonical policy prepares first,
    # transient admission then runs immediately before the route.
    install_request_resource_admission(app)
    install_request_policy(app)
    return app, resources


def test_concurrent_active_requests_cannot_overcommit_transient_budget():
    async def scenario():
        app, resources = _app(limit=100, request_bytes=60)
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
            first = asyncio.create_task(client.post("/v1/chat/completions", json=_payload()))
            await asyncio.wait_for(started.wait(), timeout=1)
            [active] = resources.snapshot(kind=ReservationKind.TRANSIENT)
            assert active.accounted_bytes == 60

            rejected = await client.post("/v1/chat/completions", json=_payload())
            assert rejected.status_code == 429
            assert rejected.json()["detail"]["code"] == "resource_exhausted"
            assert route_calls == 1

            release.set()
            assert (await first).status_code == 200

        assert resources.snapshot() == ()

    asyncio.run(scenario())


def test_resident_and_request_peak_are_admitted_against_same_ledger():
    async def scenario():
        app, resources = _app(limit=100, request_bytes=40)
        resources.reserve("runtime:other", 70, kind=ReservationKind.RESIDENT)
        resources.commit("runtime:other")
        route_calls = 0

        @app.post("/v1/chat/completions")
        async def chat():
            nonlocal route_calls
            route_calls += 1
            return JSONResponse({"ok": True})

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/v1/chat/completions", json=_payload())

        assert response.status_code == 429
        assert route_calls == 0
        [resident] = resources.snapshot()
        assert resident.kind is ReservationKind.RESIDENT
        assert resident.accounted_bytes == 70

    asyncio.run(scenario())


def test_missing_transient_estimate_remains_unknown_without_fake_reservation():
    async def scenario():
        app, resources = _app(limit=100, request_bytes=None)

        @app.post("/v1/chat/completions")
        async def chat(request: Request):
            metadata = request.state.transient_resource_admission
            return JSONResponse(
                {
                    "decision": metadata["decision"],
                    "accounted_bytes": metadata["accounted_bytes"],
                }
            )

        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/v1/chat/completions", json=_payload())

        assert response.status_code == 200
        assert response.json() == {"decision": "unknown", "accounted_bytes": None}
        assert resources.snapshot() == ()

    asyncio.run(scenario())


def test_stream_wrapper_holds_transient_reservation_until_iterator_finishes():
    async def scenario():
        resources = ResourceManager(ResourceBudget(limit_bytes=100))
        resources.reserve("request:stream", 60, kind=ReservationKind.TRANSIENT)
        resources.commit("request:stream")
        continue_stream = asyncio.Event()

        async def source():
            yield b"first"
            await continue_stream.wait()
            yield b"second"

        wrapped = _hold_reservation_for_stream(
            source(),
            resource_manager=resources,
            reservation_id="request:stream",
        )
        assert await wrapped.__anext__() == b"first"
        assert len(resources.snapshot(kind=ReservationKind.TRANSIENT)) == 1
        continue_stream.set()
        assert await wrapped.__anext__() == b"second"
        try:
            await wrapped.__anext__()
        except StopAsyncIteration:
            pass
        assert resources.snapshot() == ()

    asyncio.run(scenario())


def test_stream_wrapper_releases_transient_reservation_when_cancelled():
    async def scenario():
        resources = ResourceManager(ResourceBudget(limit_bytes=100))
        resources.reserve("request:stream", 60, kind=ReservationKind.TRANSIENT)
        resources.commit("request:stream")

        async def source():
            yield b"first"
            await asyncio.Event().wait()

        wrapped = _hold_reservation_for_stream(
            source(),
            resource_manager=resources,
            reservation_id="request:stream",
        )
        assert await wrapped.__anext__() == b"first"
        await wrapped.aclose()
        assert resources.snapshot() == ()

    asyncio.run(scenario())
