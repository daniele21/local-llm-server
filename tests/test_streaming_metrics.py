from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.testclient import TestClient

from local_llm_server.request_middleware import install_request_policy
from local_llm_server.runtime import ModelRuntimeManager
from local_llm_server.streaming_metrics import (
    StreamTimingRecorder,
    _sse_line_has_model_output,
    install_streaming_metrics,
)


class _Engine:
    backend = "fake"

    def close(self):
        pass


def _manager():
    manager = ModelRuntimeManager(default_model="demo")
    runtime = manager.add(
        {
            "model": "demo",
            "model_id": "org/demo",
            "backend": "fake",
            "modalities": ["text"],
            "max_concurrent_requests": 1,
        },
        _Engine(),
    )
    return manager, runtime


def test_sse_output_detector_ignores_role_empty_and_done_events():
    assert _sse_line_has_model_output('data: {"choices":[{"delta":{"role":"assistant"}}]}') is False
    assert _sse_line_has_model_output('data: {"choices":[{"delta":{"content":""}}]}') is False
    assert _sse_line_has_model_output("data: [DONE]") is False
    assert _sse_line_has_model_output('data: {"choices":[{"delta":{"content":"hello"}}]}') is True
    assert _sse_line_has_model_output('data: {"choices":[{"text":"hello"}]}') is True


def test_recorder_handles_sse_json_split_across_transport_chunks():
    times = iter((10.25, 10.75))
    recorder = StreamTimingRecorder(started_at=10.0, clock=lambda: next(times))

    assert recorder.observe(b'data: {"choices":[{"delta":{"cont') is False
    assert recorder.observe(b'ent":"hello"}}]}\n\n') is True
    metrics = recorder.finish(completed=True, queue_wait_ms=125.0)

    assert metrics is not None
    assert metrics.durations.queue_wait_ms == 125.0
    assert metrics.durations.ttft_ms == 250.0
    assert metrics.durations.total_ms == 750.0
    assert metrics.sources["queue_wait_ms"] == "request_scheduler.admission_wall_clock"
    assert metrics.sources["ttft_ms"] == "http_stream.first_content_delta_wall_clock"


def test_cancelled_stream_keeps_ttft_but_does_not_claim_total_duration():
    times = iter((2.2, 2.4))
    recorder = StreamTimingRecorder(started_at=2.0, clock=lambda: next(times))
    recorder.observe('data: {"choices":[{"delta":{"content":"x"}}]}\n\n')

    metrics = recorder.finish(completed=False)

    assert metrics is not None
    assert round(metrics.durations.ttft_ms or 0, 6) == 200.0
    assert metrics.durations.total_ms is None
    assert "total_ms" not in metrics.sources


def test_recorder_retains_latest_explicit_stream_usage_and_backend_timings():
    times = iter((4.1, 4.5))
    recorder = StreamTimingRecorder(started_at=4.0, clock=lambda: next(times))

    recorder.observe(
        'data: {"choices":[{"delta":{"content":"a"}}],'
        '"usage":{"prompt_tokens":8,"completion_tokens":1},'
        '"timings":{"prompt_ms":40.0,"predicted_ms":20.0,"predicted_per_second":50.0}}\n\n'
    )
    recorder.observe(
        'data: {"choices":[],"usage":{"prompt_tokens":8,"completion_tokens":4},'
        '"timings":{"prompt_ms":40.0,"predicted_ms":80.0,"predicted_per_second":50.0}}\n\n'
    )

    metrics = recorder.finish(completed=True)

    assert metrics is not None
    assert metrics.counts.input_tokens == 8
    assert metrics.counts.output_tokens == 4
    assert metrics.durations.prompt_prefill_ms == 40.0
    assert metrics.durations.decode_ms == 80.0
    assert metrics.throughput.decode_tokens_per_second == 50.0
    assert round(metrics.durations.ttft_ms or 0, 6) == 100.0
    assert metrics.durations.total_ms == 500.0
    assert metrics.sources["output_tokens"] == "response.usage.completion_tokens"
    assert metrics.sources["decode_tokens_per_second"] == "response.timings.predicted_per_second"


def test_streaming_middleware_records_first_content_delta_on_runtime():
    manager, runtime = _manager()
    app = FastAPI()
    app.state.runtime_manager = manager
    install_request_policy(app)
    install_streaming_metrics(app)

    @app.post("/v1/chat/completions")
    async def chat():
        async def events():
            yield 'data: {"choices":[{"delta":{"role":"assistant"}}]}\n\n'
            yield 'data: {"choices":[{"delta":{"content":"hello"}}]}\n\n'
            yield "data: [DONE]\n\n"

        return StreamingResponse(events(), media_type="text/event-stream")

    response = TestClient(app).post(
        "/v1/chat/completions",
        json={"model": "demo", "messages": [{"role": "user", "content": "hi"}], "stream": True},
    )

    assert response.status_code == 200
    metrics = runtime.latest_inference_metrics
    assert metrics.durations.ttft_ms is not None
    assert metrics.durations.ttft_ms >= 0
    assert metrics.durations.total_ms is not None
    assert metrics.durations.total_ms >= metrics.durations.ttft_ms
    assert metrics.counts.input_tokens is None
    assert metrics.counts.output_tokens is None
    assert metrics.sources["ttft_ms"] == "http_stream.first_content_delta_wall_clock"


def test_streaming_middleware_records_backend_usage_when_stream_exposes_it():
    manager, runtime = _manager()
    app = FastAPI()
    app.state.runtime_manager = manager
    install_request_policy(app)
    install_streaming_metrics(app)

    @app.post("/v1/chat/completions")
    async def chat():
        async def events():
            yield 'data: {"choices":[{"delta":{"content":"hello"}}]}\n\n'
            yield (
                'data: {"choices":[],"usage":{"prompt_tokens":3,"completion_tokens":2},'
                '"timings":{"predicted_per_second":12.5}}\n\n'
            )
            yield "data: [DONE]\n\n"

        return StreamingResponse(events(), media_type="text/event-stream")

    response = TestClient(app).post(
        "/v1/chat/completions",
        json={"model": "demo", "messages": [{"role": "user", "content": "hi"}], "stream": True},
    )

    assert response.status_code == 200
    metrics = runtime.latest_inference_metrics
    assert metrics.counts.input_tokens == 3
    assert metrics.counts.output_tokens == 2
    assert metrics.throughput.decode_tokens_per_second == 12.5


def test_non_streaming_request_does_not_create_streaming_metrics_snapshot():
    manager, runtime = _manager()
    app = FastAPI()
    app.state.runtime_manager = manager
    install_request_policy(app)
    install_streaming_metrics(app)

    @app.post("/v1/chat/completions")
    async def chat():
        async def events():
            yield 'data: {"choices":[{"delta":{"content":"hello"}}]}\n\n'

        return StreamingResponse(events(), media_type="text/event-stream")

    response = TestClient(app).post(
        "/v1/chat/completions",
        json={"model": "demo", "messages": [{"role": "user", "content": "hi"}], "stream": False},
    )

    assert response.status_code == 200
    assert not hasattr(runtime, "latest_inference_metrics")
