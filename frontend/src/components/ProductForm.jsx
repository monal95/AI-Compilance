import { useState } from "react";

export default function ProductForm({ onSubmit, loading }) {
  const [form, setForm] = useState({
    seller_id: "seller-001",
    product_name: "",
    description: "",
    packaging_text: "",
  });
  const [image, setImage] = useState(null);

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((previous) => ({ ...previous, [name]: value }));
  }

  function handleSubmit(event) {
    event.preventDefault();
    const payload = new FormData();
    payload.append("seller_id", form.seller_id);
    payload.append("product_name", form.product_name);
    payload.append("description", form.description);
    payload.append("packaging_text", form.packaging_text);
    if (image) {
      payload.append("image", image);
    }
    onSubmit(payload);
  }

  return (
    <form className="card" onSubmit={handleSubmit}>
      <h3>Add Product</h3>
      <input
        name="seller_id"
        placeholder="Seller ID"
        value={form.seller_id}
        onChange={handleChange}
        required
      />
      <input
        name="product_name"
        placeholder="Product Name"
        value={form.product_name}
        onChange={handleChange}
        required
      />
      <textarea
        name="description"
        placeholder="Product description"
        value={form.description}
        onChange={handleChange}
      />
      <textarea
        name="packaging_text"
        placeholder="Packaging text (if available)"
        value={form.packaging_text}
        onChange={handleChange}
      />
      <input
        type="file"
        accept="image/*"
        onChange={(event) => setImage(event.target.files?.[0] || null)}
      />
      <button type="submit" disabled={loading}>
        {loading ? "Scanning..." : "Scan Compliance"}
      </button>
    </form>
  );
}
