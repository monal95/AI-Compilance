import { useState } from "react";
import CategoryAuditForm from "../components/CategoryAuditForm";

export default function BulkAuditDashboard() {
  const [bulkResults, setBulkResults] = useState(null);
  const [selectedResult, setSelectedResult] = useState(null);

  function handleBulkAuditComplete(results) {
    setBulkResults(results);
    setSelectedResult(null);
  }

  function getRiskColor(riskLevel) {
    switch (riskLevel) {
      case "Compliant":
        return "var(--success)";
      case "Moderate Risk":
        return "var(--warning)";
      default:
        return "var(--danger)";
    }
  }

  function getRiskBadgeClass(riskLevel) {
    switch (riskLevel) {
      case "Compliant":
        return "badge-success";
      case "Moderate Risk":
        return "badge-warning";
      default:
        return "badge-danger";
    }
  }

  function getScoreClass(score) {
    if (score >= 70) return "success";
    if (score >= 40) return "warning";
    return "danger";
  }

  // Calculate summary stats
  const summaryStats = bulkResults?.results
    ? {
        compliant: bulkResults.results.filter(
          (r) => r.risk_level === "Compliant",
        ).length,
        moderate: bulkResults.results.filter(
          (r) => r.risk_level === "Moderate Risk",
        ).length,
        high: bulkResults.results.filter((r) => r.risk_level === "High Risk")
          .length,
        avgScore:
          Math.round(
            bulkResults.results.reduce(
              (sum, r) => sum + r.compliance_score,
              0,
            ) / bulkResults.results.length,
          ) || 0,
      }
    : null;

  return (
    <section>
      {/* Header */}
      <div className="dashboard-header mb-4">
        <h2 className="text-primary">📦 Bulk Category Audit</h2>
        <p className="text-secondary mt-2">
          Audit multiple products from e-commerce platforms by category for
          Legal Metrology compliance
        </p>
      </div>

      {/* Main Grid */}
      <div className="grid-2">
        {/* Left: Audit Form */}
        <div>
          <CategoryAuditForm onComplete={handleBulkAuditComplete} />

          {/* Info Card */}
          <div
            className="card mt-4"
            style={{ background: "var(--bg-secondary)" }}
          >
            <h4 className="mb-3">💡 How it works</h4>
            <ol
              className="text-secondary"
              style={{ paddingLeft: "20px", lineHeight: "2" }}
            >
              <li>Select a product category or enter custom search</li>
              <li>Choose the e-commerce marketplace</li>
              <li>Set the number of products to audit</li>
              <li>System scrapes product pages automatically</li>
              <li>AI extracts compliance fields from each product</li>
              <li>Category-specific rules are validated</li>
            </ol>
          </div>
        </div>

        {/* Right: Results Panel */}
        <div>
          {!bulkResults ? (
            <div className="card">
              <div className="empty-state">
                <div className="empty-state-icon">📊</div>
                <h3>No Audit Results Yet</h3>
                <p>Start a bulk audit to see compliance results here</p>
              </div>
            </div>
          ) : (
            <>
              {/* Summary Stats */}
              <div className="card mb-4">
                <div className="card-header">
                  <h3>Audit Summary</h3>
                </div>
                <div className="metrics-grid">
                  <div className="metric-card">
                    <span className="metric-value">{bulkResults.total}</span>
                    <span className="metric-label">Total Products</span>
                  </div>
                  <div className="metric-card">
                    <span className="metric-value text-success">
                      {summaryStats?.compliant || 0}
                    </span>
                    <span className="metric-label">Compliant</span>
                  </div>
                  <div className="metric-card">
                    <span className="metric-value text-warning">
                      {summaryStats?.moderate || 0}
                    </span>
                    <span className="metric-label">Moderate Risk</span>
                  </div>
                  <div className="metric-card">
                    <span className="metric-value text-danger">
                      {summaryStats?.high || 0}
                    </span>
                    <span className="metric-label">High Risk</span>
                  </div>
                </div>

                {/* Average Score Bar */}
                <div className="mt-3">
                  <div className="flex justify-between mb-2">
                    <span className="font-medium">
                      Average Compliance Score
                    </span>
                    <span className="font-semibold">
                      {summaryStats?.avgScore}%
                    </span>
                  </div>
                  <div className="score-bar" style={{ height: "12px" }}>
                    <div
                      className={`score-fill ${getScoreClass(summaryStats?.avgScore || 0)}`}
                      style={{ width: `${summaryStats?.avgScore || 0}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Results List */}
              <div className="card">
                <div className="card-header">
                  <h3>Audit Results ({bulkResults.results?.length || 0})</h3>
                </div>
                <div style={{ maxHeight: "500px", overflow: "auto" }}>
                  {bulkResults.results?.map((result, idx) => (
                    <div
                      key={idx}
                      className={`list-item ${selectedResult === result ? "active" : ""}`}
                      onClick={() => setSelectedResult(result)}
                      style={{
                        background:
                          selectedResult === result
                            ? "var(--bg-secondary)"
                            : undefined,
                      }}
                    >
                      <div className="list-item-content">
                        <div className="list-item-title truncate">
                          {result.scraped_data?.title || "Unknown Product"}
                        </div>
                        <div className="list-item-subtitle">
                          Category: {result.category || "N/A"}
                        </div>
                      </div>
                      <div className="text-right">
                        <div
                          className="font-semibold"
                          style={{
                            fontSize: "18px",
                            color: getRiskColor(result.risk_level),
                          }}
                        >
                          {result.compliance_score}%
                        </div>
                        <span
                          className={`badge ${getRiskBadgeClass(result.risk_level)}`}
                        >
                          {result.risk_level}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Detail Modal */}
      {selectedResult && (
        <div className="modal-overlay" onClick={() => setSelectedResult(null)}>
          <div
            className="modal-content"
            style={{ maxWidth: "800px" }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-header">
              <h3>Product Details</h3>
              <button
                className="modal-close"
                onClick={() => setSelectedResult(null)}
              >
                ×
              </button>
            </div>

            <div className="modal-body">
              {/* Product Title */}
              <h4 className="mb-4 line-clamp-2">
                {selectedResult.scraped_data?.title || "Unknown Product"}
              </h4>

              {/* Score & Risk */}
              <div className="result-container mb-4">
                <div className="flex flex-wrap gap-5">
                  <div>
                    <div className="text-sm text-secondary mb-1">
                      Compliance Score
                    </div>
                    <div
                      className="font-bold"
                      style={{
                        fontSize: "32px",
                        color: getRiskColor(selectedResult.risk_level),
                      }}
                    >
                      {selectedResult.compliance_score}%
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-secondary mb-1">
                      Risk Level
                    </div>
                    <span
                      className={`badge ${getRiskBadgeClass(selectedResult.risk_level)}`}
                    >
                      {selectedResult.risk_level}
                    </span>
                  </div>
                  <div>
                    <div className="text-sm text-secondary mb-1">Category</div>
                    <div className="font-medium">
                      {selectedResult.category || "N/A"}
                    </div>
                  </div>
                </div>
              </div>

              {/* Identified Fields */}
              {selectedResult.identified_fields && (
                <div className="mb-4">
                  <h5 className="mb-3">✅ Identified Fields</h5>
                  <div
                    className="grid-auto"
                    style={{
                      gridTemplateColumns:
                        "repeat(auto-fit, minmax(200px, 1fr))",
                    }}
                  >
                    {Object.entries(selectedResult.identified_fields)
                      .filter(([, v]) => v)
                      .map(([key, value]) => (
                        <div
                          key={key}
                          className="result-container p-3"
                          style={{ background: "var(--bg-secondary)" }}
                        >
                          <div
                            className="text-sm text-secondary mb-1"
                            style={{ textTransform: "capitalize" }}
                          >
                            {key.replace(/_/g, " ")}
                          </div>
                          <div className="font-medium truncate">
                            {String(value).substring(0, 50)}
                            {String(value).length > 50 && "..."}
                          </div>
                        </div>
                      ))}
                  </div>
                </div>
              )}

              {/* Violations */}
              {selectedResult.violations?.length > 0 && (
                <div className="mb-4">
                  <h5 className="text-danger mb-3">
                    ⚠️ Violations ({selectedResult.violations.length})
                  </h5>
                  <div className="flex flex-col gap-2">
                    {selectedResult.violations.map((violation, idx) => (
                      <div key={idx} className="alert alert-danger">
                        <div className="flex justify-between items-center flex-wrap gap-2">
                          <div>
                            <span className="font-semibold text-danger">
                              {violation.code}
                            </span>
                            <span className="text-muted mx-2">•</span>
                            <span
                              className="text-secondary"
                              style={{ textTransform: "capitalize" }}
                            >
                              {violation.field?.replace(/_/g, " ")}
                            </span>
                          </div>
                          <span className="badge badge-danger">
                            -{violation.penalty} pts
                          </span>
                        </div>
                        <div className="mt-2">{violation.message}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Product URL */}
              {selectedResult.scraped_data?.url && (
                <a
                  href={selectedResult.scraped_data.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn btn-secondary btn-block mt-4"
                >
                  🔗 View Product on Marketplace
                </a>
              )}
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
