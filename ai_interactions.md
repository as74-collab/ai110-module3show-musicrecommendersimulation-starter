# AI Interactions Log

## Phase 1 — Research and Concept Design

**Prompt used**

> Explain how Spotify- or YouTube-style recommenders use collaborative filtering and content-based filtering. Compare the two approaches and list the important data types, including likes, skips, replays, playlists, tempo, genre, mood, and listening duration. Then suggest which approach is appropriate for a small, explainable classroom simulation.

**Summary of the response**

The AI explained that collaborative filtering learns from behavior across many users, while content-based filtering compares item attributes with one user's preferences. It recommended content-based scoring for this project because the dataset is small and the reasons can remain transparent.

**My verification**

I checked that the final design does not claim to use real collaborative data. The README clearly labels VibeCompass as a content-based simulation.

## Phase 2 — Dataset and Scoring Design

**Prompt used**

> Analyze the columns in songs.csv. Suggest a diverse expansion of 10 songs and at least five advanced features. Design a closeness formula that rewards a song for being near a user's numerical target instead of always rewarding higher values. Suggest balanced weights where genre matters, but does not overpower mood, energy, valence, danceability, tempo, and acousticness.

**Summary of the response**

The AI proposed a normalized similarity formula: `1 - absolute difference / feature range`, clamped from 0 to 1. It suggested popularity, release year, instrumentalness, speechiness, duration, explicit status, and detailed mood tags. It also suggested keeping popularity as a user preference rather than an automatic quality bonus.

**My verification**

I manually checked that all 20 CSV rows have the same 17 headers. I confirmed that 0-to-1 features stay in range, popularity stays from 0 to 100, years are plausible, and every row loads with the correct Python types.

## Phase 3 — Core Implementation

**Prompt used**

> Implement load_songs with Python's csv module, convert numeric and Boolean columns, validate required headers, and raise clear errors. Implement score_song so it returns `(numeric_score, list_of_reasons)`. Implement recommend_songs with sorted ranking, stable tie behavior, top-k selection, explanations, type hints, and one-line docstrings. Preserve the starter Song, UserProfile, and Recommender APIs so the provided tests still pass.

**Summary of the response**

The AI generated CSV loading, weighted scoring, OOP and functional interfaces, ranking, explanations, validation, and path-safe CLI code.

**My verification**

I inspected each return type and ran the program through `python -m src.main`. I also ran `python -m compileall -q src tests` to catch syntax/import problems.

## Agentic Workflow — Advanced Song Features

**What task did you give the agent?**

I asked the agent to update several connected files in one workflow: expand the catalog, add advanced data fields, modify scoring, extend user preferences, add tests, and update the documentation.

**Prompts used**

> Add at least five advanced song features without breaking the original constructor or starter tests. Update data/songs.csv, Song, UserProfile, load_songs, score_song, tests, README.md, and model_card.md. Keep optional dataclass fields backward-compatible by giving them defaults. Validate every new field and explain which ones affect ranking.

**What did the agent generate or change?**

- Expanded `data/songs.csv` from 10 to 20 fictional songs.
- Added seven advanced attributes.
- Updated CSV type conversion and defaults.
- Added decade, instrumental, mood-tag, popularity, and explicit-content logic.
- Added tests and documentation.

**What did you verify or fix manually?**

I checked that the original `Song(...)` calls still work without supplying the new fields. I verified all CSV rows, confirmed that explicit values become actual Booleans, and ran the full test suite.

## Design Pattern — Multiple Scoring Modes

**Which design pattern did you use?**

I used the **Strategy pattern**.

**How did AI help you brainstorm or implement it?**

I asked for a modular design that avoids a long `if/elif` block inside `score_song`. The AI suggested one strategy interface and separate weight classes for each ranking mode.

**Prompt used**

> Design four switchable ranking modes—balanced, genre-first, mood-first, and energy-focused—using a simple Strategy pattern. Keep the scoring math in one function and let strategies provide only the weights. The CLI should select a mode by name, invalid names should produce a clear error, and tests should prove that different modes can change the winner.

**How does the pattern appear in the final code?**

`ScoringStrategy` is the abstract base. `BalancedStrategy`, `GenreFirstStrategy`, `MoodFirstStrategy`, and `EnergyFocusedStrategy` provide different weight mappings. `get_strategy()` resolves the mode, and both `Recommender` and `recommend_songs()` accept a strategy.

**Manual verification**

I compared genre-first and energy-focused output for the same High-Energy Pop profile. The ordering changed in a sensible way, and the strategy-switch test passed.

## Diversity and Fairness Logic

**Prompt used**

> Add greedy diversity reranking after base scoring. While selecting the top k, subtract a penalty if an artist is already selected and a smaller penalty for a repeated genre. Preserve deterministic tie handling, keep diversity optional, include the penalty in the explanation, and add a test where diversity changes the second recommendation.

**Summary of the response**

The AI added a 2.50 repeated-artist penalty and a 0.55 repeated-genre penalty. The reranker chooses one recommendation at a time using the adjusted score.

**My verification**

I tested diversity on and off. I confirmed that repeated results can move downward and that the explanation reports the penalty. I also noted in the model card that diversity can demote a relevant song.

## Visual Summary Table

**Prompt used**

> Use tabulate to create a readable CLI table with rank, title, artist, genre, mood, score, and reasons. Add command-line options for profile, mode, k, all profiles, and disabling diversity. Make `python -m src.main` work from the repository root.

**Summary of the response**

The AI added a GitHub-style table and an `argparse` CLI. It also changed the import to a package-relative import and added `src/__init__.py`.

**My verification**

I ran the default profile, all four profiles, multiple modes, and the no-diversity option. The table displayed correctly and included score reasons.

## Evaluation and Debugging

**Prompt used**

> Suggest three distinct test profiles and one adversarial profile. Explain what a reasonable top result would be for each. Then create tests for loading, scoring, ranking, strategy changes, diversity, explicit-content penalties, invalid modes, and invalid k values.

**What the AI got wrong or what required review**

During testing, a feature-weight key mismatch caused a `KeyError` for tempo. I corrected the key so `tempo_bpm` is used consistently. The first diversity penalty was also too small to change the crafted test case, so I increased the repeated-artist penalty and reran the tests. This showed why generated code must be executed and reviewed rather than accepted immediately.

**Final verification**

```text
python -m pytest -q
12 passed

python -m compileall -q src tests
compileall passed
```
