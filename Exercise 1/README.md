# Exercise 1

All tasks of this exercise are confined to the jupyter notebook [exercise1.ipynb](./exercise1.ipynb).

Read the notebook carefully and solve the tasks.

## Setup

The notebooks are tested against Python 3.14 and the package versions pinned in `uv.lock`.
Other versions might work, but we do not test against them.

### Recommended: uv

[Install `uv`](https://docs.astral.sh/uv/getting-started/installation/), then run in the exercise folder:

```bash
uv sync
uv run jupyter notebook
```

`uv sync` downloads Python 3.14 if necessary, creates the virtual environment `.venv`, and installs all required packages (`notebook`, `ipywidgets`, `ipympl`, `matplotlib`, and `numpy`).
If you prefer VS Code or another editor, select the interpreter `.venv` as the notebook kernel.

### Fallback: virtual environment

You need Python 3.14 installed. Run in the exercise folder:

```bash
python3.14 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
jupyter notebook
```

## Submission

Only upload the `exercise1.ipynb` to Moodle.