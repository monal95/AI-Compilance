const CATEGORY_LABELS = {
  food: "🍎 Food & Beverages",
  electronics: "💻 Electronics",
  cosmetics: "💄 Cosmetics & Personal Care",
  generic: "📦 Generic Product",
};

function FoodTypeIndicator({ value }) {
  if (!value) {
    return (
      <div className="food-type-indicator unknown">
        <div className="indicator-box">
          <div className="indicator-dot" />
        </div>
        <span>Not Specified</span>
      </div>
    );
  }

  const normalizedValue = value.toLowerCase().trim();
  const isVeg =
    normalizedValue.includes("veg") && !normalizedValue.includes("non");
  const isNonVeg = normalizedValue.includes("non");

  if (isNonVeg) {
    return (
      <div className="food-type-indicator non-veg">
        <div className="indicator-box">
          <div className="indicator-dot" />
        </div>
        <span>Non-Vegetarian</span>
      </div>
    );
  }

  if (isVeg) {
    return (
      <div className="food-type-indicator veg">
        <div className="indicator-box">
          <div className="indicator-dot" />
        </div>
        <span>Vegetarian</span>
      </div>
    );
  }

  return (
    <div className="food-type-indicator unknown">
      <div className="indicator-box">
        <div className="indicator-dot" />
      </div>
      <span>{value}</span>
    </div>
  );
}

export default function OcrResultCard({ result }) {
  if (!result) {
    return (
      <div className="card">
        <h2>Extraction Results</h2>
        <div className="empty-state">
          <div className="empty-state-icon">📸</div>
          <p>Upload an image to extract text</p>
        </div>
      </div>
    );
  }

  const getRiskBadgeClass = (riskLevel) => {
    if (riskLevel === "Compliant") return "badge-success";
    if (riskLevel === "Moderate Risk") return "badge-warning";
    return "badge-danger";
  };

  // Filter non-null fields for display
  const identifiedFields = result.identified_fields
    ? Object.entries(result.identified_fields).filter(([_, value]) => value)
    : [];

  const missingFields = result.identified_fields
    ? Object.entries(result.identified_fields).filter(([_, value]) => !value)
    : [];

  return (
    <div className="card">
      <h2>Extraction Results</h2>

      {result.error ? (
        <div className="alert alert-danger">
          <strong>Error:</strong> {result.error}
        </div>
      ) : (
        <>
          {/* Category & Compliance Score Header */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "20px",
              padding: "16px",
              background: "var(--bg-secondary)",
              borderRadius: "8px",
            }}
          >
            <div>
              <div
                style={{
                  fontSize: "12px",
                  color: "var(--text-secondary)",
                  marginBottom: "4px",
                }}
              >
                Detected Category
              </div>
              <div style={{ fontWeight: "600" }}>
                {CATEGORY_LABELS[result.category] || result.category}
              </div>
            </div>

            {result.compliance_score !== undefined && (
              <div style={{ textAlign: "right" }}>
                <div
                  style={{
                    fontSize: "12px",
                    color: "var(--text-secondary)",
                    marginBottom: "4px",
                  }}
                >
                  Compliance Score
                </div>
                <div
                  style={{ display: "flex", alignItems: "center", gap: "8px" }}
                >
                  <span
                    style={{
                      fontSize: "24px",
                      fontWeight: "700",
                      color:
                        result.compliance_score >= 85
                          ? "var(--success)"
                          : result.compliance_score >= 60
                            ? "var(--warning)"
                            : "var(--danger)",
                    }}
                  >
                    {result.compliance_score}%
                  </span>
                  {result.risk_level && (
                    <span
                      className={`badge ${getRiskBadgeClass(result.risk_level)}`}
                    >
                      {result.risk_level}
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Confidence Score */}
          {result.confidence_score !== undefined && (
            <div style={{ marginBottom: "20px" }}>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  marginBottom: "12px",
                }}
              >
                <span style={{ fontWeight: "600", color: "var(--text)" }}>
                  Text Confidence
                </span>
                <span
                  style={{
                    fontSize: "18px",
                    fontWeight: "700",
                    color: "var(--primary)",
                  }}
                >
                  {Math.round(result.confidence_score)}%
                </span>
              </div>
              <div
                style={{
                  background: "var(--bg-secondary)",
                  borderRadius: "8px",
                  height: "6px",
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    height: "100%",
                    background:
                      result.confidence_score >= 70
                        ? "var(--success)"
                        : result.confidence_score >= 40
                          ? "var(--warning)"
                          : "var(--danger)",
                    width: `${result.confidence_score}%`,
                  }}
                />
              </div>
            </div>
          )}

          {/* Violations */}
          {result.violations && result.violations.length > 0 && (
            <div className="result-container" style={{ marginBottom: "20px" }}>
              <h4
                style={{
                  marginTop: "0",
                  marginBottom: "12px",
                  color: "var(--danger)",
                }}
              >
                ⚠️ Compliance Violations ({result.violations.length})
              </h4>
              <div
                style={{ display: "flex", flexDirection: "column", gap: "8px" }}
              >
                {result.violations.map((violation, idx) => (
                  <div
                    key={idx}
                    style={{
                      background: "#fef2f2",
                      border: "1px solid #fecaca",
                      borderRadius: "6px",
                      padding: "12px",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "flex-start",
                      }}
                    >
                      <div>
                        <span
                          style={{
                            fontFamily: "monospace",
                            fontSize: "11px",
                            background: "#fee2e2",
                            padding: "2px 6px",
                            borderRadius: "3px",
                            marginRight: "8px",
                          }}
                        >
                          {violation.code}
                        </span>
                        <span style={{ fontWeight: "500" }}>
                          {violation.field.replace(/_/g, " ").toUpperCase()}
                        </span>
                      </div>
                      <span
                        style={{
                          color: "var(--danger)",
                          fontWeight: "600",
                          fontSize: "13px",
                        }}
                      >
                        -{violation.penalty} pts
                      </span>
                    </div>
                    <p
                      style={{
                        margin: "8px 0 0",
                        fontSize: "13px",
                        color: "#991b1b",
                      }}
                    >
                      {violation.message}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Identified Fields */}
          {identifiedFields.length > 0 && (
            <div className="result-container" style={{ marginBottom: "20px" }}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  marginBottom: "12px",
                }}
              >
                <h4
                  style={{
                    margin: 0,
                    color: "var(--success)",
                  }}
                >
                  ✅ Identified Fields ({identifiedFields.length})
                </h4>
                {result.category === "food" &&
                  result.identified_fields?.veg_nonveg_symbol !== undefined && (
                    <FoodTypeIndicator
                      value={result.identified_fields.veg_nonveg_symbol}
                    />
                  )}
              </div>
              {identifiedFields.map(([key, value]) => (
                <div key={key} className="result-row">
                  <span className="result-label">{key.replace(/_/g, " ")}</span>
                  {key === "veg_nonveg_symbol" ? (
                    <FoodTypeIndicator value={value} />
                  ) : (
                    <span className="result-value">{value}</span>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Missing Fields Summary */}
          {missingFields.length > 0 && (
            <details style={{ marginBottom: "20px" }}>
              <summary
                style={{
                  cursor: "pointer",
                  fontWeight: "500",
                  color: "var(--text-secondary)",
                  padding: "8px 0",
                }}
              >
                📋 Missing Fields ({missingFields.length})
              </summary>
              <div
                style={{
                  marginTop: "8px",
                  padding: "12px",
                  background: "var(--bg-secondary)",
                  borderRadius: "6px",
                }}
              >
                {missingFields.map(([key]) => (
                  <div
                    key={key}
                    style={{
                      display: "inline-block",
                      padding: "4px 8px",
                      margin: "2px",
                      background: "var(--bg-primary)",
                      borderRadius: "4px",
                      fontSize: "12px",
                      color: "var(--text-secondary)",
                    }}
                  >
                    {key.replace(/_/g, " ")}
                  </div>
                ))}
              </div>
            </details>
          )}

          {/* Extracted Text */}
          {result.extracted_text && (
            <details>
              <summary
                style={{
                  cursor: "pointer",
                  fontWeight: "500",
                  color: "var(--text-secondary)",
                  padding: "8px 0",
                }}
              >
                📝 Raw Extracted Text
              </summary>
              <div
                style={{
                  marginTop: "8px",
                  background: "var(--bg-secondary)",
                  padding: "12px",
                  borderRadius: "6px",
                  whiteSpace: "pre-wrap",
                  wordWrap: "break-word",
                  fontSize: "13px",
                  lineHeight: "1.6",
                  color: "var(--text-secondary)",
                  maxHeight: "200px",
                  overflow: "auto",
                }}
              >
                {result.extracted_text}
              </div>
            </details>
          )}
        </>
      )}
    </div>
  );
}
