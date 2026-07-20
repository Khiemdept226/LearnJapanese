$ErrorActionPreference = 'Stop'
$PythonDir = ".\.portable_python"
$PythonExe = Join-Path $PythonDir "python.exe"
$InstallerExe = "python-3.11.9-amd64.exe"
$PythonUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
$GetPipUrl = "https://bootstrap.pypa.io/get-pip.py"

if (-not (Test-Path -Path $PythonExe)) {
    if (Test-Path -Path $PythonDir) {
        Remove-Item -Path $PythonDir -Recurse -Force -ErrorAction SilentlyContinue
    }
    
    Write-Host "Downloading Python 3.11.9 Installer..."
    curl.exe -L -o $InstallerExe $PythonUrl
    
    Write-Host "Installing Python locally (this may take a minute)..."
    $tgt = "$PWD\.portable_python"
    $InstallArgs = '/quiet InstallAllUsers=0 TargetDir="' + $tgt + '" Include_test=0 Include_launcher=0'
    Start-Process -Wait -FilePath ".\" -ArgumentList $InstallArgs
    
    Remove-Item -Path $InstallerExe -ErrorAction SilentlyContinue

    Write-Host "Installing pip..."
    curl.exe -L -o "get-pip.py" $GetPipUrl
    & $PythonExe "get-pip.py"
    Remove-Item -Path "get-pip.py" -ErrorAction SilentlyContinue
}

Write-Host "Installing dependencies..."
& $PythonExe -m pip install -r requirements.txt -q

Write-Host "Starting Desktop App..."
& $PythonExe "desktop_app\main.py"
