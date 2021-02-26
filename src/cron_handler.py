from datetime import datetime
import database
import messages
import yfinance as yf


def run(conn, reddit):
    grouped_targets = database.get_grouped_targets(conn)
    now = datetime.now()

    print(grouped_targets)
    # Iterate over all unique symbols
    for symbol in grouped_targets.keys():
        try:
            ticker = yf.Ticker(symbol)

            # Access ticker into, this is where an error is thrown if the ticker was not found
            day_high = ticker.info["dayHigh"]
            day_low = ticker.info["dayLow"]

            for data_tuple in grouped_targets[symbol]:
                task_id = data_tuple[0]
                target = data_tuple[1]
                direction_is_up = data_tuple[2]
                before_condition = data_tuple[3]

                print("Task ID: " + str(task_id))
                print(now)
                print(before_condition)
                print("\n")

                if (now > before_condition):
                    print(f'Before condition {before_condition} has expired as it was less than the current time {now}')
                    database.remove_task(conn, task_id)
                    return

                print(f'Before condition {before_condition} has not expired, continue.')
                print("Direction is up: " + str(direction_is_up))

                if direction_is_up:
                    print(day_high >= target)
                    if day_high >= target:
                        print(f"Task #{task_id} finished because day high was {day_high}, which is greater than or equals the target {target}")
                        messages.finish_task(conn, reddit, task_id, day_high)
                else:
                    print(day_low <= target)
                    if day_low <= target:
                        print(f"Task #{task_id} finished because day low was {day_low}, which is less than or equals the target {target}")
                        messages.finish_task(conn, reddit, task_id, day_low)

            print(f"Symbol: {symbol}, day high: {dayHigh}")

        except Exception as e:
            print('Error when fetching finance data for ' + symbol)
            print(e)
