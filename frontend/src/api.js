import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE,
});

export async function scanProduct(formData) {
  const response = await api.post("/scan-product", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

export async function batchScan(file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await api.post("/batch-scan", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

export async function getReports(riskLevel) {
  const response = await api.get("/reports", {
    params: riskLevel ? { risk_level: riskLevel } : {},
  });
  return response.data;
}

export function getExportCsvUrl() {
  return `${API_BASE}/reports/export`;
}

export async function auditProductUrl(payload) {
  const response = await api.post("/audit/url", {
    url: payload.url,
    seller_id: payload.seller_id,
    category: payload.category || null,
  });
  return response.data;
}

export async function getAuditReports(riskLevel) {
  const response = await api.get("/audit/reports", {
    params: riskLevel ? { risk_level: riskLevel } : {},
  });
  return response.data;
}

export async function getAuditReportById(productId) {
  const response = await api.get(`/audit/reports/${productId}`);
  return response.data;
}

export async function getAuditStats() {
  const response = await api.get("/audit/stats");
  return response.data;
}

export function getAuditExportCsvUrl() {
  return `${API_BASE}/audit/export/csv`;
}

export async function getAuditExportPdfUrl() {
  return `${API_BASE}/audit/export/pdf`;
}

export async function ocrExtractImage(payload) {
  const formData = new FormData();
  formData.append("seller_id", payload.seller_id);
  formData.append("image", payload.image);
  if (payload.category) {
    formData.append("category", payload.category);
  }

  const response = await api.post("/audit/ocr", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

// ============================================
// Category-Based Bulk Audit APIs
// ============================================

export async function getCategories() {
  const response = await api.get("/audit/categories");
  return response.data;
}

export async function startCategoryAudit(payload) {
  const formData = new FormData();
  formData.append("category", payload.category);
  formData.append("max_products", payload.maxProducts || 10);
  formData.append("marketplace", payload.marketplace || "amazon.in");
  formData.append("seller_id", payload.sellerId || "regulator-audit");
  if (payload.customKeyword) {
    formData.append("custom_keyword", payload.customKeyword);
  }

  const response = await api.post("/audit/category", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

export async function getCategoryAuditStatus(taskId) {
  const response = await api.get(`/audit/category/status/${taskId}`);
  return response.data;
}

export async function bulkAuditUrls(urls, sellerId = "regulator-audit") {
  const formData = new FormData();
  urls.forEach((url) => formData.append("urls", url));
  formData.append("seller_id", sellerId);

  const response = await api.post("/audit/bulk", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return response.data;
}

// ============================================
// Enhanced Analytics APIs
// ============================================

export async function getAnalyticsSummary() {
  const response = await api.get("/analytics/summary");
  return response.data;
}

export async function getRiskDistribution() {
  const response = await api.get("/analytics/risk-distribution");
  return response.data;
}

export async function getCategoryStats() {
  const response = await api.get("/analytics/category-stats");
  return response.data;
}

export async function getViolationTrends() {
  const response = await api.get("/analytics/violation-trends");
  return response.data;
}

export async function getComplianceTimeline(days = 30) {
  const response = await api.get("/analytics/timeline", {
    params: { days },
  });
  return response.data;
}

// ============================================
// Advanced Search & Filtering
// ============================================

export async function searchAuditReports(filters = {}) {
  const response = await api.get("/audit/reports/search", {
    params: filters,
  });
  return response.data;
}
