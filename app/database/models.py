from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Table,
    Text,
    DateTime,
    create_engine,
    Float,
)
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

# Association table for indication-icd10 many-to-many relationship
indication_icd10 = Table(
    "indication_icd10",
    Base.metadata,
    Column("indication_id", Integer, ForeignKey("indications.id", ondelete="CASCADE")),
    Column("icd10_id", Integer, ForeignKey("icd10_codes.id", ondelete="CASCADE")),
    Column("confidence_score", Float),  # 0-1 score for mapping confidence
)


class Drug(Base):
    __tablename__ = "drugs"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, index=True)
    set_id = Column(String(255), unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    indication = relationship(
        "Indication", back_populates="drug", uselist=False, cascade="all, delete-orphan"
    )
    directions = relationship(
        "Directions", back_populates="drug", uselist=False, cascade="all, delete-orphan"
    )


class Indication(Base):
    __tablename__ = "indications"

    id = Column(Integer, primary_key=True)
    description = Column(Text, nullable=False)
    drug_id = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    drug = relationship("Drug", back_populates="indication")
    icd10_codes = relationship(
        "ICD10Code",
        secondary=indication_icd10,
        back_populates="indications",
    )


class Directions(Base):
    __tablename__ = "directions"

    id = Column(Integer, primary_key=True)
    description = Column(Text, nullable=False)
    drug_id = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    drug = relationship("Drug", back_populates="directions")


class ICD10Code(Base):
    __tablename__ = "icd10_codes"

    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, index=True)
    description = Column(Text, nullable=False)
    category = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    confidence_score = Column(Float)

    indications = relationship(
        "Indication",
        secondary=indication_icd10,
        back_populates="icd10_codes",
    )


class ICD10CodesSource(Base):
    __tablename__ = "icd10_codes_source"

    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, index=True)
    description = Column(Text, nullable=False)
    category = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# Create engine and tables
def init_db(db_url: str):
    engine = create_engine(db_url)
    Base.metadata.create_all(bind=engine)
    return engine
