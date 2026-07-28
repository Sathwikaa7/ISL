"""Fast, forgiving word suggestions for the alphabet recognition mode."""

from functools import lru_cache
from pathlib import Path

from rapidfuzz import fuzz


MINIMUM_LETTERS = 3
MAX_SUGGESTIONS = 6


def load_words(dictionary_path):
    """Read and normalise the project's newline-delimited English dictionary."""
    with Path(dictionary_path).open("r", encoding="utf-8") as dictionary_file:
        return tuple(
            sorted(
                {
                    cleaned_word
                    for word in dictionary_file
                    for cleaned_word in (word.strip().lower(),)
                    if cleaned_word.isalpha() and MINIMUM_LETTERS <= len(cleaned_word) <= 20
                }
            )
        )


def _score(letter_sequence, word):
    """Score signed order and an order-tolerant representation of the letters."""
    ordered_score = fuzz.WRatio(letter_sequence, word) / 100
    unordered_score = fuzz.ratio(
        "".join(sorted(letter_sequence)), "".join(sorted(word))
    ) / 100
    return max(ordered_score, unordered_score * 0.95)


def make_suggester(words):
    """Create a cached suggestion function for one already-loaded dictionary."""

    @lru_cache(maxsize=256)
    def suggest(letter_sequence, limit=MAX_SUGGESTIONS):
        query = "".join(character for character in letter_sequence.lower() if character.isalpha())
        if len(query) < MINIMUM_LETTERS:
            return ()

        matches = [(word, _score(query, word)) for word in words]
        matches.sort(key=lambda item: (-item[1], len(item[0]), item[0]))
        return tuple(
            {"word": word, "score": round(score, 3)}
            for word, score in matches[:limit]
        )

    return suggest
