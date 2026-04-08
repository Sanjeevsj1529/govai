export default function MetricCard({ label, value, icon: Icon }) {
  return (
    <div className="metric-shell">
      <div>
        <p className="metric-shell__label">{label}</p>
        <p className="metric-shell__value">{value}</p>
      </div>
      {Icon ? (
        <div className="metric-shell__icon">
          <Icon className="h-4 w-4" />
        </div>
      ) : null}
    </div>
  );
}
