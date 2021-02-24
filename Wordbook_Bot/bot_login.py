import praw
from decouple import config

def bot_login():
    print ("Logging in..")
    print (config("client_id"))
    try:
        r = praw.Reddit(username = config("reddit_username"),
                password = config("reddit_password"),
                client_id = config("client_id"),
                client_secret = config("client_secret"),
                user_agent = "https://dashboard.heroku.com/apps/price-check-bot")
        print ("Logged in!")
    except:
        print ("Failed to log in!")
    return r
