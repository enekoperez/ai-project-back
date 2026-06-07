# Agent Instructions

Always check for and use the project virtual environment before running Python commands, tests, linters, or package tools.

For this repository, prefer:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m pip
```

Do not assume the system Python has the same dependencies as `.venv`.
