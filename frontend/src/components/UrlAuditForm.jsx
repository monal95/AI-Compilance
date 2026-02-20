import { useState } from "react";

const PRODUCT_CATEGORIES = [
  {
    id: "",
    name: "Auto-detect Category",
    description: "System will detect category from product content",
  },
  {
    id: "food",
    name: "Food & Beverages",
    description: "FSSAI License, Nutritional Info, Expiry Date",
  },
  {
    id: "electronics",
    name: "Electronics",
    description: "BIS Certification, Warranty, Power Rating",
  },
  {
    id: "cosmetics",
    name: "Cosmetics & Personal Care",
    description: "Batch No, Ingredients, Usage Instructions",
  },
  {
    id: "generic",
    name: "Generic Product",
    description: "Basic Legal Metrology compliance",
  },
];

export default function UrlAuditForm({ onSubmit, loading }) {
  const [sellerId, setSellerId] = useState("seller-001");
  const [url, setUrl] = useState("");
  const [category, setCategory] = useState("");

  function handleSubmit(event) {
    event.preventDefault();
    onSubmit({ seller_id: sellerId, url, category: category || null });
  }

  return (
    <form className="card" onSubmit={handleSubmit}>
      <h2>Start Compliance Audit</h2>
      <p style={{ color: "var(--text-secondary)", marginBottom: "20px" }}>
        Enter product details for automated compliance verification
      </p>

      <div className="form-group">
        <label htmlFor="sellerId">Seller ID</label>
        <input
          id="sellerId"
          value={sellerId}
          onChange={(event) => setSellerId(event.target.value)}
          placeholder="e.g., seller-001"
          required
        />
      </div>

      <div className="form-group">
        <label htmlFor="url">Product URL</label>
        <input
          id="url"
          type="url"
          value={url}
          onChange={(event) => setUrl(event.target.value)}
          placeholder="https://example.com/product"
          required
        />
      </div>

      <div className="form-group">
        <label htmlFor="category">Product Category</label>
        <select
          id="category"
          value={category}
          onChange={(event) => setCategory(event.target.value)}
          className="category-select"
        >
          {PRODUCT_CATEGORIES.map((cat) => (
            <option key={cat.id} value={cat.id}>
              {cat.name}
            </option>
          ))}
        </select>
        {category && (
          <small className="category-hint">
            {PRODUCT_CATEGORIES.find((c) => c.id === category)?.description}
          </small>
        )}
      </div>

      <button type="submit" disabled={loading} className="btn-block">
        {loading ? (
          <>
            <span
              className="spinner"
              style={{ width: "16px", height: "16px" }}
            ></span>
            Processing...
          </>
        ) : (
          <>🔍 Run Audit</>
        )}
      </button>
    </form>
  );
}
