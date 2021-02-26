import logging
import requests
import comments
import static


request_headers = {
    'User-Agent': static.USER_AGENT,
}

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


def find_index_of_comment_with_id(comments_data, comment_id):
    for index, value in enumerate(comments_data):
        if value['id'] == comment_id:
            return index
    return None


def not_exact_created_utc(item, created_utc):
    return item.created_utc != created_utc


def run(conn, reddit, created_utc, comment_id):
    try:
        # Build the URL to request
        comment_url = build_url({
            "q": static.COMMAND,
            "size": 1,
            "sort": "asc",
            "filter": ",".join([
                "id",
                "author",
                "created_utc",
                "body",
            ]),
            "min_created_utc": created_utc
        })

        print(f"Running query with starting utc {created_utc} and comment_id {comment_id}\n")
        # Request and parse the response
        parsed_comment_json = requests.get(comment_url, headers=request_headers).json()

        comments_data = parsed_comment_json["data"]

        # Process comments if any were found
        if len(comments_data) > 0:

            # Try to find the index of the last processed comment, if present remove all items before it and itslef
            # as those were crated in the same epoch and must have been processed in an earlier cycle
            index_of_last_comment = find_index_of_comment_with_id(comments_data, comment_id)
            if index_of_last_comment is not None:
                comments_data = comments_data[index_of_last_comment+1:None]

            # If no more comments are available after slicing by the comment id this means
            # that this cycle has caught up with all previously created comments and
            # the created_utc can be moved up by one so the next cycle will not re-request the ones from this epoch
            update_cur = conn.cursor()
            if len(comments_data) == 0:
                update_cur.execute("UPDATE last_comment SET created_utc = %s", (int(created_utc) + 1,))
                conn.commit()
                update_cur.close()
                return (str(created_utc), str(comment_id))
            
            # Update last comment time and comment id when any comments were recieved
            last_comment = comments_data[-1]
            created_utc = last_comment["created_utc"]
            comment_id = last_comment["id"]
            # Update the last comment time in DB so if the bot restarts it can read that value and start where it left off
            update_cur.execute("UPDATE last_comment SET created_utc = %s, comment_id = %s", (created_utc, comment_id))
            conn.commit()
            update_cur.close()

            comments.process_comments(conn, reddit, comments_data)

    except Exception as e:
        print(str(e.__class__.__name__) + ": " + str(e))
        logging.exception("Fetching comments failed, pushshift API probably is down")

    return (str(created_utc), str(comment_id))
