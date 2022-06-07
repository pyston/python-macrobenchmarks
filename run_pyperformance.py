import os
import subprocess

import pyperformance.cli
from pyperformance._venv import VirtualEnvironment

if __name__ == "__main__":
    packages = os.environ.get("EXTRA_PACKAGES", "")
    if packages:
        packages = [pkg for pkg in packages.split(';')]

    ensure_reqs = VirtualEnvironment.ensure_reqs
    def new_ensure_reqs(self, *args, **kw):
        python = self.python

        r = ensure_reqs(self, *args, **kw)

        if packages:
            print("Installing", packages)
            subprocess.check_call([python, "-m", "pip", "install"] + packages)

            if "pyston_lite_autoload" in packages:
                subprocess.check_call([python, "-c", "import sys; assert 'pyston_lite' in sys.modules"])
        return r

    VirtualEnvironment.ensure_reqs = new_ensure_reqs


    pyperformance.cli.main()
