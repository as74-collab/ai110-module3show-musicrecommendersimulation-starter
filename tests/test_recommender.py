"""Tests for core behavior and all optional extension features."""

from pathlib import Path

import pytest

from src.recommender import (
    Recommender,
    Song,
    UserProfile,
    load_songs,
    recommend_songs,
    score_song,
)


def make_small_recommender() -> Recommender:
    songs = [
        Song(
            id=1,
            title="Test Pop Track",
            artist="Test Artist",
            genre="pop",
            mood="happy",
            energy=0.8,
            tempo_bpm=120,
            valence=0.9,
            danceability=0.8,
            acousticness=0.2,
        ),
        Song(
            id=2,
            title="Chill Lofi Loop",
            artist="Other Artist",
            genre="lofi",
            mood="chill",
            energy=0.4,
            tempo_bpm=80,
            valence=0.6,
            danceability=0.5,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score() -> None:
    user = UserProfile("pop", "happy", 0.8, False)
    results = make_small_recommender().recommend(user, k=2)
    assert len(results) == 2
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string() -> None:
    user = UserProfile("pop", "happy", 0.8, False)
    recommender = make_small_recommender()
    explanation = recommender.explain_recommendation(user, recommender.songs[0])
    assert isinstance(explanation, str)
    assert explanation.strip()
    assert "genre match" in explanation


def test_load_songs_converts_numeric_and_boolean_types() -> None:
    catalog = Path(__file__).parents[1] / "data" / "songs.csv"
    songs = load_songs(str(catalog))
    assert len(songs) == 20
    assert isinstance(songs[0]["id"], int)
    assert isinstance(songs[0]["energy"], float)
    assert isinstance(songs[0]["popularity"], int)
    assert isinstance(songs[0]["explicit"], bool)


def test_score_song_returns_score_and_reasons() -> None:
    prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}
    song = {"genre": "pop", "mood": "happy", "energy": 0.8}
    score, reasons = score_song(prefs, song)
    assert score > 4.0
    assert any("genre match" in reason for reason in reasons)
    assert any("energy similarity" in reason for reason in reasons)


def test_closer_energy_scores_higher() -> None:
    prefs = {"energy": 0.8}
    close_score, _ = score_song(prefs, {"energy": 0.75})
    far_score, _ = score_song(prefs, {"energy": 0.10})
    assert close_score > far_score


def test_scoring_modes_can_change_the_winner() -> None:
    songs = [
        {
            "id": 1,
            "title": "Genre Match",
            "artist": "A",
            "genre": "rock",
            "mood": "calm",
            "energy": 0.2,
        },
        {
            "id": 2,
            "title": "Energy Match",
            "artist": "B",
            "genre": "jazz",
            "mood": "intense",
            "energy": 0.95,
            "danceability": 0.9,
            "tempo_bpm": 150,
        },
    ]
    prefs = {
        "genre": "rock",
        "mood": "intense",
        "energy": 0.95,
        "danceability": 0.9,
        "tempo_bpm": 150,
    }
    genre_first = recommend_songs(prefs, songs, k=1, mode="genre-first", diversity=False)
    energy_first = recommend_songs(
        prefs, songs, k=1, mode="energy-focused", diversity=False
    )
    assert genre_first[0][0]["title"] == "Genre Match"
    assert energy_first[0][0]["title"] == "Energy Match"


def test_diversity_reranking_reduces_repeat_artist_results() -> None:
    songs = [
        {"id": 1, "title": "A1", "artist": "Same", "genre": "pop", "mood": "happy", "energy": 0.9},
        {"id": 2, "title": "A2", "artist": "Same", "genre": "pop", "mood": "happy", "energy": 0.88},
        {"id": 3, "title": "B1", "artist": "Different", "genre": "indie", "mood": "happy", "energy": 0.82},
    ]
    prefs = {"genre": "pop", "mood": "happy", "energy": 0.9}
    plain = recommend_songs(prefs, songs, k=2, diversity=False)
    diverse = recommend_songs(prefs, songs, k=2, diversity=True)
    assert plain[0][0]["artist"] == plain[1][0]["artist"]
    assert diverse[0][0]["artist"] != diverse[1][0]["artist"]


def test_explicit_mismatch_is_penalized() -> None:
    prefs = {"energy": 0.5, "explicit_ok": False}
    clean, _ = score_song(prefs, {"energy": 0.5, "explicit": False})
    explicit, reasons = score_song(prefs, {"energy": 0.5, "explicit": True})
    assert clean > explicit
    assert any("explicit-content mismatch" in reason for reason in reasons)


def test_invalid_mode_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown scoring mode"):
        score_song({"energy": 0.5}, {"energy": 0.5}, mode="mystery")


def test_negative_k_is_rejected() -> None:
    with pytest.raises(ValueError, match="k must be zero or greater"):
        recommend_songs({}, [], k=-1)


def test_all_advanced_features_can_affect_scoring() -> None:
    prefs = {
        "popularity": 80,
        "speechiness": 0.05,
        "duration_min": 3.5,
        "preferred_decade": 2020,
        "prefers_instrumental": True,
        "explicit_ok": False,
        "mood_tags": ["dreamy", "focused"],
    }
    matching_song = {
        "popularity": 80,
        "speechiness": 0.05,
        "duration_min": 3.5,
        "release_year": 2022,
        "instrumentalness": 0.85,
        "explicit": False,
        "mood_tags": "dreamy|focused",
    }
    mismatching_song = {
        "popularity": 5,
        "speechiness": 0.90,
        "duration_min": 8.5,
        "release_year": 1981,
        "instrumentalness": 0.0,
        "explicit": True,
        "mood_tags": "aggressive|dark",
    }
    matching_score, matching_reasons = score_song(prefs, matching_song)
    mismatching_score, mismatching_reasons = score_song(prefs, mismatching_song)

    assert matching_score > mismatching_score
    assert any("popularity similarity" in reason for reason in matching_reasons)
    assert any("speechiness similarity" in reason for reason in matching_reasons)
    assert any("duration_min similarity" in reason for reason in matching_reasons)
    assert any("release-era similarity" in reason for reason in matching_reasons)
    assert any("instrumental fit" in reason for reason in matching_reasons)
    assert any("mood-tag fit" in reason for reason in matching_reasons)
    assert any("explicit-content mismatch" in reason for reason in mismatching_reasons)


def test_k_larger_than_catalog_returns_each_song_once() -> None:
    songs = [
        {"id": 1, "title": "One", "artist": "A", "genre": "pop", "mood": "happy", "energy": 0.8},
        {"id": 2, "title": "Two", "artist": "B", "genre": "rock", "mood": "intense", "energy": 0.9},
    ]
    results = recommend_songs({"energy": 0.8}, songs, k=10)
    assert len(results) == 2
    assert {result[0]["id"] for result in results} == {1, 2}
