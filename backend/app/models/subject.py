from app.db.session import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column,Integer,VARCHAR,DateTime,func,ForeignKey,Index
from sqlalchemy.dialects.mysql import TINYINT

class subjects(Base):
    __tablename__="subjects"
    id=Column(Integer,primary_key=True,index=True)
    name=Column(VARCHAR(255),nullable=False)
    class_year=Column(TINYINT,nullable=False)
    department=Column(VARCHAR(150),nullable=False)
    syllabus_scheme=Column(VARCHAR(100),nullable=False)
    created_by=Column(Integer,ForeignKey("users.id",ondelete="CASCADE"),nullable=False)
    created_at=Column(DateTime,default=func.now())
    updated_at=Column(DateTime,onupdate=func.now())

    user=relationship("users",back_populates="subject")
    experiment=relationship("experiments",back_populates="subject",cascade="all,delete-orphan")

# Composite index for the public filter UI (class_year + department + syllabus_scheme)
Index("ix_subjects_filter", subjects.class_year, subjects.department, subjects.syllabus_scheme)