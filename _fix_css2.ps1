$f = Resolve-Path "zoho-survey/shared/css/dashboard.css"
$c = [System.IO.File]::ReadAllText($f, [System.Text.Encoding]::UTF8)

# Remove the csat-labels-above and csat-label-row styles, restore original csat-bar
$old = ".csat-bar {`n  height: auto;`n  display: flex;`n  flex-direction: column;`n  border-radius: 4px;`n  font-size: 11px;`n}"
$new = ".csat-bar {`n  height: 32px;`n  display: flex;`n  border-radius: 4px;`n  overflow: hidden;`n  font-size: 11px;`n  animation: stackedGrow 0.8s ease-out forwards;`n}"
$c = $c.Replace($old, $new)

# Remove .csat-labels-above section
$remove1 = ".csat-labels-above {`n  position: relative;`n}`n`n.csat-label-row {`n  position: relative;`n  height: 18px;`n}`n`n.csat-label-above {`n  position: absolute;`n  font-size: 10px;`n  font-weight: var(--font-bold);`n"
$c = $c.Replace($remove1, "")

# Find and remove remaining csat-label-above and csat-label-row styles
$idx = $c.IndexOf(".csat-label-row")
if ($idx -ge 0) {
    $endIdx = $c.IndexOf(".legend", $idx)
    if ($endIdx -ge 0) {
        $c = $c.Remove($idx, $endIdx - $idx)
    }
}

[System.IO.File]::WriteAllText($f, $c, [System.Text.Encoding]::UTF8)
Write-Host "CSS cleaned"
