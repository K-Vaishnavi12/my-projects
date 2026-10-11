# =============================================================
# Symposium - PowerShell task runner
# Usage: .\tasks.ps1 <task>
# =============================================================
param(
    [Parameter(Position = 0)]
    [ValidateSet(
        'install', 'lint', 'test', 'etl', 'train', 'debate',
        'export', 'faiss', 'app', 'docker-up', 'docker-down',
        'showcase', 'clean', 'help'
    )]
    [string]$Task = 'help'
)

$ErrorActionPreference = 'Stop'

function Invoke-Install {
    # 1. Upgrade pip
    python -m pip install --upgrade pip

    # 2. Install torch FIRST from the CPU wheel index (~200 MB).
    #    This is required on Windows so sentence-transformers doesn't try
    #    to pull a CUDA build.
    python -m pip install torch --index-url https://download.pytorch.org/whl/cpu

    # 3. Everything else from the standard PyPI index.
    python -m pip install -r requirements.txt

    Write-Host ''
    Write-Host 'Install complete. Verify with: .\tasks.ps1 test' -ForegroundColor Green
}

function Invoke-Lint {
    # ruff is optional; fall back to a simple compile check
    if (Get-Command ruff -ErrorAction SilentlyContinue) {
        ruff check symposium app scripts tests
    } else {
        Get-ChildItem -Recurse -Filter *.py |
            Where-Object { $_.FullName -notmatch '\\\.venv\\|__pycache__' } |
            ForEach-Object { python -m py_compile $_.FullName }
        Write-Host 'All Python files compile.' -ForegroundColor Green
    }
}

function Invoke-Test {
    pytest tests -v
}

function Invoke-Etl {
    python scripts\run_etl.py --topics all
}

function Invoke-Train {
    python scripts\train_models.py
}

function Invoke-Debate {
    python scripts\run_debate.py "Is progress in AI good for humanity?" --rounds 1
}

function Invoke-Export {
    python scripts\export_csv.py
}

function Invoke-Faiss {
    python scripts\build_faiss.py
}

function Invoke-App {
    streamlit run app\Home.py
}

function Invoke-DockerUp {
    docker compose up -d --build
}

function Invoke-DockerDown {
    docker compose down
}

function Invoke-Showcase {
    python -m symposium.utils.python_showcase
}

function Invoke-Clean {
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue data\raw\*, data\staging\*, data\processed\*, data\models\*, data\exports\*
    Write-Host 'Cleaned data\* directories.'
}

function Show-Help {
    Write-Host @'
Symposium tasks:
  install       Install Python dependencies
  lint          Run ruff linter
  test          Run pytest
  etl           Run full ETL for all topics
  train         Train + save all ML models
  debate        Run one debate on the CLI
  export        Export DWH tables to CSV for Power BI
  faiss         Build local FAISS snapshots from Mongo
  app           Launch Streamlit UI
  docker-up     docker compose up -d --build
  docker-down   docker compose down
  showcase      Run the Python-advanced showcase script
  clean         Wipe data/ subfolders (raw/staging/processed/models/exports)
  help          Show this message

Example: .\tasks.ps1 etl
'@
}

switch ($Task) {
    'install'     { Invoke-Install }
    'lint'        { Invoke-Lint }
    'test'        { Invoke-Test }
    'etl'         { Invoke-Etl }
    'train'       { Invoke-Train }
    'debate'      { Invoke-Debate }
    'export'      { Invoke-Export }
    'faiss'       { Invoke-Faiss }
    'app'         { Invoke-App }
    'docker-up'   { Invoke-DockerUp }
    'docker-down' { Invoke-DockerDown }
    'showcase'    { Invoke-Showcase }
    'clean'       { Invoke-Clean }
    default       { Show-Help }
}
