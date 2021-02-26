from apscheduler.schedulers.blocking import BlockingScheduler
from decouple import config
import bot_login
import cron_handler
import interval_handler
import psycopg2
import static

global reddit
global created_utc
global conn

created_utc = None

# Log in to reddit when starting clock
reddit = bot_login.bot_login()

if static.ENVIRONMENT != "development":
    # Create DB connection
    DATABASE_URL = config('DATABASE_URL')
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')

    # Create Cursor to get last valid comment_time
    cur = conn.cursor()
    cur.execute("SELECT created_utc from comment_time")
    created_utc_result = cur.fetchall()
    cur.close()

    # Use last comment time or None if not available
    if (len(created_utc_result) > 0):
        created_utc = str(created_utc_result[0][0])
    else:
        created_utc = None

print("Started bot cycle with starting utc: " + str(created_utc))

sched = BlockingScheduler()


# TODO change to 30
@sched.scheduled_job('interval', seconds=10)
def timed_job():
    global created_utc
    try:
        created_utc = interval_handler.run(conn, reddit, created_utc)
    except Exception as e:
        print("Error in INTERVAL job occured, restarting DB connection")
        print(e)
        conn.close()
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')


@sched.scheduled_job('cron', day_of_week='0-6', second=0)
def scheduled_job():
    try:
        cron_handler.run(conn)
    except Exception as e:
        print("Error in CRON job occured, restarting DB connection")
        print(e)
        conn.close()
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')


sched.start()
