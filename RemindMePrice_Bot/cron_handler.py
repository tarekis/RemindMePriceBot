import yfinance as yf


def run(conn):
    select_cur = conn.cursor()
    select_cur.execute("SELECT * from tasks")
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
        symbol_target_tuple = (task_id, target)
        if symbol not in grouped_targets:
            grouped_targets[symbol] = [symbol_target_tuple]
        else:
            grouped_targets[symbol].append(symbol_target_tuple)

    print(grouped_targets)

    # Iterate over all unique symbols
    for symbol in grouped_targets.keys():
        try:
            ticker = yf.Ticker(symbol)

            # Access ticker into, this is where an error is thrown if the ticker was not found
            dayHigh = ticker.info["dayHigh"]

            print(f"Symbol: {symbol}, dayHigh: {dayHigh}")

        except Exception as e:
            print('Error when fetching current day high')
            print(e)
