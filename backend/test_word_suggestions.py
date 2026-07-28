from pathlib import Path

from backend.utils.rapidfuzz_utils import load_words, make_suggester


def test_suggestions_start_after_three_letters():
    suggest = make_suggester(("hello", "hole", "help"))
    assert suggest("HE") == ()


def test_out_of_order_letters_still_produce_useful_words():
    suggest = make_suggester(("hello", "hole", "help", "world"))
    words = [result["word"] for result in suggest("OHEL")]
    assert "hole" in words
    assert "hello" in words


def test_project_dictionary_loads_cleanly():
    dictionary = Path(__file__).parents[1] / "data" / "english_words.txt"
    assert len(load_words(dictionary)) > 10_000
