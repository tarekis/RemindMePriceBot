import database


def finish_task(conn, task_id):
    subscribers = database.get_subscribers(conn, task_id)
    print(subscribers)
    for subscriber in subscribers:
        print("Message {subscriber} that {task_id} is finished")
    database.remove_task(conn, task_id)
