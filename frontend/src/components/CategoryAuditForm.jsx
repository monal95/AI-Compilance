import { useEffect, useState } from "react";
import {
  getCategories,
  startCategoryAudit,
  getCategoryAuditStatus,
} from "../api";

const MARKETPLACES = [
  { value: "amazon.in", label: "Amazon India" },
  { value: "flipkart.com", label: "Flipkart" },
];

export default function CategoryAuditForm({ onComplete }) {
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState("");
  const [customKeyword, setCustomKeyword] = useState("");
  const [maxProducts, setMaxProducts] = useState(10);
  const [marketplace, setMarketplace] = useState("amazon.in");
  const [loading, setLoading] = useState(false);
  const [taskId, setTaskId] = useState(null);
  const [progress, setProgress] = useState(null);

  useEffect(() => {
    loadCategories();
  }, []);

  useEffect(() => {
    let interval;
    if (taskId) {
      interval = setInterval(async () => {
        try {
          const status = await getCategoryAuditStatus(taskId);
          setProgress(status);

          if (status.status === "completed" || status.status === "failed") {
            clearInterval(interval);
            setLoading(false);
            if (status.status === "completed" && onComplete) {
              onComplete(status);
            }
          }
        } catch (error) {
          console.error("Error checking status:", error);
        }
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [taskId, onComplete]);

  async function loadCategories() {
    try {
      const data = await getCategories();
      setCategories(data.categories || []);
    } catch (error) {
      console.error("Failed to load categories:", error);
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();

    if (!selectedCategory) {
      alert("Please select a category");
      return;
    }

    if (selectedCategory === "Custom Search" && !customKeyword.trim()) {
      alert("Please enter a search keyword");
      return;
    }

    setLoading(true);
    setProgress(null);

    try {
      const response = await startCategoryAudit({
        category: selectedCategory,
        maxProducts,
        marketplace,
        customKeyword:
          selectedCategory === "Custom Search" ? customKeyword : undefined,
      });

      setTaskId(response.task_id);
      setProgress({ status: "started", total: 0, completed: 0 });
    } catch (error) {
      alert(error.response?.data?.detail || "Failed to start bulk audit");
      setLoading(false);
    }
  }

  const isCustom = selectedCategory === "Custom Search";
  const progressPercent =
    progress?.total > 0
      ? Math.round((progress.completed / progress.total) * 100)
      : 0;

  return (
    <div className="card">
      <div className="card-header">
        <h3>📦 Category-Based Bulk Audit</h3>
      </div>

      <form onSubmit={handleSubmit} style={{ padding: "20px" }}>
        <div className="form-group">
          <label>Product Category</label>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            disabled={loading}
          >
            <option value="">Select Category...</option>
            {categories.map((cat) => (
              <option key={cat.value} value={cat.value}>
                {cat.value}
              </option>
            ))}
          </select>
        </div>

        {isCustom && (
          <div className="form-group">
            <label>Search Keyword</label>
            <input
              type="text"
              value={customKeyword}
              onChange={(e) => setCustomKeyword(e.target.value)}
              placeholder="e.g., protein powder, vitamin tablets"
              disabled={loading}
            />
          </div>
        )}

        <div className="form-group">
          <label>Marketplace</label>
          <select
            value={marketplace}
            onChange={(e) => setMarketplace(e.target.value)}
            disabled={loading}
          >
            {MARKETPLACES.map((mp) => (
              <option key={mp.value} value={mp.value}>
                {mp.label}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>Max Products to Audit</label>
          <input
            type="number"
            value={maxProducts}
            onChange={(e) => setMaxProducts(parseInt(e.target.value) || 10)}
            min="1"
            max="50"
            disabled={loading}
          />
          <small
            style={{
              color: "var(--text-secondary)",
              marginTop: "4px",
              display: "block",
            }}
          >
            Maximum 50 products per audit
          </small>
        </div>

        <button
          type="submit"
          className="btn btn-primary"
          disabled={loading}
          style={{ width: "100%" }}
        >
          {loading ? (
            <>
              <span className="spinner" style={{ marginRight: "8px" }}></span>
              Auditing...
            </>
          ) : (
            "🔍 Start Bulk Audit"
          )}
        </button>
      </form>

      {/* Progress Display */}
      {progress && (
        <div style={{ padding: "0 20px 20px" }}>
          <div
            style={{
              background: "var(--bg-secondary)",
              borderRadius: "8px",
              padding: "16px",
            }}
          >
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                marginBottom: "8px",
              }}
            >
              <span style={{ fontWeight: "500" }}>
                {progress.status === "completed"
                  ? "✅ Completed"
                  : progress.status === "failed"
                    ? "❌ Failed"
                    : "⏳ Processing..."}
              </span>
              <span style={{ color: "var(--text-secondary)" }}>
                {progress.completed || 0} / {progress.total || "?"} products
              </span>
            </div>

            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{
                  width: `${progressPercent}%`,
                  backgroundColor:
                    progress.status === "failed"
                      ? "var(--danger)"
                      : "var(--primary)",
                }}
              ></div>
            </div>

            {progress.status === "completed" && (
              <div style={{ marginTop: "12px", fontSize: "14px" }}>
                <p style={{ color: "var(--success)" }}>
                  ✓ {progress.completed} products audited successfully
                </p>
                {progress.failed > 0 && (
                  <p style={{ color: "var(--warning)" }}>
                    ⚠ {progress.failed} products failed
                  </p>
                )}
              </div>
            )}

            {progress.errors?.length > 0 && (
              <div style={{ marginTop: "12px" }}>
                <details>
                  <summary
                    style={{ cursor: "pointer", color: "var(--danger)" }}
                  >
                    View Errors ({progress.errors.length})
                  </summary>
                  <ul
                    style={{
                      margin: "8px 0 0 20px",
                      fontSize: "13px",
                      color: "var(--text-secondary)",
                    }}
                  >
                    {progress.errors.slice(0, 5).map((err, idx) => (
                      <li key={idx}>{err}</li>
                    ))}
                  </ul>
                </details>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
