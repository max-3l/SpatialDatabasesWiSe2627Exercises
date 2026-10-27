# Exercises Spatial Databases (WiSe 2026/27)

Welcome to the repository for the exercises of the lecture *Spatial Databases*. For each exercise session, one folder with the canonical name `Exercise N` will be published.

Read the `README.md` within each folder. It describes what we expect of you to solve the exercise.

## AI Guideline

Do **not** use AI in any form (coding assistants, tab completion, chat, etc.) to solve the tasks.
The exercises are designed to help you understand the fundamentals and to prepare you for the exam.
If you do not have enough time to finish, leave tasks unsolved instead of letting AI solve the rest.
We reserve the right to ask you for a detailed in-person explanation of your submission whenever we suspect the use of AI.

## Submitting Solutions

Submissions are generally handled over the assignment management in [Moodle](https://moodle.hpi.de/course/view.php?id=1236) by uploading changed files, if not stated otherwise in the `README.md` of the exercise.

## Fetching New Exercises

To retrieve the new exercises, pull the new changes of this repository into your local copy:

```bash
git pull --autostash
```

`--autostash` temporarily sets aside your uncommitted edits, pulls, and then restores them.
New exercises are added as new `Exercise N` folders, so this does not touch your work on earlier exercises.

If Git reports a conflict because we changed a file that you also edited (for example, because we publish a fix), copy your edited notebook to a different place, run `git restore "Exercise N"` for the affected folder, run `git pull`, and then copy the changes in your notebook back.
