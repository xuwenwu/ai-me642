import type { ThermoSeries } from '@/lib/types';

const plotColumns = [
  { field: 'Temp', label: 'Temperature' },
  { field: 'TotEng', label: 'Total energy' },
  { field: 'Press', label: 'Pressure' },
  { field: 'Volume', label: 'Volume' },
];

function formatValue(value: number) {
  if (!Number.isFinite(value)) return 'n/a';
  if (Math.abs(value) >= 10000 || (Math.abs(value) > 0 && Math.abs(value) < 0.01)) return value.toExponential(2);
  return value.toPrecision(4);
}

function pathFor(points: Array<{ x: number; y: number }>) {
  return points.map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`).join(' ');
}

function ThermoPlot({ series, field, label }: { series: ThermoSeries; field: string; label: string }) {
  const rows = series.points.filter((point) => Number.isFinite(point[series.x_field]) && Number.isFinite(point[field]));
  if (rows.length < 2) return null;

  const width = 360;
  const height = 150;
  const padding = 28;
  const xValues = rows.map((point) => point[series.x_field]);
  const yValues = rows.map((point) => point[field]);
  const xMin = Math.min(...xValues);
  const xMax = Math.max(...xValues);
  const yMin = Math.min(...yValues);
  const yMax = Math.max(...yValues);
  const xSpan = xMax - xMin || 1;
  const ySpan = yMax - yMin || 1;
  const coords = rows.map((point) => ({
    x: padding + ((point[series.x_field] - xMin) / xSpan) * (width - padding * 2),
    y: height - padding - ((point[field] - yMin) / ySpan) * (height - padding * 2),
  }));

  return (
    <div className="plot-card">
      <div className="plot-heading">
        <strong>{label}</strong>
        <span>{series.source}</span>
      </div>
      <svg className="thermo-plot" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`${label} versus ${series.x_field}`}>
        <line x1={padding} y1={height - padding} x2={width - padding} y2={height - padding} />
        <line x1={padding} y1={padding} x2={padding} y2={height - padding} />
        <path d={pathFor(coords)} />
        <text x={padding} y={height - 8}>{formatValue(xMin)}</text>
        <text x={width - padding} y={height - 8} textAnchor="end">{formatValue(xMax)}</text>
        <text x={8} y={height - padding}>{formatValue(yMin)}</text>
        <text x={8} y={padding + 4}>{formatValue(yMax)}</text>
      </svg>
    </div>
  );
}

export function ThermoPlots({ series }: { series: ThermoSeries[] }) {
  const plots = series.flatMap((item) => plotColumns
    .filter((column) => item.columns.includes(column.field))
    .map((column) => ({ item, ...column })));

  if (!plots.length) return null;

  return (
    <div className="thermo-section">
      <h3>Thermo Plots</h3>
      <div className="plot-grid">
        {plots.map((plot) => (
          <ThermoPlot key={`${plot.item.source}-${plot.field}`} series={plot.item} field={plot.field} label={plot.label} />
        ))}
      </div>
    </div>
  );
}
