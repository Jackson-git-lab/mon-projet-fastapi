from database import Base
from sqlalchemy import Column,String,Integer,Boolean,ARRAY,ForeignKey


class Players(Base):
    __tablename__ = "Players"

    id = Column(Integer, primary_key=True, index=True,autoincrement=True)
    nom = Column(String, nullable=False)
    classe = Column(String, nullable=False)
    niveau = Column(Integer, default=1)
    trophe = Column(ARRAY(String), nullable=False) 
    actif = Column(Boolean, default=True) 
    owner_id = Column(Integer, ForeignKey("Users.id"), nullable=False)


class Users(Base):
    __tablename__ = "Users"

    id = Column(Integer, primary_key=True, index=True,autoincrement=True)
    nom = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user")

