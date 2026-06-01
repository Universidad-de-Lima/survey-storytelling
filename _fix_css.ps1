$f = Resolve-Path "zoho-survey/shared/css/dashboard.css"
$c = [System.IO.File]::ReadAllText($f, [System.Text.Encoding]::UTF8)

$old = ".csat-labels-above {`n  position: relative;`n  height: 56px;`n  margin-bottom: 2px;`n}"
$new = ".csat-labels-above {`n  position: relative;`n}`n"
$c = $c.Replace($old, $new)

$old2 = ".csat-label-above {`n  position: absolute;`n  font-size: 10px;`n  font-weight: var(--font-bold);`n  color: var(--gray-700);`n  white-space: nowrap;`n  text-align: center;`n  transform: translateX(-50%);`n}`n`n.csat-label-above::after {`n  content: '';`n  position: absolute;`n  left: 50%;`n  top: 100%;`n  width: 1px;`n  height: 6px;`n  background: var(--gray-400);`n}"
$new2 = ".csat-label-row {`n  position: relative;`n  height: 18px;`n}`n`n.csat-label-above {`n  position: absolute;`n  font-size: 10px;`n  font-weight: var(--font-bold);`n  color: var(--gray-700);`n  white-space: nowrap;`n  text-align: center;`n  transform: translateX(-50%);`n}`n`n.csat-label-row:last-child .csat-label-above::after {`n  content: '';`n  position: absolute;`n  left: 50%;`n  top: 100%;`n  width: 1px;`n  height: 6px;`n  background: var(--gray-400);`n}"
$c = $c.Replace($old2, $new2)

[System.IO.File]::WriteAllText($f, $c, [System.Text.Encoding]::UTF8)
Write-Host "CSS updated"
