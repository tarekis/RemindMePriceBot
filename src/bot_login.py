import praw
from decouple import config
import static

def bot_login():
    print("Logging in..")
    try:
        r = praw.Reddit(
            username=config("reddit_username"),
            password=config("reddit_password"),
            client_id=config("client_id"),
            client_secret=config("client_secret"),
            user_agent=static.USER_AGENT
        )
        print("Logged in!")
    except Exception:
        print("Failed to log in!")
    return r
