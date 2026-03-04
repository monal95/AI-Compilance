// MongoDB Initialization Script
// Creates database, collections, and indexes

db = db.getSiblingDB("compliance_db");

// Create collections
db.createCollection("products");
db.createCollection("audits");
db.createCollection("rules");
db.createCollection("crawl_jobs");
db.createCollection("bulk_tasks");
db.createCollection("audit_products");

// Create indexes for products collection
db.products.createIndex({ url: 1 }, { unique: true, sparse: true });
db.products.createIndex({ name: "text", description: "text" });
db.products.createIndex({ category: 1 });
db.products.createIndex({ risk_level: 1 });
db.products.createIndex({ created_at: -1 });
db.products.createIndex({ compliance_score: 1 });

// Create indexes for audits collection
db.audits.createIndex({ product_id: 1 });
db.audits.createIndex({ status: 1 });
db.audits.createIndex({ risk_level: 1 });
db.audits.createIndex({ created_at: -1 });
db.audits.createIndex({ compliance_score: 1 });

// Create indexes for rules collection
db.rules.createIndex({ name: 1 }, { unique: true });
db.rules.createIndex({ category: 1 });
db.rules.createIndex({ status: 1 });
db.rules.createIndex({ severity: 1 });
db.rules.createIndex({ tags: 1 });

// Create indexes for crawl_jobs collection
db.crawl_jobs.createIndex({ url: 1 });
db.crawl_jobs.createIndex({ status: 1 });
db.crawl_jobs.createIndex({ created_at: -1 });
db.crawl_jobs.createIndex({ priority: -1, created_at: 1 });

// Create indexes for bulk_tasks collection
db.bulk_tasks.createIndex({ status: 1 });
db.bulk_tasks.createIndex({ created_at: -1 });

// Create indexes for audit_products collection
db.audit_products.createIndex({ audit_id: 1 });
db.audit_products.createIndex({ url: 1 });
db.audit_products.createIndex({ created_at: -1 });

// Insert default rules
db.rules.insertMany([
  {
    name: "FSSAI Number Required",
    description:
      "All food products must display a valid 14-digit FSSAI license number",
    rule_type: "required_field",
    category: "food_safety",
    severity: "critical",
    conditions: [{ field: "fssai", operator: "exists", value: true }],
    actions: [{ type: "error", message: "FSSAI license number is missing" }],
    tags: ["fssai", "mandatory", "food"],
    applicable_to: ["food", "beverages"],
    status: "active",
    version: 1,
    created_at: new Date(),
    updated_at: new Date(),
    created_by: "system",
  },
  {
    name: "FSSAI Format Validation",
    description: "FSSAI number must be exactly 14 digits with valid state code",
    rule_type: "format_validation",
    category: "food_safety",
    severity: "high",
    conditions: [
      { field: "fssai", operator: "regex", value: "^[0-3][0-9]\\d{12}$" },
    ],
    actions: [{ type: "error", message: "FSSAI number format is invalid" }],
    tags: ["fssai", "format", "food"],
    applicable_to: ["food", "beverages"],
    status: "active",
    version: 1,
    created_at: new Date(),
    updated_at: new Date(),
    created_by: "system",
  },
  {
    name: "MRP Required",
    description: "All products must display Maximum Retail Price",
    rule_type: "required_field",
    category: "pricing",
    severity: "critical",
    conditions: [{ field: "mrp", operator: "exists", value: true }],
    actions: [{ type: "error", message: "MRP is missing" }],
    tags: ["mrp", "mandatory", "pricing"],
    applicable_to: ["all"],
    status: "active",
    version: 1,
    created_at: new Date(),
    updated_at: new Date(),
    created_by: "system",
  },
  {
    name: "Expiry Date Required",
    description: "Food products must display expiry or best before date",
    rule_type: "required_field",
    category: "food_safety",
    severity: "critical",
    conditions: [{ field: "expiry_date", operator: "exists", value: true }],
    actions: [{ type: "error", message: "Expiry date is missing" }],
    tags: ["expiry", "mandatory", "food"],
    applicable_to: ["food", "beverages", "medicine"],
    status: "active",
    version: 1,
    created_at: new Date(),
    updated_at: new Date(),
    created_by: "system",
  },
  {
    name: "Net Weight Required",
    description: "Products must display net weight or quantity",
    rule_type: "required_field",
    category: "packaging",
    severity: "high",
    conditions: [{ field: "net_weight", operator: "exists", value: true }],
    actions: [{ type: "error", message: "Net weight/quantity is missing" }],
    tags: ["weight", "quantity", "packaging"],
    applicable_to: ["food", "beverages"],
    status: "active",
    version: 1,
    created_at: new Date(),
    updated_at: new Date(),
    created_by: "system",
  },
  {
    name: "Country of Origin Required",
    description: "Products must display country of origin",
    rule_type: "required_field",
    category: "labeling",
    severity: "medium",
    conditions: [
      { field: "country_of_origin", operator: "exists", value: true },
    ],
    actions: [{ type: "warning", message: "Country of origin is missing" }],
    tags: ["origin", "labeling"],
    applicable_to: ["all"],
    status: "active",
    version: 1,
    created_at: new Date(),
    updated_at: new Date(),
    created_by: "system",
  },
]);

print("Database initialized successfully!");
print(
  "Collections created: products, audits, rules, crawl_jobs, bulk_tasks, audit_products",
);
print("Default rules inserted: 6");
