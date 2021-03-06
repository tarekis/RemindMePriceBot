import logging
from datetime import datetime
import database
import messages
import yfinance as yf


def run(conn, reddit):
    grouped_targets = database.get_grouped_targets(conn)
    now = datetime.now()
    print(f"Running CRON job at {now}.")

    print(grouped_targets)
    # Iterate over all unique symbols
    for symbol in grouped_targets.keys():
        print(f'Checking {len(grouped_targets[symbol])} tasks for symbol {symbol}')
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

                if (now > before_condition):
                    print(f'Before condition {before_condition} has expired as it was less than the current time {now}')
                    database.remove_task(conn, task_id)
                    return

                if direction_is_up:
                    if day_high >= target:
                        print(f"Task #{task_id} finished because day high was {day_high}, which is greater than or equals the target {target}")
                        messages.finish_task(conn, reddit, task_id, day_high)
                else:
                    if day_low <= target:
                        print(f"Task #{task_id} finished because day low was {day_low}, which is less than or equals the target {target}")
                        messages.finish_task(conn, reddit, task_id, day_low)

            print(f"Symbol: {symbol}, day high: {day_high}, day low: {day_low}")

        except Exception as e:
            logging.exception("Error when fetching finance data for " + symbol)
            print(e)
