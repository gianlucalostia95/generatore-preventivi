$cartella = $PSScriptRoot
$collegamento = (New-Object -ComObject WScript.Shell).CreateShortcut("$env:USERPROFILE\Desktop\Generatore Preventivi.lnk")
$collegamento.TargetPath = Join-Path $cartella "avvia_preventivi.vbs"
$collegamento.WorkingDirectory = $cartella
$collegamento.IconLocation = Join-Path $cartella "venv\Scripts\python.exe,0"
$collegamento.Description = "Avvia il Generatore di Preventivi in locale"
$collegamento.Save()
Write-Output "Icona 'Generatore Preventivi' creata sul Desktop."
