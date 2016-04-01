from threading import Thread
from Queue import Queue

import requests
import sys
import time

import locale
from socket import error as SocketError

try:
    from colorama import Fore, Back, Style
except ImportError:
    print 'Pain requires Colorama - You should `pip install colorama`'
    sys.exit(1)

try:
    import click
except ImportError:
    print 'Pain requires Click - You should `pip install click`'
    sys.exit(1)


timeout_count = 0
success_count = 0
five_hundred_count = 0
connection_error_count = 0

durations = []
elapsed = []
q = Queue()

result_codes = {}
locale.setlocale(locale.LC_ALL, 'en_US')

update_ui_now = True


def update_ui():
    global update_ui_now

    while update_ui_now:
        _update_ui()
        time.sleep(0.1)


def _update_ui():
    global timeout_count, result_codes, connection_error_count

    print '\r',

    for k, v in result_codes.iteritems():

        print "%s:" % k,

        if k == '200 OK':
            print(Fore.LIGHTGREEN_EX),

        else:
            print(Fore.RED),

        print "%s     " % v,
        print(Style.RESET_ALL),

    if timeout_count > 0:
        print('Timeouts:  '+Fore.YELLOW + str(timeout_count) + Style.RESET_ALL) + '     ',

    if connection_error_count >0:
        print('Connection Errors:  '+Fore.RED + str(connection_error_count) + Style.RESET_ALL),

    sys.stdout.flush()

_timeout = 5


def do_work():
    global timeout_count, result_codes, durations, elapsed, connection_error_count

    while True:
        url = q.get()
        try:
            start = time.time()
            res = requests.get(url, timeout=_timeout)

            elapsed.append(res.elapsed.total_seconds())

            if '%s %s' % (res.status_code, res.reason) not in result_codes:
                result_codes['%s %s' % (res.status_code, res.reason)] = 0

            result_codes['%s %s' % (res.status_code, res.reason)] += 1

            if res.status_code == 200:
                durations.append(time.time() - start)

        except requests.RequestException:
            timeout_count += 1

        except SocketError as e:
            connection_error_count += 1

        q.task_done()


@click.command()
@click.option('--hits', default=2000, help='Number of requests')
@click.option('--workers', default=500, help='Number of workers')
@click.option('--url', prompt="URL to request")
@click.option('--timeout', default=5)
def main(hits, workers, url, timeout):

    global _timeout, durations, result_codes, update_ui_now
    _timeout = timeout
    print ""
    print Fore.CYAN + 'PAIN IS GOOD  v0.0001              ' + Style.RESET_ALL
    print ""
    print '%sHitting: %s%s' % (Style.DIM, Style.NORMAL, url)
    print '%sHits:    %s%s%s' % (Style.DIM, Style.NORMAL, locale.format("%d", hits, grouping=True), Style.NORMAL)
    print '%sWorkers: %s%s%s' % (Style.DIM, Style.NORMAL, locale.format("%d", workers, grouping=True), Style.NORMAL)
    print '%sTimeout: %s%s seconds%s' % (Style.DIM, Style.NORMAL, timeout, Style.NORMAL)

    main_start = time.time()
    print Style.DIM + '\nStarting Workers...' + Style.RESET_ALL,
    sys.stdout.flush()

    for i in range(workers):
        t = Thread(target=do_work)
        t.daemon = True
        t.start()
    print ' Done.'

    print "\n" + Fore.CYAN + "Result Codes:" + Style.NORMAL

    ui = Thread(target=update_ui)
    ui.daemon = True
    ui.start()

    try:
        for i in range(hits):
            q.put(url.strip())

        q.join()

    except KeyboardInterrupt:
        sys.exit(1)

    _update_ui()
    update_ui_now = False

    print ""

    total_seconds = time.time()-main_start

    print "Total time: %.2f seconds." % total_seconds

    if '200 OK' in result_codes:
        print "Successful Requests Per Second: %.2f" % (result_codes['200 OK'] / total_seconds)

    if durations:
        print "Average response: %.2f seconds." % (reduce(lambda x, y: x + y, durations) / len(durations))
        print "Longest Response: %.2f seconds" % max(durations)
        print "Quickest Response: %.2f seconds" % min(durations)

    if elapsed:
        print "Longest Elapsed: %.2f seconds" % max(elapsed)
        print "Quickest Elapsed: %.2f seconds" % min(elapsed)

    print ""

if __name__ == "__main__":
    main()
