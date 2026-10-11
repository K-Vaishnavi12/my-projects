"""Topic seed lists for the Wikipedia extractor.

Kept as data (not code) so a non-programmer can edit them for a
different debate corpus without touching Python.
"""

from __future__ import annotations

# Each key is a "topic bucket" the user can request on the CLI.
# The values are Wikipedia page titles that will be fetched verbatim.
TOPIC_SEEDS: dict[str, list[str]] = {
    "history": [
        "French Revolution",
        "Industrial Revolution",
        "World War I",
        "World War II",
        "Cold War",
        "Ancient Rome",
        "Silk Road",
        "Mongol Empire",
        "Renaissance",
        "Fall of the Western Roman Empire",
    ],
    "science": [
        "General relativity",
        "Quantum mechanics",
        "Evolution",
        "DNA",
        "Climate change",
        "Photosynthesis",
        "Vaccine",
        "CRISPR",
        "Nuclear fusion",
        "Neuroscience",
    ],
    "philosophy": [
        "Socrates",
        "Immanuel Kant",
        "Existentialism",
        "Stoicism",
        "Utilitarianism",
        "Nietzsche",
        "Philosophy of mind",
        "Free will",
        "Ethics",
        "Epistemology",
    ],
    "literature": [
        "William Shakespeare",
        "Iliad",
        "Don Quixote",
        "Fyodor Dostoevsky",
        "Jane Austen",
        "James Joyce",
        "One Hundred Years of Solitude",
        "Beowulf",
        "Toni Morrison",
        "Franz Kafka",
    ],
    "current_events": [
        "Artificial intelligence",
        "Large language model",
        "Climate change mitigation",
        "Renewable energy",
        "Cryptocurrency",
        "Space exploration",
        "Pandemic",
        "Cybersecurity",
        "Social media",
        "Globalization",
    ],
}


def available_topics() -> list[str]:
    return sorted(TOPIC_SEEDS.keys())


def seeds_for(topic: str) -> list[str]:
    key = topic.lower().strip().replace("-", "_")
    if key not in TOPIC_SEEDS:
        raise KeyError(
            f"Unknown topic '{topic}'. Available: {', '.join(available_topics())}"
        )
    return TOPIC_SEEDS[key]
