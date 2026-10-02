# Writes printers.json by letting the user pick this PC's two label printers
# from a numbered list, so nobody has to type exact names or JSON by hand.
#
# Run it again any time the printers change:
#   powershell -NoProfile -ExecutionPolicy Bypass -File choose_printers.ps1
#
# -Shoe / -Box take a number from the list or an exact printer name, and skip
# the questions (used by setup.bat tests).
param(
    [string]$Path = (Join-Path $PSScriptRoot 'printers.json'),
    [string]$Shoe,
    [string]$Box
)
$ErrorActionPreference = 'Stop'

$printers = @(Get-Printer | Select-Object -ExpandProperty Name | Sort-Object)
if ($printers.Count -eq 0) {
    Write-Host ""
    Write-Host "  No printers are installed on this PC. Install the two label printers in"
    Write-Host "  Windows first, then run this again."
    exit 1
}

Write-Host ""
Write-Host "  Printers installed on this PC:"
for ($i = 0; $i -lt $printers.Count; $i++) {
    Write-Host ("    {0}. {1}" -f ($i + 1), $printers[$i])
}
Write-Host ""

function Pick([string]$question, [string]$given) {
    while ($true) {
        $answer = if ($given) { $given } else { Read-Host "  $question" }
        $given = $null
        $n = 0
        if ([int]::TryParse($answer, [ref]$n) -and $n -ge 1 -and $n -le $printers.Count) {
            return $printers[$n - 1]
        }
        if ($printers -contains $answer) { return $answer }
        Write-Host "    Type a number from 1 to $($printers.Count)."
    }
}

$shoeName = Pick "Number of the printer for the SMALL labels (one per pair)" $Shoe
$boxName  = Pick "Number of the printer for the 4x6 BOX labels" $Box

$json = [ordered]@{ shoe_printer = $shoeName; big_box_printer = $boxName } | ConvertTo-Json
# The program reads this file with Windows' default encoding, so keep it pure
# ASCII: escape anything else (an accent in a printer name) as \uXXXX, and
# write it without the byte-order mark Windows PowerShell adds to UTF-8.
$json = [regex]::Replace($json, '[^\x00-\x7F]', { param($m) '\u{0:x4}' -f [int][char]$m.Value })
[IO.File]::WriteAllText($Path, $json + "`r`n", (New-Object Text.ASCIIEncoding))

Write-Host ""
Write-Host "  Saved:"
Write-Host "    Small labels (pairs) -> $shoeName"
Write-Host "    4x6 box labels       -> $boxName"
