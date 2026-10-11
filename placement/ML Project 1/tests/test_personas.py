from symposium.config.personas import PERSONAS, get_persona


def test_all_five_personas_registered():
    keys = set(PERSONAS.keys())
    assert keys == {"historian", "scientist", "poet", "skeptic", "child"}


def test_persona_has_required_fields():
    p = get_persona("historian")
    assert p.name
    assert p.tagline
    assert p.system.startswith("You are")
    assert p.color.startswith("#")


def test_unknown_persona_raises():
    import pytest
    with pytest.raises(KeyError):
        get_persona("dragon")
