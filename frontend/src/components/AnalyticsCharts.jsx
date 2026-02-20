import { useEffect, useState } from "react";
import {
  getRiskDistribution,
  getCategoryStats,
  getViolationTrends,
  getComplianceTimeline,
} from "../api";

export default function AnalyticsCharts() {
  const [riskData, setRiskData] = useState(null);
  const [categoryData, setCategoryData] = useState(null);
  const [violationData, setViolationData] = useState([]);
  const [timelineData, setTimelineData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAllData();
  }, []);

  async function loadAllData() {
    setLoading(true);
    try {
      const [risk, categories, violations, timeline] = await Promise.all([
        getRiskDistribution(),
        getCategoryStats(),
        getViolationTrends(),
        getComplianceTimeline(30),
      ]);
      setRiskData(risk);
      setCategoryData(categories);
      setViolationData(violations);
      setTimelineData(timeline);
    } catch (error) {
      console.error("Failed to load analytics:", error);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="card" style={{ padding: "40px", textAlign: "center" }}>
        <span className="spinner"></span>
        <p style={{ marginTop: "12px", color: "var(--text-secondary)" }}>
          Loading analytics...
        </p>
      </div>
    );
  }

  const totalRisk = riskData
    ? Object.values(riskData).reduce((a, b) => a + b, 0)
    : 0;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* Risk Distribution */}
      <div className="card">
        <div className="card-header">
          <h3>📊 Risk Distribution</h3>
        </div>
        <div style={{ padding: "20px" }}>
          {riskData && totalRisk > 0 ? (
            <div>
              {/* Visual Bar Chart */}
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "12px",
                }}
              >
                {Object.entries(riskData).map(([level, count]) => {
                  const percent = Math.round((count / totalRisk) * 100);
                  const color =
                    level === "Compliant"
                      ? "var(--success)"
                      : level === "Moderate Risk"
                        ? "var(--warning)"
                        : "var(--danger)";
                  return (
                    <div key={level}>
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          marginBottom: "4px",
                        }}
                      >
                        <span style={{ fontWeight: "500" }}>{level}</span>
                        <span style={{ color: "var(--text-secondary)" }}>
                          {count} ({percent}%)
                        </span>
                      </div>
                      <div
                        style={{
                          height: "24px",
                          background: "var(--bg-secondary)",
                          borderRadius: "4px",
                          overflow: "hidden",
                        }}
                      >
                        <div
                          style={{
                            width: `${percent}%`,
                            height: "100%",
                            background: color,
                            transition: "width 0.3s ease",
                          }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Pie Chart Visualization */}
              <div
                style={{
                  display: "flex",
                  justifyContent: "center",
                  marginTop: "24px",
                  gap: "8px",
                }}
              >
                {Object.entries(riskData).map(([level, count]) => {
                  const percent = Math.round((count / totalRisk) * 100);
                  const color =
                    level === "Compliant"
                      ? "#28a745"
                      : level === "Moderate Risk"
                        ? "#ffc107"
                        : "#dc3545";
                  return (
                    <div
                      key={level}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                        fontSize: "13px",
                      }}
                    >
                      <span
                        style={{
                          width: "12px",
                          height: "12px",
                          borderRadius: "2px",
                          background: color,
                        }}
                      />
                      <span>
                        {level}: {percent}%
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : (
            <p style={{ textAlign: "center", color: "var(--text-secondary)" }}>
              No data available
            </p>
          )}
        </div>
      </div>

      {/* Category-wise Compliance */}
      <div className="card">
        <div className="card-header">
          <h3>📦 Category-wise Compliance</h3>
        </div>
        <div style={{ padding: "20px" }}>
          {categoryData && Object.keys(categoryData).length > 0 ? (
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Category</th>
                    <th>Total</th>
                    <th>Compliant</th>
                    <th>High Risk</th>
                    <th>Compliance Rate</th>
                    <th>Avg Score</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(categoryData).map(([category, stats]) => (
                    <tr key={category}>
                      <td style={{ fontWeight: "500" }}>{category}</td>
                      <td>{stats.total}</td>
                      <td style={{ color: "var(--success)" }}>
                        {stats.compliant}
                      </td>
                      <td style={{ color: "var(--danger)" }}>
                        {stats.high_risk}
                      </td>
                      <td>
                        <div
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "8px",
                          }}
                        >
                          <div
                            style={{
                              width: "60px",
                              height: "8px",
                              background: "var(--bg-secondary)",
                              borderRadius: "4px",
                              overflow: "hidden",
                            }}
                          >
                            <div
                              style={{
                                width: `${stats.compliance_rate}%`,
                                height: "100%",
                                background:
                                  stats.compliance_rate >= 70
                                    ? "var(--success)"
                                    : stats.compliance_rate >= 40
                                      ? "var(--warning)"
                                      : "var(--danger)",
                              }}
                            />
                          </div>
                          <span>{stats.compliance_rate}%</span>
                        </div>
                      </td>
                      <td>{stats.avg_score}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p style={{ textAlign: "center", color: "var(--text-secondary)" }}>
              No category data available
            </p>
          )}
        </div>
      </div>

      {/* Top Violations */}
      <div className="card">
        <div className="card-header">
          <h3>⚠️ Most Common Violations</h3>
        </div>
        <div style={{ padding: "20px" }}>
          {violationData.length > 0 ? (
            <div
              style={{ display: "flex", flexDirection: "column", gap: "12px" }}
            >
              {violationData.map((item, idx) => {
                const maxCount = violationData[0]?.count || 1;
                const percent = Math.round((item.count / maxCount) * 100);
                return (
                  <div key={idx}>
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        marginBottom: "4px",
                        fontSize: "14px",
                      }}
                    >
                      <span
                        style={{
                          flex: 1,
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                        }}
                      >
                        {item.violation}
                      </span>
                      <span
                        style={{
                          marginLeft: "12px",
                          color: "var(--danger)",
                          fontWeight: "600",
                        }}
                      >
                        {item.count}
                      </span>
                    </div>
                    <div
                      style={{
                        height: "8px",
                        background: "var(--bg-secondary)",
                        borderRadius: "4px",
                        overflow: "hidden",
                      }}
                    >
                      <div
                        style={{
                          width: `${percent}%`,
                          height: "100%",
                          background: "var(--danger)",
                          opacity: 0.8,
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <p style={{ textAlign: "center", color: "var(--text-secondary)" }}>
              No violations recorded yet
            </p>
          )}
        </div>
      </div>

      {/* Compliance Timeline */}
      <div className="card">
        <div className="card-header">
          <h3>📈 Compliance Timeline (Last 30 Days)</h3>
        </div>
        <div style={{ padding: "20px" }}>
          {timelineData.length > 0 ? (
            <div>
              {/* Simple line chart visualization */}
              <div
                style={{
                  display: "flex",
                  alignItems: "flex-end",
                  gap: "4px",
                  height: "150px",
                  borderBottom: "1px solid var(--border)",
                  paddingBottom: "8px",
                }}
              >
                {timelineData.map((day, idx) => {
                  const height = Math.max(
                    10,
                    (day.avg_compliance_score / 100) * 130,
                  );
                  return (
                    <div
                      key={idx}
                      style={{
                        flex: 1,
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        gap: "4px",
                      }}
                      title={`${day.date}: ${day.total_audited} audits, Avg: ${day.avg_compliance_score}%`}
                    >
                      <span
                        style={{
                          fontSize: "10px",
                          color: "var(--text-secondary)",
                        }}
                      >
                        {day.avg_compliance_score}%
                      </span>
                      <div
                        style={{
                          width: "100%",
                          maxWidth: "30px",
                          height: `${height}px`,
                          background:
                            day.avg_compliance_score >= 70
                              ? "var(--success)"
                              : day.avg_compliance_score >= 40
                                ? "var(--warning)"
                                : "var(--danger)",
                          borderRadius: "4px 4px 0 0",
                          transition: "height 0.3s ease",
                        }}
                      />
                    </div>
                  );
                })}
              </div>

              {/* Date labels */}
              <div style={{ display: "flex", gap: "4px", marginTop: "8px" }}>
                {timelineData.map((day, idx) => (
                  <div
                    key={idx}
                    style={{
                      flex: 1,
                      textAlign: "center",
                      fontSize: "10px",
                      color: "var(--text-secondary)",
                    }}
                  >
                    {day.date.split("-").slice(1).join("/")}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p style={{ textAlign: "center", color: "var(--text-secondary)" }}>
              No timeline data available
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
