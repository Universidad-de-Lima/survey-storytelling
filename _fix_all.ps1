$jsf = Resolve-Path "zoho-survey/shared/js/dashboard.js"
$cssf = Resolve-Path "zoho-survey/shared/css/dashboard.css"
$jsc = [System.IO.File]::ReadAllText($jsf, [System.Text.Encoding]::UTF8)
$cssc = [System.IO.File]::ReadAllText($cssf, [System.Text.Encoding]::UTF8)

# JS: Find renderCSATBar and simplify
$start = $jsc.IndexOf("  function renderCSATBar(csat) {")
$end = $jsc.IndexOf("  // ==================== SECCI", $start)
$oldFunc = $jsc.Substring($start, $end - $start)

$newFunc = "  function renderCSATBar(csat) {" + "`n"
$newFunc += "    const labels = [" + "`n"
$newFunc += "      { key: 'Totalmente satisfecho', color: 'var(--gray-900)' }," + "`n"
$newFunc += "      { key: 'Muy satisfecho', color: 'var(--gray-600)' }," + "`n"
$newFunc += "      { key: 'Satisfecho', color: 'var(--gray-400)' }," + "`n"
$newFunc += "      { key: 'Insatisfecho', color: 'var(--ulima-orange)' }," + "`n"
$newFunc += "      { key: 'Totalmente insatisfecho', color: 'var(--ulima-red)' }," + "`n"
$newFunc += "    ];" + "`n"
$newFunc += "    const total = labels.reduce((s, l) => s + (csat[l.key] || 0), 0);" + "`n"
$newFunc += "    const visibleLabels = labels.filter((l) => csat[l.key] > 0);" + "`n"
$newFunc += "    DOM.csatBar.innerHTML = visibleLabels" + "`n"
$newFunc += "      .map((l) => {" + "`n"
$newFunc += "        const p = pct(csat[l.key], total);" + "`n"
$newFunc += '        return `<div class="csat-segment" style="width:${p}%; background:${l.color};"' + "`n"
$newFunc += '              data-label="${l.key}" data-value="${formatInteger(csat[l.key])} (${formatPctDecimal(csat[l.key], total)})">${formatPctSimple(csat[l.key], total)}</div>`;' + "`n"
$newFunc += "      })" + "`n"
$newFunc += "      .join('');" + "`n"
$newFunc += "    DOM.csatLegend.innerHTML = visibleLabels" + "`n"
$newFunc += "      .map(" + "`n"
$newFunc += "        (l) =>" + "`n"
$newFunc += '          `<div class="legend-item"><div class="legend-dot" style="background:${l.color};"></div>${l.key}: ${formatInteger(csat[l.key])}</div>`,' + "`n"
$newFunc += "      )" + "`n"
$newFunc += "      .join('');" + "`n"
$newFunc += "    addTooltipToSegments('#csat-bar .csat-segment');" + "`n"
$newFunc += "  }" + "`n"

$jsc = $jsc.Remove($start, $end - $start).Insert($start, $newFunc)
[System.IO.File]::WriteAllText($jsf, $jsc, [System.Text.Encoding]::UTF8)
Write-Host "JS updated"

# CSS: Remove csat-label related classes
$lines = $cssc -split "`n"
$newLines = @()
$skip = $false
for ($i = 0; $i -lt $lines.Count; $i++) {
    $line = $lines[$i]
    if ($line -match "^\.csat-labels-above|^\.csat-label-row|^\.csat-label-above") {
        $skip = $true
    }
    if ($skip -and ($line -match "^\}" -or $i -eq $lines.Count - 1)) {
        $skip = $false
        continue
    }
    if ($skip) { continue }
    # Restore csat-bar height
    if ($line -match "height: auto;" -and ($i -gt 0 -and $lines[$i-1] -match "\.csat-bar")) {
        $line = "  height: 32px;"
    }
    $newLines += $line
}
$cssc = $newLines -join "`n"
[System.IO.File]::WriteAllText($cssf, $cssc, [System.Text.Encoding]::UTF8)
Write-Host "CSS updated"

Write-Host "=== DONE ==="
