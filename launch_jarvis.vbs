Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "powershell.exe -ExecutionPolicy Bypass -Command ""$env:PATH = 'C:\Users\21COMP1067\.local\bin;' + $env:PATH; uv run --python 3.12 'C:\Users\21COMP1067\.gemini\antigravity\scratch\jarvis-assistant\jarvis.py'""", 0, False
