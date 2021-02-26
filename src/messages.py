from datetime import datetime
import database


def finish_task(conn, task_id):
    subscribers = database.get_subscribers(conn, task_id)
    task_details = database.get_task_details(conn, task_id)

    symbol, target, direction_is_up, currency, before_condition = task_details
    print("\n")
    print("Task details: " + str(task_id))
    print(subscribers)
    print(symbol)
    print(target)
    print(direction_is_up)
    print(currency)
    print(before_condition)
    print(before_condition == datetime.max)
    print("\n")

    for subscriber in subscribers:
        before_string = "" if (before_condition == datetime.max) else f" before {before_condition}"
        direction_string = "hit" if direction_is_up else "dropped to"
        print(f"Message {subscriber} that {symbol} {direction_string} {target} {currency}{before_string}")
    database.remove_task(conn, task_id)
