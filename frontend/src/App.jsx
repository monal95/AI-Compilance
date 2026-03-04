import { useState } from "react";
import SellerDashboard from "./pages/SellerDashboard";
import AdminDashboard from "./pages/AdminDashboard";
import BulkAuditDashboard from "./pages/BulkAuditDashboard";
import LandingPage from "./pages/LandingPage";

export default function App() {
  const [currentPage, setCurrentPage] = useState("landing");
  const [menuOpen, setMenuOpen] = useState(false);

  // Show landing page first
  if (currentPage === "landing") {
    return <LandingPage onEnterApp={() => setCurrentPage("compliance")} />;
  }

  return (
    <div className="app-container">
      <nav className="navbar">
        <div className="nav-content">
          <div
            className="nav-brand"
            onClick={() => setCurrentPage("landing")}
            style={{ cursor: "pointer" }}
          >
            <div className="brand-icon">⚖️</div>
            <div className="brand-text">
              <h1>Legal Metrology</h1>
              <p>Compliance Cloud</p>
            </div>
          </div>

          {/* Mobile Menu Toggle */}
          <button
            className={`menu-toggle ${menuOpen ? "active" : ""}`}
            onClick={() => setMenuOpen(!menuOpen)}
            aria-label="Toggle menu"
          >
            <span></span>
            <span></span>
            <span></span>
          </button>

          <ul className={`nav-menu ${menuOpen ? "open" : ""}`}>
            <li>
              <button
                className={`nav-link ${currentPage === "compliance" ? "active" : ""}`}
                onClick={() => {
                  setCurrentPage("compliance");
                  setMenuOpen(false);
                }}
              >
                <span className="nav-icon">📋</span>
                <span className="nav-text">Compliance Audit</span>
              </button>
            </li>
            <li>
              <button
                className={`nav-link ${currentPage === "bulk" ? "active" : ""}`}
                onClick={() => {
                  setCurrentPage("bulk");
                  setMenuOpen(false);
                }}
              >
                <span className="nav-icon">📦</span>
                <span className="nav-text">Bulk Audit</span>
              </button>
            </li>
            <li>
              <button
                className={`nav-link ${currentPage === "analytics" ? "active" : ""}`}
                onClick={() => {
                  setCurrentPage("analytics");
                  setMenuOpen(false);
                }}
              >
                <span className="nav-icon">📊</span>
                <span className="nav-text">Analytics</span>
              </button>
            </li>
          </ul>

          <div className="nav-user">
            <span className="user-badge">
              <span className="user-avatar">👤</span>
              <span className="user-name">Admin</span>
            </span>
          </div>
        </div>
      </nav>

      <div className="app-layout">
        <main className="main-content">
          <header className="page-header">
            <div className="header-content">
              <div className="header-breadcrumb">
                <span
                  onClick={() => setCurrentPage("landing")}
                  style={{ cursor: "pointer" }}
                >
                  Home
                </span>
                <span className="breadcrumb-separator">/</span>
                <span className="current">
                  {currentPage === "compliance"
                    ? "Compliance Audit"
                    : currentPage === "bulk"
                      ? "Bulk Audit"
                      : "Analytics"}
                </span>
              </div>
              <h1>
                {currentPage === "compliance"
                  ? "🔍 AI-Powered Compliance Audit"
                  : currentPage === "bulk"
                    ? "📦 Bulk Product Auditing"
                    : "📊 Analytics Dashboard"}
              </h1>
              <p>
                {currentPage === "compliance"
                  ? "Validate product compliance with intelligent OCR, NLP extraction, and rule-based verification"
                  : currentPage === "bulk"
                    ? "Process multiple products simultaneously with parallel category-based auditing"
                    : "Real-time insights, compliance trends, and risk assessment metrics"}
              </p>
            </div>
          </header>

          <div className="page-content animate-fade-in">
            {currentPage === "compliance" ? (
              <SellerDashboard />
            ) : currentPage === "bulk" ? (
              <BulkAuditDashboard />
            ) : (
              <AdminDashboard />
            )}
          </div>
        </main>
      </div>

      {/* Mobile Menu Overlay */}
      {menuOpen && (
        <div className="menu-overlay" onClick={() => setMenuOpen(false)}></div>
      )}
    </div>
  );
}
