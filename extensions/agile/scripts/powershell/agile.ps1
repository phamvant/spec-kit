$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
& python (Join-Path $ScriptDir "..\agile\cli.py") @args
exit $LASTEXITCODE

