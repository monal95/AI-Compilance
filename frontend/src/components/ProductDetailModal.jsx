export default function ProductDetailModal({ report, onClose }) {
  if (!report) {
    return null;
  }

  const fields = report.identified_fields || {};
  const violations = report.violations || [];

  const getRiskBadgeClass = (riskLevel) => {
    if (riskLevel === "Compliant") return "badge-success";
    if (riskLevel === "Moderate Risk") return "badge-warning";
    return "badge-danger";
  };

  const getRiskColor = (riskLevel) => {
    if (riskLevel === "Compliant") return "#10b981";
    if (riskLevel === "Moderate Risk") return "#f59e0b";
    return "#ef4444";
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content"
        style={{ maxWidth: "900px" }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="modal-header">
          <h2 style={{ margin: 0, color: "#1f2937" }}>Product Details</h2>
          <button className="modal-close" onClick={onClose}>
            ×
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body">
          {/* Product Image Section */}
          {report.scraped_data?.image_urls &&
            report.scraped_data.image_urls.length > 0 && (
              <div style={{ marginBottom: "24px" }}>
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
                    gap: "12px",
                  }}
                >
                  {report.scraped_data.image_urls.map((imageUrl, index) => (
                    <div
                      key={index}
                      style={{
                        borderRadius: "8px",
                        overflow: "hidden",
                        background: "#ffffff",
                        border: "1px solid #e5e7eb",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        minHeight: "150px",
                      }}
                    >
                      <img
                        src={imageUrl}
                        alt={`Product ${index + 1}`}
                        style={{
                          width: "100%",
                          height: "100%",
                          objectFit: "contain",
                          maxWidth: "100%",
                          background: "#ffffff",
                          padding: "8px",
                        }}
                        onError={(e) => {
                          e.target.style.display = "none";
                          e.target.parentElement.innerHTML =
                            '<div style="font-size: 12px; color: #6b7280; padding: 12px; text-align: center; background: #f9fafb;"><div>📷</div><div>Image unavailable</div></div>';
                        }}
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}

          {/* Product Title */}
          <h3
            style={{
              marginTop: 0,
              marginBottom: "8px",
              lineHeight: 1.3,
              color: "#1f2937",
            }}
          >
            {report.scraped_data?.title ||
              report.product_name ||
              "Unknown Product"}
          </h3>
          {report.scraped_data?.url && (
            <p
              style={{
                color: "#6b7280",
                margin: "0 0 20px 0",
                fontSize: "13px",
                wordBreak: "break-all",
              }}
            >
              {report.scraped_data.url}
            </p>
          )}

          {/* Score & Risk at Top */}
          <div
            className="result-container"
            style={{
              marginBottom: "24px",
              padding: "16px",
              background: "#f9fafb",
              borderRadius: "8px",
              border: "1px solid #e5e7eb",
            }}
          >
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(120px, 1fr))",
                gap: "24px",
              }}
            >
              <div>
                <div style={{ fontSize: "12px", color: "#6b7280" }}>
                  ✓ Compliance Score
                </div>
                <div
                  style={{
                    fontSize: "32px",
                    fontWeight: "700",
                    color: getRiskColor(report.risk_level),
                    marginTop: "4px",
                  }}
                >
                  {report.compliance_score ?? report.score}%
                </div>
              </div>
              <div>
                <div style={{ fontSize: "12px", color: "#6b7280" }}>
                  ⚠️ Risk Level
                </div>
                <div style={{ marginTop: "8px" }}>
                  <span
                    className={`badge ${getRiskBadgeClass(report.risk_level)}`}
                  >
                    {report.risk_level}
                  </span>
                </div>
              </div>
              <div>
                <div style={{ fontSize: "12px", color: "#6b7280" }}>
                  📦 Category
                </div>
                <div
                  style={{
                    fontSize: "14px",
                    fontWeight: "500",
                    marginTop: "8px",
                    color: "#1f2937",
                    textTransform: "capitalize",
                  }}
                >
                  {report.category || "Generic"}
                </div>
              </div>
              <div>
                <div style={{ fontSize: "12px", color: "#6b7280" }}>
                  Seller ID
                </div>
                <div
                  style={{
                    fontSize: "14px",
                    fontWeight: "500",
                    marginTop: "8px",
                    color: "#1f2937",
                  }}
                >
                  {report.seller_id || "N/A"}
                </div>
              </div>
              <div>
                <div style={{ fontSize: "12px", color: "#6b7280" }}>Date</div>
                <div
                  style={{
                    fontSize: "14px",
                    fontWeight: "500",
                    marginTop: "8px",
                    color: "#1f2937",
                  }}
                >
                  {new Date(report.created_at).toLocaleDateString()}
                </div>
              </div>
            </div>
          </div>

          {/* Mandatory Fields Grid */}
          <div style={{ marginBottom: "24px" }}>
            <h4 style={{ marginTop: "12px", color: "#1f2937" }}>
              Mandatory Declarations
            </h4>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
                gap: "12px",
              }}
            >
              <div className="result-container">
                <div className="result-row">
                  <span className="result-label">Manufacturer/Importer</span>
                  <span className="result-value">
                    {fields.manufacturer_or_importer || "⚠️ Not found"}
                  </span>
                </div>
              </div>
              <div className="result-container">
                <div className="result-row">
                  <span className="result-label">Net Quantity</span>
                  <span className="result-value">
                    {fields.net_quantity || "⚠️ Not found"}
                  </span>
                </div>
              </div>
              <div className="result-container">
                <div className="result-row">
                  <span className="result-label">MRP (Incl. Taxes)</span>
                  <span className="result-value">
                    {fields.mrp_inclusive_of_taxes || "⚠️ Not found"}
                  </span>
                </div>
              </div>
              <div className="result-container">
                <div className="result-row">
                  <span className="result-label">Consumer Care</span>
                  <span className="result-value">
                    {fields.consumer_care_information || "⚠️ Not found"}
                  </span>
                </div>
              </div>
              <div className="result-container">
                <div className="result-row">
                  <span className="result-label">Date of Mfg/Import</span>
                  <span className="result-value">
                    {fields.date_of_manufacture_or_import || "⚠️ Not found"}
                  </span>
                </div>
              </div>
              <div className="result-container">
                <div className="result-row">
                  <span className="result-label">Country of Origin</span>
                  <span className="result-value">
                    {fields.country_of_origin || "⚠️ Not found"}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Compliance Summary Section */}
          <div
            style={{
              marginBottom: "24px",
              padding: "16px",
              borderRadius: "8px",
              background:
                report.risk_level === "Compliant"
                  ? "rgba(16, 185, 129, 0.1)"
                  : report.risk_level === "Moderate Risk"
                    ? "rgba(245, 158, 11, 0.1)"
                    : "rgba(239, 68, 68, 0.1)",
              borderLeft: `4px solid ${report.risk_level === "Compliant" ? "#10b981" : report.risk_level === "Moderate Risk" ? "#f59e0b" : "#ef4444"}`,
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <div>
                <h4
                  style={{
                    margin: "0 0 8px 0",
                    fontSize: "16px",
                    color: "#1f2937",
                  }}
                >
                  {report.risk_level === "Compliant" &&
                    "✅ Audit Status: Compliant"}
                  {report.risk_level === "Moderate Risk" &&
                    "⚠️ Audit Status: Moderate Risk"}
                  {report.risk_level === "High Risk" &&
                    "❌ Audit Status: High Risk"}
                </h4>
                <div
                  style={{
                    fontSize: "13px",
                    color: "#6b7280",
                    lineHeight: "1.6",
                  }}
                >
                  {violations.length === 0 ? (
                    <p style={{ margin: "0" }}>
                      All mandatory declarations have been identified and
                      verified. This product meets the compliance requirements.
                    </p>
                  ) : (
                    <p style={{ margin: "0" }}>
                      {violations.length} compliance issue
                      {violations.length !== 1 ? "s" : ""} detected. Review the
                      violations below for details and required corrections.
                    </p>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Violations Grid (if any) */}
          {violations.length > 0 && (
            <div style={{ marginBottom: "24px" }}>
              <h4
                style={{
                  marginTop: "12px",
                  color: "#ef4444",
                  display: "flex",
                  alignItems: "center",
                  gap: "8px",
                }}
              >
                <span>
                  ⚠️ Audit Results: {violations.length} Violation
                  {violations.length !== 1 ? "s" : ""} Found
                </span>
              </h4>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(100%, 1fr))",
                  gap: "12px",
                }}
              >
                {violations.map((violation, index) => (
                  <div
                    key={index}
                    className="result-container result-danger"
                    style={{
                      padding: "16px",
                      borderLeft: "4px solid #ef4444",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "start",
                        marginBottom: "8px",
                      }}
                    >
                      <div>
                        <div
                          style={{
                            fontWeight: "700",
                            color: "#ef4444",
                            fontSize: "14px",
                          }}
                        >
                          {violation.code}
                        </div>
                        {violation.field && (
                          <div
                            style={{
                              fontSize: "12px",
                              color: "#6b7280",
                              marginTop: "2px",
                            }}
                          >
                            Field: <strong>{violation.field}</strong>
                          </div>
                        )}
                      </div>
                      {violation.penalty && (
                        <div
                          style={{
                            background: "#ef4444",
                            color: "white",
                            padding: "4px 12px",
                            borderRadius: "4px",
                            fontSize: "12px",
                            fontWeight: "600",
                          }}
                        >
                          -{violation.penalty} pts
                        </div>
                      )}
                    </div>
                    <div
                      style={{
                        fontSize: "13px",
                        color: "#374151",
                        lineHeight: "1.6",
                      }}
                    >
                      {violation.message}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Category-Specific Fields */}
          {report.category && report.category !== "generic" && (
            <div style={{ marginBottom: "24px" }}>
              <h4 style={{ marginTop: "12px", color: "#1f2937" }}>
                {report.category === "food" && "🍔"}
                {report.category === "electronics" && "🔌"}
                {report.category === "cosmetics" && "💅"}{" "}
                {report.category.charAt(0).toUpperCase() +
                  report.category.slice(1)}{" "}
                Specific Fields
              </h4>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))",
                  gap: "12px",
                }}
              >
                {report.category === "food" && (
                  <>
                    {fields.fssai_license && (
                      <div className="result-container">
                        <div className="result-row">
                          <span className="result-label">FSSAI License</span>
                          <span className="result-value">
                            {fields.fssai_license}
                          </span>
                        </div>
                      </div>
                    )}
                    {fields.expiry_date && (
                      <div className="result-container">
                        <div className="result-row">
                          <span className="result-label">Expiry Date</span>
                          <span className="result-value">
                            {fields.expiry_date}
                          </span>
                        </div>
                      </div>
                    )}
                    {fields.ingredients_list && (
                      <div className="result-container">
                        <div className="result-row">
                          <span className="result-label">Ingredients</span>
                          <span className="result-value">
                            {fields.ingredients_list}
                          </span>
                        </div>
                      </div>
                    )}
                    {fields.allergen_info && (
                      <div className="result-container">
                        <div className="result-row">
                          <span className="result-label">Allergen Info</span>
                          <span className="result-value">
                            {fields.allergen_info}
                          </span>
                        </div>
                      </div>
                    )}
                  </>
                )}
                {report.category === "electronics" && (
                  <>
                    {fields.bis_certification && (
                      <div className="result-container">
                        <div className="result-row">
                          <span className="result-label">
                            BIS Certification
                          </span>
                          <span className="result-value">
                            {fields.bis_certification}
                          </span>
                        </div>
                      </div>
                    )}
                    {fields.model_number && (
                      <div className="result-container">
                        <div className="result-row">
                          <span className="result-label">Model Number</span>
                          <span className="result-value">
                            {fields.model_number}
                          </span>
                        </div>
                      </div>
                    )}
                    {fields.warranty_period && (
                      <div className="result-container">
                        <div className="result-row">
                          <span className="result-label">Warranty Period</span>
                          <span className="result-value">
                            {fields.warranty_period}
                          </span>
                        </div>
                      </div>
                    )}
                    {fields.energy_rating && (
                      <div className="result-container">
                        <div className="result-row">
                          <span className="result-label">Energy Rating</span>
                          <span className="result-value">
                            {fields.energy_rating}
                          </span>
                        </div>
                      </div>
                    )}
                  </>
                )}
                {report.category === "cosmetics" && (
                  <>
                    {fields.usage_instructions && (
                      <div className="result-container">
                        <div className="result-row">
                          <span className="result-label">
                            Usage Instructions
                          </span>
                          <span className="result-value">
                            {fields.usage_instructions}
                          </span>
                        </div>
                      </div>
                    )}
                    {fields.warnings && (
                      <div className="result-container">
                        <div className="result-row">
                          <span className="result-label">Warnings</span>
                          <span className="result-value">
                            {fields.warnings}
                          </span>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          )}

          {/* OCR Text (if available) */}
          {report.ocr_text && (
            <div style={{ marginBottom: "0" }}>
              <h4 style={{ marginTop: "12px", color: "#1f2937" }}>
                📖 Extracted Text
              </h4>
              <div
                className="result-container"
                style={{
                  maxHeight: "300px",
                  overflow: "auto",
                  padding: "12px",
                  fontSize: "13px",
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-word",
                  color: "#6b7280",
                }}
              >
                {report.ocr_text.substring(0, 500)}
                {report.ocr_text.length > 500 ? "..." : ""}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
