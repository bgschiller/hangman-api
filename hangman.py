import os
import random
from functools import wraps
from flask import Flask, request, session, jsonify

app = Flask(__name__)

app.secret_key = os.getenv('FLASK_SECRET_KEY', 'moosefeathers')
app.debug = False

with open('google-10000-english-usa-no-swears-medium.txt') as f:
    WORDS = [w.strip() for w in f]

def new_puzzle(word=None):
    word = word or random.choice(WORDS)
    return {
        'word_so_far': list('_' * len(word)),
        'actual_word': word.upper(),
        'guesses': [],
    }

class PuzzleError(Exception):
    def __init__(self, message, code):
        Exception.__init__(self)
        self.message = message
        self.code = code
    def to_dict(self):
        return {
            'message': self.message,
            'code': self.code,
        }

@app.errorhandler(PuzzleError)
def handle_puzzle_error(error):
    response = jsonify(error.to_dict())
    response.status_code = 400
    return response

@app.after_request
def add_cors(resp):
    """ Ensure all responses have the CORS headers. This ensures any failures are also accessible
        by the client. """
    resp.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin','*')
    resp.headers['Access-Control-Allow-Credentials'] = 'true'
    resp.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS, GET'
    resp.headers['Access-Control-Allow-Headers'] = request.headers.get(
        'Access-Control-Request-Headers', 'Authorization' )
    # set low for debugging
    if app.debug:
        resp.headers['Access-Control-Max-Age'] = '1'
    return resp

def game_in_progress(view):
    @wraps(view)
    def check_game_in_progress(*args, **kwargs):
        if 'puzzle' not in session:
            raise PuzzleError(
                "Couldn't find a game for you. Please visit /new_game",
                code='no_game_in_progress')
        return view(*args, **kwargs)
    return check_game_in_progress

def make_guess(puzzle, letter):
    if len(letter) != 1 or not letter.isalpha():
        raise PuzzleError(
            'Expected guess to be one letter, received "{}"'.format(letter),
            code='invalid_guess')
    if letter in puzzle['guesses'] or letter in puzzle['word_so_far']:
        raise PuzzleError(
            "You've already guessed that letter!",
            code='already_guessed_letter')
    if len(puzzle['guesses']) >= 6:
        raise PuzzleError(
            "You're out of guesses",
            code='out_of_guesses')
    if '_' not in puzzle['word_so_far']:
        raise PuzzleError(
            "You've solved the puzzle!",
            code='already_solved')

    if letter.lower() not in puzzle['actual_word'].lower():
        puzzle['guesses'].append(letter.upper())
        session['puzzle'] = puzzle
        return {
            'new_state': hide_word(puzzle),
            'guess_result': 'not_found',
            'action': 'guess',
        }
    puzzle['word_so_far'] = list(puzzle['word_so_far'])
    for ix, loc in enumerate(puzzle['actual_word']):
        if loc.lower() == letter.lower():
            puzzle['word_so_far'][ix] = loc
    session['puzzle'] = puzzle
    return {
        'new_state': hide_word(puzzle),
        'guess_result': 'found' if '_' in puzzle['word_so_far'] else 'solved',
        'action': 'guess',
    }

def hide_word(puzzle):
    d = {
        'word_so_far': puzzle['word_so_far'],
        'guesses': puzzle['guesses'],
    }
    if len(d['guesses']) >= 6 or '_' not in d['word_so_far']:
        # if already solved, or too many guesses
        d['actual_word'] = puzzle['actual_word']
    return d

@app.route('/new_game')
def new_game():
    session['puzzle'] = new_puzzle()
    return jsonify(
        new_state=hide_word(session['puzzle']),
        action='new_game',
    )

@app.route('/guess/<letter>')
@game_in_progress
def guess(letter):
    puzzle = session['puzzle']
    return jsonify(**make_guess(puzzle, letter))


@app.route('/')
def index():
    if 'puzzle' in session:
        return jsonify(
            new_state=hide_word(session['puzzle']),
            action='get_state',
        )
    return new_game()

if __name__ == '__main__':
    app.run()
