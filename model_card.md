# 🎧 Model Card: VibeCompass 1.0

## 1. Model Name

**VibeCompass 1.0**

## 2. Goal / Task

VibeCompass suggests songs that match a user's stated taste. It is a classroom simulation for learning how features, weights, ranking, explanations, and bias work. It is not a production recommendation service.

## 3. Intended Use and Non-Intended Use

The intended user is a student or developer exploring a transparent content-based recommender. A user supplies preferences such as genre, mood, energy, tempo, and acousticness. The system assumes those stated preferences describe what the user wants right now.

It should not be used to make high-stakes decisions, infer sensitive traits, label a person's identity, or represent the full quality of an artist's work. It should not be treated as evidence that one genre or song is objectively better than another.

## 4. How the Model Works

The model compares every song with one user profile. Exact genre and mood matches receive fixed points. Numerical features receive more points when the song value is close to the user's target. The program can emphasize different ideas of similarity through balanced, genre-first, mood-first, and energy-focused modes.

After scoring, the songs are sorted from highest to lowest. An optional diversity step lowers the score of repeated artists and genres while selecting the top results. Every recommendation includes reasons so the user can see which matches and penalties affected it.

## 5. Data Used

The catalog contains 20 fictional songs. It includes pop, lofi, rock, ambient, jazz, synthwave, indie pop, electronic, folk, chiptune, classical, hip hop, metal, reggae, R&B, and world music.

The starter features are genre, mood, energy, tempo, valence, danceability, and acousticness. I added popularity, release year, instrumentalness, speechiness, duration, explicit-content status, and detailed mood tags.

The catalog is small and manually designed. It does not represent the full range of languages, cultures, subgenres, artists, production styles, or listener communities.

## 6. Strengths

The system works well when a user has clear preferences that match the catalog. The Chill Lofi profile ranked `Midnight Coding` first, while Deep Intense Rock ranked `Storm Runner` first. Those results matched my intuition.

The reasons make the ranking inspectable. The strategy modes also make it easy to show how the same songs can move when the definition of similarity changes.

## 7. Limitations and Bias

The model can create a filter bubble because exact genre and mood matches receive large rewards. A user may keep seeing familiar categories and miss songs from another genre that share the same musical feel. The small catalog gives more opportunities to categories with several songs, while a genre represented by one song has fewer chances to appear.

The labels are subjective. A song can be both happy and nostalgic, but the main `mood` field stores only one label. Popularity values are fictional and could introduce mainstream bias if given too much weight. The diversity penalty can also demote a highly relevant song just because another selected song has the same artist or genre.

The system does not use lyrics, language, audio embeddings, location, time of day, listening history, skips, replays, or playlist behavior. It cannot tell whether contradictory preferences are intentional.

## 8. Evaluation Process

I tested four profiles and reviewed their top five recommendations:

1. **High-Energy Pop** — `Sunrise City` ranked first.
2. **Chill Lofi** — `Midnight Coding` ranked first.
3. **Deep Intense Rock** — `Storm Runner` ranked first.
4. **Conflicted Sad Workout** — `After the Goodbye` ranked first.

High-Energy Pop and Chill Lofi produced very different lists. This makes sense because one profile rewards high energy and danceability while the other rewards low energy, acousticness, and instrumentalness.

Chill Lofi and Deep Intense Rock also separated clearly. The rock profile moved fast, intense songs upward, while the lofi profile preferred calm and focused songs.

Deep Intense Rock and Conflicted Sad Workout shared a high energy target, but their mood and valence targets differed. The rock profile selected `Storm Runner`; the conflicted profile selected a sad R&B song because its exact mood and valence were more important in balanced mode.

I also ran a weight-shift experiment. In genre-first mode, `Gym Hero` ranked second for the pop profile. In energy-focused mode, `Rooftop Lights` and `Pixel Hearts` moved ahead because their overall activity-related features were closer. This showed that the rankings are sensitive to human-selected weights.

Automated checks cover CSV type conversion, scoring explanations, energy closeness, strategy changes, diversity reranking, explicit-content penalties, invalid modes, and invalid `k` values. All 12 tests passed.

## 9. Observed Behavior

The exact-match labels have a strong effect. However, numerical features let near matches from other genres enter the top list. Diversity reranking increases variety, but it changes the meaning of the displayed score because the final score can include a repetition penalty.

The adversarial profile was the most surprising. It requested ambient, sad, high-energy, danceable, acoustic, and instrumental music at the same time. The system did not understand the contradiction; it simply added the weighted evidence and selected the highest total.

## 10. Future Work

- Learn from likes, skips, replays, and playlist additions.
- Combine content-based ranking with collaborative filtering.
- Use audio or lyric embeddings instead of single manual labels.
- Let users adjust weights and diversity strength.
- Evaluate with a larger, culturally broader dataset and real user feedback.
- Show a score breakdown chart for each recommendation.

## 11. Personal Reflection

My biggest learning moment was realizing that scoring one song and ranking a whole catalog are separate problems. A formula can produce a plausible recommendation, but the final experience also depends on tie handling, diversity, explanations, and the data available.

AI helped me brainstorm additional features, strategy classes, edge cases, and tests. I needed to double-check import paths, CSV conversions, score ranges, return types, and whether changes actually altered the rankings as expected. I was surprised by how intelligent a simple system can feel when the reasons match my intuition. If I extended it, I would add real listening behavior and test whether a hybrid model improves discovery without hiding why a song was recommended.
