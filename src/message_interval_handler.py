import logging
import requests
import messages

def run(reddit):
    inbox = reddit.inbox.unread()

    for message in inbox:
        mark_read = True
        if reddit.is_message(message):
            if message.author is None:
                print(f"Message {message.id} is a system notification")
            elif message.author.name == "reddit":
                print(f"Message {message.id} is from reddit, skipping")
            else:
                try:
                    messages.process_message(reddit, message)
                except Exception as err:
                    mark_read = False
                    logging.exception(f"Error processing message: {message.id} : u/{message.author.name}")
        else:
            print(f"Object not message, skipping: {message.id}")

        if mark_read:
            try:
                reddit.mark_read(message)
            except Exception as err:
                logging.exception(f"Error marking message read: {message.id} : u/{message.author.name}")

    return len(messages)
