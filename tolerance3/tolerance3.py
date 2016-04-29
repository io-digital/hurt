#!/usr/bin/python3
from queue import Queue
from queue import Empty
import time
import threading
import sys
import requests
import click

from requests.exceptions import ReadTimeout
from socket import error as socket_error

import logging
logging.basicConfig(filename='log.log', level=logging.INFO)

# Tests are loaded as (hits, workers,),
tests = [
    (50, 50,),
    (100, 100,),
    (200, 200,),
    (400, 400,),
    (600, 600,),
    (800, 800,),
    (1000, 1000,),
    (1500, 1500,),
    (2000, 2000,),
    (3000, 2000,),
    (5000, 2000,)
]


def print_logo():
    print('''\033[1;32m
 _           _                                        _____
| |         | |                                      |____ |
| |_   ___  | |  ___  _ __   __ _  _ __    ___   ___     / /
| __| / _ \ | | / _ \| '__| / _` || '_ \  / __| / _ \    \ \\
| |_ | (_) || ||  __/| |   | (_| || | | || (__ |  __/.___/ /
 \__| \___/ |_| \___||_|    \__,_||_| |_| \___| \___|\____/\033[m''')


def process_report(report, error_tolerance):
    total_non_200 = 0
    total_ms = 0
    total_not_present = 0
    result_codes = {'Timeouts': 0, 'Connection Errors': 0}

    for r in report:
        status_code = r.get('status_code')
        total_ms += r.get('ms')

        if status_code:
            if status_code not in result_codes:
                result_codes[status_code] = 0

            result_codes[status_code] += 1

            if status_code != 200:
                total_non_200 += 1

            if r.get('expect_not_present'):
                total_not_present += 1

        else:
            total_non_200 += 1
            if r.get('timeout'):
                result_codes['Timeouts'] += 1

            if r.get('connection_error'):
                result_codes['Connection Errors'] += 1

    if total_non_200 <= error_tolerance and total_not_present < error_tolerance:
        test_passed = True
    else:
        test_passed = False

    total_time = report[-1].get('tstop') - report[0].get('tstart')

    total_success = len(report)-total_non_200

    out = "%s success, %s failed, %.2f RPS, %.2fs ART, %.2fs Total" % \
        (total_success, total_non_200, total_success/total_time, total_ms/1000/len(report), total_time)

    if not test_passed:
        out += '\n' + str(result_codes) + '  Not Present: ' + str(total_not_present)

    return test_passed, out


def do_work(job):
    tstart = time.perf_counter()

    status_code = None
    timeout = False
    connection_error = False
    expect_not_present = False

    try:
        result = requests.get(job.get('url'), timeout=job.get('timeout'))
        status_code = result.status_code

        if job.get('expect'):
            if job.get('expect') not in result.text:
                expect_not_present = True

    except ReadTimeout:
        timeout = True

    except socket_error:
        connection_error = True

    return {'status_code': status_code, 'ms': (time.perf_counter()-tstart)*1000, 'timeout': timeout,
            'connection_error': connection_error,
            'tstart': tstart, 'tstop': time.perf_counter(), 'expect_not_present': expect_not_present}


def worker():
    while True:
        try:
            job = q.get(True, 2)

        except Empty:
            break

        result = do_work(job)
        job.get('report').append(result)
        q.task_done()


q = Queue()


@click.command()
@click.option('--url', prompt="URL to request", help='The URL to run the test on.')
@click.option('--timeout', default=10, help='Timeout in seconds before moving on.')
@click.option('--tolerance', default=5, help='How many errors will we tolerate?')
@click.option('--expect', default=None, help='Only consider a request valid if it sees this value in the response.')
def main(url, timeout, tolerance, expect):
    print_logo()
    print()
    print("URL: %s" % url)
    print("Timeout: %s    Tolerance: %s" % (timeout, tolerance))

    if expect:
        print('Expecting: "%s"' % expect)

    print()
    print('RPS: Requests Per Second. (only counts successful requests)')
    print('ART: Average Request Time. (includes timeouts etc)')
    print()

    for test in tests:
        hits = test[0]
        workers = test[1]

        thread_stopper_start = time.perf_counter()
        while threading.active_count() > 1:
            time.sleep(0.1)
            if time.perf_counter() - thread_stopper_start > 30:
                print('Timed out while waiting for threads to spin down... Waited 30 seconds and still had %s '
                      'threads.' % str(threading.active_count()-1))
                sys.exit(1)

        print('%s hits with %s workers' % (hits, workers))

        report = []

        for i in range(workers):
            try:
                t = threading.Thread(target=worker)
                t.daemon = True
                t.start()

            except RuntimeError:
                print('Unable to create threads. What OS is this?')
                sys.exit(1)

        for item in range(hits):
            q.put({'url': url, 'timeout': timeout, 'report': report, 'expect': expect})

        q.join()       # block until all tasks are done

        logging.info(report)

        test_passed, summary = process_report(report, tolerance)

        if test_passed:
            print('\033[1;32mPassed: ', end='')
        else:
            print('\033[1;31mFailed: ', end='')

        print(summary + '\033[m')
        print()

        if not test_passed:
            break


if __name__ == "__main__":
    main()
