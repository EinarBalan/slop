# README

To run with background generation
```sh
python3 server.py --background
```

To run without background generation (for testing purposes)
```sh
python3 server.py
```

Notes:
- Argument parsing does not enforce choices; unknown values won’t match any branch.
- Some modes (`finetuned`, `slop`) are marked TODO in code.