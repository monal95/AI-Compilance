export default function AdminMetrics({ stats }) {
  const total = stats?.total_audited || 0;
  const compliant = stats?.compliant_count || 0;
  const nonCompliant = stats?.non_compliant_count || 0;
  const complianceRate =
    total === 0 ? 0 : ((compliant / total) * 100).toFixed(2);

  return (
    <>
      {/* Key Metrics */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-label">📊 Total Audited</div>
          <div className="metric-value">{total}</div>
          <div className="metric-small">Products audited</div>
        </div>
        <div className="metric-card">
          <div className="metric-label">✅ Compliant</div>
          <div className="metric-value" style={{ color: "var(--success)" }}>
            {compliant}
          </div>
          <div className="metric-small">
            {total === 0 ? "0" : ((compliant / total) * 100).toFixed(1)}% of
            total
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-label">⚠️ Non-Compliant</div>
          <div className="metric-value" style={{ color: "var(--danger)" }}>
            {nonCompliant}
          </div>
          <div className="metric-small">
            {total === 0 ? "0" : ((nonCompliant / total) * 100).toFixed(1)}% of
            total
          </div>
        </div>
        <div className="metric-card">
          <div className="metric-label">📈 Compliance Rate</div>
          <div className="metric-value" style={{ color: "var(--primary)" }}>
            {complianceRate}%
          </div>
          <div className="metric-small">Overall score</div>
        </div>
      </div>

      {/* Most Common Violations */}
      {stats?.most_common_violations?.length ? (
        <div className="card">
          <h3>🚨 Most Common Violations</h3>
          <div
            style={{ display: "flex", flexDirection: "column", gap: "12px" }}
          >
            {stats.most_common_violations.map((item, index) => (
              <div
                key={item.violation}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "12px",
                  background: "var(--bg-secondary)",
                  borderRadius: "8px",
                }}
              >
                <div>
                  <div style={{ fontWeight: "600", color: "var(--text)" }}>
                    {index + 1}. {item.violation}
                  </div>
                  <div
                    style={{
                      fontSize: "12px",
                      color: "var(--text-secondary)",
                      marginTop: "4px",
                    }}
                  >
                    Occurrences
                  </div>
                </div>
                <div
                  style={{
                    background: "var(--danger)",
                    color: "white",
                    padding: "8px 12px",
                    borderRadius: "6px",
                    fontWeight: "700",
                  }}
                >
                  {item.count}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </>
  );
}
