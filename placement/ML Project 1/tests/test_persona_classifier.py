from symposium.etl.transform.persona_classifier import (
    extract_features,
    score_chunk_for_personas,
)


def test_features_return_all_keys():
    feats = extract_features("In 1848 the study measured the effect.")
    for k in ("date_density", "evidence_density", "narrative_density",
              "counter_density", "reading_ease", "avg_word_len", "token_count"):
        assert k in feats


def test_scientist_score_is_higher_on_evidence_text():
    scientific = "The study measured the effect size in a controlled experiment."
    lyrical = "The river of memory carried a shadow of light and sorrow."
    s_scores = score_chunk_for_personas(scientific)
    l_scores = score_chunk_for_personas(lyrical)
    assert s_scores["scientist"] > l_scores["scientist"]


def test_poet_score_is_higher_on_narrative_text():
    scientific = "The study measured the effect size in a controlled experiment."
    lyrical = "The river of memory carried a shadow of light and sorrow."
    s_scores = score_chunk_for_personas(scientific)
    l_scores = score_chunk_for_personas(lyrical)
    assert l_scores["poet"] > s_scores["poet"]


def test_scores_are_bounded():
    scores = score_chunk_for_personas("Random text with nothing special.")
    for v in scores.values():
        assert 0.0 < v < 2.0
