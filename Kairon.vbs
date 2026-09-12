Set shell = CreateObject("WScript.Shell")
Set fileSystem = CreateObject("Scripting.FileSystemObject")

projectPath = fileSystem.GetParentFolderName(WScript.ScriptFullName)
command = "powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command ""Set-Location -LiteralPath '" & projectPath & "'; pnpm dev"""

shell.Run command, 0, False
