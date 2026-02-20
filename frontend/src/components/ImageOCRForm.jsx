import { useState } from "react";
import { ocrExtractImage } from "../api";

const PRODUCT_CATEGORIES = [
  {
    id: "",
    name: "Auto-detect Category",
    description: "System will detect category from image content",
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

export default function ImageOCRForm({ onSubmit, loading }) {
  const [sellerId, setSellerId] = useState("seller-001");
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [category, setCategory] = useState("");

  function handleImageChange(event) {
    const file = event.target.files?.[0];
    if (file) {
      setImage(file);
      const reader = new FileReader();
      reader.onload = (e) => {
        setPreview(e.target?.result);
      };
      reader.readAsDataURL(file);
    }
  }

  function handleSubmit(event) {
    event.preventDefault();
    if (!image) {
      alert("Please select an image");
      return;
    }
    onSubmit({ seller_id: sellerId, image, category: category || null });
  }

  return (
    <form className="card" onSubmit={handleSubmit}>
      <h2>OCR Image Extraction</h2>
      <p style={{ color: "var(--text-secondary)", marginBottom: "20px" }}>
        Upload product images for direct OCR text extraction with category-based
        validation
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

      <div className="form-group">
        <label htmlFor="image">Product Image</label>
        <input
          id="image"
          type="file"
          accept="image/*"
          onChange={handleImageChange}
          required
        />
      </div>

      {preview && (
        <div style={{ marginBottom: "16px" }}>
          <img
            src={preview}
            alt="Preview"
            style={{
              maxWidth: "100%",
              maxHeight: "250px",
              borderRadius: "8px",
              border: "1px solid var(--border)",
            }}
          />
        </div>
      )}

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
          <>🖼️ Extract & Validate</>
        )}
      </button>
    </form>
  );
}
