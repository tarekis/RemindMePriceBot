import static
import comments
import requests
import time
import yfinance as yf

def build_url(query_paramters_dict):
    url_builder = [static.API_URL, "?"]

    for key in query_paramters_dict.keys():
        value = query_paramters_dict[key]
        if value is not None:
            url_builder.append(f"{key}=")
            url_builder.append(str(value))
            url_builder.append("&")
    url_builder.pop()
    return ''.join(url_builder)


def save_task(conn, symbol, target, direction_is_up, before_condition):
    # Just throw the task in the DB

    values_dict = {
        'symbol': symbol,
        'target': target,
        'direction_is_up': direction_is_up,
    }

    if before_condition is not None:
        values_dict['before_condition'] = before_condition

    print(values_dict)
    keys = values_dict.keys()

    create_cur = conn.cursor()
    create_cur.execute(f"""
    WITH cte AS (
        INSERT INTO tasks({keys})
        VALUES ({"%s" * len(keys)})
        ON CONFLICT DO NOTHING
        RETURNING id
    )
    SELECT (SELECT id FROM cte) AS result
    WHERE EXISTS (SELECT 1 FROM cte)
    UNION ALL
    SELECT id
    FROM tasks
    {"WHERE " + " AND ".join(map(lambda name: f"{name} = %s", keys))}
    AND NOT EXISTS (SELECT 1 FROM cte);
    """, (symbol, target, direction_is_up, before_condition, symbol, target, direction_is_up, before_condition))
    id_of_task = create_cur.fetchone()[0]
    conn.commit()
    create_cur.close()

    print(id_of_task)

    return id_of_task


# TODO guess old posts wont be replyable so send a message instead then
def reply_to_comment(reddit, comment_id, comment_reply, comment_author, comment_body_lower):
    try:
        print("\nReply details:\nComment: \"{}\"\nUser: u/{}\a". format(comment_body_lower, comment_author))
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
            if static.ENVIRONMENT != "development":
                # Update the last comment time in DB so if the bot restarts it can read that value and start where it left off
                update_cur = conn.cursor()
                update_cur.execute("UPDATE comment_time SET created_utc = {}". format(created_utc))
                conn.commit()
                update_cur.close()

            process_comments(conn, reddit, parsed_comment_json["data"])

    except Exception as e:
        print("Fetching comments failed, pushshift API probably is down")
        print(str(e.__class__.__name__) + ": " + str(e))

    print(str(created_utc))
    return str(created_utc)


def process_comments(conn, reddit, comments):
    # Loop over all comments found in this batch
    for comment in comments:
        # Aggregate all used fields
        comment_id = comment["id"]
        comment_author = comment["author"]
        comment_body_lower = comment["body"].lower()

        if (static.COMMAND_LOWER in comment_body_lower and comment_author != static.REDDIT_USERNAME):
            print("\n\nFound a comment!")

            body_details = comments.get_comment_body_details(comment_body_lower)

            comment_reply_builder = ["**Please do not use me yet, I'm not finished yet.**\n\n"]

            if body_details is not None:
                # Deconstruct details
                symbol = body_details['symbol']
                target = body_details['target']
                direction_is_up = body_details['direction_is_up']
                before_condition = body_details['before_condition']
                before_condition_successfull = body_details['before_condition_successfull']

                if before_condition_successfull:
                    try:
                        # Initiate ticker
                        ticker = yf.Ticker(symbol)

                        # Access ticker into, this is where an error is thrown if the ticker was not found
                        currency = ticker.info["currency"]
                        dayHigh = ticker.info["dayHigh"]

                        comment_reply_builder.append(f"Haven't fully saved your lookup in the DB yet, I actually should tell you when {symbol} hits {target} {currency}\n\n")
                        comment_reply_builder.append(f"I hope you're not sad about it, here's {symbol}'s day high instead: {dayHigh} {currency}.\n\n")

                        id_of_task = save_task(conn, symbol, target, direction_is_up, before_condition)

                        comment_reply_builder.append("Subscribing to this task ID: " + str(id_of_task))

                    except Exception as e:
                        print('Error in comment processing')
                        print(e)
                        comment_reply_builder.append(f"Can't find the symbol {symbol}, did you write that correctly?")
                else:
                    comment_reply_builder.append("Your command specified a before time, but the time could not be interpreted.\n\n")
            else:
                comment_reply_builder.append("Your command seems to be malformed, please check it's format.\n\n")

            # Bottom Section
            comment_reply_builder.append("\n\n\n\n---\n\n^(Beep boop. I am a bot. If there are any issues, contact my) [^Master ](https://www.reddit.com/message/compose/?to=Tarekis&subject=/u/RemindMePriceBot)")

            comment_reply = "".join(comment_reply_builder)

            reply_to_comment(reddit, comment_id, comment_reply, comment_author, comment_body_lower)


def run(conn, reddit, created_utc):
    return get_comments(conn, reddit, created_utc)
