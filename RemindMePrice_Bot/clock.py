from apscheduler.schedulers.blocking import BlockingScheduler

sched = BlockingScheduler()

@sched.scheduled_job('interval', seconds=10)
def timed_job():
    print('This job is run every ten seconds')

@sched.scheduled_job('cron', day_of_week='0-6', second=0)
def scheduled_job():
    print('This job is run every minute of the day')

sched.start()
