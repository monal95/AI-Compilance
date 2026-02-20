const CATEGORY_LABELS = {
  food: "🍎 Food & Beverages",
  electronics: "💻 Electronics",
  cosmetics: "💄 Cosmetics & Personal Care",
  generic: "📦 Generic Product",
};

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

function FieldRow({ label, value, found = true }) {
  return (
    <div className="result-row">
      <span className="result-label">{label}</span>
      <span className={`result-value ${!found || !value ? "not-found" : ""}`}>
        {value || "⚠️ Not found"}
      </span>
    </div>
  );
}

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

export default function UrlAuditResultCard({ result }) {
  if (!result) {
    return (
      <div className="card">
        <h2>Audit Results</h2>
        <div className="empty-state">
          <div className="empty-state-icon">📊</div>
          <h3>No Audit Results Yet</h3>
          <p>Submit a product URL to start the audit process</p>
        </div>
      </div>
    );
  }

  const fields = result.identified_fields;
  const extractedJson = JSON.stringify(
    {
      product_title: result.scraped_data.title,
      description: result.scraped_data.description,
      specifications_table: result.scraped_data.specifications,
      image_urls: result.scraped_data.image_urls,
    },
    null,
    2,
  );
  const fieldsJson = JSON.stringify(fields, null, 2);

  return (
    <div className="card">
      <h2>Audit Results</h2>

      {/* Score and Status */}
      <div className="mb-4">
        <div className="score-display">
          <span className={`badge ${getRiskColor(result.risk_level)}`}>
            {result.risk_level}
          </span>
          <span className="score-value">{result.compliance_score}%</span>
        </div>
        <div className="score-bar">
          <div
            className={`score-fill ${getScoreClass(result.compliance_score)}`}
            style={{ width: `${result.compliance_score}%` }}
          />
        </div>
      </div>

      {/* Product Info */}
      <div className="result-container mb-4">
        <h4 className="mb-3">📦 Product Information</h4>
        <FieldRow label="Product Title" value={result.scraped_data.title} />
        <FieldRow
          label="Product Category"
          value={
            CATEGORY_LABELS[result.category] || result.category || "Generic"
          }
        />
        <FieldRow
          label="Description"
          value={
            result.scraped_data.description
              ? `${result.scraped_data.description.substring(0, 150)}...`
              : null
          }
        />
        <FieldRow
          label="Images Extracted"
          value={`${result.scraped_data.image_urls?.length || 0} images`}
        />
        <FieldRow
          label="OCR Text Length"
          value={`${result.ocr_text?.length || 0} characters`}
        />
      </div>

      {/* Identified Fields - Universal */}
      <div className="result-container mb-4">
        <h4 className="mb-3">📋 Mandatory Fields (Universal)</h4>
        <FieldRow
          label="Manufacturer/Importer"
          value={fields.manufacturer_or_importer}
        />
        <FieldRow label="Net Quantity" value={fields.net_quantity} />
        <FieldRow
          label="MRP (Inc. Tax)"
          value={fields.mrp_inclusive_of_taxes}
        />
        <FieldRow
          label="Consumer Care"
          value={fields.consumer_care_information}
        />
        <FieldRow
          label="Date of Mfg/Import"
          value={fields.date_of_manufacture_or_import}
        />
        <FieldRow label="Country of Origin" value={fields.country_of_origin} />
      </div>

      {/* Category-Specific Fields */}
      {result.category === "food" && (
        <div className="result-container mb-4">
          <div
            className="flex"
            style={{
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "1rem",
            }}
          >
            <h4 style={{ margin: 0 }}>🍎 Food-Specific Fields</h4>
            <FoodTypeIndicator value={fields.veg_nonveg_symbol} />
          </div>
          <FieldRow label="FSSAI License" value={fields.fssai_license} />
          <FieldRow label="Expiry Date" value={fields.expiry_date} />
          <FieldRow label="Ingredients" value={fields.ingredients_list} />
          <FieldRow label="Nutritional Info" value={fields.nutritional_info} />
          <FieldRow label="Allergen Info" value={fields.allergen_info} />
          <FieldRow label="Batch/Lot No" value={fields.batch_lot_number} />
          <FieldRow
            label="Storage Instructions"
            value={fields.storage_instructions}
          />
        </div>
      )}

      {result.category === "electronics" && (
        <div className="result-container mb-4">
          <h4 className="mb-3">💻 Electronics-Specific Fields</h4>
          <FieldRow
            label="BIS Certification"
            value={fields.bis_certification}
          />
          <FieldRow label="Model Number" value={fields.model_number} />
          <FieldRow label="Warranty Period" value={fields.warranty_period} />
          <FieldRow label="Power Rating" value={fields.power_rating} />
          <FieldRow
            label="Voltage/Frequency"
            value={fields.voltage_frequency}
          />
          <FieldRow label="Energy Rating" value={fields.energy_rating} />
          <FieldRow label="Serial Number" value={fields.serial_number} />
          <FieldRow
            label="Safety Instructions"
            value={fields.safety_instructions}
          />
        </div>
      )}

      {result.category === "cosmetics" && (
        <div className="result-container mb-4">
          <h4 className="mb-3">💄 Cosmetics-Specific Fields</h4>
          <FieldRow label="Batch/Lot No" value={fields.batch_lot_number} />
          <FieldRow label="Expiry Date" value={fields.expiry_date} />
          <FieldRow label="Ingredients" value={fields.ingredients_list} />
          <FieldRow
            label="Usage Instructions"
            value={fields.usage_instructions}
          />
          <FieldRow label="Warnings" value={fields.warnings} />
          <FieldRow label="Cruelty Free" value={fields.cruelty_free} />
          <FieldRow label="Allergen Info" value={fields.allergen_info} />
        </div>
      )}

      {/* Violations */}
      <div className="result-container mb-4">
        <h4 className="mb-3">⚠️ Violations</h4>
        {result.violations.length === 0 ? (
          <div className="text-center text-success p-3">
            ✅ No violations found
          </div>
        ) : (
          <ul style={{ margin: 0, paddingLeft: "20px" }}>
            {result.violations.map((violation) => (
              <li key={violation.code} className="text-danger mb-2">
                <strong>{violation.code}</strong> - {violation.message}
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Technical Details */}
      <details className="mt-4">
        <summary
          className="font-semibold text-primary"
          style={{ cursor: "pointer" }}
        >
          🔧 Technical Details
        </summary>

        <div className="mt-3">
          <h5
            className="text-sm text-secondary mb-2"
            style={{ textTransform: "uppercase" }}
          >
            Scraped Data Output
          </h5>
          <pre className="code-block">{extractedJson}</pre>
        </div>

        <div className="mt-3">
          <h5
            className="text-sm text-secondary mb-2"
            style={{ textTransform: "uppercase" }}
          >
            OCR Extracted Text ({result.ocr_text?.length || 0} chars)
          </h5>
          <pre className="code-block">
            {result.ocr_text || "No OCR text extracted"}
          </pre>
        </div>

        <div className="mt-3">
          <h5
            className="text-sm text-secondary mb-2"
            style={{ textTransform: "uppercase" }}
          >
            NLP Identified Fields
          </h5>
          <pre className="code-block">{fieldsJson}</pre>
        </div>
      </details>
    </div>
  );
}
