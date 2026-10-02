from app.db.session import Base
from sqlalchemy.orm import relationship
from sqlalchemy import Column,ForeignKey,Integer,VARCHAR,Enum,DateTime,Text,func
from sqlalchemy.dialects.mysql import LONGTEXT

class experiments(Base):
    __tablename__="experiments"
    id=Column(Integer,primary_key=True,index=True)
    subject_id=Column(Integer,ForeignKey("subjects.id",ondelete="CASCADE"),nullable=False,index=True)
    experiment_number=Column(Integer,nullable=False)
    experiment_name=Column(VARCHAR(255),nullable=False)
    language=Column(Enum(
        # Core CS languages
        "C", "C++", "Java", "Python", "JavaScript", "TypeScript",
        # Data & scripting
        "SQL", "R", "MATLAB", "Bash", "PowerShell",
        # ECE / Embedded
        "Assembly", "VHDL", "Verilog", "Arduino",
        # Web & misc
        "PHP", "Ruby", "Go", "Rust", "Swift", "Kotlin",
        # Catch-all
        "Other"
    ), nullable=False)
    code_content=Column(LONGTEXT,nullable=False)
    description=Column(Text,nullable=True)
    viva_questions=Column(Text,nullable=True)
    created_by=Column(Integer,ForeignKey("users.id",ondelete="CASCADE"),nullable=False)
    created_at=Column(DateTime,default=func.now())
    updated_at=Column(DateTime,onupdate=func.now())

    subject=relationship("subjects",back_populates="experiment")
    user=relationship("users",back_populates="experiment")