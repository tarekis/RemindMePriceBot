from datetime import datetime
import parsedatetime
import re
import static

cal = parsedatetime.Calendar()


direction_is_up_regex = "hits"
direction_is_down_regex = "drops\s*(?:to)?"
# "Explanation": https://regex101.com/r/svsM5v/1
command_regex = f"{static.COMMAND_LOWER}\s+(?:of\s+)?([^\s]+)\s+(?:(hits|drops\s*(?:to)?)\s+)?([0-9]+(?:[,.][0-9]+)?)(?:\s+(?:(?:before)\s+([^\s]*))?)?"


def get_direction_is_up(direction_raw):
    if direction_raw is None:
        return True
    if re.compile(direction_is_up_regex).search(direction_raw) is not None:
        return True
    if re.compile(direction_is_down_regex).search(direction_raw) is not None:
        return False


def get_before_condition(before_condition_raw):
    if before_condition_raw is None:
        return (None, True)

    before_condition_raw = before_condition_raw.strip()

    time_struct, parse_status = cal.parse(before_condition_raw)

    if parse_status == 1:
        return (datetime(*time_struct[:6]), True)

    return (None, False)


# Process comment body and extract options, or return None if not possible
def get_comment_body_details(comment_body):
    search_results = re.compile(command_regex).search(comment_body)

    if search_results is not None:
        symbol_raw = search_results.group(1)
        direction_raw = search_results.group(2)
        target_raw = search_results.group(3)
        before_condition_raw = search_results.group(4)

        (before_condition, before_condition_successfull) = get_before_condition(before_condition_raw)

        if not (symbol_raw and target_raw):
            return None

        return {
            "symbol": symbol_raw.strip().upper(),
            "target": target_raw.strip(),
            "direction_is_up": get_direction_is_up(direction_raw),
            "before_condition": before_condition,
            "before_condition_successfull": before_condition_successfull
        }

    return None
