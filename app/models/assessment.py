from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, utcnow


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target: Mapped[str] = mapped_column(String(255), nullable=False)
    finding_name: Mapped[str] = mapped_column(String(255), nullable=False)
    found_on: Mapped[date] = mapped_column(Date, nullable=False)
    researcher: Mapped[str] = mapped_column(String(120), nullable=False, default="")

    cvss_vector: Mapped[str] = mapped_column(String(120), nullable=False)
    cvss_score: Mapped[float] = mapped_column(Float, nullable=False)
    base_severity: Mapped[str] = mapped_column(String(20), nullable=False)
    final_severity: Mapped[str] = mapped_column(String(20), nullable=False)
    severity_upgraded: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    severity_reasons: Mapped[str] = mapped_column(Text, nullable=False, default="")

    business_impact: Mapped[str] = mapped_column(String(20), nullable=False, default="Low")
    deadline_label: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    deadline_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    owner: Mapped["User"] = relationship(lazy="selectin")
    detail: Mapped["AssessmentDetail"] = relationship(
        back_populates="assessment",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    exports: Mapped[list["ExportRecord"]] = relationship(
        back_populates="assessment", cascade="all, delete-orphan"
    )


class AssessmentDetail(Base):
    __tablename__ = "assessment_details"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    assessment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("assessments.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    attack_vector: Mapped[str] = mapped_column(String(2), nullable=False)
    attack_complexity: Mapped[str] = mapped_column(String(2), nullable=False)
    privileges_required: Mapped[str] = mapped_column(String(2), nullable=False)
    user_interaction: Mapped[str] = mapped_column(String(2), nullable=False)
    scope: Mapped[str] = mapped_column(String(2), nullable=False)
    confidentiality: Mapped[str] = mapped_column(String(2), nullable=False)
    integrity: Mapped[str] = mapped_column(String(2), nullable=False)
    availability: Mapped[str] = mapped_column(String(2), nullable=False)

    public_exploit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cve_id: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    reproducible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    poc_available: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    poc_attachment_path: Mapped[str] = mapped_column(String(255), nullable=False, default="")

    impacted_data: Mapped[str] = mapped_column(Text, nullable=False, default="")
    estimated_users: Mapped[str] = mapped_column(String(80), nullable=False, default="")
    regulations: Mapped[str] = mapped_column(Text, nullable=False, default="")

    chain_phpinfo_cve: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    chain_dev_credentials: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    chain_version_critical_cve: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    chain_entry_point: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    remediation_name: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    remediation_steps: Mapped[str] = mapped_column(Text, nullable=False, default="")
    remediation_owasp: Mapped[str] = mapped_column(String(120), nullable=False, default="")
    remediation_cwe: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    remediation_capec: Mapped[str] = mapped_column(String(40), nullable=False, default="")
    remediation_references: Mapped[str] = mapped_column(Text, nullable=False, default="")

    assessment: Mapped[Assessment] = relationship(back_populates="detail")


class ExportRecord(Base):
    __tablename__ = "exports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    assessment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    file_path: Mapped[str] = mapped_column(String(400), nullable=False)
    file_format: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    assessment: Mapped[Assessment] = relationship(back_populates="exports")
