from decouple import config

ENVIRONMENT = config('environment')
# RemindMeBot doesn't like me, so lets use that for now :(
COMMAND = "!RemindMiWhenPriceTEST"
COMMAND_LOWER = COMMAND.lower()
REDDIT_USERNAME = "RemindMePriceBot"
API_URL = "https://beta.pushshift.io/search/reddit/comments/"
BOTTOM_REPLY_SECTION = "\n\n\n\n---\n\n^(Beep boop. I am a bot. If there are any issues, contact my) [^Master ](https://www.reddit.com/message/compose/?to=Tarekis&subject=/u/RemindMePriceBot)"
