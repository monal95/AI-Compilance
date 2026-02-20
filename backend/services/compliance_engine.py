import uuid

from backend.models import ComplianceResult, ProductInput, RiskLevel
from backend.services.ingestion_service import IngestionService
from backend.services.llm_service import LLMService
from backend.services.nlp_service import NLPService
from backend.services.ocr_service import OCRService
from backend.services.rag_service import RAGService
from backend.services.rule_engine import RuleEngine


class ComplianceEngine:
    def __init__(self) -> None:
        self.ingestion_service = IngestionService()
        self.ocr_service = OCRService()
        self.nlp_service = NLPService()
        self.rule_engine = RuleEngine()
        self.rag_service = RAGService()
        self.llm_service = LLMService()

    def classify_risk(self, score: int) -> RiskLevel:
        if score >= 85:
            return RiskLevel.COMPLIANT
        if score >= 60:
            return RiskLevel.MODERATE
        return RiskLevel.HIGH

    def run_scan(self, payload: ProductInput, image_bytes: bytes | None = None) -> ComplianceResult:
        ocr_text = self.ocr_service.extract_text(image_bytes) if image_bytes else ""
        normalized_input = self.ingestion_service.parse_single(payload, ocr_text)

        extracted = self.nlp_service.extract_and_normalize(normalized_input["source_text"])
        base_score, violations = self.rule_engine.evaluate(extracted)

        query = f"{payload.product_name} {normalized_input['source_text']}"
        clauses = self.rag_service.retrieve_clauses(query, top_k=3)

        llm_result = self.llm_service.explain_violations(
            product_data={
                "product_name": payload.product_name,
                "seller_id": payload.seller_id,
                "extracted_fields": extracted.model_dump(),
            },
            violations=[item.model_dump() for item in violations],
            clauses=clauses,
        )

        risk_level = self.classify_risk(base_score)

        return ComplianceResult(
            product_id=str(uuid.uuid4()),
            seller_id=payload.seller_id,
            product_name=payload.product_name,
            extracted_fields=extracted,
            violations=violations,
            legal_clauses=clauses,
            llm_explanation=llm_result["explanation"],
            suggested_correction=llm_result["suggested_correction"],
            risk_summary=llm_result["risk_summary"],
            score=base_score,
            risk_level=risk_level,
        )
