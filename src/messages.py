import database


def finish_task(conn, task_id):
    print("TODO Implement: Should send messages to the subscribers")
    subscribers = database.get_subscribers(conn, task_id)
    print(subscribers)
    database.remove_task(conn, task_id)
