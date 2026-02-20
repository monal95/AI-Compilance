import re

from backend.models import ExtractedFields


class NLPService:
    def extract_and_normalize(self, text: str) -> ExtractedFields:
        data = ExtractedFields()

        mrp_match = re.search(r"(?:MRP|M\.R\.P\.)\s*[:₹Rs\. ]*\s*(\d+[\.,]?\d*)", text, re.IGNORECASE)
        qty_match = re.search(r"(\d+(?:\.\d+)?)\s*(kg|g|gram|grams|ml|l|litre|litres)", text, re.IGNORECASE)
        manufacturer_match = re.search(r"Manufacturer\s*[:\-]\s*([A-Za-z0-9 ,.&-]+)", text, re.IGNORECASE)
        country_match = re.search(r"(?:Country of Origin|Made in)\s*[:\-]?\s*([A-Za-z ]+)", text, re.IGNORECASE)

        if mrp_match:
            data.mrp = f"INR {mrp_match.group(1).replace(',', '')}"

        if qty_match:
            value = float(qty_match.group(1))
            unit = qty_match.group(2).lower()
            if unit in {"kg"}:
                value *= 1000
                normalized_unit = "grams"
            elif unit in {"g", "gram", "grams"}:
                normalized_unit = "grams"
            elif unit in {"l", "litre", "litres"}:
                value *= 1000
                normalized_unit = "ml"
            else:
                normalized_unit = "ml"
            data.quantity = f"{int(value) if value.is_integer() else value} {normalized_unit}"

        if manufacturer_match:
            data.manufacturer = manufacturer_match.group(1).strip()

        if country_match:
            data.country_of_origin = country_match.group(1).strip().title()

        return data
