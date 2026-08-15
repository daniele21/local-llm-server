"""Backend-specific metric adapters that preserve canonical evidence semantics."""
from __future__ import annotations

from typing import Any

from .metrics import CountMetrics, DurationMetrics, InferenceMetrics, ThroughputMetrics
from .mlx_generation_evidence import openai_evidence_from_mlx_generation


def metrics_from_mlx_generation_response(response: Any) -> InferenceMetrics:
    """Map explicit ``mlx_lm.stream_generate`` response fields.

    The same translation now feeds MLXEngine's OpenAI-compatible payloads and
    this direct adapter, keeping one interpretation of cumulative MLX counters
    and rates. Missing or malformed fields remain unavailable.
    """
    usage, timings, finish_reason = openai_evidence_from_mlx_generation(response)
    prompt_tokens = usage.get("prompt_tokens")
    output_tokens = usage.get("completion_tokens")
    prompt_ms = timings.get("prompt_ms")
    decode_ms = timings.get("predicted_ms")
    generation_tps = timings.get("predicted_per_second")

    sources: dict[str, str] = {}
    if prompt_tokens is not None:
        sources["input_tokens"] = "mlx_generation.prompt_tokens"
    if output_tokens is not None:
        sources["output_tokens"] = "mlx_generation.generation_tokens"
    if prompt_ms is not None:
        sources["prompt_prefill_ms"] = "mlx_generation.prompt_tokens/prompt_tps"
    if decode_ms is not None:
        sources["decode_ms"] = "mlx_generation.generation_tokens/generation_tps"
    if generation_tps is not None:
        sources["decode_tokens_per_second"] = "mlx_generation.generation_tps"
    if finish_reason is not None:
        sources["termination_reason"] = "mlx_generation.finish_reason"

    return InferenceMetrics(
        durations=DurationMetrics(
            prompt_prefill_ms=prompt_ms,
            decode_ms=decode_ms,
        ),
        counts=CountMetrics(
            input_tokens=prompt_tokens,
            output_tokens=output_tokens,
        ),
        throughput=ThroughputMetrics(
            decode_tokens_per_second=generation_tps,
        ),
        termination_reason=finish_reason,
        sources=sources,
    )
