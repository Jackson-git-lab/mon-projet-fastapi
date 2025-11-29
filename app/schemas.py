# Imports Pydantic pour la validation des données
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime


# Schéma de base contenant tous les champs communs d'un héros
class HeroBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Nom du héros")
    first_name: Optional[str] = Field(None, max_length=100, description="Prénom du héros")
    occupation: Optional[List[str]] = Field(default=[], description="Liste des occupations")
    powers: Optional[List[str]] = Field(default=[], description="Liste des pouvoirs")
    hobbies: Optional[List[str]] = Field(default=[], description="Liste des hobbies")
    type: Optional[str] = Field(None, max_length=50, description="Type de héros")
    rank: Optional[int] = Field(None, ge=0, le=100, description="Niveau du héros (0-100)")

    # Validateur : S'assurer que le nom n'est pas vide
    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Le nom ne peut pas être vide')
        return v.strip()

    # Validateur : Vérifier que le type est dans la liste autorisée
    @field_validator('type')
    @classmethod
    def type_must_be_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        
        valid_types = [
            'vigilante', 'alien', 'amazon', 'mutated', 'tech',
            'enhanced', 'god', 'mutant', 'magic', 'cosmic'
        ]
        
        if v.lower() not in valid_types:
            raise ValueError(
                f"Type invalide. Types autorisés: {', '.join(valid_types)}"
            )
        
        return v.lower()


# Schéma pour créer un nouveau héros (hérite de HeroBase)
class HeroCreate(HeroBase):
    pass

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Aquaman",
                "first_name": "Arthur",
                "occupation": ["king", "superhero"],
                "powers": ["Underwater breathing", "Super strength", "Telepathy with sea life"],
                "hobbies": ["Swimming", "Protecting the oceans"],
                "type": "enhanced",
                "rank": 84
            }
        }


# Schéma pour mettre à jour un héros (tous les champs optionnels)
class HeroUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    occupation: Optional[List[str]] = None
    powers: Optional[List[str]] = None
    hobbies: Optional[List[str]] = None
    type: Optional[str] = Field(None, max_length=50)
    rank: Optional[int] = Field(None, ge=0, le=100)

    # Validateur : Nom non vide si fourni
    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v or not v.strip()):
            raise ValueError('Le nom ne peut pas être vide')
        return v.strip() if v else v

    # Validateur : Type valide si fourni
    @field_validator('type')
    @classmethod
    def type_must_be_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        
        valid_types = [
            'vigilante', 'alien', 'amazon', 'mutated', 'tech',
            'enhanced', 'god', 'mutant', 'magic', 'cosmic'
        ]
        
        if v.lower() not in valid_types:
            raise ValueError(
                f"Type invalide. Types autorisés: {', '.join(valid_types)}"
            )
        
        return v.lower()

    class Config:
        json_schema_extra = {
            "example": {
                "rank": 90,
                "powers": ["Underwater breathing", "Super strength", "Telepathy with sea life", "Trident mastery"]
            }
        }


# Schéma pour les réponses API (inclut ID et timestamps)
class HeroResponse(HeroBase):
    id: int = Field(..., description="ID unique du héros")
    created_at: datetime = Field(..., description="Date de création")
    updated_at: datetime = Field(..., description="Date de dernière modification")

    class Config:
        from_attributes = True  # Permet la conversion depuis SQLAlchemy
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Batman",
                "first_name": "Bruce",
                "occupation": ["billionaire", "vigilante"],
                "powers": ["Intelligence", "Martial arts", "Technology"],
                "hobbies": ["Reading", "Flying", "Philanthropy"],
                "type": "vigilante",
                "rank": 50,
                "created_at": "2024-01-01T12:00:00",
                "updated_at": "2024-01-01T12:00:00"
            }
        }


# Schéma pour les paramètres de recherche avancée
class HeroSearchParams(BaseModel):
    name: Optional[str] = Field(None, description="Recherche par nom (partielle)")
    type: Optional[str] = Field(None, description="Recherche par type")
    min_rank: Optional[int] = Field(None, ge=0, le=100, description="Rank minimum")
    max_rank: Optional[int] = Field(None, ge=0, le=100, description="Rank maximum")
    skip: int = Field(0, ge=0, description="Nombre d'éléments à sauter")
    limit: int = Field(100, ge=1, le=100, description="Nombre maximum d'éléments")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "vigilante",
                "min_rank": 50,
                "max_rank": 90,
                "skip": 0,
                "limit": 10
            }
        }