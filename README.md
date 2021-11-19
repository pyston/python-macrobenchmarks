# python-macrobenchmarks
A collection of macro benchmarks for the Python programming language


## usage

```shell
# Run the default benchmarks:
python3 -m pyperformance run --manifest ./benchmarks/MANIFEST
```

The benchmarks can still be run without pyperformance.  This will produce
 the old results format.

```shell
# Run the benchmarks:
sh ./run_all.sh

# Run the mypy benchmark using mypyc:
sh ./run_mypy.sh
```
