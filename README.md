# python-macrobenchmarks
A collection of macro benchmarks for the Python programming language


## Usage

```shell
# Run the benchmarks that Pyston uses to measure itself:
python3 -m pyperformance run --manifest $PWD/benchmarks/MANIFEST -b pyston_standard

# Run (almost) all the benchmarks in the repository:
python3 -m pyperformance run --manifest $PWD/benchmarks/MANIFEST -b all
```

The benchmarks can still be run without pyperformance.  This will produce
 the old results format.

```shell
# Run the benchmarks:
sh ./run_all.sh

# Run the mypy benchmark using mypyc:
sh ./run_mypy.sh
```
