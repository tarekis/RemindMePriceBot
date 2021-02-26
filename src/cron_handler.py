from datetime import datetime
import database
import yfinance as yf


def run(conn):
    grouped_targets = database.get_grouped_targets(conn)

    print(grouped_targets)
    # Iterate over all unique symbols
    for symbol in grouped_targets.keys():
        try:
            ticker = yf.Ticker(symbol)

            # Access ticker into, this is where an error is thrown if the ticker was not found
            dayHigh = ticker.info["dayHigh"]
            dayLow = ticker.info["dayLow"]

            for data_tuple in grouped_targets[symbol]:
                task_id = data_tuple[0]
                target = data_tuple[1]
                direction_is_up = data_tuple[2]
                before_condition = data_tuple[3]

                now = datetime.now()

                print(now)
                print(before_condition)

                if (now > before_condition):
                    print('Before condition {before_condition} has expired as it was less than the current time {now}')
                    database.remove_task(conn, task_id)
                    return

                    if direction_is_up:
                        print(dayHigh >= target)
                        if dayHigh >= target:
                            database.finish_task(conn, task_id)
                            print(f"Task #{task_id} finished because day high was {dayHigh}, which is greater than or equals the target {target}")
                    else:
                        print(dayHigh <= target)
                        if dayHigh <= target:
                            database.finish_task(conn, task_id)
                            print(f"Task #{task_id} finished because day low was {dayLow}, which is less than or equals the target {target}")

            print(f"Symbol: {symbol}, day high: {dayHigh}")

        except Exception as e:
            print('Error when fetching finance data for ' + symbol)
            print(e)
