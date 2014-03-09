
from datetime import date, timedelta


ONE_DAY = timedelta(1)


def convert_to_int(possible_number, use_if_not_int):
    """
    Save conversion of string to int with ability to specify default if string is not a number
    """
    try:
        result = int(possible_number)
    except ValueError:
        result = use_if_not_int
    return result


def join_with_space_and_convert_spaces(segments, replace_with='-'):
    """
    Helper function joins array pieces together and then replaces any spaces
    with specified value.
    """
    return " ".join(segments).replace(" ", replace_with)


def just_empty_lines(lines):
    for line in lines:
        if len(line) > 0:
            return False
    return True


def strip_line(line):
    return line.strip()


def strip_the_lines(lines):
    return map(strip_line, lines)


def yesterday():
    return date.today() - ONE_DAY
