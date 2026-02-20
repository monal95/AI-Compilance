import { useState } from "react";
import { auditProductUrl, ocrExtractImage } from "../api";
import UrlAuditForm from "../components/UrlAuditForm";
import UrlAuditResultCard from "../components/UrlAuditResultCard";
import ImageOCRForm from "../components/ImageOCRForm";
import OcrResultCard from "../components/OcrResultCard";

export default function SellerDashboard() {
  const [urlResult, setUrlResult] = useState(null);
  const [urlLoading, setUrlLoading] = useState(false);
  const [ocrResult, setOcrResult] = useState(null);
  const [ocrLoading, setOcrLoading] = useState(false);

  async function handleUrlScan(payload) {
    setUrlLoading(true);
    try {
      const response = await auditProductUrl(payload);
      setUrlResult(response.result);
    } catch (error) {
      alert(error.response?.data?.detail || "Scan failed");
    } finally {
      setUrlLoading(false);
    }
  }

  async function handleOcrExtract(payload) {
    setOcrLoading(true);
    try {
      const response = await ocrExtractImage(payload);
      setOcrResult(response.result || response);
    } catch (error) {
      alert(error.response?.data?.detail || "OCR extraction failed");
    } finally {
      setOcrLoading(false);
    }
  }

  return (
    <section>
      {/* Web Scraper Audit */}
      <div className="mb-5">
        <div className="section-header">
          <h2>🌐 Single URL Audit</h2>
        </div>
        <div className="grid-2">
          <UrlAuditForm onSubmit={handleUrlScan} loading={urlLoading} />
          <UrlAuditResultCard result={urlResult} />
        </div>
      </div>

      {/* OCR Image Extraction */}
      <div>
        <div className="section-header">
          <h2>🖼️ OCR Image Extraction</h2>
        </div>
        <div className="grid-2">
          <ImageOCRForm onSubmit={handleOcrExtract} loading={ocrLoading} />
          <OcrResultCard result={ocrResult} />
        </div>
      </div>
    </section>
  );
}
