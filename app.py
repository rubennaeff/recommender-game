"""Super quick n dirty script for a recommender system game."""
from flask import Flask, render_template, escape, url_for, session
import numpy as np

app = Flask(__name__)
app.secret_key = "34447154-463f-464f-ad95-1b090d9bc1b3"

# constants
POSITIVE = '✔️'
NEGATIVE = '❌'
UNKNOWN = '_'
INTERESTS = "📚🎵⚽🍻💃🤺🥊🎭"
nice_output = {'0': NEGATIVE, '1': POSITIVE, UNKNOWN: UNKNOWN}

# config
n_interests = 3
n_users = 3 * n_interests
n_items = 3 * n_interests


@app.route('/reset')
def reset():
    """Clear variables for a new game."""    
    # select subset of possible topics
    nice_topics = dict(enumerate(np.random.choice(list(INTERESTS), size=n_interests, replace=False).tolist()))
    session['nice_topics'] = nice_topics
    
    # each item has exactly one topic, spread equally, and shuffle items
    items = np.array([[item % n_interests == interest for interest in range(n_interests)] for item in range(n_items)])
    items = np.random.permutation(items).astype(int)
    session['items'] = items.tolist()
    session['item_topics'] = [nice_topics[np.where(item)[0][0]] for item in items]

    # each user has exactly one or two interests, spread equally, and shuffle users
    users = np.array([[user % n_interests == interest for interest in range(n_interests)] for user in range(n_users)])
    users = np.random.permutation(users)
    # add second interest to half of them
    second = np.array([[user % n_interests == interest for interest in range(n_interests)] for user in range(n_users)])
    users = users | second * \
        np.concatenate([np.ones(n_users * 2 // 3), np.zeros(n_users - (n_users * 2 // 3))]).reshape(-1, 1).astype(bool)
    users = np.random.permutation(users).astype(int)
    session['users'] = users.tolist()
    session['user_interests'] = ["".join(sorted([nice_topics[i] for i in np.where(user)[0]])) for user in users]

    true_responses = users.dot(items.T).astype(int).tolist()
    true_responses = {user: {item: item_feedback for item, item_feedback in enumerate(user_feedback)} for user, user_feedback in enumerate(true_responses)}
    session['true_responses'] = true_responses
    session['total_score'] = sum([f for d in true_responses.values() for f in d.values()])
    session['feedback'] = {user: {item: UNKNOWN for item in range(n_items)} for user in range(n_users)}
    session['score_found'] = 0
    session['score_misses'] = 0
    return index()

@app.route("/")
def index(): 
    if not 'score_found' in session:
        reset()
    nice_feedback = {
        user: {item: nice_output[str(item_feedback)] for item, item_feedback in user_feedback.items()} 
               for user, user_feedback in session['feedback'].items()}
    return render_template(
        "home.html", feedback=nice_feedback, n_users=n_users, n_items=n_items, 
        item_topics=session['item_topics'], user_interests=session['user_interests'], won=session['score_found'] == session['total_score'],
        found=session['score_found'], harm=session['score_misses'], total_score=session['total_score'])

@app.route('/action/<rec>')
def action(rec):
    try:    
        u, i = rec.split('-')
    except:
        raise ValueError("Fix this please")
    if session['feedback'][u][i] == UNKNOWN:
        session['feedback'][u][i] = session['true_responses'][u][i]
        if session['true_responses'][u][i]:
            session['score_found'] += 1  # number found
        else:
            session['score_misses'] += 1  # miss
    return index()

if __name__ == "__main__":
    app.directory='./'
    app.run(host='127.0.0.1', port=5000)