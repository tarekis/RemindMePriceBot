from apscheduler.schedulers.blocking import BlockingScheduler
from decouple import config
import bot_login
import time
import cron_handler
import interval_handler
import psycopg2
import static

# TODO rename uppercase
global reddit
global created_utc
global comment_id
global conn

created_utc = None

# Log in to reddit when starting clock
reddit = bot_login.bot_login()

# Create DB connection
DATABASE_URL = config('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL, sslmode='require')

# Create Cursor to get last valid comment time
cur = conn.cursor()
cur.execute("SELECT created_utc, comment_id from last_comment")
last_comment_result = cur.fetchall()
cur.close()

# Use last comment time or None if not available
if len(last_comment_result) > 0:
    created_utc = str(last_comment_result[0][0])
else:
    created_utc = None

# Use last comment id or None if not available
if len(last_comment_result) > 0:
    comment_id = str(last_comment_result[0][1])
else:
    comment_id = None

print("Started bot cycle with starting utc: " + str(created_utc))

sched = BlockingScheduler()


# TODO change to 30
@sched.scheduled_job('interval', seconds=10)
def timed_job():
    global created_utc
    global comment_id
    global conn
    try:
        created_utc = interval_handler.run(conn, reddit, created_utc, comment_id)
    except Exception as e:
        print("Error in INTERVAL job occured, restarting DB connection")
        print(e)
        conn.close()
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')

# TODO change to minute, so it runs hourly
@sched.scheduled_job('cron', second=0)
def scheduled_job():
    global conn
    try:
        cron_handler.run(conn, reddit)
    except Exception as e:
        print("Error in CRON job occured, restarting DB connection, retrying job")
        print(e)
        conn.close()
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        time.sleep(15)
        cron_handler.run(conn)


sched.start()
