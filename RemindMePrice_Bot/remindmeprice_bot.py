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
command = "!PriceReminderTarekis"
command_lower = command.lower()
base_url = "https://beta.pushshift.io/search/reddit/comments/"

environment = config('environment')

def build_url(query_paramters_dict):
    url_builder = [base_url, "?"]

    for key in query_paramters_dict.keys():
        value = query_paramters_dict[key]
        if value is not None:
            url_builder.append(f"{key}=")
            url_builder.append(str(value))
            url_builder.append("&")
    url_builder.pop()
    return ''.join(url_builder)


# guess old posts wont be replyable so send a message instead then
def reply_to_comment(r, comment_id, comment_reply, comment_author, comment_body):
    try:
        print ("\nReply details:\nComment: \"{}\"\nUser: u/{}\a". format(comment_body, comment_author))
        comment_to_be_replied_to = r.comment(id=comment_id)
        comment_to_be_replied_to.reply(comment_reply)

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

def get_comments(r, created_utc):
    try:
        # Build the URL to request
        comment_url = build_url({
            "q": command,
            "size": 100,
            "filter": ",".join([
                "id",
                "author",
                "created_utc",
                "body",
            ]),
            "min_created_utc": created_utc
        })

        print(comment_url)
        # Request and parse the response
        parsed_comment_json = requests.get(comment_url).json()

        # Process comments if any were found
        if (len(parsed_comment_json["data"]) > 0):
            print(parsed_comment_json)

            # Update last comment time so the next request can omit already processed comments by including only >= date + 1
            # This is done only when a comment was recieved because otherwise we'd increase the last comment time for no reason every loop
            created_utc = int(parsed_comment_json["data"][0]["created_utc"]) + 1
            if environment != "development":
                # Update the last comment time in DB so if the bot restarts it can read that value and start where it left off
                cur.execute("UPDATE comment_time SET created_utc = {}". format(created_utc))
                conn.commit()

            process_comments(parsed_comment_json["data"])

    except Exception as e:
        print (str(e.__class__.__name__) + ": " + str(e))

    print(str(created_utc))
    return str(created_utc)

def process_comments(comments):
    # Loop over all comments found in this batch
    for comment in comments:
        # Aggregate all used fields
        comment_author = comment["author"]
        comment_body = comment["body"]
        comment_id = comment["id"]

        print("comment_author")
        print(comment_author)
        print("comment_body")
        print(comment_body)
        print("comment_id")
        print(comment_id)

        if (command_lower in comment_body.lower() and comment_author != reddit_username):
            print ("\n\nFound a comment!")
            search_results = re.compile(f"{command_lower}\s*([^\s]*)\s*([0-9,.]*)$").search(comment_body.lower())
            symbol_raw = search_results.group(1)
            target_raw = search_results.group(2)

            if (symbol_raw and target_raw):
                symbol = symbol_raw.strip().upper()
                target = target_raw.strip()

                comment_reply_builder = []

                try:
                    ticker = yf.Ticker(symbol)

                    comment_reply_builder.append("**Please do not use me yet, I'm not finished yet.**\n\n")

                    currency = ticker.info["currency"]
                    dayHigh = ticker.info["dayHigh"]

                    comment_reply_builder.append(f"Haven't saved your lookup in the DB yet, I actually should tell you when {symbol} hits {target} {currency}\n\n")
                    comment_reply_builder.append(f"I hope you're not sad about it, here's {symbol}'s day high instead: {dayHigh}.")

                    # Bottom Section
                    comment_reply_builder.append("\n\n\n\n---\n\n^(Beep boop. I am a bot. If there are any issues, contact my) [^Master ](https://www.reddit.com/message/compose/?to=Tarekis&subject=/u/RemindMePriceBot)")
                except Exception as e:
                    print('error in comment processing')
                    print(e)
                    comment_reply_builder.append("Can't find that ticker, did you write that correctly?")

                comment_reply = "".join(comment_reply_builder)

                reply_to_comment(r, comment_id, comment_reply, comment_author, comment_body)


if __name__ == "__main__":
    while True:
        try:
            r = bot_login.bot_login()

            if environment != "development":
                # Create DB connection
                DATABASE_URL = config('DATABASE_URL')
                conn = psycopg2.connect(DATABASE_URL, sslmode='require')

                # Create Cursor to get last valid comment_time
                cur = conn.cursor()
                cur.execute("SELECT created_utc from comment_time")
                created_utc = cur.fetchall()

                print(created_utc)

                # Use last comment time or None if not available
                if (len(created_utc) > 0):
                    created_utc = str(created_utc[0][0])
                else:
                    created_utc = None
            else:
                created_utc = None

            print(created_utc)

            print ("\nFetching comments..")
            while True:
                # Fetching all new comments that were created after created_utc time
                created_utc = get_comments(r, created_utc)
                # TODO CHANGE THIS TO 30
                time.sleep(10)

        except Exception as e:
            print (str(e.__class__.__name__) + ": " + str(e))
            # cur.close()
            # conn.close()
            time.sleep(15)
