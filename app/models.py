# Imports SQLAlchemy pour définir les modèles de base de données
from sqlalchemy import Column, Integer, String, ARRAY, Text, DateTime, CheckConstraint
from sqlalchemy.sql import func
from app.database import Base


# Modèle représentant la table "heroes" dans PostgreSQL
class Hero(Base):
    __tablename__ = "heroes"

    # Colonne ID : clé primaire auto-incrémentée avec index
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # Colonne name : nom unique du héros (obligatoire, indexé)
    name = Column(String(100), unique=True, nullable=False, index=True)
    
    # Colonne first_name : prénom du héros (optionnel)
    first_name = Column(String(100), nullable=True)
    
    # Colonnes ARRAY : listes de valeurs textuelles stockées en PostgreSQL
    occupation = Column(ARRAY(Text), nullable=True)  # Liste des métiers
    powers = Column(ARRAY(Text), nullable=True)      # Liste des pouvoirs
    hobbies = Column(ARRAY(Text), nullable=True)     # Liste des hobbies
    
    # Colonne type : catégorie du héros (vigilante, alien, etc.) avec index
    type = Column(String(50), nullable=True, index=True)
    
    # Colonne rank : niveau de puissance du héros (0-100) avec index
    rank = Column(Integer, nullable=True, index=True)
    
    # Timestamps : dates de création et modification automatiques
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Contrainte CHECK : valider que rank est entre 0 et 100
    __table_args__ = (
        CheckConstraint('rank >= 0 AND rank <= 100', name='check_rank_range'),
    )

    # Représentation string de l'objet pour le debugging
    def __repr__(self):
        return f"<Hero(id={self.id}, name='{self.name}', type='{self.type}', rank={self.rank})>"

    # Convertir l'objet Hero en dictionnaire (utile pour les APIs)
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "first_name": self.first_name,
            "occupation": self.occupation,
            "powers": self.powers,
            "hobbies": self.hobbies,
            "type": self.type,
            "rank": self.rank,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }