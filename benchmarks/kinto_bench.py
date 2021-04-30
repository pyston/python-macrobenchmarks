import json
import os
import requests
import subprocess
import sys
import threading
import time
import urllib

from djangocms import waitUntilUp

from os.path import join, abspath, dirname

if __name__ == "__main__":
    exe = sys.executable
    def bin(name):
        return join(dirname(exe), name)
    def rel(path):
        return abspath(join(dirname(__file__), path))

    times = []

    subprocess.check_call([abspath(exe), rel("../data/kinto_project/setup.py"), "develop"], cwd=rel("../data/kinto_project"), stdout=open("/dev/null", "w"), stderr=subprocess.STDOUT)

    try:
        os.remove("/tmp/kinto.sock")
    except FileNotFoundError:
        pass
    p1 = subprocess.Popen([bin("uwsgi"), rel("../data/kinto_project/production.ini")], cwd=rel("../data/kinto_project"), stdout=open("/dev/null", "w"), stderr=subprocess.STDOUT)
    # p1 = subprocess.Popen([bin("uwsgi"), rel("../data/kinto_project/production.ini")], cwd=rel("../data/kinto_project"))
    while not os.path.exists("/tmp/kinto.sock"):
        time.sleep(0.001)

    # p2 = subprocess.Popen(["nginx", "-c", abspath("../data/kinto_project/nginx.conf"), "-p", abspath("../data/kinto_project")], cwd="../data/kinto_project", stdout=open("/dev/null", "w"), stderr=subprocess.STDOUT)
    p2 = subprocess.Popen(["nginx", "-c", rel("../data/kinto_project/nginx.conf"), "-p", rel("../data/kinto_project")], cwd=rel("../data/kinto_project"))

    time.sleep(0.010)

    try:
        waitUntilUp(("127.0.0.1", 8000))

        assert p1.poll() is None, p1.poll()
        assert p2.poll() is None, p2.poll()

        print(requests.get("http://localhost:8000/v1").text)
        # print(requests.put("http://localhost:8000/v1/accounts/testuser", json={"data": {"password": "password1"}}).text)

        n = 5000
        if len(sys.argv) > 1:
            n = int(sys.argv[1])

        start = time.time()
        for i in range(n):
            times.append(time.time())
            if i % 100 == 0:
                print(i, time.time() - start)
            # requests.get("http://localhost:8000/v1/").text
            urllib.request.urlopen("http://localhost:8000/v1/").read()
        times.append(time.time())
        elapsed = time.time() - start
        print("%.2fs (%.3freq/s)" % (elapsed, n / elapsed))

        assert p1.poll() is None, p1.poll()
        assert p2.poll() is None, p2.poll()

    finally:
        p1.terminate()
        p1.kill()
        p1.wait()
        # p2.kill()
        p2.terminate()
        p2.wait()

    if len(sys.argv) > 2:
        json.dump(times, open(sys.argv[2], 'w'))
