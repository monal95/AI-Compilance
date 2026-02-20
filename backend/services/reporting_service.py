import csv
from io import BytesIO, StringIO

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from backend.database import db_client
from backend.models import ComplianceResult


class ReportingService:
    async def save_result(self, result: ComplianceResult) -> None:
        await db_client.save_report(result.model_dump(mode="json"))

    async def list_reports(self, risk_level: str | None = None) -> list[dict]:
        reports = await db_client.get_reports()
        if risk_level:
            reports = [item for item in reports if item.get("risk_level") == risk_level]
        return reports

    async def get_product(self, product_id: str) -> dict | None:
        return await db_client.get_product(product_id)

    async def export_csv(self) -> str:
        reports = await self.list_reports()
        buffer = StringIO()
        writer = csv.DictWriter(
            buffer,
            fieldnames=[
                "product_id",
                "seller_id",
                "product_name",
                "score",
                "risk_level",
                "created_at",
            ],
        )
        writer.writeheader()
        for report in reports:
            writer.writerow(
                {
                    "product_id": report.get("product_id"),
                    "seller_id": report.get("seller_id"),
                    "product_name": report.get("product_name"),
                    "score": report.get("score"),
                    "risk_level": report.get("risk_level"),
                    "created_at": report.get("created_at"),
                }
            )
        return buffer.getvalue()

    async def get_dashboard_stats(self) -> dict:
        reports = await self.list_reports()
        total_audited = len(reports)
        compliant_count = sum(1 for item in reports if item.get("risk_level") == "Compliant")
        non_compliant_count = total_audited - compliant_count

        violation_counter: dict[str, int] = {}
        for item in reports:
            for violation in item.get("violations", []):
                message = violation.get("message") or violation.get("code") or "Unknown Violation"
                violation_counter[message] = violation_counter.get(message, 0) + 1

        most_common_violations = [
            {"violation": key, "count": value}
            for key, value in sorted(violation_counter.items(), key=lambda pair: pair[1], reverse=True)[:5]
        ]

        return {
            "total_audited": total_audited,
            "compliant_count": compliant_count,
            "non_compliant_count": non_compliant_count,
            "most_common_violations": most_common_violations,
        }

    async def export_pdf(self) -> bytes:
        reports = await self.list_reports()
        buffer = BytesIO()
        pdf_canvas = canvas.Canvas(buffer, pagesize=letter)
        page_width, page_height = letter

        y = page_height - 40
        pdf_canvas.setFont("Helvetica-Bold", 12)
        pdf_canvas.drawString(40, y, "Legal Metrology Audit Report")
        y -= 25
        pdf_canvas.setFont("Helvetica", 9)

        if not reports:
            pdf_canvas.drawString(40, y, "No reports available.")
        else:
            for report in reports:
                lines = [
                    f"Product: {report.get('scraped_data', {}).get('title') or report.get('product_name', 'N/A')}",
                    f"Seller: {report.get('seller_id', 'N/A')}",
                    f"Score: {report.get('compliance_score', report.get('score', 'N/A'))}",
                    f"Risk: {report.get('risk_level', 'N/A')}",
                ]
                for line in lines:
                    if y < 60:
                        pdf_canvas.showPage()
                        y = page_height - 40
                        pdf_canvas.setFont("Helvetica", 9)
                    pdf_canvas.drawString(40, y, line)
                    y -= 14
                y -= 8

        pdf_canvas.save()
        return buffer.getvalue()
