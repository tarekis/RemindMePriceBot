from datetime import datetime
import static
import database


def finish_task(conn, reddit, task_id, trigger_price):
    subscribers = database.get_subscribers(conn, task_id)
    task_details = database.get_task_details(conn, task_id)

    symbol, target, direction_is_up, currency, before_condition = task_details

    for subscriber_tuple in subscribers:
        before_string = "" if (before_condition == datetime.max) else f" before {before_condition}"
        direction_string_present_tense = "hits" if direction_is_up else "drops to"
        direction_string_past_tens = "hit" if direction_is_up else "dropped to"
        trigger_string = "high" if direction_is_up else "low"
        emoji = "📈" if direction_is_up else "📉"

        subject = f"{symbol} {direction_string_past_tens} {target}{currency}"

        message_builder = []
        message_builder.append(f"You asked me to remind you when {symbol} {direction_string_present_tense} {target} {currency}{before_string}.\n\n")
        message_builder.append(f"{symbol} just {direction_string_past_tens} {target} {currency} with the current {trigger_string} at {trigger_price}. {emoji}\n\n")
        message_builder.append(static.BOTTOM_REPLY_SECTION)

        message = "".join(message_builder)
        reddit.redditor(subscriber_tuple[0]).message(subject, message)
    database.remove_task(conn, task_id)
