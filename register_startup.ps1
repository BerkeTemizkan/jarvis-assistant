$WshShell = New-Object -ComObject WScript.Shell
$StartupFolder = [System.IO.Path]::Combine($env:APPDATA, 'Microsoft\Windows\Start Menu\Programs\Startup')
$ShortcutPath = [System.IO.Path]::Combine($StartupFolder, 'Jarvis.lnk')
$VbsPath = "C:\Users\21COMP1067\.gemini\antigravity\scratch\jarvis-assistant\launch_jarvis.vbs"

$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = "wscript.exe"
$Shortcut.Arguments = "`"$VbsPath`""
$Shortcut.WorkingDirectory = "C:\Users\21COMP1067\.gemini\antigravity\scratch\jarvis-assistant"
$Shortcut.Save()

Write-Host "Jarvis Windows Başlangıç kısayolu başarıyla kaydedildi!"
Write-Host "Kısayol Yolu: $ShortcutPath"
