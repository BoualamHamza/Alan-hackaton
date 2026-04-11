import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

from patient_intake.config import DATABASE_URL

Base = declarative_base()


def _uuid() -> str:
    return str(uuid.uuid4())


class IntakeSession(Base):
    __tablename__ = "intake_sessions"

    id = Column(String(36), primary_key=True, default=_uuid)
    patient_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="active")  # active | completed

    messages = relationship(
        "ConversationMessage",
        back_populates="session",
        order_by="ConversationMessage.created_at",
        cascade="all, delete-orphan",
    )
    files = relationship(
        "UploadedFile",
        back_populates="session",
        order_by="UploadedFile.upload_date",
        cascade="all, delete-orphan",
    )
    report = relationship(
        "MedicalReportDB",
        back_populates="session",
        uselist=False,
        cascade="all, delete-orphan",
    )


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id = Column(String(36), primary_key=True, default=_uuid)
    session_id = Column(String(36), ForeignKey("intake_sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # "patient" | "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("IntakeSession", back_populates="messages")


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(String(36), primary_key=True, default=_uuid)
    session_id = Column(String(36), ForeignKey("intake_sessions.id", ondelete="CASCADE"), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_type = Column(String(100), nullable=False)
    storage_path = Column(String(1000), nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    extraction_status = Column(String(50), default="pending")  # pending | processing | done | failed
    extracted_content = Column(Text, nullable=True)  # JSON string

    session = relationship("IntakeSession", back_populates="files")


class MedicalReportDB(Base):
    __tablename__ = "medical_reports"

    id = Column(String(36), primary_key=True, default=_uuid)
    session_id = Column(String(36), ForeignKey("intake_sessions.id", ondelete="CASCADE"), nullable=False, unique=True)
    generated_at = Column(DateTime, default=datetime.utcnow)
    report_json = Column(Text, nullable=False)

    session = relationship("IntakeSession", back_populates="report")


# ---------------------------------------------------------------------------
# Engine & session factory
# ---------------------------------------------------------------------------

engine = create_async_engine(DATABASE_URL, echo=False)
async_session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with async_session_factory() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
