from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,Session
from sqlalchemy.ext.declarative import declarative_base
from typing import Annotated
from fastapi import Depends
import os
from dotenv import load_dotenv

# charge les variables d'environnement
load_dotenv()


# déclare l'URL de la base de données

SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")

# déclare le moteur de connexion

engine = create_engine(SQLALCHEMY_DATABASE_URI)

# déclare la session locale 
sessionlocal = sessionmaker(autoflush=False,autocommit=False,bind=engine)

# déclare la classe de base
Base = declarative_base()

# déclare la fonction get_db
def get_db():
    db = sessionlocal()
    try:
        yield db
    finally:
        db.close()

# déclare la dépendance db_dependency
db_dependency = Annotated[Session, Depends(get_db)]