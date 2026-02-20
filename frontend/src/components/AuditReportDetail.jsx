function getRiskBadgeClass(risk) {
  if (risk === "Compliant") return "badge-success";
  if (risk === "Moderate Risk") return "badge-warning";
  return "badge-danger";
}

// Function to clean OCR text by removing JSON objects and keeping only readable text
function cleanOCRText(text) {
  if (!text) return "";

  // Remove JSON objects (content between { and })
  let cleaned = text.replace(/\{[\s\S]*?\}/g, "");

  // Remove extra whitespace and line breaks
  cleaned = cleaned.replace(/\n\n+/g, "\n").trim();

  // Remove lines that look like JSON keys
  cleaned = cleaned
    .split("\n")
    .filter(
      (line) => !line.trim().match(/^["']?[a-zA-Z_][a-zA-Z0-9_]*["']?\s*[:=]/),
    )
    .join("\n");

  return cleaned || "No readable text extracted";
}

export default function AuditReportDetail({ report }) {
  if (!report) {
    return null;
  }

  const fields = report.identified_fields || {};
  const violations = report.violations || [];
  const cleanedOCRText = cleanOCRText(report.ocr_text);

  return (
    <div className="card">
      <h2>📋 Detailed Audit Report</h2>

      {/* Header Info */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "2fr 1fr",
          gap: "20px",
          marginBottom: "20px",
          paddingBottom: "20px",
          borderBottom: "1px solid var(--border)",
        }}
      >
        <div>
          <h3 style={{ marginTop: "0" }}>
            {report.scraped_data?.title || "N/A"}
          </h3>
          <p style={{ color: "var(--text-secondary)", margin: "4px 0" }}>
            {report.scraped_data?.url || "N/A"}
          </p>
        </div>
        <div style={{ textAlign: "right" }}>
          <div
            style={{
              fontSize: "32px",
              fontWeight: "700",
              color: "var(--primary)",
            }}
          >
            {report.compliance_score ?? report.score}%
          </div>
          <span className={`badge ${getRiskBadgeClass(report.risk_level)}`}>
            {report.risk_level}
          </span>
        </div>
      </div>

      {/* Mandatory Fields */}
      <div style={{ marginBottom: "20px" }}>
        <h3>📦 Mandatory Declarations</h3>
        <div className="result-container">
          <div className="result-row">
            <span className="result-label">Manufacturer/Importer</span>
            <span className="result-value">
              {fields.manufacturer_or_importer || "⚠️ Not found"}
            </span>
          </div>
          <div className="result-row">
            <span className="result-label">Net Quantity</span>
            <span className="result-value">
              {fields.net_quantity || "⚠️ Not found"}
            </span>
          </div>
          <div className="result-row">
            <span className="result-label">MRP (Inclusive of taxes)</span>
            <span className="result-value">
              {fields.mrp_inclusive_of_taxes || "⚠️ Not found"}
            </span>
          </div>
          <div className="result-row">
            <span className="result-label">Consumer Care Information</span>
            <span className="result-value">
              {fields.consumer_care_information || "⚠️ Not found"}
            </span>
          </div>
          <div className="result-row">
            <span className="result-label">Date of Mfg/Import</span>
            <span className="result-value">
              {fields.date_of_manufacture_or_import || "⚠️ Not found"}
            </span>
          </div>
          <div className="result-row">
            <span className="result-label">Country of Origin</span>
            <span className="result-value">
              {fields.country_of_origin || "⚠️ Not found"}
            </span>
          </div>
        </div>
      </div>

      {/* Violations */}
      {violations.length > 0 && (
        <div style={{ marginBottom: "20px" }}>
          <h3>⚠️ Violations Found</h3>
          <div className="result-container result-danger">
            {violations.map((violation, index) => (
              <div
                key={index}
                style={{
                  marginBottom: "12px",
                  paddingBottom: "12px",
                  borderBottom:
                    violations.length - 1 !== index
                      ? "1px solid var(--border)"
                      : "none",
                }}
              >
                <div style={{ fontWeight: "600", color: "var(--danger)" }}>
                  {violation.code}
                </div>
                <div
                  style={{
                    fontSize: "13px",
                    color: "var(--text-secondary)",
                    marginTop: "4px",
                  }}
                >
                  {violation.message}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Specifications */}
      {Object.keys(report.scraped_data?.specifications || {}).length > 0 && (
        <div style={{ marginBottom: "20px" }}>
          <h3>📋 Product Specifications</h3>
          <div className="result-container">
            {Object.entries(report.scraped_data?.specifications || {})
              .slice(0, 10)
              .map(([key, value]) => (
                <div key={key} className="result-row">
                  <span className="result-label">{key}</span>
                  <span className="result-value">{value}</span>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Extracted Text (Cleaned OCR) */}
      {cleanedOCRText && (
        <div style={{ marginBottom: "20px" }}>
          <h3>📝 Extracted Product Text</h3>
          <div
            className="result-container"
            style={{
              background: "var(--bg-secondary)",
              padding: "16px",
              borderRadius: "8px",
              whiteSpace: "pre-wrap",
              wordWrap: "break-word",
              fontSize: "13px",
              lineHeight: "1.6",
              color: "var(--text-secondary)",
              maxHeight: "250px",
              overflow: "auto",
            }}
          >
            {cleanedOCRText}
          </div>
        </div>
      )}

      {/* Technical Details (Hidden by default) */}
      <details style={{ marginTop: "20px" }}>
        <summary
          style={{
            cursor: "pointer",
            fontWeight: "600",
            color: "var(--primary)",
            fontSize: "16px",
            marginBottom: "12px",
          }}
        >
          🔧 Raw Technical Data (For Developers)
        </summary>

        {report.ocr_text && (
          <div style={{ marginTop: "16px" }}>
            <h4
              style={{
                fontSize: "14px",
                color: "var(--text-secondary)",
                textTransform: "uppercase",
                marginBottom: "8px",
              }}
            >
              Raw OCR Output
            </h4>
            <pre
              className="code-block"
              style={{ maxHeight: "200px", overflow: "auto" }}
            >
              {report.ocr_text}
            </pre>
          </div>
        )}

        {report.scraped_data && (
          <div style={{ marginTop: "16px" }}>
            <h4
              style={{
                fontSize: "14px",
                color: "var(--text-secondary)",
                textTransform: "uppercase",
                marginBottom: "8px",
              }}
            >
              Scraped Data
            </h4>
            <pre
              className="code-block"
              style={{ maxHeight: "200px", overflow: "auto" }}
            >
              {JSON.stringify(
                {
                  title: report.scraped_data.title,
                  description: report.scraped_data.description,
                  image_urls: report.scraped_data.image_urls,
                  specifications: report.scraped_data.specifications,
                },
                null,
                2,
              )}
            </pre>
          </div>
        )}
      </details>
    </div>
  );
}
