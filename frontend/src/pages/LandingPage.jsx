import { useState, useEffect } from "react";

export default function LandingPage({ onEnterApp }) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  const features = [
    {
      icon: "🔍",
      title: "AI-Powered OCR",
      description:
        "Advanced optical character recognition extracts product details from images with high accuracy",
      color: "#3b82f6",
    },
    {
      icon: "🧠",
      title: "NLP Processing",
      description:
        "Natural Language Processing identifies mandatory declarations and compliance fields",
      color: "#8b5cf6",
    },
    {
      icon: "⚖️",
      title: "Rule Engine",
      description:
        "Automated compliance checking against Legal Metrology (Packaged Commodities) Rules, 2011",
      color: "#10b981",
    },
    {
      icon: "📊",
      title: "Risk Assessment",
      description:
        "Severity-based scoring system categorizes violations from minor to critical",
      color: "#f59e0b",
    },
    {
      icon: "📦",
      title: "Bulk Auditing",
      description:
        "Process thousands of products simultaneously with parallel processing",
      color: "#ef4444",
    },
    {
      icon: "📈",
      title: "Analytics Dashboard",
      description:
        "Real-time insights, trends, and compliance metrics visualization",
      color: "#06b6d4",
    },
  ];

  const complianceSteps = [
    { step: 1, title: "Upload", desc: "Product image or URL" },
    { step: 2, title: "Extract", desc: "AI-powered data extraction" },
    { step: 3, title: "Validate", desc: "Rule-based compliance check" },
    { step: 4, title: "Report", desc: "Detailed risk assessment" },
  ];

  return (
    <div className={`landing-page ${isVisible ? "visible" : ""}`}>
      {/* Animated Background */}
      <div className="landing-bg">
        <div className="bg-gradient"></div>
        <div className="bg-pattern"></div>
        <div className="floating-shapes">
          {[...Array(6)].map((_, i) => (
            <div key={i} className={`shape shape-${i + 1}`}></div>
          ))}
        </div>
      </div>

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          <div className="hero-badge animate-fade-down">
            <span className="badge-icon">🇮🇳</span>
            <span>Compliant with Indian Legal Metrology Act, 2011</span>
          </div>

          <h1 className="hero-title animate-fade-up">
            <span className="gradient-text">AI-Powered</span>
            <br />
            Legal Metrology Compliance
          </h1>

          <p className="hero-subtitle animate-fade-up delay-1">
            Intelligent automation for packaged commodity compliance. Validate
            MRP, Net Quantity, Manufacturer details, and 20+ mandatory
            declarations in seconds.
          </p>

          <div className="hero-actions animate-fade-up delay-2">
            <button className="btn-primary-lg pulse" onClick={onEnterApp}>
              <span>Launch Dashboard</span>
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </div>

        <div className="hero-visual animate-scale-in">
          <div className="visual-card">
            <div className="visual-header">
              <div className="visual-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <span className="visual-title">Compliance Scanner</span>
            </div>
            <div className="visual-content">
              <div className="scan-animation">
                <div className="scan-product">
                  <div className="product-icon">📦</div>
                  <div className="product-info">
                    <span className="product-name">Sample Product</span>
                    <span className="product-category">Food - Packaged</span>
                  </div>
                </div>
                <div className="scan-line"></div>
                <div className="scan-results">
                  <div className="result-item valid">
                    <span className="check">✓</span>
                    <span>MRP Declaration</span>
                  </div>
                  <div className="result-item valid">
                    <span className="check">✓</span>
                    <span>Net Quantity</span>
                  </div>
                  <div className="result-item valid">
                    <span className="check">✓</span>
                    <span>Manufacturer Info</span>
                  </div>
                  <div className="result-item warning">
                    <span className="check">!</span>
                    <span>Date Format</span>
                  </div>
                </div>
                <div className="compliance-score">
                  <div className="score-ring">
                    <svg viewBox="0 0 100 100">
                      <circle
                        className="score-bg"
                        cx="50"
                        cy="50"
                        r="45"
                      ></circle>
                      <circle
                        className="score-progress"
                        cx="50"
                        cy="50"
                        r="45"
                      ></circle>
                    </svg>
                    <div className="score-value">87%</div>
                  </div>
                  <span className="score-label">Compliance Score</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Process Flow Section */}
      <section className="process-section">
        <div className="section-container">
          <h2 className="section-title animate-fade-up">
            How It <span className="gradient-text">Works</span>
          </h2>
          <p className="section-subtitle animate-fade-up delay-1">
            Simple 4-step process to validate product compliance
          </p>

          <div className="process-steps">
            {complianceSteps.map((item, index) => (
              <div
                key={item.step}
                className={`process-step animate-fade-up delay-${index + 1}`}
              >
                <div className="step-number">{item.step}</div>
                <div className="step-content">
                  <h3>{item.title}</h3>
                  <p>{item.desc}</p>
                </div>
                {index < complianceSteps.length - 1 && (
                  <div className="step-connector">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path d="M5 12h14M12 5l7 7-7 7" />
                    </svg>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="features-section">
        <div className="section-container">
          <h2 className="section-title animate-fade-up">
            Powerful <span className="gradient-text">Features</span>
          </h2>
          <p className="section-subtitle animate-fade-up delay-1">
            Everything you need for comprehensive compliance management
          </p>

          <div className="features-grid">
            {features.map((feature, index) => (
              <div
                key={index}
                className={`feature-card animate-fade-up delay-${(index % 3) + 1}`}
                style={{ "--accent-color": feature.color }}
              >
                <div className="feature-icon">{feature.icon}</div>
                <h3 className="feature-title">{feature.title}</h3>
                <p className="feature-desc">{feature.description}</p>
                <div className="feature-glow"></div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Compliance Categories */}
      <section className="categories-section">
        <div className="section-container">
          <h2 className="section-title animate-fade-up">
            Compliance <span className="gradient-text">Categories</span>
          </h2>

          <div className="categories-grid animate-fade-up delay-1">
            <div className="category-card category-a">
              <div className="category-header">
                <span className="category-badge">A</span>
                <span className="category-severity">Critical</span>
              </div>
              <h3>Prohibited Practices</h3>
              <p>Misleading declarations, price violations</p>
              <span className="penalty">-25 points</span>
            </div>

            <div className="category-card category-b">
              <div className="category-header">
                <span className="category-badge">B</span>
                <span className="category-severity">Serious</span>
              </div>
              <h3>Missing Declarations</h3>
              <p>MRP, Net Qty, Manufacturer details</p>
              <span className="penalty">-20 points</span>
            </div>

            <div className="category-card category-c">
              <div className="category-header">
                <span className="category-badge">C</span>
                <span className="category-severity">Moderate</span>
              </div>
              <h3>Format Errors</h3>
              <p>SI units, font size, MRP format</p>
              <span className="penalty">-10 points</span>
            </div>

            <div className="category-card category-d">
              <div className="category-header">
                <span className="category-badge">D</span>
                <span className="category-severity">Minor</span>
              </div>
              <h3>Technical Issues</h3>
              <p>Spacing, alignment, formatting</p>
              <span className="penalty">-5 points</span>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="cta-content animate-fade-up">
          <h2>Ready to Ensure Compliance?</h2>
          <p>
            Start auditing your products now with AI-powered Legal Metrology
            compliance validation
          </p>
          <button className="btn-primary-lg pulse" onClick={onEnterApp}>
            <span>Get Started Free</span>
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
            >
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="footer-content">
          <div className="footer-brand">
            <span className="footer-icon">⚖️</span>
            <div>
              <h3>Legal Metrology Compliance Cloud</h3>
              <p>AI-Powered Compliance Automation</p>
            </div>
          </div>
          <div className="footer-links">
            <a href="#">Documentation</a>
            <a href="#">API Reference</a>
            <a href="#">Support</a>
            <a href="#">Privacy Policy</a>
          </div>
          <p className="footer-copyright">
            © 2026 Legal Metrology Compliance Cloud. Based on Legal Metrology
            Act, 2011 & Rules.
          </p>
        </div>
      </footer>
    </div>
  );
}
