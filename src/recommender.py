"""Core loading, scoring, ranking, and explanation logic for VibeCompass."""

from __future__ import annotations

import csv
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


SongDict = Dict[str, Any]
Recommendation = Tuple[SongDict, float, str]


@dataclass(frozen=True)
class Song:
    """Represent one catalog song and the attributes used for ranking."""

    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    popularity: int = 50
    release_year: int = 2020
    instrumentalness: float = 0.0
    speechiness: float = 0.05
    duration_min: float = 3.0
    explicit: bool = False
    mood_tags: str = ""

    def as_dict(self) -> SongDict:
        """Return the song as a dictionary compatible with functional APIs."""

        return {
            "id": self.id,
            "title": self.title,
            "artist": self.artist,
            "genre": self.genre,
            "mood": self.mood,
            "energy": self.energy,
            "tempo_bpm": self.tempo_bpm,
            "valence": self.valence,
            "danceability": self.danceability,
            "acousticness": self.acousticness,
            "popularity": self.popularity,
            "release_year": self.release_year,
            "instrumentalness": self.instrumentalness,
            "speechiness": self.speechiness,
            "duration_min": self.duration_min,
            "explicit": self.explicit,
            "mood_tags": self.mood_tags,
        }


@dataclass(frozen=True)
class UserProfile:
    """Represent a user's explicit taste targets."""

    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    target_valence: float = 0.60
    target_danceability: float = 0.60
    target_tempo_bpm: float = 110.0
    target_popularity: int = 50
    target_speechiness: float = 0.05
    preferred_duration_min: float = 3.5
    preferred_decade: Optional[int] = None
    prefers_instrumental: Optional[bool] = None
    explicit_ok: bool = True
    preferred_mood_tags: Tuple[str, ...] = ()

    def as_preferences(self) -> Dict[str, Any]:
        """Convert this profile into the dictionary expected by score_song."""

        return {
            "genre": self.favorite_genre,
            "mood": self.favorite_mood,
            "energy": self.target_energy,
            "acousticness": 0.82 if self.likes_acoustic else 0.18,
            "valence": self.target_valence,
            "danceability": self.target_danceability,
            "tempo_bpm": self.target_tempo_bpm,
            "popularity": self.target_popularity,
            "speechiness": self.target_speechiness,
            "duration_min": self.preferred_duration_min,
            "preferred_decade": self.preferred_decade,
            "prefers_instrumental": self.prefers_instrumental,
            "explicit_ok": self.explicit_ok,
            "mood_tags": list(self.preferred_mood_tags),
        }


class ScoringStrategy(ABC):
    """Define a replaceable set of feature weights for recommendation scoring."""

    name: str

    @property
    @abstractmethod
    def weights(self) -> Mapping[str, float]:
        """Return feature weights for this strategy."""


class BalancedStrategy(ScoringStrategy):
    """Balance categorical matches with several numerical similarities."""

    name = "balanced"
    weights = {
        "genre": 2.00,
        "mood": 1.50,
        "energy": 1.50,
        "valence": 0.85,
        "danceability": 0.75,
        "tempo_bpm": 0.55,
        "acousticness": 0.60,
        "popularity": 0.35,
        "speechiness": 0.25,
        "duration_min": 0.20,
        "decade": 0.45,
        "instrumentalness": 0.45,
        "mood_tags": 0.55,
    }


class GenreFirstStrategy(ScoringStrategy):
    """Place the strongest emphasis on matching the requested genre."""

    name = "genre-first"
    weights = {
        "genre": 3.50,
        "mood": 1.20,
        "energy": 1.00,
        "valence": 0.45,
        "danceability": 0.45,
        "tempo_bpm": 0.35,
        "acousticness": 0.35,
        "popularity": 0.25,
        "speechiness": 0.18,
        "duration_min": 0.15,
        "decade": 0.30,
        "instrumentalness": 0.30,
        "mood_tags": 0.35,
    }


class MoodFirstStrategy(ScoringStrategy):
    """Favor emotional fit over genre labels."""

    name = "mood-first"
    weights = {
        "genre": 1.10,
        "mood": 3.25,
        "energy": 1.10,
        "valence": 1.10,
        "danceability": 0.50,
        "tempo_bpm": 0.35,
        "acousticness": 0.45,
        "popularity": 0.20,
        "speechiness": 0.25,
        "duration_min": 0.18,
        "decade": 0.25,
        "instrumentalness": 0.35,
        "mood_tags": 1.00,
    }


class EnergyFocusedStrategy(ScoringStrategy):
    """Favor energy, tempo, and danceability for activity-based listening."""

    name = "energy-focused"
    weights = {
        "genre": 0.85,
        "mood": 0.90,
        "energy": 3.25,
        "valence": 0.55,
        "danceability": 1.35,
        "tempo_bpm": 1.20,
        "acousticness": 0.35,
        "popularity": 0.20,
        "speechiness": 0.20,
        "duration_min": 0.15,
        "decade": 0.20,
        "instrumentalness": 0.25,
        "mood_tags": 0.35,
    }


STRATEGIES: Dict[str, ScoringStrategy] = {
    strategy.name: strategy
    for strategy in (
        BalancedStrategy(),
        GenreFirstStrategy(),
        MoodFirstStrategy(),
        EnergyFocusedStrategy(),
    )
}


def get_strategy(mode: str | ScoringStrategy = "balanced") -> ScoringStrategy:
    """Resolve a strategy instance from a mode name or existing strategy."""

    if isinstance(mode, ScoringStrategy):
        return mode
    normalized = str(mode).strip().lower().replace("_", "-")
    try:
        return STRATEGIES[normalized]
    except KeyError as exc:
        valid = ", ".join(sorted(STRATEGIES))
        raise ValueError(f"Unknown scoring mode '{mode}'. Choose one of: {valid}.") from exc


class Recommender:
    """Provide an object-oriented interface to the same scoring and ranking logic."""

    def __init__(self, songs: Sequence[Song], mode: str | ScoringStrategy = "balanced"):
        self.songs = list(songs)
        self.strategy = get_strategy(mode)

    def recommend(
        self,
        user: UserProfile,
        k: int = 5,
        *,
        diversity: bool = True,
    ) -> List[Song]:
        """Return the highest-ranked Song objects for a user."""

        song_dicts = [song.as_dict() for song in self.songs]
        ranked = recommend_songs(
            user.as_preferences(),
            song_dicts,
            k=k,
            mode=self.strategy,
            diversity=diversity,
        )
        songs_by_id = {song.id: song for song in self.songs}
        return [songs_by_id[int(item[0]["id"])] for item in ranked]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Explain the positive and negative factors in one recommendation."""

        score, reasons = score_song(
            user.as_preferences(), song.as_dict(), mode=self.strategy
        )
        return f"Score {score:.2f}: " + "; ".join(reasons)


_REQUIRED_COLUMNS = {
    "id",
    "title",
    "artist",
    "genre",
    "mood",
    "energy",
    "tempo_bpm",
    "valence",
    "danceability",
    "acousticness",
}

_FLOAT_COLUMNS = {
    "energy",
    "tempo_bpm",
    "valence",
    "danceability",
    "acousticness",
    "instrumentalness",
    "speechiness",
    "duration_min",
}
_INT_COLUMNS = {"id", "popularity", "release_year"}


def _parse_bool(value: Any) -> bool:
    """Convert common CSV truthy values to bool."""

    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _clamp(value: float, lower: float, upper: float) -> float:
    """Clamp a number to an inclusive range."""

    return max(lower, min(upper, value))


def load_songs(csv_path: str) -> List[SongDict]:
    """Load and type-convert songs from a CSV catalog."""

    path = Path(csv_path)
    if not path.is_file():
        raise FileNotFoundError(f"Song catalog not found: {path}")

    songs: List[SongDict] = []
    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        fieldnames = set(reader.fieldnames or [])
        missing = sorted(_REQUIRED_COLUMNS - fieldnames)
        if missing:
            raise ValueError(f"CSV is missing required columns: {', '.join(missing)}")

        for row_number, row in enumerate(reader, start=2):
            try:
                song: SongDict = {
                    key: (value.strip() if isinstance(value, str) else value)
                    for key, value in row.items()
                }
                for column in _FLOAT_COLUMNS & song.keys():
                    song[column] = float(song[column] or 0)
                for column in _INT_COLUMNS & song.keys():
                    song[column] = int(float(song[column] or 0))
                if "explicit" in song:
                    song["explicit"] = _parse_bool(song["explicit"])
                song.setdefault("popularity", 50)
                song.setdefault("release_year", 2020)
                song.setdefault("instrumentalness", 0.0)
                song.setdefault("speechiness", 0.05)
                song.setdefault("duration_min", 3.0)
                song.setdefault("explicit", False)
                song.setdefault("mood_tags", "")
                songs.append(song)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid value in CSV row {row_number}: {exc}") from exc

    if not songs:
        raise ValueError("Song catalog is empty.")
    return songs


def _similarity(value: float, target: float, scale: float = 1.0) -> float:
    """Return a 0-to-1 closeness score between a value and target."""

    if scale <= 0:
        raise ValueError("Similarity scale must be positive.")
    return _clamp(1.0 - abs(float(value) - float(target)) / scale, 0.0, 1.0)


def _normalized_tags(value: Any) -> set[str]:
    """Normalize comma/pipe-separated tags or an iterable into lowercase tokens."""

    if value is None:
        return set()
    if isinstance(value, str):
        raw_tags = value.replace("|", ",").split(",")
    elif isinstance(value, Iterable):
        raw_tags = value
    else:
        raw_tags = [value]
    return {str(tag).strip().lower() for tag in raw_tags if str(tag).strip()}


def score_song(
    user_prefs: Mapping[str, Any],
    song: Mapping[str, Any],
    mode: str | ScoringStrategy = "balanced",
) -> Tuple[float, List[str]]:
    """Score one song against a user profile and return human-readable reasons."""

    strategy = get_strategy(mode)
    weights = strategy.weights
    score = 0.0
    reasons: List[str] = []

    preferred_genre = str(
        user_prefs.get("genre", user_prefs.get("favorite_genre", ""))
    ).strip().lower()
    preferred_mood = str(
        user_prefs.get("mood", user_prefs.get("favorite_mood", ""))
    ).strip().lower()

    if preferred_genre and str(song.get("genre", "")).lower() == preferred_genre:
        score += weights["genre"]
        reasons.append(f"genre match (+{weights['genre']:.2f})")
    if preferred_mood and str(song.get("mood", "")).lower() == preferred_mood:
        score += weights["mood"]
        reasons.append(f"mood match (+{weights['mood']:.2f})")

    numerical_targets = (
        ("energy", "energy", 1.0),
        ("valence", "valence", 1.0),
        ("danceability", "danceability", 1.0),
        ("tempo_bpm", "tempo_bpm", 100.0),
        ("acousticness", "acousticness", 1.0),
        ("popularity", "popularity", 100.0),
        ("speechiness", "speechiness", 1.0),
        ("duration_min", "duration_min", 5.0),
    )
    for preference_key, weight_key, scale in numerical_targets:
        if preference_key not in user_prefs or user_prefs[preference_key] is None:
            continue
        if preference_key not in song:
            continue
        similarity = _similarity(song[preference_key], user_prefs[preference_key], scale)
        points = weights[weight_key] * similarity
        score += points
        reasons.append(f"{preference_key} similarity {similarity:.0%} (+{points:.2f})")

    preferred_decade = user_prefs.get("preferred_decade")
    if preferred_decade is not None and song.get("release_year"):
        song_decade = (int(song["release_year"]) // 10) * 10
        decade_similarity = _similarity(song_decade, int(preferred_decade), 40.0)
        points = weights["decade"] * decade_similarity
        score += points
        reasons.append(f"release-era similarity {decade_similarity:.0%} (+{points:.2f})")

    instrumental_preference = user_prefs.get("prefers_instrumental")
    if instrumental_preference is not None:
        target = 0.85 if bool(instrumental_preference) else 0.10
        instrumental_similarity = _similarity(song.get("instrumentalness", 0), target)
        points = weights["instrumentalness"] * instrumental_similarity
        score += points
        reasons.append(
            f"instrumental fit {instrumental_similarity:.0%} (+{points:.2f})"
        )

    preferred_tags = _normalized_tags(user_prefs.get("mood_tags"))
    song_tags = _normalized_tags(song.get("mood_tags"))
    if preferred_tags:
        overlap = preferred_tags & song_tags
        tag_similarity = len(overlap) / len(preferred_tags)
        points = weights["mood_tags"] * tag_similarity
        score += points
        matched = ", ".join(sorted(overlap)) if overlap else "none"
        reasons.append(f"mood-tag fit [{matched}] (+{points:.2f})")

    if not bool(user_prefs.get("explicit_ok", True)) and _parse_bool(song.get("explicit", False)):
        score -= 2.0
        reasons.append("explicit-content mismatch (-2.00)")

    if not reasons:
        reasons.append("no explicit preference matched (+0.00)")
    return round(score, 4), reasons


def recommend_songs(
    user_prefs: Mapping[str, Any],
    songs: Sequence[SongDict],
    k: int = 5,
    mode: str | ScoringStrategy = "balanced",
    *,
    diversity: bool = True,
    artist_penalty: float = 2.50,
    genre_penalty: float = 0.55,
) -> List[Recommendation]:
    """Rank songs and optionally rerank them to improve artist/genre diversity."""

    if k < 0:
        raise ValueError("k must be zero or greater.")
    if k == 0 or not songs:
        return []

    strategy = get_strategy(mode)
    candidates: List[Dict[str, Any]] = []
    for original_index, song in enumerate(songs):
        base_score, reasons = score_song(user_prefs, song, mode=strategy)
        candidates.append(
            {
                "song": song,
                "base_score": base_score,
                "reasons": reasons,
                "index": original_index,
            }
        )

    if not diversity:
        ordered = sorted(
            candidates,
            key=lambda item: (-item["base_score"], item["index"]),
        )[:k]
        return [
            (
                item["song"],
                item["base_score"],
                f"{strategy.name} mode: " + "; ".join(item["reasons"]),
            )
            for item in ordered
        ]

    selected: List[Recommendation] = []
    selected_artists: Dict[str, int] = {}
    selected_genres: Dict[str, int] = {}
    remaining = list(candidates)

    while remaining and len(selected) < min(k, len(songs)):
        reranked: List[Tuple[float, int, Dict[str, Any], float, List[str]]] = []
        for item in remaining:
            song = item["song"]
            artist_key = str(song.get("artist", "")).strip().lower()
            genre_key = str(song.get("genre", "")).strip().lower()
            duplicate_artist_count = selected_artists.get(artist_key, 0)
            duplicate_genre_count = selected_genres.get(genre_key, 0)
            penalty = (
                artist_penalty * duplicate_artist_count
                + genre_penalty * duplicate_genre_count
            )
            adjusted_score = item["base_score"] - penalty
            diversity_reasons: List[str] = []
            if duplicate_artist_count:
                diversity_reasons.append(
                    f"repeat-artist diversity penalty (-{artist_penalty * duplicate_artist_count:.2f})"
                )
            if duplicate_genre_count:
                diversity_reasons.append(
                    f"repeat-genre diversity penalty (-{genre_penalty * duplicate_genre_count:.2f})"
                )
            reranked.append(
                (
                    adjusted_score,
                    item["index"],
                    item,
                    penalty,
                    diversity_reasons,
                )
            )

        adjusted_score, _, winner, _, diversity_reasons = max(
            reranked, key=lambda entry: (entry[0], -entry[1])
        )
        song = winner["song"]
        all_reasons = winner["reasons"] + diversity_reasons
        explanation = f"{strategy.name} mode: " + "; ".join(all_reasons)
        selected.append((song, round(adjusted_score, 4), explanation))

        artist_key = str(song.get("artist", "")).strip().lower()
        genre_key = str(song.get("genre", "")).strip().lower()
        selected_artists[artist_key] = selected_artists.get(artist_key, 0) + 1
        selected_genres[genre_key] = selected_genres.get(genre_key, 0) + 1
        remaining.remove(winner)

    return selected
