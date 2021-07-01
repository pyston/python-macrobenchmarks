import json
import os
import requests
import subprocess
import sys
import threading
import time

from djangocms import waitUntilUp

if __name__ == "__main__":
    exe = sys.executable

    times = []

    p = subprocess.Popen([exe, "gunicorn_serve.py"], stdout=open("/dev/null", "w"), stderr=subprocess.STDOUT, cwd=os.path.join(os.path.dirname(__file__), "../data"))
    try:
        waitUntilUp(("127.0.0.1", 8080))

        n = 3000
        if len(sys.argv) > 1:
            n = int(sys.argv[1])

        start = time.time()
        for i in range(n):
            times.append(time.time())
            if i % 100 == 0:
                print(i, time.time() - start)
            requests.get("http://localhost:8080/blog/").text
        times.append(time.time())
        elapsed = time.time() - start
        print("%.2fs (%.3freq/s)" % (elapsed, n / elapsed))

        assert p.poll() is None, p.poll()

    finally:
        p.terminate()
        p.wait()

    if len(sys.argv) > 2:
        json.dump(times, open(sys.argv[2], 'w'))
