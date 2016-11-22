from hangman import PuzzleError, make_guess, new_puzzle, WORDS
from hypothesis.strategies import builds, sampled_from, choice
from hypothesis import given

puzzle_strategy = builds(new_puzzle, word=sampled_from(WORDS))
letter_strategy = sampled_from(string.ascii_lowercase)

def assertRaises(func, *args, **kwargs, excClass=PuzzleError):
    try:
        func(*args, **kwargs)
    except excClass:
        return
    assert False, '{} failed to raise {}'.format(func, excClass)

def test_invalid_guess():
    p = new_puzzle()
    assertRaises(make_guess, p, 'loong')
    assertRaises(make_guess, p, '2')
    assertRaises(make_guess, p, ';')

@given(puzzle_strategy, letter_strategy)
def test_uppercase_and_lowercase_equivalent(puzzle, guess):
    assert make_guess(puzzle, guess.lower()) == make_guess(puzzle, guess.upper()), "expected upper- and lower-case case to produce equivalent results"

@given(puzzle_strategy, letter_strategy)
def test_repeat_guess_fails(puzzle, letter):
    make_guess(puzzle, letter)
    assertRaises(make_guess, puzzle, letter)

def test_too_many_guesses_fails():
    p = new_puzzle()
    for g in 'abcdef':
        make_guess(p, g)
    assertRaises(make_guess, p, 'g')

@given(puzzle_strategy, letter_strategy)
def test_already_solved_guess(puzzle, letter):
    for g in set(puzzle['actual_word']):
        make_guess(puzzle, g)
    assertRaises(make_guess, puzzle, letter)

@given(puzzle_strategy, choice)
def test_guess_reveals_all_spots(puzzle, choice):
    guess = choice(set(puzzle['actual_word'])).lower()
    for ix, letter in enumerate(puzzle['actual_word']):
        if letter.lower() == guess:
            assert puzzle['word_so_far'][ix].lower() == guess, "Expected location {} to have been revealed".format(ix)

@given(puzzle_strategy, letter_strategy)
def test_guess_hides_word(puzzle, guess):
    res = make_guess(puzzle, guess)
    assert 'actual_word' not in res['new_state'], "expected actual_word' to have been hidden"

@given(puzzle_strategy)
def test_6th_guess_reveals_word(puzzle):
    guesses = [g for g in string.ascii_lowercase if g not in puzzle['actual_word']]
    for g in guesses[:6]:
        res = make_guess(puzzle, g)
    assert 'actual_word' in res['new_state'], "expected 6th guess to reveal word"

if __name__ == '__main__':
    import nose
    nose.run()
