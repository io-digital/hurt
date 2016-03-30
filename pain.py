from threading import Thread
from Queue import Queue

import requests
import sys
import time

import locale

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

other_result_codes = []
durations = []
q = Queue()

result_codes = {}
locale.setlocale(locale.LC_ALL, 'en_US')


def update_ui():
    while True:
        _update_ui()
        time.sleep(0.1)


def _update_ui():
        global timeout_count, result_codes

        print '\r',

        for k, v in result_codes.iteritems():

            print "%ss:" % k,

            if k == 200:
                print(Fore.LIGHTGREEN_EX),

            if k >= 400 and k < 500:
                print(Fore.YELLOW),

            if k >= 500:
                print(Fore.RED),

            print "%s     " % v,
            print(Style.RESET_ALL),

        if timeout_count > 0:
            print('Timeouts:  '+Fore.RED + str(timeout_count) + Style.RESET_ALL),
        sys.stdout.flush()

_timeout = 5


def do_work():
    global timeout_count, result_codes, durations

    while True:
        url = q.get()
        try:
            start = time.time()
            res = requests.get(url, timeout=_timeout)

            if res.status_code not in result_codes:
                result_codes[res.status_code] = 0

            result_codes[res.status_code] += 1

            if res.status_code == 200:
                durations.append(time.time() - start)

        except requests.RequestException:
            timeout_count += 1

        q.task_done()


@click.command()
@click.option('--hits', default=2000, help='Number of requests')
@click.option('--workers', default=500, help='Number of workers')
@click.option('--url', prompt="URL to request")
@click.option('--timeout', default=5)
def main(hits, workers, url, timeout):

    global _timeout, durations, result_codes
    _timeout = timeout
    print ""
    print Fore.CYAN + 'PAIN SO GOOD  v0.0001              ' + Style.RESET_ALL
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

    print ""

    if durations:
        print "\nAverage 200 response time: %.2f seconds." % (reduce(lambda x, y: x + y, durations) / len(durations))

    total_seconds = time.time()-main_start

    print "Total time: %.2f seconds." % total_seconds

    if 200 in result_codes:
        print "Successful Requests Per Second: %.2f" % (result_codes[200] / total_seconds)

    print ""

if __name__ == "__main__":
    main()
