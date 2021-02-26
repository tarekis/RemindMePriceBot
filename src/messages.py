from datetime import datetime
import static
import database


def finish_task(conn, reddit, task_id, trigger_price):
    subscribers = database.get_subscribers(conn, task_id)
    task_details = database.get_task_details(conn, task_id)

    symbol, target, direction_is_up, currency, before_condition = task_details

    for subscriber_tuple in subscribers:
        before_string = "" if (before_condition == datetime.max) else f" before {before_condition}"
        direction_string = "hit" if direction_is_up else "dropped to"
        trigger_string = "high" if direction_is_up else "low"
        emoji = "📈" if direction_is_up else "📉"

        subject = f"{symbol} {direction_string} {currency}{before_string}"

        message_builder = []
        message_builder.append(f"You asked me to remind you when {symbol} {direction_string} {target} {currency}{before_string}.\n\n")
        message_builder.append(f" {symbol} just {direction_string} with the current {trigger_string} at {trigger_price}. {emoji}\n\n")
        message_builder.append(static.BOTTOM_REPLY_SECTION)

        message = "".join(message_builder)
        reddit.redditor(subscriber_tuple[0]).message(subject, message)
    database.remove_task(conn, task_id)
