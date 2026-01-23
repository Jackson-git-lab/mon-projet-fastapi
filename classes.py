from pydantic import BaseModel, Field, field_validator,EmailStr
from typing import List

class PlayerValidation(BaseModel):
    
    nom: str = Field(min_length=3, max_length=30)
    classe: str = Field(min_length=3, max_length=20)
    niveau: int = Field(default=1, ge=1, le=100)
    trophe: List[str] = Field(default_factory=list)
    actif: bool = Field(default=True)

    
    # validation personnalisée pour la classe
    @field_validator('classe')
    @classmethod
    def valider_classe(cls, value):
        classes_autorisees = ['guerrier', 'mage', 'archer', 'voleur']
        if value.lower() not in classes_autorisees:
            raise ValueError(f'La classe doit être parmi: {", ".join(classes_autorisees)}')
        return value.lower()
    
    # validation personnalisée pour les trophées
    @field_validator('trophe')
    @classmethod
    def valider_trophe(cls, value):
        if len(value) > 10:
            raise ValueError('Un joueur ne peut pas avoir plus de 10 trophées')
        return value
    
    class Config:
        json_schema_extra = {
            "example": {
                "nom": "DragonSlayer",
                "classe": "guerrier",
                "niveau": 5,
                "trophe": ["Champion", "Explorateur"],
                "actif": True
            }
        }


class UserValidation(BaseModel):
   
    nom: str = Field(min_length=3, max_length=50)
    email: EmailStr
    username: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=8, max_length=70)
    
    # validation personnalisée pour le username
    @field_validator('username')
    @classmethod
    def valider_username(cls, value):
        if ' ' in value:
            raise ValueError("Le username ne peut pas contenir d'espaces")
        if not value.isalnum():
            raise ValueError("Le username doit contenir uniquement des lettres et chiffres")
        return value.lower()
    
    # validation personnalisée pour le mot de passe
    @field_validator('password')
    @classmethod
    def valider_password(cls, value):
        if not any(char.isdigit() for char in value):
            raise ValueError("Le mot de passe doit contenir au moins un chiffre")
        if not any(char.isupper() for char in value):
            raise ValueError("Le mot de passe doit contenir au moins une majuscule")
        return value
    
    class Config:
        json_schema_extra = {
            "example": {
                "nom": "Jean Kouakou",
                "email": "jean.kouakou@example.com",
                "username": "jeankouakou",
                "password": "Password123"
            }
        }

class Token(BaseModel):
    access_token: str
    token_type: str

class Reset_password(BaseModel):
    old_password: str 
    new_password: str = Field(min_length=8, max_length=70) 