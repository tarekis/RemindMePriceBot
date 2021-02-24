from decouple import config
import bot_login
import json
import os
import praw
import psycopg2
import re
import requests
import time
import yfinance as yf

reddit_username = config("reddit_username")
command = "!botcommandtest_tarekis"
subreddits = [
    # "wallstreetbets"
    "u/RemindMePriceBot"
]

if __name__ == "__main__":
    while True:
        try:
            r = bot_login.bot_login()

            DATABASE_URL = config('DATABASE_URL')
            conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            cur = conn.cursor()
            cur.execute("SELECT * from tasks")
            test = cur.fetchall()

            print(test)

            print ("\nFetching comments..")
            subreddit = reddit.subreddit("+".join(subreddits))
            for submission in subreddit.stream.comments():
                print(comment)

        except Exception as e:
            print (str(e.__class__.__name__) + ": " + str(e))
            cur.close()
            conn.close()
            time.sleep(15)
