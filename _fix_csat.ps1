$f = Resolve-Path "zoho-survey/shared/js/dashboard.js"
$c = [System.IO.File]::ReadAllText($f, [System.Text.Encoding]::UTF8)

$old = @'
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
        const label = formatPctSimple(csat[l.key], total);
        const outside = p < 5;
        return `<div class="csat-segment${outside ? ' csat-segment-outside' : ''}" style="width:${p}%; background:${l.color};"
              data-label="${l.key}" data-value="${formatInteger(csat[l.key])} (${formatPctDecimal(csat[l.key], total)})">
                ${outside ? `<span class="csat-label">${label}</span>` : label}
              </div>`;
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

$new = @'
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

    // Separar segmentos pequeños (< 5%) para etiquetas sobre la barra
    let cumPct = 0;
    const smallSegments = [];
    const barSegments = visibleLabels.map((l) => {
      const p = pct(csat[l.key], total);
      const segStart = cumPct;
      cumPct += p;
      if (p > 0 && p < 5) {
        smallSegments.push({ key: l.key, p, label: formatPctSimple(csat[l.key], total), center: segStart + p / 2 });
      }
      return `<div class="csat-segment" style="width:${p}%; background:${l.color};"
            data-label="${l.key}" data-value="${formatInteger(csat[l.key])} (${formatPctDecimal(csat[l.key], total)})">
              ${p >= 5 ? formatPctSimple(csat[l.key], total) : ''}
            </div>`;
    });

    // Etiquetas pequeñas sobre la barra, centradas sobre su segmento
    // Cada etiqueta en su propia fila para evitar superposición
    const smallLabelsHtml = smallSegments.length
      ? `<div class="csat-labels-above">${smallSegments
          .map(
            (s) => `<div class="csat-label-row"><span class="csat-label-above" style="left:${s.center}%">${s.label}</span></div>`,
          )
          .join('')}</div>`
      : '';

    DOM.csatBar.innerHTML = (smallLabelsHtml || '')
      + `<div style="display:flex;height:32px;border-radius:4px;overflow:hidden;animation:stackedGrow 0.8s ease-out forwards">${barSegments.join('')}</div>`;
    DOM.csatLegend.innerHTML = visibleLabels
      .map(
        (l) =>
          `<div class="legend-item"><div class="legend-dot" style="background:${l.color};"></div>${l.key}: ${formatInteger(csat[l.key])}</div>`,
      )
      .join('');
    addTooltipToSegments('#csat-bar .csat-segment');
  }
'@

if ($c.Contains($old)) {
    $c = $c.Replace($old, $new)
    [System.IO.File]::WriteAllText($f, $c, [System.Text.Encoding]::UTF8)
    Write-Host "REPLACED - file written"
} else {
    Write-Host "OLD CODE NOT FOUND - checking for csat-segment-outside..."
    if ($c.Contains("csat-segment-outside")) {
        Write-Host "Found csat-segment-outside in file but exact match failed"
    }
}
