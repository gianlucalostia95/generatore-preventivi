Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

' Cartella dove si trova questo script, cosi' funziona indipendentemente da
' dove viene scaricato/posizionato il progetto sul PC di chi lo usa.
cartella = FSO.GetParentFolderName(WScript.ScriptFullName) & "\"
WshShell.CurrentDirectory = cartella

comando = """" & cartella & "venv\Scripts\python.exe"" -m streamlit run """ & cartella & "Generazione_Preventivo.py"" --browser.gatherUsageStats=false"

' Avvia il server Streamlit completamente nascosto (nessuna finestra visibile)
WshShell.Run comando, 0, False

' Attende che il server sia pronto, poi apre un'unica scheda del browser
WScript.Sleep 3000
WshShell.Run "http://localhost:8501", 1, False
