import json
import os
import re
from textwrap import dedent

from openai import OpenAI
from pydantic_settings import BaseSettings, SettingsConfigDict


PROMPT_TEMPLATE = dedent(
    """
    You are a legal metrology compliance assistant for Indian packaged commodities.

    Product Data:
    {product_data}

    Violations:
    {violations}

    Retrieved Clauses:
    {clauses}

    Return strict JSON with keys:
    explanation, suggested_correction, risk_summary
    """
)


class LLMSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=("backend/.env", ".env"), extra="ignore")

    groq_api_key: str | None = None
    groq_model: str = "llama-3.1-8b-instant"


class LLMService:
    def __init__(self) -> None:
        settings = LLMSettings()
        groq_api_key = settings.groq_api_key or os.getenv("GROQ_API_KEY")
        self.model = settings.groq_model or os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self.client = (
            OpenAI(api_key=groq_api_key, base_url="https://api.groq.com/openai/v1")
            if groq_api_key
            else None
        )

    def _parse_json_payload(self, text: str) -> dict | None:
        if not text:
            return None

        cleaned = text.strip()
        cleaned = re.sub(r"^```json\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"^```\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            return json.loads(cleaned)
        except Exception:
            pass

        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate = cleaned[start : end + 1]
            try:
                return json.loads(candidate)
            except Exception:
                return None
        return None

    def _format_section(self, value: object, fallback: str) -> str:
        if value is None:
            return fallback
        if isinstance(value, str):
            return value.strip() or fallback
        if isinstance(value, list):
            parts = [str(item).strip() for item in value if str(item).strip()]
            return "\n".join(parts) if parts else fallback
        if isinstance(value, dict):
            lines = []
            for key, item in value.items():
                if isinstance(item, (list, dict)):
                    lines.append(f"{key}: {json.dumps(item, ensure_ascii=False)}")
                else:
                    lines.append(f"{key}: {item}")
            return "\n".join(lines) if lines else fallback
        return str(value)

    def explain_violations(self, product_data: dict, violations: list[dict], clauses: list[str]) -> dict:
        if not violations:
            return {
                "explanation": "No legal metrology violations detected.",
                "suggested_correction": "No correction required.",
                "risk_summary": "Low risk. Product is compliant.",
            }

        if self.client is None:
            return {
                "explanation": "LLM explanation is disabled because GROQ_API_KEY is not configured.",
                "suggested_correction": "Set GROQ_API_KEY to enable AI-generated corrections; meanwhile, fix missing mandatory declarations.",
                "risk_summary": "Potential compliance risk exists due to reported rule violations.",
            }

        prompt = PROMPT_TEMPLATE.format(
            product_data=product_data,
            violations=violations,
            clauses=clauses,
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.2,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a legal metrology compliance assistant for Indian packaged commodities.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
            )
            text = response.choices[0].message.content if response.choices else ""

            parsed = self._parse_json_payload(text)
            if parsed:
                return {
                    "explanation": self._format_section(
                        parsed.get("explanation"),
                        "Compliance issues detected. Please review mandatory declarations.",
                    ),
                    "suggested_correction": self._format_section(
                        parsed.get("suggested_correction"),
                        "Review output and update missing/invalid fields.",
                    ),
                    "risk_summary": self._format_section(
                        parsed.get("risk_summary"),
                        "Moderate to high risk based on listed violations.",
                    ),
                }

            return {
                "explanation": (text or "No model explanation returned.").replace("```json", "").replace("```", "").strip(),
                "suggested_correction": "Review output and update missing/invalid fields.",
                "risk_summary": "Moderate to high risk based on listed violations.",
            }
        except Exception:
            return {
                "explanation": "Automated explanation unavailable. Please verify missing legal declarations.",
                "suggested_correction": "Add missing mandatory declarations per Packaged Commodities Rules.",
                "risk_summary": "Risk exists due to unresolved compliance issues.",
            }
