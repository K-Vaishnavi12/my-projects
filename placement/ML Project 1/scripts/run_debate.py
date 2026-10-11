"""Run one debate from the command line (no UI needed).

Usage:
    python scripts/run_debate.py "Is progress in AI good for humanity?"
    python scripts/run_debate.py "..." --topic science --rounds 2
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from symposium.agents.orchestrator import Symposium


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("question", help="The debate question")
    ap.add_argument("--topic", default=None, help="Force topic bucket")
    ap.add_argument("--rounds", type=int, default=1, help="Rounds per persona")
    args = ap.parse_args()

    sym = Symposium(rounds=args.rounds)

    def on_turn(t):
        print(f"\n--- {t.persona_key.upper()} (turn {t.turn_index}) ---")
        print(t.content)
        if t.stance_label:
            print(f"[svm={t.stance_label} {t.stance_score:.2f}]", end=" ")
        if t.agreement_score is not None:
            print(f"[agreement={t.agreement_score:.2f}]", end=" ")
        print(f"[latency={t.latency_ms} ms]")

    result = sym.run(args.question, topic=args.topic, on_turn=on_turn)
    print("\n=================== MODERATOR ===================")
    if result.verdict:
        print(result.verdict.summary_markdown)
        print(f"\nConsensus: {result.verdict.consensus_score:.2f}")
        print(f"Winner: {result.verdict.winner_persona}")
    sym.close()


if __name__ == "__main__":
    main()
