' uninstall.vbs
' Ejecuta el desinstalador escondido (sin cmd visible)

Set objFSO = CreateObject("Scripting.FileSystemObject")
Set objShell = CreateObject("WScript.Shell")

' Pega o diretório do script
strPath = objFSO.GetParentFolderName(WScript.ScriptFullName)
strBatchFile = objFSO.BuildPath(strPath, "uninstall.bat")

' Executa o batch escondido (0 = janela escondida)
objShell.Run strBatchFile, 0, False
