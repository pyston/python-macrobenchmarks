import sys


def maybe_handle_legacy(bench_func, *args, loopsarg='loops', legacyarg=None):
    if '--legacy' not in sys.argv:
        return
    argv = list(sys.argv[1:])
    argv.remove('--legacy')

    kwargs = {}
    if legacyarg:
        kwargs[legacyarg] = True
    if argv:
        assert loopsarg
        kwargs[loopsarg] = int(argv[0])

    _, times = bench_func(*args, **kwargs)
    if len(argv) > 1:
        json.dump(times, open(argv[1], 'w'))

    sys.exit(0)
