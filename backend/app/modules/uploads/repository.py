import json

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import Holding, Portfolio, UploadJob, UploadRow


class UploadRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_job(self, *, portfolio: Portfolio, filename: str, rows: list[dict]) -> UploadJob:
        upload_job = UploadJob(
            portfolio_id=portfolio.id,
            filename=filename,
            status="uploaded",
            total_rows=len(rows),
            valid_rows=0,
            invalid_rows=0,
            column_mapping_json="{}",
        )
        self.db.add(upload_job)
        self.db.flush()

        upload_rows = [
            UploadRow(
                upload_job_id=upload_job.id,
                row_number=index,
                raw_data_json=json.dumps(row),
                mapped_data_json="{}",
                validation_errors_json="[]",
                status="pending",
            )
            for index, row in enumerate(rows, start=1)
        ]
        self.db.add_all(upload_rows)
        self.db.commit()
        self.db.refresh(upload_job)
        return upload_job

    def get_job(self, *, upload_job_id: str) -> UploadJob | None:
        statement = (
            select(UploadJob)
            .where(UploadJob.id == upload_job_id)
            .options(selectinload(UploadJob.rows))
        )
        return self.db.scalar(statement)

    def save_mapping(self, *, upload_job: UploadJob, mapping: dict[str, str]) -> UploadJob:
        upload_job.column_mapping_json = json.dumps(mapping)
        upload_job.status = "mapped"
        upload_job.valid_rows = 0
        upload_job.invalid_rows = 0
        for row in upload_job.rows:
            row.mapped_data_json = json.dumps({})
            row.validation_errors_json = json.dumps([])
            row.status = "mapped"
        self.db.add(upload_job)
        self.db.commit()
        self.db.refresh(upload_job)
        return upload_job

    def save_mapped_rows(self, *, upload_job: UploadJob, mapped_rows: dict[str, dict]) -> UploadJob:
        for row in upload_job.rows:
            row.mapped_data_json = json.dumps(mapped_rows[row.id])
            row.validation_errors_json = json.dumps([])
            row.status = "mapped"
        upload_job.status = "mapped"
        self.db.add(upload_job)
        self.db.commit()
        self.db.refresh(upload_job)
        return upload_job

    def save_validation(
        self,
        *,
        upload_job: UploadJob,
        row_results: dict[str, tuple[str, dict, list[str]]],
    ) -> UploadJob:
        valid_rows = 0
        invalid_rows = 0
        for row in upload_job.rows:
            row_status, mapped_data, errors = row_results[row.id]
            row.status = row_status
            row.mapped_data_json = json.dumps(mapped_data)
            row.validation_errors_json = json.dumps(errors)
            if row_status == "valid":
                valid_rows += 1
            else:
                invalid_rows += 1

        upload_job.status = "validated"
        upload_job.valid_rows = valid_rows
        upload_job.invalid_rows = invalid_rows
        self.db.add(upload_job)
        self.db.commit()
        self.db.refresh(upload_job)
        return upload_job

    def existing_symbols(self, *, portfolio: Portfolio) -> set[str]:
        statement = select(Holding.symbol).where(Holding.portfolio_id == portfolio.id)
        return set(self.db.scalars(statement).all())

    def create_holdings(self, *, portfolio: Portfolio, rows: list[dict]) -> list[Holding]:
        holdings = [
            Holding(
                portfolio_id=portfolio.id,
                symbol=row["symbol"],
                company_name=row.get("company_name"),
                quantity=row["quantity"],
                average_cost=row.get("average_cost"),
                current_price=row.get("current_price"),
                currency=row["currency"],
                sector=row.get("sector"),
                asset_class=row.get("asset_class"),
                exchange=row.get("exchange"),
            )
            for row in rows
        ]
        self.db.add_all(holdings)
        self.db.flush()
        for holding in holdings:
            self.db.refresh(holding)
        return holdings

    def mark_imported(self, *, upload_job: UploadJob, status: str) -> UploadJob:
        upload_job.status = status
        self.db.add(upload_job)
        self.db.commit()
        self.db.refresh(upload_job)
        return upload_job


def row_raw_data(row: UploadRow) -> dict:
    return json.loads(row.raw_data_json)


def row_mapped_data(row: UploadRow) -> dict:
    return json.loads(row.mapped_data_json)


def row_errors(row: UploadRow) -> list[str]:
    return json.loads(row.validation_errors_json)


def job_mapping(upload_job: UploadJob) -> dict[str, str]:
    return json.loads(upload_job.column_mapping_json or "{}")
