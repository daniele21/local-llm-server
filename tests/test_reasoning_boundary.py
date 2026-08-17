from __future__ import annotations

import itertools

from local_llm_server.reasoning_boundary import (
    ReasoningStreamParser,
    split_reasoning_content,
)


def _chunkings(value: str):
    # Deterministic adversarial partitions around every delimiter character plus
    # a few multi-split combinations. This catches tags fragmented across chunks
    # without exploding into the full powerset of all string partitions.
    yield [value]
    for cut in range(1, len(value)):
        yield [value[:cut], value[cut:]]
    cuts = sorted({1, 2, 3, 5, 7, len(value) // 2, len(value) - 3, len(value) - 1})
    valid = [cut for cut in cuts if 0 < cut < len(value)]
    for first, second in itertools.combinations(valid, 2):
        yield [value[:first], value[first:second], value[second:]]


def _parse(chunks, *, expect_reasoning: bool):
    parser = ReasoningStreamParser(
        expect_reasoning=expect_reasoning,
        collect_reasoning=True,
    )
    exposed = "".join(parser.feed(chunk) for chunk in chunks) + parser.finish()
    return parser, exposed


def test_open_and_close_tags_are_chunk_boundary_invariant():
    value = "<think>private chain</think>{\"answer\":42}"

    for chunks in _chunkings(value):
        parser, exposed = _parse(chunks, expect_reasoning=True)
        assert exposed == '{"answer":42}', chunks
        assert parser.reasoning == "private chain", chunks
        assert parser.carry_size == 0


def test_missing_open_tag_still_hides_reasoning_until_close():
    value = "private chain without opening tag</think>FINAL"

    for chunks in _chunkings(value):
        parser, exposed = _parse(chunks, expect_reasoning=True)
        assert exposed == "FINAL", chunks
        assert parser.reasoning == "private chain without opening tag", chunks


def test_missing_close_tag_never_leaks_expected_reasoning():
    for chunks in (
        ["private reasoning"],
        ["<thi", "nk>private", " reasoning"],
        ["private", " reasoning with no delimiters"],
    ):
        parser, exposed = _parse(chunks, expect_reasoning=True)
        assert exposed == ""
        assert parser.reasoning


def test_thinking_disabled_preserves_final_text_and_consumes_explicit_block():
    parser, exposed = _parse(["hello world"], expect_reasoning=False)
    assert exposed == "hello world"
    assert parser.reasoning == ""

    parser, exposed = _parse(
        ["prefix ", "<thi", "nk>hidden</th", "ink> suffix"],
        expect_reasoning=False,
    )
    assert exposed == "prefix  suffix"
    assert parser.reasoning == "hidden"


def test_partial_delimiter_at_end_is_not_lost_after_final_state():
    parser, exposed = _parse(
        ["reason</think>answer ends with <thi"],
        expect_reasoning=True,
    )
    assert exposed == "answer ends with <thi"
    assert parser.reasoning == "reason"


def test_partial_delimiter_at_end_remains_hidden_in_reasoning_state():
    parser, exposed = _parse(
        ["secret ending with </thi"],
        expect_reasoning=True,
    )
    assert exposed == ""
    assert parser.reasoning == "secret ending with </thi"


def test_carry_is_strictly_bounded_by_longest_delimiter():
    parser = ReasoningStreamParser(expect_reasoning=True)
    for chunk in ["x" * 1000, "<", "/", "t", "h", "i"]:
        parser.feed(chunk)
        assert parser.carry_size <= len("</think>") - 1


def test_non_stream_split_contract_matches_reasoning_semantics():
    reasoning, final = split_reasoning_content(
        "analysis</think>{\"ok\":true}",
        expect_reasoning=True,
    )
    assert reasoning == "analysis"
    assert final == '{"ok":true}'

    reasoning, final = split_reasoning_content(
        "ordinary answer",
        expect_reasoning=False,
    )
    assert reasoning == ""
    assert final == "ordinary answer"
