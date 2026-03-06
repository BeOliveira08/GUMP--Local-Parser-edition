' run_gump.vbs
' Executa run_gump.bat escondido (sem exibir a janela do CMD)

Set objFSO = CreateObject("Scripting.FileSystemObject")
Set objShell = CreateObject("WScript.Shell")

' Pega o diretório do script
strPath = objFSO.GetParentFolderName(WScript.ScriptFullName)
strBatchFile = objFSO.BuildPath(strPath, "run_gump.bat")

' Executa o batch escondido (0 = janela escondida, True = espera terminar)
objShell.Run strBatchFile, 0, True

' Quando o batch termina, o script termina junto (encerra tudo)
