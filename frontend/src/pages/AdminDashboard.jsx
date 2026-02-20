import { useEffect, useMemo, useState } from "react";
import {
  getAuditExportCsvUrl,
  getAuditExportPdfUrl,
  getAuditReportById,
  getAuditReports,
  getAuditStats,
  searchAuditReports,
} from "../api";
import AdminMetrics from "../components/AdminMetrics";
import AuditReportDetail from "../components/AuditReportDetail";
import AnalyticsCharts from "../components/AnalyticsCharts";

const riskOptions = ["All", "Compliant", "Moderate Risk", "High Risk"];
const tabs = ["Reports", "Analytics"];

export default function AdminDashboard() {
  const [activeTab, setActiveTab] = useState("Reports");
  const [reports, setReports] = useState([]);
  const [risk, setRisk] = useState("All");
  const [stats, setStats] = useState(null);
  const [selectedReport, setSelectedReport] = useState(null);

  // Advanced filters
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({
    minScore: "",
    maxScore: "",
    dateFrom: "",
    dateTo: "",
    sellerId: "",
  });

  async function loadReports() {
    try {
      // Check if any advanced filters are active
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
  }

  useEffect(() => {
    loadReports();
    loadStats();
  }, [risk]);

  const sorted = useMemo(() => {
    return [...reports].sort((a, b) => (a.created_at < b.created_at ? 1 : -1));
  }, [reports]);

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
            <div className="card-header">
              <h2>Audit Reports</h2>
              <div className="toolbar-right">
                <button
                  className="btn btn-secondary"
                  onClick={() => setShowFilters(!showFilters)}
                >
                  🔍 {showFilters ? "Hide Filters" : "Filters"}
                </button>
                <select
                  value={risk}
                  onChange={(event) => setRisk(event.target.value)}
                >
                  {riskOptions.map((item) => (
                    <option key={item}>{item}</option>
                  ))}
                </select>
                <a
                  className="btn btn-secondary"
                  href={getAuditExportCsvUrl()}
                  target="_blank"
                  rel="noreferrer"
                >
                  📥 CSV
                </a>
                <a
                  className="btn btn-secondary"
                  href={getAuditExportPdfUrl()}
                  target="_blank"
                  rel="noreferrer"
                >
                  📄 PDF
                </a>
              </div>
            </div>

            {/* Advanced Filters Panel */}
            {showFilters && (
              <div
                className="p-4"
                style={{
                  background: "var(--bg-secondary)",
                  borderBottom: "1px solid var(--border)",
                }}
              >
                <div
                  className="grid-auto mb-3"
                  style={{
                    gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
                  }}
                >
                  <div className="form-group">
                    <label className="text-sm text-secondary">Min Score</label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={filters.minScore}
                      onChange={(e) =>
                        setFilters({ ...filters, minScore: e.target.value })
                      }
                      placeholder="0"
                    />
                  </div>
                  <div className="form-group">
                    <label className="text-sm text-secondary">Max Score</label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={filters.maxScore}
                      onChange={(e) =>
                        setFilters({ ...filters, maxScore: e.target.value })
                      }
                      placeholder="100"
                    />
                  </div>
                  <div className="form-group">
                    <label className="text-sm text-secondary">From Date</label>
                    <input
                      type="date"
                      value={filters.dateFrom}
                      onChange={(e) =>
                        setFilters({ ...filters, dateFrom: e.target.value })
                      }
                    />
                  </div>
                  <div className="form-group">
                    <label className="text-sm text-secondary">To Date</label>
                    <input
                      type="date"
                      value={filters.dateTo}
                      onChange={(e) =>
                        setFilters({ ...filters, dateTo: e.target.value })
                      }
                    />
                  </div>
                  <div className="form-group">
                    <label className="text-sm text-secondary">Seller ID</label>
                    <input
                      type="text"
                      value={filters.sellerId}
                      onChange={(e) =>
                        setFilters({ ...filters, sellerId: e.target.value })
                      }
                      placeholder="Filter by seller"
                    />
                  </div>
                </div>
                <div className="flex gap-2 flex-wrap">
                  <button className="btn btn-primary" onClick={loadReports}>
                    Apply Filters
                  </button>
                  <button className="btn btn-secondary" onClick={clearFilters}>
                    Clear
                  </button>
                </div>
              </div>
            )}

            {sorted.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-icon">📋</div>
                <p>No reports found</p>
              </div>
            ) : (
              <div className="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Product</th>
                      <th>Seller</th>
                      <th>Compliance Score</th>
                      <th>Status</th>
                      <th>Date</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sorted.map((item) => (
                      <tr key={item.product_id}>
                        <td style={{ fontWeight: "500" }}>
                          {item.scraped_data?.title ||
                            item.product_name ||
                            "N/A"}
                        </td>
                        <td>{item.seller_id}</td>
                        <td>
                          <strong>
                            {item.compliance_score ?? item.score}%
                          </strong>
                        </td>
                        <td>
                          <span
                            className={`badge ${getRiskBadgeClass(item.risk_level)}`}
                          >
                            {item.risk_level}
                          </span>
                        </td>
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
                            type="button"
                            onClick={() => viewReport(item.product_id)}
                          >
                            View
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Report Detail */}
          {selectedReport && <AuditReportDetail report={selectedReport} />}
        </>
      )}
    </section>
  );
}
