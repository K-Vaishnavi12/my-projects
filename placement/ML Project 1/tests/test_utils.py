import pytest

from symposium.utils import (
    batched,
    chunk_by_sentences,
    extract_years,
    iter_sentences,
    normalize_whitespace,
    stable_id,
    strip_wiki_refs,
)


def test_normalize_whitespace():
    assert normalize_whitespace("  a\tb\nc  ") == "a b c"
    assert normalize_whitespace("no change") == "no change"


def test_strip_wiki_refs():
    assert strip_wiki_refs("hello [1] world [23]") == "hello  world "


def test_extract_years_finds_only_parens():
    text = "In (1848) revolutions broke out. Not 1900 or 2020."
    assert extract_years(text) == [1848]


def test_iter_sentences_yields_and_strips():
    text = "First. Second! Third?"
    result = list(iter_sentences(text))
    assert result == ["First.", "Second!", "Third?"]


def test_chunk_by_sentences_respects_target_and_overlap():
    text = ". ".join(f"Sentence {i}" for i in range(1, 21)) + "."
    chunks = list(chunk_by_sentences(text, target_chars=60, overlap_chars=10))
    assert len(chunks) > 1
    assert all(isinstance(c, str) and c for c in chunks)


def test_stable_id_is_deterministic():
    a = stable_id("wiki", "Napoleon")
    b = stable_id("wiki", "Napoleon")
    c = stable_id("wiki", "Napoleonn")
    assert a == b
    assert a != c
    assert len(a) == 16


def test_batched_yields_correct_sizes():
    out = list(batched(range(10), 3))
    assert out == [[0, 1, 2], [3, 4, 5], [6, 7, 8], [9]]


def test_batched_raises_on_bad_size():
    with pytest.raises(ValueError):
        list(batched(range(3), 0))
