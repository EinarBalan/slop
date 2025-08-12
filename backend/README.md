# README

To run with background generation
```sh
python3 server.py --background
```

To run without background generation (for testing purposes)
```sh
python3 server.py
```

### Experiment modes
Use the `--experiment` argument to select an experiment mode.

Allowed values:
- base (default)
- summarize
- user-defined
- finetuned
- slop

Examples:
```sh
python3 server.py --experiment summarize
python3 server.py --experiment base --background
```

Notes:
- Argument parsing does not enforce choices; unknown values won’t match any branch.
- Some modes (`finetuned`, `slop`) are marked TODO in code.