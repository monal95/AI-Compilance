function getRiskColor(risk) {
  if (risk === "Compliant") return "badge-success";
  if (risk === "Moderate Risk") return "badge-warning";
  return "badge-danger";
}

function getScoreClass(score) {
  if (score >= 70) return "success";
  if (score >= 40) return "warning";
  return "danger";
}

export default function ComplianceResultCard({ result }) {
  if (!result) {
    return (
      <div className="card">
        <h3>Compliance Result</h3>
        <div className="empty-state">
          <div className="empty-state-icon">📋</div>
          <p>No scan completed yet.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <h3>Compliance Result</h3>

      {/* Score and Status */}
      <div className="mb-4">
        <div className="score-display">
          <span className={`badge ${getRiskColor(result.risk_level)}`}>
            {result.risk_level}
          </span>
          <span className="score-value">{result.score}/100</span>
        </div>
        <div className="score-bar">
          <div
            className={`score-fill ${getScoreClass(result.score)}`}
            style={{ width: `${result.score}%` }}
          />
        </div>
      </div>

      {/* Product Details */}
      <div className="result-container mb-3">
        <div className="result-row">
          <span className="result-label">Product</span>
          <span className="result-value">{result.product_name}</span>
        </div>
      </div>

      {/* LLM Analysis */}
      {result.llm_explanation && (
        <div className="result-container mb-3">
          <h4 className="mb-2">📝 Explanation</h4>
          <p className="text-secondary">{result.llm_explanation}</p>
        </div>
      )}

      {/* Suggested Correction */}
      {result.suggested_correction && (
        <div className="alert alert-info mb-3">
          <strong>Suggested Correction:</strong>
          <p className="mt-1 mb-0">{result.suggested_correction}</p>
        </div>
      )}

      {/* Risk Summary */}
      {result.risk_summary && (
        <div className="result-container mb-3">
          <h4 className="mb-2">⚠️ Risk Summary</h4>
          <p className="text-secondary">{result.risk_summary}</p>
        </div>
      )}

      {/* Violations */}
      <div className="result-container">
        <h4 className="mb-2">🚫 Violations</h4>
        {result.violations?.length === 0 ? (
          <div className="text-center text-success p-3">
            ✅ No violations found
          </div>
        ) : (
          <ul style={{ margin: 0, paddingLeft: "20px" }}>
            {result.violations?.map((violation) => (
              <li key={violation.code} className="text-danger mb-2">
                <strong>{violation.code}</strong> - {violation.message}
                {violation.penalty && (
                  <span
                    className="badge badge-danger ml-2"
                    style={{ marginLeft: "8px" }}
                  >
                    Penalty: {violation.penalty}
                  </span>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
