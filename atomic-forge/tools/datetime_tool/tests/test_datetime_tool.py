from tool.datetime_tool import (
    DateTimeTool,
    DateTimeToolInputSchema,
    DateTimeToolOutputSchema,
)


def test_now_default_utc():
    tool = DateTimeTool()
    out = tool.run(DateTimeToolInputSchema(operation="now"))
    assert isinstance(out, DateTimeToolOutputSchema)
    assert out.operation == "now"
    assert out.iso is not None
    assert out.error is None
    assert out.weekday in {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}


def test_now_in_tokyo():
    tool = DateTimeTool()
    out = tool.run(DateTimeToolInputSchema(operation="now", timezone="Asia/Tokyo"))
    assert out.error is None
    assert out.timezone == "Asia/Tokyo"
    assert "+09:00" in out.iso


def test_parse_iso_with_timezone():
    tool = DateTimeTool()
    out = tool.run(DateTimeToolInputSchema(operation="parse", input="2026-04-29T15:30:00Z"))
    assert out.error is None
    assert (out.year, out.month, out.day, out.hour, out.minute) == (2026, 4, 29, 15, 30)
    assert out.iso.startswith("2026-04-29T15:30:00")


def test_parse_naive_uses_default_tz():
    tool = DateTimeTool()
    out = tool.run(DateTimeToolInputSchema(operation="parse", input="2026-04-29T15:30:00", timezone="Europe/Brussels"))
    assert out.error is None
    assert out.timezone == "Europe/Brussels"


def test_convert_brussels_to_new_york():
    tool = DateTimeTool()
    out = tool.run(
        DateTimeToolInputSchema(
            operation="convert",
            input="2026-04-29T15:30:00",
            timezone="Europe/Brussels",
            target_timezone="America/New_York",
        )
    )
    assert out.error is None
    assert out.timezone == "America/New_York"
    assert (out.year, out.month, out.day) == (2026, 4, 29)
    assert (out.hour, out.minute) == (9, 30)


def test_shift_forward_and_backward():
    tool = DateTimeTool()
    out = tool.run(
        DateTimeToolInputSchema(
            operation="shift",
            input="2026-04-29T00:00:00Z",
            days=3,
            hours=-2,
            minutes=30,
        )
    )
    assert out.error is None
    assert out.year == 2026
    assert out.month == 5
    assert out.day == 1
    assert out.hour == 22
    assert out.minute == 30


def test_diff_positive():
    tool = DateTimeTool()
    out = tool.run(
        DateTimeToolInputSchema(
            operation="diff",
            input="2026-04-29T00:00:00Z",
            input_2="2026-04-30T01:30:00Z",
        )
    )
    assert out.error is None
    assert out.diff_seconds == 25 * 3600 + 30 * 60
    assert "1 day" in out.diff_human and "1 hour" in out.diff_human and "30 minute" in out.diff_human


def test_diff_negative_keeps_sign():
    tool = DateTimeTool()
    out = tool.run(
        DateTimeToolInputSchema(
            operation="diff",
            input="2026-04-30T00:00:00Z",
            input_2="2026-04-29T00:00:00Z",
        )
    )
    assert out.error is None
    assert out.diff_seconds == -86400.0
    assert out.diff_human.startswith("-")


def test_unknown_timezone_returns_error():
    tool = DateTimeTool()
    out = tool.run(DateTimeToolInputSchema(operation="now", timezone="Mars/Olympus"))
    assert out.error is not None
    assert "Unknown timezone" in out.error


def test_missing_input_for_parse_returns_error():
    tool = DateTimeTool()
    out = tool.run(DateTimeToolInputSchema(operation="parse"))
    assert out.error is not None
    assert "input" in out.error


def test_missing_target_timezone_for_convert():
    tool = DateTimeTool()
    out = tool.run(DateTimeToolInputSchema(operation="convert", input="2026-04-29T15:30:00Z"))
    assert out.error is not None
    assert "target_timezone" in out.error


def test_unparseable_input():
    tool = DateTimeTool()
    out = tool.run(DateTimeToolInputSchema(operation="parse", input="not-a-date"))
    assert out.error is not None
    assert "Could not parse" in out.error


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
