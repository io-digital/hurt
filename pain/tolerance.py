from threading import Thread
import threading
import Queue
import time
from socket import error as SocketError
import sys

try:
    import requests
    import curses
    import click
except ImportError:
    print 'Tolerance requires the following Python modules: Requests, Curses and Click. You should be able to ' \
          '`sudo pip install requests curses click`'
    sys.exit(1)

import utils

q = Queue.Queue()

result_codes = {}
_timeout = None

elapsed = []
timeout_count = 0
connection_error_count = 0
non_200_count = 0
durations = []
main_start = None
status = "Starting up"
test_number = 1
total_seconds = 0

test_start = None
test_stop = None
test_seconds = None

target_hits = None
requests_handled = 0

_tolerance = None
_url = None
hits = None
workers = None

break_out = False

import logging
logging.basicConfig(filename='log.log', level=logging.WARNING)


def do_work():
    global _timeout, timeout_count, connection_error_count, main_start, status, non_200_count, total_seconds, \
        test_start, test_stop, requests_handled, _tolerance, break_out

    while True:
        try:
            url = q.get(True, 2)

        except Queue.Empty:
            break

        status = "Running"

        if test_start is None:
            test_start = time.time()

        if main_start is None:
            main_start = time.time()

        try:
            start = time.time()
            res = requests.get(url, timeout=_timeout)
            elapsed.append(res.elapsed.total_seconds())

            if '%s %s' % (res.status_code, res.reason) not in result_codes:
                result_codes['%s %s' % (res.status_code, res.reason)] = 0

            result_codes['%s %s' % (res.status_code, res.reason)] += 1

            if res.status_code == 200:
                durations.append(time.time() - start)

            else:
                non_200_count += 1

        except requests.RequestException:
            timeout_count += 1
            non_200_count += 1

        except SocketError:
            connection_error_count += 1
            non_200_count += 1

        requests_handled += 1

        if non_200_count > _tolerance:
            break_out = True
            test_stop = time.time()
            with q.mutex:
                q.queue.clear()
            q.task_done()
            status = "Failed, stopping..."
            break

        if requests_handled == target_hits:
            test_stop = time.time()

        q.task_done()


def update_ui_worker():
    global main_start, total_seconds, _timeout, hits, workers, status, test_number, total_seconds, test_start, \
        test_stop, requests_handled, test_seconds, _tolerance, _url, break_out

    while True:

        rc = utils.render_result_codes(result_codes, timeout_count, connection_error_count)

        if not q.empty():
            total_seconds = time.time()-main_start

        # screen.addstr(1, 70, 'Break Out: %s     ' % break_out)

        screen.addstr(1, 2, 'PAIN TOLERANCE on %s' % _url, curses.color_pair(3)|curses.A_BOLD)

        screen.addstr(3, 2, 'Status: %s                             ' % status)

        screen.addstr(5, 2, 'Trying %s hits with %s workers          ' % (hits, workers))
        screen.addstr(6, 2, 'Timeout: %s seconds                     ' % (_timeout,))
        screen.addstr(6, 40, 'Tolerance: %s errors                   ' % (_tolerance,))

        screen.addstr(7, 2, 'Active Workers: %s       ' % (threading.active_count() - 2))
        screen.addstr(7, 40,'Queue: %s        ' % q.qsize())

        if test_start is None:
            test_seconds = 0

        else:
            if test_stop is None:
                test_seconds = time.time() - test_start
            else:
                test_seconds = test_stop - test_start

        screen.addstr(10, 2, 'Test Seconds: %.2f         ' % test_seconds)
        screen.addstr(10, 40, 'Requests handled: %s      ' % requests_handled)

        if result_codes and test_seconds and '200 OK' in result_codes:
            screen.addstr(11, 2, 'Requests per second: %.2f        ' % (int(result_codes['200 OK']) / test_seconds), )

        if durations:
            screen.addstr(11, 40, 'Average Request: %.2f seconds   ' % (reduce(lambda x, y: x + y, durations) / len(durations)))

        screen.addstr(13, 2, rc)

        screen.refresh()
        time.sleep(0.1)


tests = [
    (50, 50,),
    (100, 100,),
    (200, 200,),
    (400, 400,),
    (600, 600,),
    (800, 800,),
    (1000, 1000,),
    (1500, 1000,),
    (2000, 1000,),
    (2000, 1500,),
    (2000, 2000,)
]


@click.command()
@click.option('--url', prompt="URL to request")
@click.option('--timeout', default=10)
@click.option('--tolerance', default=5)
def main(url, timeout, tolerance):
    global break_out, status, target_hits, timeout_count, connection_error_count, non_200_count, test_number, \
        result_codes, elapsed, requests_handled, test_start, test_stop, _timeout, _tolerance, screen, hits, workers, \
        _url, durations

    _timeout = timeout
    _tolerance = tolerance
    _url = url

    logging.warning('Starting up...')

    # Check that the url provided is valid
    try:
        requests.get(url, timeout=5)
    except requests.exceptions.MissingSchema:
        print "Invalid URL"
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print "Is that a valid URL? We can't connect to it."
        sys.exit(1)
    except Exception as e:
        print "Something went wrong trying to connect... timeout?"
        print e
        sys.exit(1)

    try:
        screen = curses.initscr()

        screen.border(0)
        curses.start_color()
        curses.init_color(0, 0, 0, 0)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)

        curses.init_pair(10, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(11, curses.COLOR_CYAN, curses.COLOR_BLACK)

        curses.curs_set(0)
        # curses.noecho()

        ui = Thread(target=update_ui_worker)
        ui.daemon = True
        ui.start()

        for test in tests:
            hits = test[0]
            workers = test[1]

            if break_out:
                break

            target_hits = hits

            for t in range(hits):
                q.put(url)

            for w in range(workers):
                t = Thread(target=do_work)
                t.start()

            # q.join()

            status = "Waiting for workers to spin down..."
            while True:
                if threading.active_count() <= 2:
                    break

            if timeout_count + connection_error_count + non_200_count > tolerance:
                result = 'Fail'
                cp = curses.color_pair(2)|curses.A_BOLD
            else:
                result = 'Pass'
                cp = curses.color_pair(3)|curses.A_BOLD

            result_200 = result_codes.get('200 OK')
            if result_200 is None:
                result_200 = 0
            else:
                result_200 = int(result_200)

            if durations:
                average_request_time = reduce(lambda x, y: x + y, durations) / len(durations)

            screen.addstr(15 + test_number, 2, '%s hits with %s workers: %s   (%.2f RPS %.2f ART)           ' %
                          (hits, workers, result, result_200/test_seconds, average_request_time), cp)

            if 'Fail' in result:
                break_out = True
                break

            status = "Restarting..."
            time.sleep(2)
            result_codes = {}
            non_200_count = 0
            elapsed = []
            durations = []
            timeout_count = 0
            connection_error_count = 0
            test_number += 1
            requests_handled = 0
            test_start = None
            test_stop = None

    except KeyboardInterrupt:
        with q.mutex:
            q.queue.clear()

        break_out = True
        test_stop = time.time()
        screen.addstr(16 + test_number, 2, "Test cancelled.")
        logging.warning('Keyboard Exit')

    finally:
        curses.endwin()
        logging.warning('Exit 2a')

    screen.addstr(16 + test_number, 2, "Press any key to exit.")
    screen.getch()

    curses.endwin()
    logging.warning('Exit 2')


if __name__ == "__main__":
    main()
