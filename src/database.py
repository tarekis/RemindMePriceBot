def save_task(conn, user_name, symbol, target, direction_is_up, before_condition):
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
    values_list = list(values_dict.values())
    repeated_values = tuple(values_list + values_list)

    # Create and return the ID of new task or return the ID of an existing task with the same conditions
    # Inserts only values that exist in the values dict
    create_cur = conn.cursor()
    create_cur.execute(f"""
        WITH cte AS (
            INSERT INTO tasks({", ".join(keys)})
            VALUES ({", ".join(["%s"] * len(keys))})
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
    """, repeated_values)
    task_id = create_cur.fetchone()[0]

    # Add the user to the subscriber list if they are not yet present
    create_cur.execute("""
        WITH cte AS (
            INSERT INTO subscribers(user_name)
            VALUES (%s)
            ON CONFLICT DO NOTHING
            RETURNING id
        )
        SELECT (SELECT id FROM cte) AS result
        WHERE EXISTS (SELECT 1 FROM cte)
        UNION ALL
        SELECT id
        FROM subscribers
        WHERE user_name = %s
        AND NOT EXISTS (SELECT 1 FROM cte);
    """, (user_name, user_name))
    subscriber_id = create_cur.fetchone()[0]

    # Create a relation between subscriber and task
    create_cur.execute("INSERT INTO tasks_subscribers(task_id, subscriber_id) VALUES (%s, %s)", (task_id, subscriber_id))

    conn.commit()
    create_cur.close()

    print("task_id " + str(task_id))
    print("subscriber_id " + str(subscriber_id))

    return task_id


def get_task_details(conn, task_id):
    get_cur = conn.cursor()

    get_cur.execute("SELECT symbol, target, direction_is_up, before_condition FROM tasks WHERE id = %s;", (task_id,))
    task_details = get_cur.fetchone()[0]

    get_cur.close()

    return task_details


def remove_task(conn, task_id):
    print("TODO Implement: Should remove task " + str(task_id))


def get_subscribers(conn, task_id):
    get_cur = conn.cursor()

    get_cur.execute("SELECT subscribers.user_name FROM subscribers, tasks_subscribers WHERE tasks_subscribers.task_id = %s;", (task_id,))
    subscribers = get_cur.fetchall()

    get_cur.close()

    return subscribers


def get_grouped_targets(conn):
    select_cur = conn.cursor()
    select_cur.execute("SELECT id, symbol, target, direction_is_up, before_condition from tasks")
    results = select_cur.fetchall()
    select_cur.close()

    print("Printing all results from tasks table")
    print(results)

    # Sort all targets by symbol
    grouped_targets = {}
    for result in results:
        task_id = result[0]
        symbol = result[1]
        target = result[2]
        direction_is_up = result[3]
        before_condition = result[4]

        data_tuple = (task_id, target, direction_is_up, before_condition)
        if symbol not in grouped_targets:
            grouped_targets[symbol] = [data_tuple]
        else:
            grouped_targets[symbol].append(data_tuple)

    return grouped_targets
