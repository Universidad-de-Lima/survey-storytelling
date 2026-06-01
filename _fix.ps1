$jsf = Resolve-Path "zoho-survey/shared/js/dashboard.js"
$cssf = Resolve-Path "zoho-survey/shared/css/dashboard.css"
$jsc = [System.IO.File]::ReadAllText($jsf, [System.Text.Encoding]::UTF8)
$cssc = [System.IO.File]::ReadAllText($cssf, [System.Text.Encoding]::UTF8)

# JS: Find renderCSATBar and simplify
$start = $jsc.IndexOf("  function renderCSATBar(csat) {")
$end = $jsc.IndexOf("  // ==================== SECCI", $start)
$oldFunc = $jsc.Substring($start, $end - $start)

$newFunc = @'
  function renderCSATBar(csat) {
    const labels = [
      { key: 'Totalmente satisfecho', color: 'var(--gray-900)' },
      { key: 'Muy satisfecho', color: 'var(--gray-600)' },
      { key: 'Satisfecho', color: 'var(--gray-400)' },
      { key: 'Insatisfecho', color: 'var(--ulima-orange)' },
      { key: 'Totalmente insatisfecho', color: 'var(--ulima-red)' },
    ];
    const total = labels.reduce((s, l) => s + (csat[l.key] || 0), 0);
    const visibleLabels = labels.filter((l) => csat[l.key] > 0);
    DOM.csatBar.innerHTML = visibleLabels
      .map((l) => {
        const p = pct(csat[l.key], total);
        return `<div class="csat-segment" style="width:${p}%; background:${l.color};"
              data-label="${l.key}" data-value="${formatInteger(csat[l.key])} (${formatPctDecimal(csat[l.key], total)})">${formatPctSimple(csat[l.key], total)}</div>`;
      })
      .join('');
    DOM.csatLegend.innerHTML = visibleLabels
      .map(
        (l) =>
          `<div class="legend-item"><div class="legend-dot" style="background:${l.color};"></div>${l.key}: ${formatInteger(csat[l.key])}</div>`,
      )
      .join('');
    addTooltipToSegments('#csat-bar .csat-segment');
  }

'@

$jsc = $jsc.Remove($start, $end - $start).Insert($start, $newFunc)
[System.IO.File]::WriteAllText($jsf, $jsc, [System.Text.Encoding]::UTF8)
Write-Host "JS updated"

# CSS: Remove csat-labels-above, csat-label-row styles; restore csat-bar
$cssc = $cssc -replace '(?s)\.csat-bar \{[^}]*height: auto;[^}]*\}', '.csat-bar {
  height: 32px;
  display: flex;
  border-radius: 4px;
  overflow: hidden;
  font-size: 11px;
  animation: stackedGrow 0.8s ease-out forwards;
}'
$cssc = $cssc -replace '(?s)\.csat-labels-above \{.*?\n\}', ''
$cssc = $cssc -replace '(?s)\.csat-label-row \{.*?\n\}', ''
$cssc = $cssc -replace '(?s)\.csat-label-above \{.*?\n\}', ''
$cssc = $cssc -replace '(?s)\.csat-label-row:last-child .*?\n\}', ''

# Also remove the .csat-segment-outside .csat-label if present
$cssc = $cssc -replace '(?s)\.csat-segment-outside \.csat-label \{.*?\n\}', ''

[System.IO.File]::WriteAllText($cssf, $cssc, [System.Text.Encoding]::UTF8)
Write-Host "CSS updated"

# Clean up
Remove-Item "_fix.ps1"
