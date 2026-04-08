export default function GlassPanel({ title, subtitle, action, children, className = "" }) {
  return (
    <section className={`panel-shell ${className}`.trim()}>
      {(title || subtitle || action) && (
        <div className="panel-shell__header">
          <div>
            {title ? <h2 className="panel-shell__title">{title}</h2> : null}
            {subtitle ? <p className="panel-shell__subtitle">{subtitle}</p> : null}
          </div>
          {action}
        </div>
      )}
      <div>{children}</div>
    </section>
  );
}
