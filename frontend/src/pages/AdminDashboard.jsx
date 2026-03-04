import { useEffect, useMemo, useState } from "react";
import {
  getAuditExportCsvUrl,
  getAuditReportById,
  getAuditReports,
  getAuditStats,
  searchAuditReports,
} from "../api";
import AdminMetrics from "../components/AdminMetrics";
import AuditReportDetail from "../components/AuditReportDetail";
import AnalyticsCharts from "../components/AnalyticsCharts";
import ProductDetailModal from "../components/ProductDetailModal";

const riskOptions = ["All", "Compliant", "Moderate Risk", "High Risk"];
const tabs = ["Reports", "Analytics"];

export default function AdminDashboard() {
  const [activeTab, setActiveTab] = useState("Reports");
  const [reports, setReports] = useState([]);
  const [risk, setRisk] = useState("All");
  const [stats, setStats] = useState(null);
  const [selectedReport, setSelectedReport] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [showAdvancedFilters, setShowAdvancedFilters] = useState(false);
  const [filters, setFilters] = useState({
    minScore: "",
    maxScore: "",
    dateFrom: "",
    dateTo: "",
    sellerId: "",
  });

  async function loadReports() {
    try {
      const hasAdvancedFilters = Object.values(filters).some((v) => v !== "");

      if (hasAdvancedFilters) {
        const searchFilters = {
          risk_level: risk !== "All" ? risk : undefined,
          min_score: filters.minScore || undefined,
          max_score: filters.maxScore || undefined,
          date_from: filters.dateFrom || undefined,
          date_to: filters.dateTo || undefined,
          seller_id: filters.sellerId || undefined,
        };
        const data = await searchAuditReports(searchFilters);
        setReports(data.results || []);
      } else {
        const selectedRisk = risk === "All" ? undefined : risk;
        const data = await getAuditReports(selectedRisk);
        setReports(data);
      }
    } catch (error) {
      console.error("Failed to load reports:", error);
    }
  }

  async function loadStats() {
    const statsData = await getAuditStats();
    setStats(statsData);
  }

  async function viewReport(productId) {
    const report = await getAuditReportById(productId);
    setSelectedReport(report);
  }

  function clearFilters() {
    setFilters({
      minScore: "",
      maxScore: "",
      dateFrom: "",
      dateTo: "",
      sellerId: "",
    });
    setRisk("All");
    setSearchQuery("");
  }

  useEffect(() => {
    loadReports();
    loadStats();
  }, [risk]);

  const sorted = useMemo(() => {
    let filtered = [...reports];

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        (item) =>
          item.scraped_data?.title?.toLowerCase().includes(query) ||
          item.product_name?.toLowerCase().includes(query) ||
          item.seller_id?.toLowerCase().includes(query),
      );
    }

    return filtered.sort((a, b) => (a.created_at < b.created_at ? 1 : -1));
  }, [reports, searchQuery]);

  const getRiskBadgeClass = (riskLevel) => {
    if (riskLevel === "Compliant") return "badge-success";
    if (riskLevel === "Moderate Risk") return "badge-warning";
    return "badge-danger";
  };

  return (
    <section>
      {/* Metrics */}
      <AdminMetrics stats={stats} />

      {/* Tabs */}
      <div className="tabs">
        {tabs.map((tab) => (
          <button
            key={tab}
            className={`tab ${activeTab === tab ? "active" : ""}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab === "Reports" ? "📋" : "📊"} {tab}
          </button>
        ))}
      </div>

      {/* Analytics Tab */}
      {activeTab === "Analytics" && <AnalyticsCharts />}

      {/* Reports Tab */}
      {activeTab === "Reports" && (
        <>
          {/* Reports List */}
          <div className="card">
            <div style={{ padding: "20px" }}>
              <h2 style={{ margin: "0 0 20px 0" }}>📋 Audit Reports</h2>

              {/* Quick Filter Buttons + Search + Export */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "12px",
                  marginBottom: "20px",
                  flexWrap: "wrap",
                }}
              >
                {/* Quick Risk Filters */}
                <div style={{ display: "flex", gap: "8px" }}>
                  {["All", "Compliant", "Moderate Risk", "High Risk"].map(
                    (riskLevel) => (
                      <button
                        key={riskLevel}
                        className="btn btn-secondary"
                        onClick={() => setRisk(riskLevel)}
                        style={{
                          background:
                            risk === riskLevel
                              ? riskLevel === "Compliant"
                                ? "var(--success)"
                                : riskLevel === "Moderate Risk"
                                  ? "var(--warning)"
                                  : riskLevel === "High Risk"
                                    ? "var(--danger)"
                                    : "var(--primary)"
                              : "var(--bg-secondary)",
                          color:
                            risk === riskLevel
                              ? "white"
                              : "var(--text-secondary)",
                          border:
                            risk === riskLevel
                              ? "none"
                              : "1px solid var(--border)",
                          padding: "8px 14px",
                          fontSize: "13px",
                          fontWeight: "500",
                          cursor: "pointer",
                          transition: "all 0.2s ease",
                        }}
                      >
                        {riskLevel === "All" && "📊 All"}
                        {riskLevel === "Compliant" && "✅ Compliant"}
                        {riskLevel === "Moderate Risk" && "⚠️ Moderate"}
                        {riskLevel === "High Risk" && "❌ High Risk"}
                      </button>
                    ),
                  )}
                </div>

                {/* Advanced Filters Toggle */}
                <button
                  className="btn btn-secondary"
                  onClick={() => setShowAdvancedFilters(!showAdvancedFilters)}
                  style={{
                    padding: "8px 12px",
                    fontSize: "13px",
                  }}
                >
                  🔍 {showAdvancedFilters ? "Hide" : "Advanced"}
                </button>

                {/* Export Dropdown */}
                <div
                  style={{
                    position: "relative",
                  }}
                >
                  <button
                    className="btn btn-secondary"
                    style={{
                      padding: "8px 12px",
                      fontSize: "13px",
                      display: "flex",
                      alignItems: "center",
                      gap: "6px",
                    }}
                    onClick={(e) => {
                      const menu =
                        e.currentTarget.parentElement.querySelector(
                          ".export-menu",
                        );
                      if (menu) {
                        menu.style.display =
                          menu.style.display === "none" ? "block" : "none";
                      }
                    }}
                  >
                    📥 Export
                  </button>
                  <div
                    className="export-menu"
                    style={{
                      display: "none",
                      position: "absolute",
                      right: 0,
                      top: "100%",
                      background: "var(--card)",
                      border: "1px solid var(--border)",
                      borderRadius: "8px",
                      boxShadow: "var(--shadow-md)",
                      zIndex: 10,
                      minWidth: "200px",
                      marginTop: "4px",
                    }}
                  >
                    <a
                      href={getAuditExportCsvUrl()}
                      target="_blank"
                      rel="noreferrer"
                      style={{
                        display: "block",
                        padding: "12px 16px",
                        color: "var(--text)",
                        textDecoration: "none",
                        borderBottom: "1px solid var(--border)",
                        fontSize: "13px",
                        cursor: "pointer",
                        transition: "background 0.2s",
                      }}
                      onMouseEnter={(e) =>
                        (e.currentTarget.style.background =
                          "var(--bg-secondary)")
                      }
                      onMouseLeave={(e) =>
                        (e.currentTarget.style.background = "transparent")
                      }
                    >
                      <span>📊 CSV Report</span>
                      <div
                        style={{
                          fontSize: "11px",
                          color: "var(--text-secondary)",
                          marginTop: "4px",
                        }}
                      >
                        For spreadsheets & analysis
                      </div>
                    </a>
                    <a
                      href={getAuditExportCsvUrl()}
                      target="_blank"
                      rel="noreferrer"
                      style={{
                        display: "block",
                        padding: "12px 16px",
                        color: "var(--text)",
                        textDecoration: "none",
                        borderBottom: "1px solid var(--border)",
                        fontSize: "13px",
                        cursor: "pointer",
                        transition: "background 0.2s",
                      }}
                      onMouseEnter={(e) =>
                        (e.currentTarget.style.background =
                          "var(--bg-secondary)")
                      }
                      onMouseLeave={(e) =>
                        (e.currentTarget.style.background = "transparent")
                      }
                    >
                      <span>⚖️ Regulatory Report</span>
                      <div
                        style={{
                          fontSize: "11px",
                          color: "var(--text-secondary)",
                          marginTop: "4px",
                        }}
                      >
                        For authorities & compliance
                      </div>
                    </a>
                    <a
                      href={getAuditExportCsvUrl()}
                      target="_blank"
                      rel="noreferrer"
                      style={{
                        display: "block",
                        padding: "12px 16px",
                        color: "var(--text)",
                        textDecoration: "none",
                        fontSize: "13px",
                        cursor: "pointer",
                        transition: "background 0.2s",
                      }}
                      onMouseEnter={(e) =>
                        (e.currentTarget.style.background =
                          "var(--bg-secondary)")
                      }
                      onMouseLeave={(e) =>
                        (e.currentTarget.style.background = "transparent")
                      }
                    >
                      <span>🔐 Detailed Analysis</span>
                      <div
                        style={{
                          fontSize: "11px",
                          color: "var(--text-secondary)",
                          marginTop: "4px",
                        }}
                      >
                        Complete audit details
                      </div>
                    </a>
                  </div>
                </div>
              </div>

              {/* Search Field */}
              <div style={{ marginBottom: "20px" }}>
                <input
                  type="text"
                  placeholder="🔍 Search by product name, seller ID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "12px 16px",
                    border: "1px solid var(--border)",
                    borderRadius: "8px",
                    fontSize: "14px",
                    background: "var(--bg-secondary)",
                  }}
                />
              </div>

              {/* Advanced Filters Panel */}
              {showAdvancedFilters && (
                <div
                  style={{
                    padding: "16px",
                    background: "var(--bg-secondary)",
                    borderRadius: "8px",
                    marginBottom: "20px",
                    border: "1px solid var(--border)",
                  }}
                >
                  <div
                    style={{
                      display: "grid",
                      gridTemplateColumns:
                        "repeat(auto-fit, minmax(150px, 1fr))",
                      gap: "12px",
                      marginBottom: "12px",
                    }}
                  >
                    <div className="form-group">
                      <label style={{ fontSize: "12px" }}>Min Score</label>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        value={filters.minScore}
                        onChange={(e) =>
                          setFilters({ ...filters, minScore: e.target.value })
                        }
                        placeholder="0"
                        style={{ padding: "8px 12px", fontSize: "13px" }}
                      />
                    </div>
                    <div className="form-group">
                      <label style={{ fontSize: "12px" }}>Max Score</label>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        value={filters.maxScore}
                        onChange={(e) =>
                          setFilters({ ...filters, maxScore: e.target.value })
                        }
                        placeholder="100"
                        style={{ padding: "8px 12px", fontSize: "13px" }}
                      />
                    </div>
                    <div className="form-group">
                      <label style={{ fontSize: "12px" }}>From Date</label>
                      <input
                        type="date"
                        value={filters.dateFrom}
                        onChange={(e) =>
                          setFilters({ ...filters, dateFrom: e.target.value })
                        }
                        style={{ padding: "8px 12px", fontSize: "13px" }}
                      />
                    </div>
                    <div className="form-group">
                      <label style={{ fontSize: "12px" }}>To Date</label>
                      <input
                        type="date"
                        value={filters.dateTo}
                        onChange={(e) =>
                          setFilters({ ...filters, dateTo: e.target.value })
                        }
                        style={{ padding: "8px 12px", fontSize: "13px" }}
                      />
                    </div>
                    <div className="form-group">
                      <label style={{ fontSize: "12px" }}>Seller ID</label>
                      <input
                        type="text"
                        value={filters.sellerId}
                        onChange={(e) =>
                          setFilters({ ...filters, sellerId: e.target.value })
                        }
                        placeholder="Filter by seller"
                        style={{ padding: "8px 12px", fontSize: "13px" }}
                      />
                    </div>
                  </div>
                  <div
                    style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}
                  >
                    <button
                      className="btn btn-primary"
                      onClick={loadReports}
                      style={{
                        padding: "8px 14px",
                        fontSize: "13px",
                      }}
                    >
                      Apply
                    </button>
                    <button
                      className="btn btn-secondary"
                      onClick={clearFilters}
                      style={{
                        padding: "8px 14px",
                        fontSize: "13px",
                      }}
                    >
                      Reset
                    </button>
                  </div>
                </div>
              )}

              {/* Reports Table */}
              <div style={{ overflowX: "auto" }}>
                {sorted.length === 0 ? (
                  <div
                    style={{
                      textAlign: "center",
                      padding: "40px 20px",
                      color: "var(--text-secondary)",
                    }}
                  >
                    <div style={{ fontSize: "40px", marginBottom: "10px" }}>
                      📋
                    </div>
                    <p>
                      No reports found. Try adjusting your filters or search
                      query.
                    </p>
                  </div>
                ) : (
                  <table className="table table-striped">
                    <thead>
                      <tr>
                        <th>Product</th>
                        <th>Seller</th>
                        <th>Status</th>
                        <th>Score</th>
                        <th>Violations</th>
                        <th>Date</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {sorted.map((item) => (
                        <tr key={item._id || item.product_id}>
                          <td>
                            <strong>
                              {item.scraped_data?.title ||
                                item.product_title ||
                                item.product_name ||
                                "N/A"}
                            </strong>
                          </td>
                          <td>{item.seller_id}</td>
                          <td>
                            <span
                              style={{
                                display: "inline-block",
                                padding: "6px 12px",
                                borderRadius: "4px",
                                fontSize: "12px",
                                fontWeight: "500",
                                background:
                                  (item.compliance_score ?? item.score) >= 80
                                    ? "var(--success-light)"
                                    : (item.compliance_score ?? item.score) >=
                                        50
                                      ? "var(--warning-light)"
                                      : "var(--danger-light)",
                                color:
                                  (item.compliance_score ?? item.score) >= 80
                                    ? "var(--success)"
                                    : (item.compliance_score ?? item.score) >=
                                        50
                                      ? "var(--warning)"
                                      : "var(--danger)",
                              }}
                            >
                              {(item.compliance_score ?? item.score) >= 80
                                ? "✅ Compliant"
                                : (item.compliance_score ?? item.score) >= 50
                                  ? "⚠️ Moderate"
                                  : "❌ High Risk"}
                            </span>
                          </td>
                          <td>
                            <strong>
                              {(item.compliance_score ?? item.score).toFixed(2)}
                              %
                            </strong>
                          </td>
                          <td>{item.violations?.length || 0}</td>
                          <td
                            style={{
                              fontSize: "13px",
                              color: "var(--text-secondary)",
                            }}
                          >
                            {new Date(item.created_at).toLocaleDateString()}
                          </td>
                          <td>
                            <button
                              className="btn btn-primary"
                              onClick={() =>
                                viewReport(item._id || item.product_id)
                              }
                              style={{
                                padding: "6px 12px",
                                fontSize: "12px",
                              }}
                            >
                              👁️ View
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          </div>

          {/* Report Detail Modal */}
          {selectedReport && (
            <ProductDetailModal
              report={selectedReport}
              onClose={() => setSelectedReport(null)}
            />
          )}
        </>
      )}
    </section>
  );
}
