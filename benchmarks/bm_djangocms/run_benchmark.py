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


def bench_djangocms(sitedir, loops=INNER_LOOPS):
    requests_get = requests.get
    loops = iter(range(loops))

    with netutils.serving(ARGV_SERVE, sitedir, "127.0.0.1:8000"):
        t0 = pyperf.perf_counter()
        for _ in loops:
            requests_get("http://localhost:8000/").text
        return pyperf.perf_counter() - t0


if __name__ == "__main__":
    """
    Usage:
        python djangocms.py
        python djangocms.py --setup DATADIR
        python djangocms.py --serve DATADIR

    The first form creates a temporary directory, sets up djangocms in it,
    serves out of it, and removes the directory.
    The second form sets up a djangocms installation in the given directory.
    The third form runs a benchmark out of an already-set-up directory
    The second and third forms are useful if you want to benchmark the
    initial migration phase separately from the second serving phase.
    """
    runner = pyperf.Runner()
    runner.metadata['description'] = "Test the performance of a Django data migration"

    # Parse the CLI args.
    runner.argparser.add_argument("--setup", action="store_const", const=True)
    group = runner.argparser.add_mutually_exclusive_group()
    group.add_argument("--serve")
    group.add_argument("datadir", nargs="?")
    if True:
        runner.argparser.add_argument("--pre", action="store_true")
        runner.argparser.add_argument("--post", action="store_true")
        args = runner.argparser.parse_args()
        if args.pre:
            print('### running as prescript ###')
            sys.exit()
        if args.post:
            print('### running as postscript ###')
            sys.exit()
    args = runner.argparser.parse_args()

    if args.serve is not None:
        args.datadir = args.serve
        args.serve = True
        if not args.setup:
            args.setup = False
            if not args.datadir:
                runner.argparser.error("missing datadir")
            elif not os.path.exists(args.datadir):
                cmd = f"{sys.executable} {sys.argv[0]} --setup {args.datadir}?"
                sys.exit(f"ERROR: Did you forget to run {cmd}?")
        default = False
    elif args.setup is not None:
        args.serve = False
        default = False
    else:
        args.setup = True
        args.serve = True
        default = True

    # DjangoCMS looks for Python on $PATH?
    _ensure_python_on_PATH()

    # Get everything ready and then perform the requested operations.
    preserve = True if args.setup and not args.serve else None
    with _ensure_datadir(args.datadir, preserve) as datadir:
        # First, set up the site.
        if args.setup:
            sitedir, elapsed = setup(datadir)
            print("%.2fs to initialize db" % (elapsed,))
            print(f"site created in {sitedir}")
            if not args.serve:
                print(f"now run {sys.executable} {sys.argv[0]} --serve {datadir}")
        else:
            # This is what a previous call to setup() would have returned.
            sitedir = os.path.join(datadir, SITE_NAME)

        # Then run the benchmark.
        if args.serve:
            def add_worker_args(cmd, _, _datadir=datadir):
                cmd.extend([
                    '--serve', _datadir,
                ])
            # XXX This is an internal attr but we don't have any other good option.
            runner._add_cmdline_args = add_worker_args

            def time_func(loops, *args):
                return bench_djangocms(*args, loops=loops)

            runner.bench_time_func("djangocms", time_func, sitedir,
                                   inner_loops=INNER_LOOPS)
