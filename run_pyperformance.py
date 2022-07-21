import os
import subprocess

import pyperformance.cli
from pyperformance._venv import VirtualEnvironment

if __name__ == "__main__":
    raw_wheels = os.environ["EXTRA_WHEELS"]
    assert raw_wheels
    wheels = []
    for fn in raw_wheels.split(';'):
        if os.path.exists(fn):
            wheels.append(os.path.abspath(fn))
        else:
            wheels.append(fn)
    assert wheels

    ensure_reqs = VirtualEnvironment.ensure_reqs
    def new_ensure_reqs(self, *args, **kw):
        python = self.python

        r = ensure_reqs(self, *args, **kw)

        print("Installing", wheels)
        subprocess.check_call([python, "-m", "pip", "install"] + wheels)
        if "pyston_lite_autoload" in raw_wheels:
            subprocess.check_call([python, "-c", "import sys; assert 'pyston_lite' in sys.modules"])
        return r

    VirtualEnvironment.ensure_reqs = new_ensure_reqs


    pyperformance.cli.main()
