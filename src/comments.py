from datetime import datetime
import database
import parsedatetime
import re
import static
import time
import yfinance as yf

cal = parsedatetime.Calendar()


direction_is_up_regex = "hits"
direction_is_down_regex = "drops\s*(?:to)?"
# "Explanation": https://regex101.com/r/svsM5v/1
command_regex = f"{static.COMMAND_LOWER}\s+(?:of\s+)?([^\s]+)\s+(?:(hits|drops\s*(?:to)?)\s+)?([0-9]+(?:[,.][0-9]+)?)(?:\s+(?:(?:before)\s+([^\n]*))?)?"


def get_direction_is_up(direction_raw):
    if direction_raw is None:
        return True
    if re.compile(direction_is_up_regex).search(direction_raw) is not None:
        return True
    if re.compile(direction_is_down_regex).search(direction_raw) is not None:
        return False


def get_before_condition(before_condition_raw):
    if before_condition_raw is None:
        return (None, True)

    before_condition_raw = before_condition_raw.strip()

    time_struct, parse_status = cal.parse(before_condition_raw)

    if parse_status == 1:
        return (datetime(*time_struct[:6]), True)

    return (None, False)


# Process comment body and extract options, or return None if not possible
def get_comment_body_details(comment_body):
    search_results = re.compile(command_regex).search(comment_body)

    if search_results is not None:
        symbol_raw = search_results.group(1)
        direction_raw = search_results.group(2)
        target_raw = search_results.group(3)
        before_condition_raw = search_results.group(4)

        (before_condition, before_condition_successfull) = get_before_condition(before_condition_raw)

        if not (symbol_raw and target_raw):
            return None

        return {
            "symbol": symbol_raw.strip().upper(),
            "target": target_raw.strip(),
            "direction_is_up": get_direction_is_up(direction_raw),
            "before_condition": before_condition,
            "before_condition_successfull": before_condition_successfull
        }

    return None


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


def process_comments(conn, reddit, comments):
    # Loop over all comments found in this batch
    for comment in comments:
        # Aggregate all used fields
        comment_id = comment["id"]
        comment_author = comment["author"]
        comment_body_lower = comment["body"].lower()

        print(static.COMMAND_LOWER)
        print(comment_body_lower)
        print(static.COMMAND_LOWER in comment_body_lower)

        if (static.COMMAND_LOWER in comment_body_lower and comment_author != static.REDDIT_USERNAME):
            print("\n\nFound a comment!")

            body_details = get_comment_body_details(comment_body_lower)

            comment_reply_builder = ["**Please do not use me yet, I'm not finished yet. Command may change, database cleared, etc**\n\n"]

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

                    except Exception as e:
                        print('Error in symbol aquisition')
                        print(e)
                        comment_reply_builder.append(f"Can't find the symbol {symbol}, did you write that correctly?")

                    try:
                        id_of_task = database.save_task(conn, comment_author, symbol, target, direction_is_up, currency, before_condition)

                        print(type(before_condition))
                        print(before_condition)

                        before_string = "" if before_condition is not None else f" before {before_condition}"
                        comment_reply_builder.append(f"I will be messaging you when {symbol} hits {target} {currency}{before_string}\n\n")

                    except Exception as e:
                        print('Error in comment processing')
                        print(e)
                        comment_reply_builder.append(f"Something happend that should have not happend, sorry that happened. Will try to fix it ASAP.")

                else:
                    comment_reply_builder.append("Your command specified a before time, but the time could not be interpreted.\n\n")
            else:
                comment_reply_builder.append("Your command seems to be malformed, please check it's format.\n\n")

            # Bottom Section
            comment_reply_builder.append(static.BOTTOM_REPLY_SECTION)

            comment_reply = "".join(comment_reply_builder)

            reply_to_comment(reddit, comment_id, comment_reply, comment_author, comment_body_lower)
