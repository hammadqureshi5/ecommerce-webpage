# Start Modern Elegance frontend (static shop UI)
Set-Location $PSScriptRoot
Write-Host "Modern Elegance shop: http://127.0.0.1:5500/index.html"
Write-Host "Backend (separate terminal): cd ..\backend; python app.py"
python -m http.server 5500
