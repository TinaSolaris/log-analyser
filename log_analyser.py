import logging
import re
import sys
from datetime import datetime
import ipaddress
from pprint import pprint
from os.path import exists


# lab 7 task 2
def read_config() -> tuple:
    fname = 'info.config'
    lines = read_file(fname)

    display_settings = {}
    filename = ''
    header = re.compile(r'^\[\w*\]$')
    empty = re.compile(r'^$')
    name = re.compile(r'^name=([^\\/]*)$')
    debug = re.compile(r'^debug=(DEBUG|INFO|WARNING|ERROR|CRITICAL)$')
    lines_regex = re.compile(r'^lines=(\d*)$')
    separator = re.compile(r'^separator=(.?)$')
    filter_regex = re.compile(
        r'^filter=' +
        r'(GET|HEAD|POST|PUT|DELETE|CONNECT|OPTIONS|TRACE|PATCH)$'
    )

    for line in lines:
        if header.match(line) or empty.match(line):
            continue
        elif name.match(line):
            filename = name.match(line).group(1)
            if not filename or not exists(filename):
                filename = 'access_log-20201025.txt'    # set the default value
            print(f'filename: {filename}')
        elif debug.match(line):
            logging_level = debug.match(line).group(1)
            if not logging_level:
                logging_level = 'INFO'
            set_logging_level(logging_level)
        elif lines_regex.match(line):
            lines_no = lines_regex.match(line).group(1)
            if not lines_no:
                lines_no = 20
            elif int(lines_no) <= 0:
                lines_no = 20
            display_settings['lines'] = int(lines_no)
        elif separator.match(line):
            sep = separator.match(line).group(1)
            if not sep:
                sep = '|'
            display_settings['separator'] = sep
        elif filter_regex.match(line):
            filter_word = filter_regex.match(line).group(1)
            if not filter_word:
                filter_word = 'GET'
            display_settings['filter'] = filter_word
        else:
            print('Other!!!')

    return_tuple = (filename, display_settings)
    print('Configuration:')
    print(return_tuple)

    return return_tuple


# lab 7 task 3
def read_file(fname) -> list:
    try:
        with open(fname, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except FileNotFoundError:
        logging.info(f'The file named \"{0}\" does not exist!'.format(fname))
        sys.exit()
    else:
        return lines


# lab 7 task 4
def parse_line(line: str) -> tuple:
    parser = re.compile(
        r'^((?:\d+\.){3}\d+) - - ' +
        r'\[([0-3]\d/[A-Z][a-z]{2}/20\d{2}:' +
        r'[0-2]\d:[0-5]\d:[0-5]\d \+\d{4})\]' +
        r' \"(.+)\" (\d{3}) (\d+|-) \".+\" \"(.+)\"$'
    )
    matched = parser.match(line)
    ip_address = ipaddress.ip_address(matched.group(1))
    timestamp = create_datetime(matched.group(2))
    request = matched.group(3)
    status_code = int(matched.group(4))
    # cast to int is not possible for response_size,
    # because for some entries the value is represented as "-"
    response_size = matched.group(5)
    user_agent = matched.group(6)

    return_tuple = (
        ip_address,
        timestamp,
        request,
        status_code,
        response_size,
        user_agent
        )
    return return_tuple


# lab 7 task 5
def analyse_log_lines(lines: list) -> list:
    database = []
    for line in lines:
        log_entry = parse_line(line)
        database.append(log_entry)

    return database


# lab 6 task 4
def set_logging_level(logging_level: str) -> None:
    logging.basicConfig(level=logging_level)


def create_datetime(timestamp: str) -> datetime:
    date_time_obj = datetime.strptime(timestamp, '%d/%b/%Y:%H:%M:%S %z')
    return date_time_obj


# lab 7 task 6
def print_requests(database, lines_number: int) -> None:
    host_mask_length = 268891 % 16 + 8
    my_ip = ipaddress.ip_address('185.191.171.7')
    network = ipaddress.IPv4Network(f'{my_ip}/{host_mask_length}',
                                    strict=False)
    subnet = network.network_address

    requests_from_subnet = []

    def check(ip, subnet, mask):
        return ip in ipaddress.ip_network(f'{subnet}/{mask}')

    for log_entry in database:
        ip = log_entry[0]
        request = log_entry[2]
        if check(ip, subnet, host_mask_length):
            value_to_print = (ip, request)
            requests_from_subnet.append(value_to_print)

    print_and_wait(requests_from_subnet, lines_number)


# lab 7 task 7
def requests_from_browser(database) -> None:
    for log_entry in database:
        if 'Chrome' in log_entry[5]:
            pprint(log_entry)


# lab 7 task 8
def total_bytes(database, filter, separator) -> None:
    filter_regex = re.compile(f'{filter}')
    total = 0
    for log_entry in database:
        try:
            if filter_regex.match(log_entry[2]):
                total += int(log_entry[4])
        except ValueError:  # in case of invalid data for the response size
            continue

    print(f'{filter} {separator} {total}')


# helper
def print_and_wait(lines_to_print, lines_number) -> None:
    counter = 0
    while lines_to_print:
        if counter > 0:
            input("Press Enter to continue...")
        slice_to_print = lines_to_print[:lines_number]
        print('\n'.join(map(str, slice_to_print)))
        del lines_to_print[:lines_number]
        counter += 1


def run() -> None:
    configuration = read_config()
    log_file_name = configuration[0]
    lines = read_file(log_file_name)
    data = analyse_log_lines(lines)

    print('\nprint_requests output:')
    print_requests(data, configuration[1]['lines'])

    print('\nrequests_from_browser output:')
    requests_from_browser(data)

    print('\ntotal_bytes output:')
    total_bytes(data, configuration[1]['filter'],
                configuration[1]['separator'])


if __name__ == "__main__":
    run()
