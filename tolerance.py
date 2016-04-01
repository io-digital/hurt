import requests
from threading import Thread
import threading
import Queue
import time
from socket import error as SocketError
import curses
import click

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


def do_work():
    global _timeout, timeout_count, connection_error_count, main_start, status, non_200_count, total_seconds, \
        test_start, test_stop, requests_handled

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

        except SocketError:
            connection_error_count += 1

        requests_handled += 1

        if requests_handled == target_hits:
            test_stop = time.time()

        q.task_done()


def update_ui_worker():
    global main_start, total_seconds, _timeout, hits, workers, status, test_number, total_seconds, test_start, \
        test_stop, requests_handled, test_seconds, _tolerance, _url

    while True:

        rc = utils.render_result_codes(result_codes, timeout_count, connection_error_count)

        if not q.empty():
            total_seconds = time.time()-main_start

        screen.addstr(1, 2, 'PAIN TOLERANCE on %s' % _url, curses.color_pair(3)|curses.A_BOLD)

        screen.addstr(3, 2, 'Status: %s                               ' % (status))
        screen.addstr(5, 2, 'Trying %s hits with %s workers  (Tolerance: %s Errors)    ' % (hits, workers, _tolerance))
        screen.addstr(6, 2, 'Timeout: %s seconds                      ' % (_timeout,))
        screen.addstr(7, 2, 'Active Workers: %s                       ' % (threading.active_count() - 2))

        if test_start is None:
            test_seconds = 0

        else:
            if test_stop is None:
                test_seconds = time.time() - test_start
            else:
                test_seconds = test_stop - test_start

        screen.addstr(9, 2, 'Test Seconds: %.2f                    ' % test_seconds)
        screen.addstr(10, 2, 'Requests Handled: %.2f               ' % requests_handled)

        if result_codes and test_seconds:
            screen.addstr(11, 2, 'Requests per second: %.2f        ' % (int(result_codes['200 OK']) / test_seconds), )

        screen.addstr(13, 2, rc)

        screen.refresh()
        time.sleep(0.1)


@click.command()
@click.option('--url', prompt="URL to request")
@click.option('--timeout', default=5)
@click.option('--tolerance', default=5)
def main(url, timeout, tolerance):
    global break_out, status, target_hits, timeout_count, connection_error_count, non_200_count, test_number, \
        result_codes, elapsed, requests_handled, test_start, test_stop, _timeout, _tolerance, screen, hits, workers, \
        _url

    _timeout = timeout
    _tolerance = tolerance
    _url = url

    screen = curses.initscr()

    screen.border(0)
    curses.start_color()
    curses.init_color(0, 0, 0, 0)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)

    curses.init_pair(10, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(11, curses.COLOR_CYAN, curses.COLOR_BLACK)

    curses.curs_set(0)

    ui = Thread(target=update_ui_worker)
    ui.daemon = True
    ui.start()

    break_out = False

    try:
        for workers in [100, 200, 400, 800, 1000, 1200]:
            if break_out:
                break

            for hits in [100, 1000, 2000]:
                if break_out:
                    break

                target_hits = hits

                for t in range(hits):
                    q.put(url)

                for w in range(workers):
                    t = Thread(target=do_work)
                    t.start()

                q.join()

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

                screen.addstr(15 + test_number, 2, '%s hits with %s workers: %s   (%.2f requests per second)           ' %
                              (hits, workers, result, int(result_codes['200 OK'])/test_seconds), cp)
                if 'Fail' in result:
                    break_out = True
                    break

                status = "Restarting..."
                time.sleep(2)
                result_codes = {}
                non_200_count = 0
                elapsed = []
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

    screen.addstr(30, 2, "Complete. Press any key to exit.")
    screen.getch()
    curses.endwin()


if __name__ == "__main__":
    main()