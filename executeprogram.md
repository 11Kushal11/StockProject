Yes. All the project packages (yfinance, pandas, scipy, aiohttp, etc.) are installed specifically inside that isolated venv folder rather than globally across your system.

Step-by-Step Run Routine After PC Restart

Open the Project in VS Code

Launch VS Code and open C:\stockanalysis (or click File > Open Folder...).

Open the Terminal

Press Ctrl + `  (backtick) or go to Terminal > New Terminal.

Check for (venv)

Look at your terminal line. If it already starts with (venv), VS Code auto-activated it.

If it does not show (venv), activate it manually:

In PowerShell:

PowerShell
.\venv\Scripts\Activate.ps1
In Command Prompt (CMD):

DOS
.\venv\Scripts\activate.bat
Run the Engine

Bash
python main.py