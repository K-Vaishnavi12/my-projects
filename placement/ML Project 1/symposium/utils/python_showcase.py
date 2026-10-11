"""Advanced-Python showcase.

This file is *demoware*: it exists so the report / slides can point
at concrete usages of every syllabus topic under **Python (Advanced)**
without hunting through the whole codebase.

Run it directly to see each example:

    python -m symposium.utils.python_showcase
"""

from __future__ import annotations

import functools
import re
import time
from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum
from typing import Callable


# ------------------------------------------------------------------
# 1. Enum
# ------------------------------------------------------------------

class Confidence(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3

    def label(self) -> str:
        return f"{self.name.title()} confidence"


# ------------------------------------------------------------------
# 2. Dataclass + tuples/dicts/sets
# ------------------------------------------------------------------

@dataclass(frozen=True)
class Turn:
    persona: str
    text: str
    conf: Confidence

    def to_tuple(self) -> tuple[str, str, int]:
        return (self.persona, self.text, self.conf.value)


# ------------------------------------------------------------------
# 3. Comprehensions (list, dict, set, generator)
# ------------------------------------------------------------------

def comprehensions_demo(turns: list[Turn]) -> dict[str, list[str]]:
    """Group turn texts by persona - dict-comp + list-comp."""
    personas = {t.persona for t in turns}                    # set comp
    return {p: [t.text for t in turns if t.persona == p]      # dict + list comp
            for p in personas}


# ------------------------------------------------------------------
# 4. map / filter / reduce
# ------------------------------------------------------------------

def total_words(turns: list[Turn]) -> int:
    lengths = map(lambda t: len(t.text.split()), turns)      # map
    long_only = filter(lambda n: n >= 5, lengths)            # filter
    return functools.reduce(lambda a, b: a + b, long_only, 0)  # reduce


# ------------------------------------------------------------------
# 5. Iterators + generators
# ------------------------------------------------------------------

def rolling_window(seq: list[int], k: int) -> Iterator[list[int]]:
    """Custom generator emitting rolling windows of size ``k``."""
    for i in range(len(seq) - k + 1):
        yield seq[i:i + k]


# ------------------------------------------------------------------
# 6. Regular expressions
# ------------------------------------------------------------------

_HASHTAG_RE = re.compile(r"#(\w+)")


def extract_hashtags(text: str) -> list[str]:
    return _HASHTAG_RE.findall(text)


# ------------------------------------------------------------------
# 7. Closures + partial functions
# ------------------------------------------------------------------

def make_weighter(bias: float) -> Callable[[float], float]:
    """A closure that captures ``bias`` from the enclosing scope."""
    def weight(score: float) -> float:
        return score * bias
    return weight


round2 = functools.partial(round, ndigits=2)  # partial application


# ------------------------------------------------------------------
# 8. Decorators
# ------------------------------------------------------------------

def announce(fn: Callable) -> Callable:
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        print(f"-> {fn.__name__}({args=}, {kwargs=})")
        result = fn(*args, **kwargs)
        print(f"<- {fn.__name__} returned {result!r}")
        return result
    return wrapper


# ------------------------------------------------------------------
# 9. Serialization
# ------------------------------------------------------------------

def serialise_demo(turns: list[Turn]) -> str:
    import json
    return json.dumps([t.to_tuple() for t in turns], indent=2)


# ------------------------------------------------------------------
# 10. Overloading via singledispatch
# ------------------------------------------------------------------

@functools.singledispatch
def describe(obj) -> str:
    return f"<generic {type(obj).__name__}>"


@describe.register
def _(obj: str) -> str:
    return f"<str len={len(obj)}>"


@describe.register
def _(obj: list) -> str:
    return f"<list of {len(obj)}>"


# ------------------------------------------------------------------
# Runnable demo
# ------------------------------------------------------------------

@announce
def _run() -> None:
    turns = [
        Turn("historian", "In 1848 a wave of revolutions swept Europe.", Confidence.HIGH),
        Turn("scientist", "Effect size was modest but statistically significant.", Confidence.MEDIUM),
        Turn("poet", "History is a river we can only wade in once.", Confidence.LOW),
        Turn("skeptic", "But is the sample representative? #evidence #stats", Confidence.HIGH),
        Turn("child", "But why did they fight?", Confidence.LOW),
    ]
    print("comprehensions:", comprehensions_demo(turns))
    print("total_words   :", total_words(turns))
    print("rolling window:", list(rolling_window([1, 2, 3, 4, 5], 3)))
    print("hashtags      :", extract_hashtags(turns[3].text))

    heavy = make_weighter(1.6)
    print("weighted(0.5) :", round2(heavy(0.5)))

    print("describe(str) :", describe("hello"))
    print("describe(list):", describe([1, 2]))
    print("describe(int) :", describe(42))

    print(serialise_demo(turns))


if __name__ == "__main__":
    _run()
