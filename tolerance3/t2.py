#!/usr/bin/python3
from Queue import Queue
from Queue import Empty
import time
import threading
import sys
import requests
import click
import socket
from urlparse import urlparse

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
    (2000, 1000,),
    (4000, 1000,),
]


def print_logo():
    print('''\033[1;32;40m
  ______ ___
 /_  __/|__ \\
  / /   __/ /
 / /   / __/
/_/   /____/
 \033[1;37;40m''')


def process_report(report, error_tolerance):
    total_non_200 = 0
    total_ms = 0
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

        else:
            total_non_200 += 1
            if r.get('timed_out'):
                result_codes['Timeouts'] += 1

            if r.get('connection_error'):
                result_codes['Connection Errors'] += 1

    if total_non_200 <= error_tolerance:
        test_passed = True
    else:
        test_passed = False

    total_time = report[-1].get('tstop') - report[0].get('tstart')

    total_success = len(report)-total_non_200

    out = "%s success, %s failed, %.2f RPS, %.2fs ART, %.2fs Total" % \
        (total_success, total_non_200, total_success/total_time, total_ms/1000/len(report), total_time)

    if not test_passed:
        out += '\n'.ljust(32) + str(result_codes)

    return test_passed, out


def do_work(job):
    url = job.get('url')
    timeout = job.get('timeout')
    ip = job.get('ip')
    port = job.get('port')
    path = job.get('path')
    netloc = job.get('netloc')

    status_code = None
    connection_error = False
    timed_out = False

    tstart = time.time()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ip, port))
    s.settimeout(timeout)
    s.send("GET /%s HTTP/1.0\nHost:%s\nUser-Agent:Mozilla 5.0\n\n" % (path, netloc,))
    out = ""

    while True:
        try:
            resp = s.recv(4094)

            if not status_code:
                l = resp.split('\n')

                if l[0].startswith('HTTP/'):
                    i = l[0].split(' ')
                    status_code = int(i[1])

            if resp == "":
                break

            out += resp

        except socket.timeout:
            timed_out = True

    s.close()

    return {'status_code': status_code, 'ms': (time.time()-tstart)*1000, 'timed_out': timed_out,
            'connection_error': connection_error,
            'tstart': tstart, 'tstop': time.time()}


def worker():
    while True:
        if q:
            try:
                job = q.get(True, 2)

            except Empty:
                break

            result = do_work(job)
            job.get('report').append(result)
            q.task_done()

        else:
            break


q = Queue()


@click.command()
@click.option('--url', prompt="URL to request", help='The URL to run the test on.')
@click.option('--timeout', default=10, help='Timeout in seconds before moving on.')
@click.option('--tolerance', default=5, help='How many errors will we tolerate?')
def main(url, timeout, tolerance):
    print_logo()
    print("URL: %s" % url)
    print("Timeout: %s    Tolerance: %s" % (timeout, tolerance))
    print('')
    print('RPS: Requests Per Second. (only counts successful requests)')
    print('ART: Average Request Time. (includes timeouts etc)')
    print('')

    print('Looking up DNS once: '),
    parsed = urlparse(url)
    ip = socket.gethostbyname(parsed.netloc)
    print ip + ''

    if parsed.scheme == 'http':
        port = 80
    elif parsed.scheme == 'https':
        port = 443
    else:
        raise Exception("Can't figure out port?")

    path = parsed.path
    netloc = parsed.netloc

    for test in tests:
        hits = test[0]
        workers = test[1]

        thread_stopper_start = time.time()
        while threading.active_count() > 1:
            time.sleep(0.1)
            if time.time() - thread_stopper_start > 30:
                print('Timed out while waiting for threads to spin down... Waited 30 seconds and still had %s '
                      'threads.' % str(threading.active_count()-1))
                sys.exit(1)

        print('%s hits with %s workers' % (hits, workers)).ljust(30),
        sys.stdout.flush()
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
            q.put({'url': url, 'timeout': timeout, 'report': report, 'ip': ip, 'port': port, 'path': path,
                   'netloc': netloc})

        q.join()       # block until all tasks are done

        logging.info(report)

        test_passed, summary = process_report(report, tolerance)

        if test_passed:
            print('\033[1;32;40mPassed:'),
        else:
            print('\033[1;31;40mFailed:'),

        print(summary + '\033[1;37;40m')

        if not test_passed:
            break


if __name__ == "__main__":
    main()
