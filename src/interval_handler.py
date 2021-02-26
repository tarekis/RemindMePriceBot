import static
import comments
import requests

def build_url(query_paramters_dict):
    url_builder = [static.API_URL, "?"]

    for key in query_paramters_dict.keys():
        value = query_paramters_dict[key]
        if value is not None:
            url_builder.append(f"{key}=")
            url_builder.append(str(value))
            url_builder.append("&")
    url_builder.pop()
    return ''.join(url_builder)

def run(conn, reddit, created_utc):
    try:
        # Build the URL to request
        comment_url = build_url({
            "q": static.COMMAND,
            "size": 2,
            "filter": ",".join([
                "id",
                "author",
                "created_utc",
                "body",
            ]),
            "min_created_utc": created_utc
        })

        print(comment_url)
        # Request and parse the response
        parsed_comment_json = requests.get(comment_url).json()

        # Process comments if any were found
        if (len(parsed_comment_json["data"]) > 0):
            print(parsed_comment_json)

            # Update last comment time so the next request can omit already processed comments by including only >= date + 1
            # This is done only when a comment was recieved because otherwise we'd increase the last comment time for no reason every loop
            created_utc = int(parsed_comment_json["data"][0]["created_utc"]) + 1
            if static.ENVIRONMENT != "development":
                # Update the last comment time in DB so if the bot restarts it can read that value and start where it left off
                update_cur = conn.cursor()
                update_cur.execute("UPDATE comment_time SET created_utc = {}". format(created_utc))
                conn.commit()
                update_cur.close()

            comments.process_comments(conn, reddit, parsed_comment_json["data"])

    except Exception as e:
        print("Fetching comments failed, pushshift API probably is down")
        print(str(e.__class__.__name__) + ": " + str(e))

    print(str(created_utc))
    return str(created_utc)
