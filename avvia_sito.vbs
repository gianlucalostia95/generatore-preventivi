Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

' Cartella dove si trova questo script, cosi' funziona indipendentemente da
' dove viene scaricato/posizionato il progetto sul PC di chi lo usa.
cartella = FSO.GetParentFolderName(WScript.ScriptFullName) & "\"
WshShell.CurrentDirectory = cartella

comando = """" & cartella & "venv\Scripts\python.exe"" -m uvicorn webapp.main:app --host 127.0.0.1 --port 8443 --ssl-keyfile """ & cartella & "certs\localhost-key.pem"" --ssl-certfile """ & cartella & "certs\localhost-cert.pem"""

' Avvia il server completamente nascosto (nessuna finestra visibile)
WshShell.Run comando, 0, False

' Attende che il server sia pronto, poi apre un'unica scheda del browser
WScript.Sleep 3000
WshShell.Run "https://localhost:8443", 1, False
