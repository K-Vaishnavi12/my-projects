from symposium.etl.transform.cleaner import (
    clean_article,
    drop_bad_sections,
    looks_like_content,
)


def test_drop_bad_sections_removes_references():
    raw = """
    Intro paragraph text goes here with many words.

    == Main Content ==
    Actual meaningful content that should survive the cleaning.

    == References ==
    [1] Something
    [2] Something else

    == See also ==
    - Article A
    - Article B
    """
    out = drop_bad_sections(raw)
    assert "meaningful content" in out
    assert "References" not in out
    assert "See also" not in out


def test_looks_like_content_rejects_short():
    assert not looks_like_content("too short")


def test_looks_like_content_accepts_real_text():
    assert looks_like_content(
        "This is a full paragraph with enough alphabetic content to pass the "
        "quality gate for the ETL pipeline used inside Symposium." * 3
    )


def test_clean_article_ok():
    article = {
        "id": "abc",
        "title": "Test",
        "text": "Some [1] real content. " * 30,
    }
    out = clean_article(article)
    assert "clean_text" in out
    assert "[1]" not in out["clean_text"]


def test_clean_article_raises_on_junk():
    import pytest
    article = {"id": "abc", "title": "Test", "text": "!!!!!!!!!!!!"}
    with pytest.raises(ValueError):
        clean_article(article)
