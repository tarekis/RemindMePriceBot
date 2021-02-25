import praw
from decouple import config


def bot_login():
    print("Logging in..")
    try:
        r = praw.Reddit(
            username=config("reddit_username"),
            password=config("reddit_password"),
            client_id=config("client_id"),
            client_secret=config("client_secret"),
            user_agent="python.heroku.tarekis.price-check-bot:v0.0.1 (by u/Tarekis)"
        )
        print("Logged in!")
    except:
        print("Failed to log in!")
    return r
