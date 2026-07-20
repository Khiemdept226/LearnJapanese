$ErrorActionPreference = 'Stop'
$PythonExe = ".\.portable_python\python.exe"

if (-not (Test-Path -Path $PythonExe)) {
    Write-Error "Portable Python không tồn tại. Vui lòng chạy .\run.ps1 trước để cài đặt môi trường."
    exit 1
}

Write-Host "Installing PyInstaller..."
& $PythonExe -m pip install pyinstaller -q

Write-Host "Building EXE with PyInstaller..."
# We use --paths to help PyInstaller find our modules
# We use --hidden-import because import_flashcards is imported dynamically
& ".\.portable_python\Scripts\pyinstaller.exe" `
    --onefile `
    --noconsole `
    --name "LearnJapanese" `
    --paths "src" `
    --paths "tools" `
    --hidden-import "import_flashcards" `
    --hidden-import "flashcards" `
    --hidden-import "learning_items" `
    --hidden-import "db" `
    --hidden-import "config" `
    --hidden-import "sheets" `
    --hidden-import "flashcard_sources.sheet_source" `
    --hidden-import "flashcard_sources.pdf_source" `
    --hidden-import "learning_sources.sheet_source" `
    "desktop_app\main.py"

Write-Host "Build complete! File EXE nằm trong thư mục 'dist\LearnJapanese.exe'"
Write-Host "Lưu ý: Khi chạy file EXE này, hãy copy file .env và thư mục credentials/ (nếu có) để cùng cấp với file EXE."
