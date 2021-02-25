from decouple import config
import re
import requests
import time
import yfinance as yf

environment = config('environment')
reddit_username = config("reddit_username")
command = "!PriceReminderTarekis"
command_lower = command.lower()
base_url = "https://beta.pushshift.io/search/reddit/comments/"


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


def save_task(conn, symbol, target):
    # Just throw the task in the DB
    create_cur = conn.cursor()
    create_cur.execute("""
    WITH cte AS (
        INSERT INTO tasks(symbol, target)
        VALUES (%s, %s)
        ON CONFLICT DO NOTHING
        RETURNING id
    )
    SELECT (SELECT id FROM cte) AS result
    WHERE EXISTS (SELECT 1 FROM cte)
    UNION ALL
    SELECT id
    FROM tasks
    WHERE symbol = %s AND target = %s AND NOT EXISTS (SELECT 1 FROM cte);
    """, (symbol, target, symbol, target))
    id_of_task = create_cur.fetchone()[0]
    conn.commit()
    create_cur.close()

    print(id_of_task)

    return id_of_task


# TODO guess old posts wont be replyable so send a message instead then
def reply_to_comment(reddit, comment_id, comment_reply, comment_author, comment_body):
    try:
        print("\nReply details:\nComment: \"{}\"\nUser: u/{}\a". format(comment_body, comment_author))
        comment_to_be_replied_to = reddit.comment(id=comment_id)
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

        print(str(e.__class__.__name__) + ": " + str(e))
        for i in range(time_remaining, 0, -5):
            print("Retrying in", i, "seconds..")
            time.sleep(5)


def get_comments(conn, reddit, created_utc):
    try:
        # Build the URL to request
        comment_url = build_url({
            "q": command,
            "size": 250,
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
                update_cur = conn.cursor()
                update_cur.execute("UPDATE comment_time SET created_utc = {}". format(created_utc))
                conn.commit()
                update_cur.close()

            process_comments(parsed_comment_json["data"], reddit)

    except Exception as e:
        print(str(e.__class__.__name__) + ": " + str(e))

    print(str(created_utc))
    return str(created_utc)


def process_comments(conn, reddit, comments):
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
            print("\n\nFound a comment!")
            search_results = re.compile(f"{command_lower}\s*([^\s]*)\s*([0-9,.]*)$").search(comment_body.lower())
            symbol_raw = search_results.group(1)
            target_raw = search_results.group(2)

            if (symbol_raw and target_raw):
                symbol = symbol_raw.strip().upper()
                target = target_raw.strip()

                comment_reply_builder = []

                try:
                    # Initiate ticker
                    ticker = yf.Ticker(symbol)

                    comment_reply_builder.append("**Please do not use me yet, I'm not finished yet.**\n\n")

                    # Access ticker into, this is where an error is thrown if the ticker was not found
                    currency = ticker.info["currency"]
                    dayHigh = ticker.info["dayHigh"]

                    comment_reply_builder.append(f"Haven't fully saved your lookup in the DB yet, I actually should tell you when {symbol} hits {target} {currency}\n\n")
                    comment_reply_builder.append(f"I hope you're not sad about it, here's {symbol}'s day high instead: {dayHigh} {currency}.\n\n")

                    id_of_task = save_task(conn, symbol, target)

                    comment_reply_builder.append("Subscribing to this task ID: " + str(id_of_task))

                    # Bottom Section
                    comment_reply_builder.append("\n\n\n\n---\n\n^(Beep boop. I am a bot. If there are any issues, contact my) [^Master ](https://www.reddit.com/message/compose/?to=Tarekis&subject=/u/RemindMePriceBot)")
                except Exception as e:
                    print('error in comment processing')
                    print(e)
                    comment_reply_builder.append("Can't find that ticker, did you write that correctly?")

                comment_reply = "".join(comment_reply_builder)

                reply_to_comment(reddit, comment_id, comment_reply, comment_author, comment_body)


def run(conn, reddit, created_utc):
    return get_comments(conn, reddit, created_utc)
