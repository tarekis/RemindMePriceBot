from decouple import config

ENVIRONMENT = config('environment')
# RemindMeBot doesn't like me, so lets use that for now :(
COMMAND = "!RemindMiWhenPrice_TEST"
COMMAND_LOWER = COMMAND.lower()
REDDIT_USERNAME = "RemindMePriceBot"
API_URL = "https://beta.pushshift.io/search/reddit/comments/"