from io import StringIO

import pandas as pd

from backend.models import ProductInput


class IngestionService:
    def parse_single(self, payload: ProductInput, ocr_text: str | None) -> dict:
        merged_text = "\n".join(filter(None, [payload.description, payload.packaging_text, ocr_text]))
        return {
            "seller_id": payload.seller_id,
            "product_name": payload.product_name,
            "source_text": merged_text,
        }

    def parse_batch_csv(self, csv_bytes: bytes) -> list[ProductInput]:
        dataframe = pd.read_csv(StringIO(csv_bytes.decode("utf-8")))
        records: list[ProductInput] = []

        for _, row in dataframe.iterrows():
            records.append(
                ProductInput(
                    seller_id=str(row.get("seller_id", "unknown")),
                    product_name=str(row.get("product_name", "Unnamed Product")),
                    description=str(row.get("description", "")),
                    packaging_text=str(row.get("packaging_text", "")),
                )
            )

        return records
