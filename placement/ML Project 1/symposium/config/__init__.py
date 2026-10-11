"""Configuration package: settings loader + persona registry."""

from symposium.config.settings import Settings, get_settings
from symposium.config.personas import PERSONAS, Persona, get_persona

__all__ = ["Settings", "get_settings", "PERSONAS", "Persona", "get_persona"]
