def run(conn):
    select_cur = conn.cursor()
    select_cur.execute("SELECT * from tasks")
    results = cur.fetchall()
    select_cur.close()

    print("Printing all results from tasks table")
    print(results)