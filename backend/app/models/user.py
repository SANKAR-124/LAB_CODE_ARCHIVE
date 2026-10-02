from app.db.session import Base
from sqlalchemy import Integer,VARCHAR,Enum,DateTime,Column,func
from sqlalchemy.orm import relationship

class users(Base):
    __tablename__="users"
    id=Column(Integer,primary_key=True,index=True)
    username=Column(VARCHAR(150),nullable=False,unique=True)
    email=Column(VARCHAR(255),nullable=False,unique=True)
    password_hash=Column(VARCHAR(255),nullable=False)
    role=Column(Enum('super_admin', 'contributor_admin'),nullable=False)
    created_at=Column(DateTime,default=func.now())

    subject=relationship("subjects",back_populates="user",cascade="all,delete-orphan")
    experiment=relationship("experiments",back_populates="user",cascade="all,delete-orphan")