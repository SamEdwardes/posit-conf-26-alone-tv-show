# AGENTS.md

## Rules

- Format the code on every turn with `uvx ruff check --select I,F401 --fix . && uvx ruff format .`
- Lint the code on every turn and fix errors with `uvx ruff --fix`
- Commit on every turn

## Tooling

- Python 3.14
- Use the `polars` library for all data analysis
- Use `uv` for all package management (e.g. `uv add polars`)

## Setup

```bash
uv sync
uv run prek install
```

## Shiny App

```bash
uv run shiny run --reload app.py
```

## Data

[data/alone-contestants.csv](data/alone-contestants.csv) has 124 contestants from
seasons 1 to 12: age, hometown, days lasted, how their run ended, and the 10 items
they took.

Two things to know about the data:

- Season 4 was played by two-person teams. It has 14 contestants and two winners,
  so there are 13 winners across 12 seasons.
- Each season records the 10 items with different wording (`Sleeping bag` and
  `Sleeping Bag`, `Bow & arrows` and `Bow and 6 arrows`). The server folds the 65
  raw strings into 25 canonical items, so counts are correct.
