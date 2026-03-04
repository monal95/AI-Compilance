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
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({
    riskLevel: "All",
    dateRange: 30,
    customDateFrom: "",
    customDateTo: "",
  });

  const quickFilterOptions = [
    { label: "Last 7 Days", days: 7 },
    { label: "Last 30 Days", days: 30 },
    { label: "Last 3 Months", days: 90 },
    { label: "Last 6 Months", days: 180 },
  ];

  const riskLevels = ["All", "Compliant", "Moderate Risk", "High Risk"];

  useEffect(() => {
    loadAllData();
  }, [filters.dateRange]);

  async function loadAllData() {
    setLoading(true);
    try {
      const [risk, categories, violations, timeline] = await Promise.all([
        getRiskDistribution(),
        getCategoryStats(),
        getViolationTrends(),
        getComplianceTimeline(filters.dateRange),
      ]);

      // Filter risk data by selected risk level
      let filteredRisk = risk;
      if (filters.riskLevel !== "All") {
        filteredRisk = {
          [filters.riskLevel]: risk[filters.riskLevel] || 0,
        };
      }

      setRiskData(filteredRisk);
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

  const totalAudits =
    categoryData && categoryData.all ? categoryData.all.total || 0 : totalRisk;
  const compliantRate =
    categoryData && categoryData.all
      ? categoryData.all.compliance_rate || 0
      : totalAudits > 0
        ? Math.round(((riskData?.Compliant || 0) / totalRisk) * 100)
        : 0;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* Header with Filters */}
      <div className="card" style={{ padding: "20px" }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "16px",
            flexWrap: "wrap",
            gap: "12px",
          }}
        >
          <h2 style={{ margin: 0, fontSize: "20px" }}>
            📊 Analytics Dashboard
          </h2>
          <button
            className="btn btn-secondary"
            onClick={() => setShowFilters(!showFilters)}
            style={{
              background: showFilters
                ? "var(--primary-light)"
                : "var(--bg-secondary)",
              color: showFilters ? "white" : "var(--text)",
            }}
          >
            🔍 {showFilters ? "Hide" : "Show"} Filters
          </button>
        </div>

        {/* Filter Panel */}
        {showFilters && (
          <div
            style={{
              padding: "16px",
              background: "var(--bg-secondary)",
              borderRadius: "8px",
              borderTop: "2px solid var(--border)",
            }}
          >
            {/* Quick Filters */}
            <div style={{ marginBottom: "16px" }}>
              <label
                style={{
                  fontSize: "12px",
                  fontWeight: "600",
                  color: "var(--text-secondary)",
                  display: "block",
                  marginBottom: "8px",
                }}
              >
                ⏱️ Quick Date Filters
              </label>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(110px, 1fr))",
                  gap: "8px",
                }}
              >
                {quickFilterOptions.map((option) => (
                  <button
                    key={option.days}
                    className="btn btn-secondary"
                    onClick={() =>
                      setFilters({ ...filters, dateRange: option.days })
                    }
                    style={{
                      background:
                        filters.dateRange === option.days
                          ? "var(--primary)"
                          : "var(--card)",
                      color:
                        filters.dateRange === option.days
                          ? "white"
                          : "var(--text)",
                      border: `1px solid ${filters.dateRange === option.days ? "var(--primary)" : "var(--border)"}`,
                      cursor: "pointer",
                      fontSize: "13px",
                    }}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Risk Level Filter */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
                gap: "12px",
              }}
            >
              <div className="form-group">
                <label style={{ fontSize: "13px" }}>⚠️ Risk Level</label>
                <select
                  value={filters.riskLevel}
                  onChange={(e) =>
                    setFilters({ ...filters, riskLevel: e.target.value })
                  }
                  style={{
                    padding: "8px 12px",
                    borderRadius: "6px",
                    border: "1px solid var(--border)",
                    background: "var(--card)",
                    color: "var(--text)",
                  }}
                >
                  {riskLevels.map((level) => (
                    <option key={level} value={level}>
                      {level}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label style={{ fontSize: "13px" }}>📅 From Date</label>
                <input
                  type="date"
                  value={filters.customDateFrom}
                  onChange={(e) =>
                    setFilters({ ...filters, customDateFrom: e.target.value })
                  }
                  style={{
                    padding: "8px 12px",
                    borderRadius: "6px",
                    border: "1px solid var(--border)",
                    background: "var(--card)",
                  }}
                />
              </div>

              <div className="form-group">
                <label style={{ fontSize: "13px" }}>📅 To Date</label>
                <input
                  type="date"
                  value={filters.customDateTo}
                  onChange={(e) =>
                    setFilters({ ...filters, customDateTo: e.target.value })
                  }
                  style={{
                    padding: "8px 12px",
                    borderRadius: "6px",
                    border: "1px solid var(--border)",
                    background: "var(--card)",
                  }}
                />
              </div>
            </div>

            <div
              style={{
                marginTop: "12px",
                display: "flex",
                gap: "8px",
                flexWrap: "wrap",
              }}
            >
              <button
                className="btn btn-primary"
                onClick={loadAllData}
                style={{ padding: "8px 16px", fontSize: "13px" }}
              >
                Apply Filters
              </button>
              <button
                className="btn btn-secondary"
                onClick={() => {
                  setFilters({
                    riskLevel: "All",
                    dateRange: 30,
                    customDateFrom: "",
                    customDateTo: "",
                  });
                }}
                style={{ padding: "8px 16px", fontSize: "13px" }}
              >
                Reset
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Summary Metrics */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: "16px",
        }}
      >
        <div
          className="card"
          style={{
            textAlign: "center",
            padding: "20px",
            background: "linear-gradient(135deg, #e0f2fe 0%, #dbeafe 100%)",
          }}
        >
          <div
            style={{
              fontSize: "32px",
              fontWeight: "700",
              color: "var(--primary)",
            }}
          >
            {totalAudits}
          </div>
          <div
            style={{
              fontSize: "13px",
              color: "var(--text-secondary)",
              marginTop: "8px",
            }}
          >
            Total Audits
          </div>
        </div>

        <div
          className="card"
          style={{
            textAlign: "center",
            padding: "20px",
            background: "linear-gradient(135deg, #dcfce7 0%, #d1fae5 100%)",
          }}
        >
          <div
            style={{
              fontSize: "32px",
              fontWeight: "700",
              color: "var(--success)",
            }}
          >
            {riskData?.Compliant || 0}
          </div>
          <div
            style={{
              fontSize: "13px",
              color: "var(--text-secondary)",
              marginTop: "8px",
            }}
          >
            Compliant
          </div>
        </div>

        <div
          className="card"
          style={{
            textAlign: "center",
            padding: "20px",
            background: "linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)",
          }}
        >
          <div
            style={{
              fontSize: "32px",
              fontWeight: "700",
              color: "var(--warning)",
            }}
          >
            {riskData?.["Moderate Risk"] || 0}
          </div>
          <div
            style={{
              fontSize: "13px",
              color: "var(--text-secondary)",
              marginTop: "8px",
            }}
          >
            Moderate Risk
          </div>
        </div>

        <div
          className="card"
          style={{
            textAlign: "center",
            padding: "20px",
            background: "linear-gradient(135deg, #fee2e2 0%, #fecaca 100%)",
          }}
        >
          <div
            style={{
              fontSize: "32px",
              fontWeight: "700",
              color: "var(--danger)",
            }}
          >
            {riskData?.["High Risk"] || 0}
          </div>
          <div
            style={{
              fontSize: "13px",
              color: "var(--text-secondary)",
              marginTop: "8px",
            }}
          >
            High Risk
          </div>
        </div>

        <div
          className="card"
          style={{
            textAlign: "center",
            padding: "20px",
            background: "linear-gradient(135deg, #f3e8ff 0%, #e9d5ff 100%)",
          }}
        >
          <div
            style={{ fontSize: "32px", fontWeight: "700", color: "#7c3aed" }}
          >
            {compliantRate}%
          </div>
          <div
            style={{
              fontSize: "13px",
              color: "var(--text-secondary)",
              marginTop: "8px",
            }}
          >
            Compliance Rate
          </div>
        </div>
      </div>

      {/* Charts Row 1: Risk Distribution and Timeline */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
          gap: "16px",
        }}
      >
        {/* Risk Distribution */}
        <div className="card">
          <div className="card-header">
            <h3 style={{ margin: 0 }}>📊 Risk Distribution</h3>
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
                          <span style={{ fontWeight: "500", fontSize: "13px" }}>
                            {level}
                          </span>
                          <span
                            style={{
                              color: "var(--text-secondary)",
                              fontSize: "13px",
                            }}
                          >
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
              </div>
            ) : (
              <p
                style={{ textAlign: "center", color: "var(--text-secondary)" }}
              >
                No data available
              </p>
            )}
          </div>
        </div>

        {/* Compliance Timeline */}
        <div className="card">
          <div className="card-header">
            <h3 style={{ margin: 0 }}>
              📈 Timeline ({filters.dateRange} Days)
            </h3>
          </div>
          <div style={{ padding: "20px" }}>
            {timelineData.length > 0 ? (
              <div>
                {/* Simple bar chart visualization */}
                <div
                  style={{
                    display: "flex",
                    alignItems: "flex-end",
                    gap: "4px",
                    height: "140px",
                    borderBottom: "1px solid var(--border)",
                    paddingBottom: "8px",
                  }}
                >
                  {timelineData.map((day, idx) => {
                    const height = Math.max(
                      10,
                      (day.avg_compliance_score / 100) * 120,
                    );
                    return (
                      <div
                        key={idx}
                        style={{
                          flex: 1,
                          display: "flex",
                          flexDirection: "column",
                          alignItems: "center",
                          gap: "2px",
                          cursor: "pointer",
                        }}
                        title={`${day.date}: ${day.total_audited} audits, Avg: ${day.avg_compliance_score}%`}
                      >
                        <span
                          style={{
                            fontSize: "9px",
                            color: "var(--text-secondary)",
                          }}
                        >
                          {day.avg_compliance_score}%
                        </span>
                        <div
                          style={{
                            width: "100%",
                            maxWidth: "25px",
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
                <div
                  style={{
                    display: "flex",
                    gap: "4px",
                    marginTop: "8px",
                    justifyContent: "space-between",
                  }}
                >
                  <span
                    style={{ fontSize: "9px", color: "var(--text-secondary)" }}
                  >
                    {timelineData[0]?.date}
                  </span>
                  <span
                    style={{ fontSize: "9px", color: "var(--text-secondary)" }}
                  >
                    {timelineData[timelineData.length - 1]?.date}
                  </span>
                </div>
              </div>
            ) : (
              <p
                style={{ textAlign: "center", color: "var(--text-secondary)" }}
              >
                No timeline data available
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Charts Row 2: Categories and Violations */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))",
          gap: "16px",
        }}
      >
        {/* Category-wise Compliance */}
        <div className="card">
          <div className="card-header">
            <h3 style={{ margin: 0 }}>📦 Category Compliance</h3>
          </div>
          <div
            style={{ padding: "20px", maxHeight: "400px", overflowY: "auto" }}
          >
            {categoryData && Object.keys(categoryData).length > 0 ? (
              <div className="table-container">
                <table style={{ fontSize: "12px" }}>
                  <thead>
                    <tr>
                      <th>Category</th>
                      <th>Total</th>
                      <th>Rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(categoryData)
                      .filter(([cat]) => cat !== "all")
                      .map(([category, stats]) => (
                        <tr key={category}>
                          <td
                            style={{
                              fontWeight: "500",
                              textTransform: "capitalize",
                            }}
                          >
                            {category}
                          </td>
                          <td>{stats.total}</td>
                          <td>
                            <div
                              style={{
                                display: "flex",
                                alignItems: "center",
                                gap: "6px",
                              }}
                            >
                              <div
                                style={{
                                  width: "40px",
                                  height: "6px",
                                  background: "var(--bg-secondary)",
                                  borderRadius: "3px",
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
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p
                style={{ textAlign: "center", color: "var(--text-secondary)" }}
              >
                No category data available
              </p>
            )}
          </div>
        </div>

        {/* Top Violations */}
        <div className="card">
          <div className="card-header">
            <h3 style={{ margin: 0 }}>⚠️ Top Violations</h3>
          </div>
          <div
            style={{ padding: "20px", maxHeight: "400px", overflowY: "auto" }}
          >
            {violationData.length > 0 ? (
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "12px",
                }}
              >
                {violationData.slice(0, 8).map((item, idx) => {
                  const maxCount = violationData[0]?.count || 1;
                  const percent = Math.round((item.count / maxCount) * 100);
                  return (
                    <div key={idx}>
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          marginBottom: "4px",
                          fontSize: "12px",
                        }}
                      >
                        <span
                          style={{
                            flex: 1,
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap",
                          }}
                          title={item.violation}
                        >
                          {item.violation}
                        </span>
                        <span
                          style={{
                            marginLeft: "8px",
                            color: "var(--danger)",
                            fontWeight: "600",
                            flexShrink: 0,
                          }}
                        >
                          {item.count}
                        </span>
                      </div>
                      <div
                        style={{
                          height: "6px",
                          background: "var(--bg-secondary)",
                          borderRadius: "3px",
                          overflow: "hidden",
                        }}
                      >
                        <div
                          style={{
                            width: `${percent}%`,
                            height: "100%",
                            background: "var(--danger)",
                            borderRadius: "3px",
                          }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p
                style={{ textAlign: "center", color: "var(--text-secondary)" }}
              >
                No violations recorded yet
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
