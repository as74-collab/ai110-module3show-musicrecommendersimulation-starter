"""Command-line interface for the VibeCompass music recommender."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from tabulate import tabulate

from .recommender import STRATEGIES, Recommendation, load_songs, recommend_songs


PROFILES: Dict[str, Dict[str, Any]] = {
    "high-energy-pop": {
        "genre": "pop",
        "mood": "happy",
        "energy": 0.85,
        "valence": 0.82,
        "danceability": 0.84,
        "tempo_bpm": 125,
        "acousticness": 0.18,
        "popularity": 80,
        "speechiness": 0.06,
        "duration_min": 3.4,
        "preferred_decade": 2020,
        "prefers_instrumental": False,
        "explicit_ok": True,
        "mood_tags": ["euphoric", "uplifting"],
    },
    "chill-lofi": {
        "genre": "lofi",
        "mood": "chill",
        "energy": 0.34,
        "valence": 0.58,
        "danceability": 0.54,
        "tempo_bpm": 76,
        "acousticness": 0.82,
        "popularity": 48,
        "speechiness": 0.03,
        "duration_min": 3.1,
        "preferred_decade": 2020,
        "prefers_instrumental": True,
        "explicit_ok": False,
        "mood_tags": ["dreamy", "focused"],
    },
    "deep-intense-rock": {
        "genre": "rock",
        "mood": "intense",
        "energy": 0.93,
        "valence": 0.42,
        "danceability": 0.58,
        "tempo_bpm": 150,
        "acousticness": 0.08,
        "popularity": 65,
        "speechiness": 0.07,
        "duration_min": 4.2,
        "preferred_decade": 2010,
        "prefers_instrumental": False,
        "explicit_ok": True,
        "mood_tags": ["aggressive", "dramatic"],
    },
    "conflicted-sad-workout": {
        "genre": "ambient",
        "mood": "sad",
        "energy": 0.90,
        "valence": 0.20,
        "danceability": 0.78,
        "tempo_bpm": 140,
        "acousticness": 0.65,
        "popularity": 40,
        "speechiness": 0.04,
        "duration_min": 4.5,
        "preferred_decade": 2020,
        "prefers_instrumental": True,
        "explicit_ok": False,
        "mood_tags": ["melancholic", "powerful"],
    },
}


def _catalog_path() -> Path:
    """Return the catalog path regardless of the current working directory."""

    return Path(__file__).resolve().parents[1] / "data" / "songs.csv"


def _shorten(text: str, width: int = 88) -> str:
    """Shorten a long explanation without hiding the score factors entirely."""

    return text if len(text) <= width else text[: width - 3].rstrip() + "..."


def recommendation_table(recommendations: Sequence[Recommendation]) -> str:
    """Format recommendations as a readable terminal table with explanations."""

    rows: List[List[Any]] = []
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        rows.append(
            [
                rank,
                song["title"],
                song["artist"],
                song["genre"],
                song["mood"],
                f"{score:.2f}",
                _shorten(explanation),
            ]
        )
    return tabulate(
        rows,
        headers=["#", "Title", "Artist", "Genre", "Mood", "Score", "Reasons"],
        tablefmt="github",
        stralign="left",
        numalign="right",
    )


def run_profile(
    name: str,
    songs: Sequence[Dict[str, Any]],
    *,
    mode: str,
    k: int,
    diversity: bool,
) -> List[Recommendation]:
    """Run and print one named profile."""

    profile = PROFILES[name]
    recommendations = recommend_songs(
        profile,
        songs,
        k=k,
        mode=mode,
        diversity=diversity,
    )
    print(f"\nProfile: {name}")
    print(f"Mode: {mode} | Diversity reranking: {'on' if diversity else 'off'}")
    print(recommendation_table(recommendations))
    return recommendations


def build_parser() -> argparse.ArgumentParser:
    """Build command-line options for profiles, scoring modes, and diversity."""

    parser = argparse.ArgumentParser(description="Rank songs for a taste profile.")
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILES),
        default="high-energy-pop",
        help="named taste profile to evaluate",
    )
    parser.add_argument(
        "--mode",
        choices=sorted(STRATEGIES),
        default="balanced",
        help="scoring strategy",
    )
    parser.add_argument("-k", type=int, default=5, help="number of recommendations")
    parser.add_argument(
        "--all-profiles",
        action="store_true",
        help="evaluate all built-in profiles",
    )
    parser.add_argument(
        "--no-diversity",
        action="store_true",
        help="disable artist/genre diversity reranking",
    )
    return parser


def main(argv: Iterable[str] | None = None) -> None:
    """Load the catalog and print ranked, explained recommendations."""

    args = build_parser().parse_args(list(argv) if argv is not None else None)
    songs = load_songs(str(_catalog_path()))
    print(f"Loaded songs: {len(songs)}")

    profile_names = sorted(PROFILES) if args.all_profiles else [args.profile]
    for profile_name in profile_names:
        run_profile(
            profile_name,
            songs,
            mode=args.mode,
            k=args.k,
            diversity=not args.no_diversity,
        )


if __name__ == "__main__":
    main()
