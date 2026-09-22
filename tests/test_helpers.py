from pathlib import Path

import pytest

from Otui import (
    is_valid_otui_file,
    parse_padding,
    read_text_with_fallback,
    to_int,
)


@pytest.mark.parametrize(
    ("value", "default", "expected"),
    [
        ("12", 0, 12),
        ("12.9", 0, 12),
        (-3, 0, -3),
        (None, 7, 7),
        ("not-a-number", 4, 4),
    ],
)
def test_to_int(value: object, default: int, expected: int) -> None:
    assert to_int(value, default) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("8", [8, 8, 8, 8]),
        ("4 12", [4, 12, 4, 12]),
        ("1 2 3 4", [1, 2, 3, 4]),
        ("1 2 3", [0, 0, 0, 0]),
    ],
)
def test_parse_padding(value: str, expected: list[int]) -> None:
    assert parse_padding(value) == expected


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("interface.otui", True),
        ("module.OTMD", True),
        ("module.lua", False),
        ("otui.txt", False),
    ],
)
def test_is_valid_otui_file(filename: str, expected: bool) -> None:
    assert is_valid_otui_file(Path(filename)) is expected


def test_read_text_with_fallback_reads_utf8(tmp_path: Path) -> None:
    source = tmp_path / "utf8.otui"
    source.write_text("text: acao", encoding="utf-8")

    assert read_text_with_fallback(source) == "text: acao"


def test_read_text_with_fallback_reads_latin1(tmp_path: Path) -> None:
    source = tmp_path / "latin1.otui"
    source.write_bytes(b"text: a\xe7\xe3o")

    assert read_text_with_fallback(source) == "text: a\u00e7\u00e3o"
