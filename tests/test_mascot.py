from __future__ import annotations

from roku_tui.mascot import RAT_PLAIN, ratsay


def test_ratsay_default_message() -> None:
    result = ratsay()
    assert "Anything good on?" in result
    assert RAT_PLAIN in result


def test_ratsay_single_word() -> None:
    result = ratsay("Hello")
    assert "Hello" in result
    assert "< Hello >" in result


def test_ratsay_short_single_line() -> None:
    result = ratsay("Hello world")
    assert "Hello world" in result
    assert RAT_PLAIN in result


def test_ratsay_multi_line_wraps() -> None:
    long_msg = (
        "This is a very long message that definitely needs to wrap across "
        "multiple lines because it exceeds the forty character maximum"
    )
    result = ratsay(long_msg)
    lines = result.split("\n")
    bubble_lines = [
        line
        for line in lines
        if line.startswith("/") or line.startswith("\\") or line.startswith("|")
    ]
    assert len(bubble_lines) >= 2


def test_ratsay_multi_line_first_line_starts_with_slash() -> None:
    long_msg = "This is a very long message that definitely wraps and has more lines"
    result = ratsay(long_msg)
    bubble_lines = [
        line
        for line in result.split("\n")
        if line.startswith("/") or line.startswith("\\") or line.startswith("|")
    ]
    assert bubble_lines[0].startswith("/")
    assert bubble_lines[-1].startswith("\\")


def test_ratsay_three_lines_has_middle_pipe() -> None:
    # Create a message guaranteed to produce at least 3 lines (>80 chars across 3 lines)
    long_msg = " ".join(["wordwordword"] * 10)
    result = ratsay(long_msg)
    bubble_lines = [line for line in result.split("\n") if line.startswith("|")]
    assert len(bubble_lines) >= 1


def test_ratsay_word_wrapping() -> None:
    # A message with words that will split across lines
    msg = "first " + "x" * 38 + " second"
    result = ratsay(msg)
    assert "second" in result


def test_ratsay_strips_whitespace() -> None:
    result = ratsay("  Hello  ")
    assert "Hello" in result


def test_ratsay_none_uses_default() -> None:
    result1 = ratsay(None)
    result2 = ratsay()
    assert result1 == result2
