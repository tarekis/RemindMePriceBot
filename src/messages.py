import database


def finish_task(conn, task_id):
    subscribers = database.get_subscribers(conn, task_id)
    task_details = database.get_task_details(conn, task_id)

    print(task_details)
    symbol, target, direction_is_up, before_condition = task_details
    print(subscribers)
    print(symbol)
    print(target)
    print(direction_is_up)
    print(before_condition)

    for subscriber in subscribers:
        print("Message {subscriber} that {task_id} is finished")
    database.remove_task(conn, task_id)
