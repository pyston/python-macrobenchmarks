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

import contextlib
from contextlib import nullcontext
import os
import os.path
import requests
import shutil
import subprocess
import sys
import tempfile

import pyperf
import netutils


DATADIR = os.path.join(
    os.path.dirname(__file__),
    "data",
)
PID_FILE = os.path.join(DATADIR, "setup.pid")
# It might be interesting to put the temporary directory in /dev/shm,
# which makes the initial db migration about 20% faster.
TEMP_DIR = None
TEMP_PREFIX = "djangocms_bench_"

INNER_LOOPS = 800

# site
SITE_NAME = "testsite"
SETTINGS = """
from django.db.backends.signals import connection_created
def set_no_sychronous(sender, connection, **kwargs):
    if connection.vendor == 'sqlite':
        cursor = connection.cursor()
        cursor.execute('PRAGMA synchronous = OFF;')

connection_created.connect(set_no_sychronous)
"""

# django commands
DJANGOCMS = os.path.join(
    os.path.dirname(sys.executable),
    "djangocms",
)
ARGV_CREATE = [DJANGOCMS, SITE_NAME, "--verbose", "--no-sync"]
ARGV_MIGRATE = [sys.executable, "manage.py", "migrate"]
ARGV_SERVE = [sys.executable, "manage.py", "runserver", "--noreload"]


def setup(rootdir):
    """
    Set up a djangocms installation.
    Runs the initial bootstrapping without the db migration,
    so that we can turn off sqlite synchronous and avoid fs time.
    Rough testing shows that setting synchronous=OFF is basically
    the same performance as running on /dev/shm.
    """
    sitedir = os.path.join(rootdir, SITE_NAME)  # This is where Django puts it.

    # Delete the site dir if it already exists.
    if os.path.exists(sitedir):
        shutil.rmtree(datadir, ignore_errors=False)

    # First, create the site.
    subprocess.check_call(ARGV_CREATE, cwd=rootdir)

    # Add customizations.
    settingsfile = os.path.join(sitedir, SITE_NAME, "settings.py")
    with open(settingsfile, "a") as f:
        f.write(SETTINGS)

    # Finalize the site.
    t0 = pyperf.perf_counter()
    subprocess.check_call(ARGV_MIGRATE, cwd=sitedir)
    elapsed = pyperf.perf_counter() - t0

    return sitedir, elapsed


# This is a generic util that might make sense to put in a separate lib.
def _ensure_python_on_PATH(python=sys.executable):
    PATH = os.environ["PATH"].split(os.pathsep)
    PATH.insert(0, os.path.dirname(python))
    os.environ["PATH"] = os.pathsep.join(PATH)


@contextlib.contextmanager
def _ensure_datadir(datadir, preserve=True):
    if datadir:
        try:
            os.makedirs(datadir)
        except FileExistsError:
            if preserve is None:
                preserve = True
            elif not preserve:
                raise NotImplementedError(datadir)
    else:
        datadir = tempfile.mkdtemp(prefix=TEMP_PREFIX, dir=TEMP_DIR)

    try:
        yield datadir
    finally:
        if not preserve:
            shutil.rmtree(datadir, ignore_errors=True)


#############################
# benchmarks

def bench_djangocms_requests(sitedir, loops=INNER_LOOPS):
    elapsed, _ = _bench_djangocms_requests(sitedir, loops)
    return elapsed


def _bench_djangocms_requests(sitedir, loops=INNER_LOOPS, legacy=False):
    """Measure N HTTP requests to a local server.

    Note that the server is freshly started here.

    Only the time for requests is measured here.  The following are not:

    * preparing the site the server will serve
    * starting the server
    * stopping the server

    Hence this should be used with bench_time_func()
    insted of bench_func().
    """
    start = pyperf.perf_counter()
    elapsed = 0
    times = []

    for i in range(loops):
        # This is a macro benchmark for a Python implementation
        # so "elapsed" covers more than just how long a request takes.
        t0 = pyperf.perf_counter()
        requests.get("http://localhost:8000/").text
        t1 = pyperf.perf_counter()

        elapsed += t1 - t0
        times.append(t0)
        if legacy and (i % 100 == 0):
            print(i, t0 - start)
    times.append(pyperf.perf_counter())
    if legacy:
        total = times[-1] - start
        print("%.2fs (%.3freq/s)" % (total, loops / total))
    return elapsed, times


# We can't set "add_cmdline_args" on pyperf.Runner
# once we've created one.  We work around this with a subclass.

class _Runner(pyperf.Runner):
    datadir = None

    def __init__(self):
        def add_worker_args(cmd, _):
            assert self.datadir
            cmd.extend([
                '--serve', self.datadir,
            ])
        super().__init__(
            add_cmdline_args=add_worker_args,
        )


#############################
# the script

if __name__ == "__main__":
    """
    Usage:
        python benchmarks/bm_djangocms/run_benchmark.py
        python benchmarks/bm_djangocms/run_benchmark.py --setup DIR
        python benchmarks/bm_djangocms/run_benchmark.py --serve DIR

    The first form creates a temporary directory, sets up djangocms in it,
    serves out of it, and removes the directory.
    The second form sets up a djangocms installation in the given directory.
    The third form runs the benchmark out of an already-set-up directory
    The second and third forms are useful if you want to benchmark the
    initial migration phase separately from the second serving phase.
    """
    runner = _Runner()
    runner.metadata['description'] = "Test the performance of a Django data migration"

    # Parse the CLI args.
    runner.argparser.add_argument("--legacy", action='store_true')
    group = runner.argparser.add_mutually_exclusive_group()
    group.add_argument("--setup")
    group.add_argument("--serve")

    legacy_args = None
    if "--legacy" in sys.argv:
        args, legacy_args = runner.argparser.parse_known_args()
    else:
        args = runner.argparser.parse_args()

    if args.setup is not None:
        args.datadir = args.setup
        args.setup = True
        args.serve = False
    elif args.serve is not None:
        args.datadir = args.serve
        args.setup = False
        args.serve = True
        if not os.path.exists(args.datadir):
            cmd = f"{sys.executable} {sys.argv[0]} --setup {args.datadir}?"
            sys.exit(f"ERROR: Did you forget to run {cmd}?")
    else:
        args.datadir = None
        args.setup = True
        args.serve = True

    # DjangoCMS looks for Python on $PATH?
    _ensure_python_on_PATH()

    # Get everything ready and then perform the requested operations.
    preserve = True if args.setup and not args.serve else None
    with _ensure_datadir(args.datadir, preserve) as datadir:
        # First, set up the site.
        if args.setup:
            sitedir, elapsed = setup(datadir)
            if args.legacy:
                print("%.2fs to initialize db" % (elapsed,))
                print(f"site created in {sitedir}")
            if not args.serve:
                print(f"now run {sys.executable} {sys.argv[0]} --serve {datadir}")
        else:
            # This is what a previous call to setup() would have returned.
            sitedir = os.path.join(datadir, SITE_NAME)

        # Then run the benchmark.
        if args.serve:
            if "--worker" not in sys.argv:
                context = netutils.serving(ARGV_SERVE, sitedir, "127.0.0.1:8000")
            else:
                context = nullcontext()

            with context:
                if args.legacy:
                    from legacyutils import maybe_handle_legacy
                    sys.argv[1:] = ["--legacy"] + legacy_args
                    maybe_handle_legacy(_bench_djangocms_requests, sitedir, legacyarg='legacy')
                    sys.exit(0)

                runner.datadir = datadir

                def time_func(loops, *args):
                    return bench_djangocms_requests(*args, loops=loops)
                runner.bench_time_func("djangocms", time_func, sitedir,
                                       inner_loops=INNER_LOOPS)
