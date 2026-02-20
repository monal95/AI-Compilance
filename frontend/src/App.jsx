import { useState } from "react";
import SellerDashboard from "./pages/SellerDashboard";
import AdminDashboard from "./pages/AdminDashboard";
import BulkAuditDashboard from "./pages/BulkAuditDashboard";

export default function App() {
  const [currentPage, setCurrentPage] = useState("compliance");

  return (
    <div className="app-container">
      <nav className="navbar">
        <div className="nav-content">
          <div className="nav-brand">
            <div className="brand-icon">⚖️</div>
            <div className="brand-text">
              <h1>Legal Metrology</h1>
              <p>Compliance Cloud</p>
            </div>
          </div>

          <ul className="nav-menu">
            <li>
              <button
                className={`nav-link ${currentPage === "compliance" ? "active" : ""}`}
                onClick={() => setCurrentPage("compliance")}
              >
                📋 Compliance Audit
              </button>
            </li>
            <li>
              <button
                className={`nav-link ${currentPage === "bulk" ? "active" : ""}`}
                onClick={() => setCurrentPage("bulk")}
              >
                📦 Bulk Audit
              </button>
            </li>
            <li>
              <button
                className={`nav-link ${currentPage === "analytics" ? "active" : ""}`}
                onClick={() => setCurrentPage("analytics")}
              >
                📊 Analytics
              </button>
            </li>
          </ul>

          <div className="nav-user">
            <span className="user-badge">Admin</span>
          </div>
        </div>
      </nav>

      <div className="app-layout">
        <main className="main-content">
          <header className="page-header">
            <div className="header-content">
              <h1>AI-Powered Legal Metrology Compliance</h1>
              <p>
                Automated product compliance validation with intelligent OCR,
                NLP extraction, and rule-based verification
              </p>
            </div>
          </header>

          {currentPage === "compliance" ? (
            <SellerDashboard />
          ) : currentPage === "bulk" ? (
            <BulkAuditDashboard />
          ) : (
            <AdminDashboard />
          )}
        </main>
      </div>
    </div>
  );
}
