"""
Django-cms test
Sets up a djangocms installation, and hits '/' a number of times.
'/' is not super interesting, but it still exercises a little bit of
functionality; looking at cms/templates/cms/welcome.html, it seems
to do a decent amount of template logic, as well as do some basic
user auth.
We could probably improve the flow though, perhaps by logging in
and browsing around.
"""

import os
import requests
import socket
import subprocess
import sys
import tempfile
import time
import json

def setup():
    """
    Set up a djangocms installation.
    Runs the initial bootstrapping without the db migration,
    so that we can turn off sqlite synchronous and avoid fs time.
    Rough testing shows that setting synchronous=OFF is basically
    the same performance as running on /dev/shm
    """

    subprocess.check_call([exe.replace("python3", "djangocms"), "testsite", "--verbose", "--no-sync"])

    with open("testsite/testsite/settings.py", "a") as f:
        f.write("""
from django.db.backends.signals import connection_created
def set_no_sychronous(sender, connection, **kwargs):
    if connection.vendor == 'sqlite':
        cursor = connection.cursor()
        cursor.execute('PRAGMA synchronous = OFF;')

connection_created.connect(set_no_sychronous)
""")
    start = time.time()
    subprocess.check_call([exe, "manage.py", "migrate"], cwd="testsite")
    elapsed = time.time() - start
    print("%.2fs to initialize db" % (elapsed,))

def waitUntilUp(addr, timeout=10.0):
    start = time.time()
    while True:
        try:
            with socket.create_connection(addr) as sock:
                return
        except ConnectionRefusedError:
            if time.time() > start + timeout:
                raise Exception("Timeout reached when trying to connect")
            time.sleep(0.001)

def runbenchmark(n=800, out_file=None):
    p = subprocess.Popen([exe, "manage.py", "runserver", "--noreload"], cwd="testsite", stdout=open("/dev/null", "w"), stderr=subprocess.STDOUT)
    try:
        waitUntilUp(("127.0.0.1", 8000))

        start = time.time()
        times = []
        for i in range(n):
            times.append(time.time())
            if i % 100 == 0:
                print(i, time.time() - start)
            requests.get("http://localhost:8000/").text
        times.append(time.time())
        elapsed = time.time() - start
        print("%.2fs (%.3freq/s)" % (elapsed, n / elapsed))

        exitcode = p.poll()
        assert exitcode is None, exitcode

        if out_file:
            json.dump(times, open(out_file, 'w'))

    finally:
        p.terminate()
        p.wait()

if __name__ == "__main__":
    exe = sys.executable
    # Hack: make sure this file gets run as "python3" so that perf will collate across different processes
    if not exe.endswith('3'):
        os.execv(exe + '3', [exe + '3'] + sys.argv)

    os.environ["PATH"] = os.path.dirname(exe) + ":" + os.environ["PATH"]

    """
    Usage:
        python djangocms.py
        python djangocms.py --setup DIR
        python djangocms.py --serve DIR

    The first form creates a temporary directory, sets up djangocms in it,
    serves out of it, and removes the directory.
    The second form sets up a djangocms installation in the given directory.
    The third form runs a benchmark out of an already-set-up directory
    The second and third forms are useful if you want to benchmark the
    initial migration phase separately from the second serving phase.
    """
    if "--setup" in sys.argv:
        assert len(sys.argv) > 2
        dir = sys.argv[-1]
        os.makedirs(dir, exist_ok=True)
        os.chdir(dir)
        setup()
    elif "--serve" in sys.argv:
        assert len(sys.argv) > 2
        os.chdir(sys.argv[-1])
        runbenchmark()
    else:
        n = 800
        if len(sys.argv) > 1:
            n = int(sys.argv[1])
        out_file = None
        if len(sys.argv) > 2:
            out_file = os.path.abspath(sys.argv[2])

        # It might be interesting to put the temporary directory in /dev/shm,
        # which makes the initial db migration about 20% faster.
        with tempfile.TemporaryDirectory(prefix="djangocms_test_") as d:
            os.chdir(d)

            setup()
            runbenchmark(n, out_file)
