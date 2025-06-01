# app/db/models.py
import uuid
from sqlalchemy import (
    Column, String, Text, TIMESTAMP, Numeric, Boolean, ForeignKey, CheckConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

class Currency(Base):
    __tablename__ = "currency"
    code = Column(String(3), primary_key=True)
    name = Column(Text, nullable=False)
    symbol = Column(Text)

class Transaction(Base):
    __tablename__ = "transactions"
    transaction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sender_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    receiver_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(18, 2), nullable=False)
    currency = Column(String(3), ForeignKey("currency.code"), nullable=False)
    timestamp = Column(TIMESTAMP(timezone=True), nullable=False)
    status = Column(Text, nullable=False)
    is_suspicious = Column(Boolean, server_default="FALSE", nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_transactions_amount_nonnegative"),
        CheckConstraint("status IN ('pending','completed','failed')", name="ck_transactions_status_valid"),
        Index("idx_transactions_sender", "sender_id"),
        Index("idx_transactions_receiver", "receiver_id"),
        # Partial index for suspicious rows (SQLAlchemy ≥ 1.4)
        Index("idx_transactions_suspicious", "is_suspicious", postgresql_where=(Column("is_suspicious") == True)),
    )
