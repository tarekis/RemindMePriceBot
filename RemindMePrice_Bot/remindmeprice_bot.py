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

# guess old posts wont be replyable so send a message instead then
def reply_to_comment(r, comment_id, comment_reply, dictionary_type, comment_subreddit, comment_author, comment_body):
    try:
        comment_to_be_replied_to = r.comment(id=comment_id)
        comment_to_be_replied_to.reply(comment_reply)
        print ("\nReply details:\nDictionary: {}\nSubreddit: r/{}\nComment: \"{}\"\nUser: u/{}\a". format(dictionary_type, comment_subreddit, comment_body, comment_author))

    # Probably low karma so can't comment as frequently
    except Exception as e:
        time_remaining = 15
        if (str(e).split()[0] == "RATELIMIT:"):
            for i in str(e).split():
                if (i.isdigit()):
                    time_remaining = int(i)
                    break
            if (not "seconds" or not "second" in str(e).split()):
                time_remaining *= 60

        print (str(e.__class__.__name__) + ": " + str(e))
        for i in range(time_remaining, 0, -5):
            print ("Retrying in", i, "seconds..")
            time.sleep(5)

def run_bot(r, created_utc, conn):
    try:
        comment_url = "https://api.pushshift.io/reddit/search/comment/?q=" + command + "&sort=desc&size=50&fields=author,body,created_utc,id,subreddit&after=" + created_utc

        if (len(parsed_comment_json["data"]) > 0):
            created_utc = parsed_comment_json["data"][0]["created_utc"]

            # cur.execute("UPDATE comment_time SET created_utc = {}". format(created_utc))
            # cur.execute("SELECT created_utc from comment_time")
            # conn.commit()

            for command in parsed_comment_json["data"]:

                comment_author = comment["author"]
                comment_body = comment["body"]
                comment_id = comment["id"]
                comment_subreddit = comment["subreddit"]

                if (command in comment_body.lower() and comment_author != reddit_username):
                    print ("\n\nFound a comment!")
                    # word = re.compile("!dict(.*)$").search(comment_body).group(1)

                    ticker = yf.Ticker("GME")

                    comment_reply = "GME: " + ticker.info

                    # Bottom Section
                    comment_reply += "\n\n\n\n---\n\n^(Beep boop. I am a bot. If there are any issues, contact my) [^Master ](https://www.reddit.com/message/compose/?to=Tarekis&subject=/u/RemindMePriceBot)"

                    reply_to_comment(r, comment_id, comment_reply, dictionary_type, comment_subreddit, comment_author, comment_body)

                    print ("\nFetching comments..")

    except Exception as e:
        print (str(e.__class__.__name__) + ": " + str(e))

    return str(created_utc)

if __name__ == "__main__":
    while True:
        try:
            r = bot_login.bot_login()

            # DATABASE_URL = config('DATABASE_URL')
            # conn = psycopg2.connect(DATABASE_URL, sslmode='require')
            # cur = conn.cursor()
            # cur.execute("SELECT created_utc from comment_time")
            # created_utc = cur.fetchall()

            if (len(created_utc) > 0):
                created_utc = str(created_utc[0][0])
            else:
                created_utc = ""

            print ("\nFetching comments..")
            while True:
                # Fetching all new comments that were created after created_utc time
                created_utc = run_bot(r, created_utc, conn)
                time.sleep(10)

        except Exception as e:
            print (str(e.__class__.__name__) + ": " + str(e))
            cur.close()
            conn.close()
            time.sleep(15)
