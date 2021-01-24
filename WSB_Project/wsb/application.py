from flask import Flask, render_template, g, request
import re
import praw
import sqlite3
import os

app = Flask(__name__)

DATABASE = os.getcwd() + '\database.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_datatbase', None)
    if db is not None:
        db.close()

# Insert information from your registered account with Reddit's API here:
reddit = praw.Reddit(
    client_id="Update",
    client_secret="Update",
    user_agent="Update"
)

commonWords = ['this', 'it', 'but', 'a', 'an', 'the', 'just', 'like', 'me', 'be',
    'into', 'you', 'that', 'is', 'to', 'i', 'sec', 'wsb', 'moon', 'says', 'vs',
    'yolo', 'get', 'for', 'now', 'go', 'get', 'gang', 'etf', 'hold', 'on', 'out', 'red',
    'us', 'ev']

def queryTitles():
    titles = []
    db = get_db()
    # Query wallstreetbets 'hot' posts for their titles (adding a space in the front for regex ease)
    for submission in reddit.subreddit("wallstreetbets").hot(limit=50):
        titles.append(' ' + submission.title)

    posts = db.execute(
        'SELECT DISTINCT title FROM mentions'
    ).fetchall()

    listPosts = []

    for post in posts:
        listPosts.append(post[0])

    titles = [x for x in titles if x not in listPosts]
    return titles

def matches(titles):
    listMatch = {}
    tickerRegex = re.compile(r'(?:\s|\$)[A-Z]{1,4}(?=\s)')

    # Add all matches for regex to list of matches
    for title in titles:
        matches = set(tickerRegex.findall(title))
        matches = [x.strip(' ').strip('$') for x in matches]
        tickers = [x for x in matches if x.lower() not in commonWords]
        for ticker in tickers:
            if ticker not in listMatch:
                listMatch[ticker] = [title]
            else:
                listMatch[ticker].append(title)

    db = get_db()

    for key, values in listMatch.items():
        for value in values:
            symbols = db.execute(
                'INSERT INTO mentions (tickerTitle, ticker, title) VALUES (?, ?, ?)',
                (key + value, key, value)
            )
            db.commit()

@app.route("/", methods = ['GET', 'POST'])
def index():
    if request.method == "POST":
        matches(queryTitles())

    db = get_db()
    posts = db.execute('SELECT DISTINCT ticker, count(ticker) FROM mentions GROUP BY ticker').fetchall()
    return render_template("index.html", posts=posts)
