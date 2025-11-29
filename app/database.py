# Imports des bibliothèques standard et externes
import os
import logging
from typing import Generator
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

# Configuration du logging pour afficher les informations importantes
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Liste des variables d'environnement obligatoires pour se connecter à PostgreSQL
REQUIRED_ENV_VARS = [
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_HOST",
    "POSTGRES_DB"
]

# Vérifier que toutes les variables requises sont présentes
for var in REQUIRED_ENV_VARS:
    if not os.getenv(var):
        raise ValueError(f"Variable d'environnement manquante: {var}")

# Récupération des variables d'environnement pour la connexion PostgreSQL
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB")

# Configuration SSL pour les connexions sécurisées (production)
DB_SSL_MODE = os.getenv("DB_SSL_MODE", "prefer")
USE_SSL = os.getenv("USE_SSL", "false").lower() == "true"

# Configuration du pool de connexions pour optimiser les performances
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))


# Construire l'URL de connexion PostgreSQL de manière sécurisée
def get_database_url() -> str:
    base_url = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    
    # Ajouter les paramètres SSL si activés
    if USE_SSL:
        base_url += f"?sslmode={DB_SSL_MODE}"
    
    return base_url

DATABASE_URL = get_database_url()

# URL sécurisée pour les logs (le mot de passe est masqué)
SAFE_DATABASE_URL = f"postgresql://{POSTGRES_USER}:***@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# Créer le moteur SQLAlchemy avec pool de connexions
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=POOL_SIZE,
    max_overflow=MAX_OVERFLOW,
    pool_timeout=POOL_TIMEOUT,
    pool_recycle=POOL_RECYCLE,
    pool_pre_ping=True,
    echo=False,
    hide_parameters=True,
    connect_args={
        "connect_timeout": 10,
        "application_name": "heroes_api",
    }
)

# Logger les connexions établies à la base de données
@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    logger.info(f"Nouvelle connexion établie à la base de données: {SAFE_DATABASE_URL}")

# Logger les fermetures de connexions
@event.listens_for(engine, "close")
def receive_close(dbapi_conn, connection_record):
    logger.debug("Connexion à la base de données fermée")

# Créer une classe de session pour gérer les transactions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False
)

# Base pour tous les modèles SQLAlchemy
Base = declarative_base()


# Dépendance FastAPI pour obtenir une session de base de données
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db  # Fournir la session à l'endpoint
    except Exception as e:
        db.rollback()  # Annuler en cas d'erreur
        logger.error(f"Erreur dans la session de base de données: {str(e)}")
        raise
    finally:
        db.close()  # Toujours fermer la session


# Créer toutes les tables définies dans les modèles
def init_db() -> None:
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Tables de la base de données créées avec succès")
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de la base de données: {str(e)}")
        raise


# Vérifier que la connexion à PostgreSQL fonctionne
def check_db_connection() -> bool:
    try:
        with engine.connect() as connection:
            # Exécuter une requête simple pour tester la connexion
            connection.execute(text("SELECT 1"))
            connection.commit()
        logger.info(f"Connexion à la base de données réussie: {SAFE_DATABASE_URL}")
        return True
    except Exception as e:
        logger.error(f"Échec de connexion à la base de données: {str(e)}")
        return False


# Fermer proprement toutes les connexions du pool
def close_db_connection() -> None:
    try:
        engine.dispose()
        logger.info("Pool de connexions fermé proprement")
    except Exception as e:
        logger.error(f"Erreur lors de la fermeture des connexions: {str(e)}")


# Obtenir les statistiques du pool de connexions pour le monitoring
def get_pool_stats() -> dict:
    pool = engine.pool
    return {
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "total": pool.size() + pool.overflow()
    }