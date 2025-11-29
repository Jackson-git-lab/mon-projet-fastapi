# Imports des bibliothèques externes
from fastapi import FastAPI, Query, Path, Body, HTTPException, Depends
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
from typing import List, Optional
from starlette import status

# Imports des modules internes pour la gestion de la base de données et des modèles
from app.database import (
    init_db, 
    check_db_connection, 
    close_db_connection, 
    get_db,
    get_pool_stats
)
from app.models import Hero
from app.schemas import HeroCreate, HeroUpdate, HeroResponse


# Gestion du cycle de vie de l'application (démarrage et arrêt)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup : Initialiser la base de données au démarrage
    print("Démarrage de l'application Heroes API...")
    
    # Vérifier la connexion à la base de données
    if not check_db_connection():
        raise Exception("Impossible de se connecter à la base de données PostgreSQL")
    
    # Créer les tables si elles n'existent pas
    init_db()
    print("Tables de la base de données créées/vérifiées")
    print("Application prête !\n")
    
    yield
    
    # Shutdown : Fermer les connexions proprement à l'arrêt
    print("\nArrêt de l'application...")
    close_db_connection()
    print("Connexions fermées proprement")


# Initialiser l'application FastAPI avec le cycle de vie
app = FastAPI(
    title="Heroes API",
    description="API de gestion des super-héros avec PostgreSQL",
    version="2.0.0",
    lifespan=lifespan
)


# Endpoint racine : Page d'accueil de l'API
@app.get("/", tags=["Root"])
async def headbeats():
    return {
        "message": "Heroes API - PostgreSQL Edition",
        "version": "2.0.0",
        "endpoints": "/docs pour la documentation"
    }


# Endpoint de santé : Vérifier l'état de l'application et de la base de données
@app.get("/health", tags=["Health"])
async def health_check():
    db_status = check_db_connection()
    pool_stats = get_pool_stats()
    
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "pool_stats": pool_stats
    }


# Endpoint pour récupérer tous les héros avec pagination
@app.get("/heroes", response_model=List[HeroResponse], status_code=status.HTTP_200_OK, tags=["Heroes"])
async def get_all_heroes(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à sauter"),
    limit: int = Query(100, ge=1, le=100, description="Nombre maximum d'éléments à retourner"),
    db: Session = Depends(get_db)
):
    # Récupérer les héros avec offset et limit pour la pagination
    heroes = db.query(Hero).offset(skip).limit(limit).all()
    return heroes


# Endpoint pour récupérer les héros par type
@app.get("/heroes/type", response_model=List[HeroResponse], status_code=status.HTTP_200_OK, tags=["Heroes"])
async def get_heroes_by_type(
    hero_type: str = Query(..., description="Type de héros à rechercher"),
    db: Session = Depends(get_db)
):
    # Recherche insensible à la casse avec ilike
    heroes = db.query(Hero).filter(Hero.type.ilike(f"%{hero_type}%")).all()
    
    # Si aucun héros trouvé, lever une exception 404
    if not heroes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aucun héros trouvé avec le type '{hero_type}'"
        )
    
    return heroes


# Endpoint pour récupérer les héros par rank minimum
@app.get("/heroes/rank", response_model=List[HeroResponse], status_code=status.HTTP_200_OK, tags=["Heroes"])
async def get_heroes_by_rank(
    hero_rank: int = Query(..., ge=0, le=100, description="Rank minimum du héros"),
    db: Session = Depends(get_db)
):
    # Filtrer par rank >= hero_rank et trier par ordre décroissant
    heroes = db.query(Hero).filter(Hero.rank >= hero_rank).order_by(Hero.rank.desc()).all()
    
    if not heroes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aucun héros trouvé avec un rank >= {hero_rank}"
        )
    
    return heroes


# Endpoint pour récupérer un héros par son ID
@app.get("/hero/id/{hero_id}", response_model=HeroResponse, status_code=status.HTTP_200_OK, tags=["Heroes"])
async def get_hero_by_id(
    hero_id: int = Path(..., gt=0, description="ID du héros"),
    db: Session = Depends(get_db)
):
    # Rechercher le héros par ID
    hero = db.query(Hero).filter(Hero.id == hero_id).first()
    
    # Si le héros n'existe pas, lever une exception 404
    if not hero:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Héros avec l'ID {hero_id} non trouvé"
        )
    
    return hero


# Endpoint pour rechercher des héros par nom (recherche partielle)
@app.get("/hero/name/{hero_name}", response_model=List[HeroResponse], status_code=status.HTTP_200_OK, tags=["Heroes"])
async def get_hero_by_name(
    hero_name: str = Path(..., description="Nom du héros à rechercher"),
    db: Session = Depends(get_db)
):
    # Recherche partielle insensible à la casse
    heroes = db.query(Hero).filter(Hero.name.ilike(f"%{hero_name}%")).all()
    
    if not heroes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aucun héros trouvé avec le nom '{hero_name}'"
        )
    
    return heroes


# Endpoint pour créer un nouveau héros
@app.post("/hero/create", response_model=HeroResponse, status_code=status.HTTP_201_CREATED, tags=["Heroes"])
async def create_hero(
    new_hero: HeroCreate = Body(...),
    db: Session = Depends(get_db)
):
    from app.utils import hero_exists_by_name
    
    # Vérifier si un héros avec ce nom existe déjà
    if hero_exists_by_name(db, new_hero.name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Un héros avec le nom '{new_hero.name}' existe déjà"
        )
    
    # Créer le nouveau héros et l'ajouter à la base de données
    db_hero = Hero(**new_hero.model_dump())
    db.add(db_hero)
    
    try:
        db.commit()  # Sauvegarder dans la base de données
        db.refresh(db_hero)  # Recharger l'objet avec l'ID généré
    except Exception as e:
        db.rollback()  # Annuler en cas d'erreur
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création du héros: {str(e)}"
        )
    
    return db_hero


# Endpoint pour mettre à jour un héros existant
@app.put("/hero/update/{hero_id}", response_model=HeroResponse, status_code=status.HTTP_200_OK, tags=["Heroes"])
async def update_hero(
    hero_id: int = Path(..., gt=0, description="ID du héros à modifier"),
    hero_update: HeroUpdate = Body(...),
    db: Session = Depends(get_db)
):
    # Rechercher le héros à mettre à jour
    db_hero = db.query(Hero).filter(Hero.id == hero_id).first()
    
    if not db_hero:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Héros avec l'ID {hero_id} non trouvé"
        )
    
    # Mettre à jour uniquement les champs fournis
    update_data = hero_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_hero, field, value)
    
    try:
        db.commit()
        db.refresh(db_hero)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour du héros: {str(e)}"
        )
    
    return db_hero


# Endpoint pour supprimer un héros
@app.delete("/hero/delete/{hero_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Heroes"])
async def delete_hero(
    hero_id: int = Path(..., gt=0, description="ID du héros à supprimer"),
    db: Session = Depends(get_db)
):
    # Rechercher le héros à supprimer
    db_hero = db.query(Hero).filter(Hero.id == hero_id).first()
    
    if not db_hero:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Héros avec l'ID {hero_id} non trouvé"
        )
    
    try:
        db.delete(db_hero)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression du héros: {str(e)}"
        )
    
    return None


# Endpoint de recherche avancée avec plusieurs critères combinables
@app.get("/heroes/search", response_model=List[HeroResponse], status_code=status.HTTP_200_OK, tags=["Heroes"])
async def search_heroes(
    name: Optional[str] = Query(None, description="Recherche par nom"),
    type: Optional[str] = Query(None, description="Recherche par type"),
    min_rank: Optional[int] = Query(None, ge=0, le=100, description="Rank minimum"),
    max_rank: Optional[int] = Query(None, ge=0, le=100, description="Rank maximum"),
    db: Session = Depends(get_db)
):
    # Construire la requête en ajoutant les filtres fournis
    query = db.query(Hero)
    
    if name:
        query = query.filter(Hero.name.ilike(f"%{name}%"))
    
    if type:
        query = query.filter(Hero.type.ilike(f"%{type}%"))
    
    if min_rank is not None:
        query = query.filter(Hero.rank >= min_rank)
    
    if max_rank is not None:
        query = query.filter(Hero.rank <= max_rank)
    
    heroes = query.all()
    
    if not heroes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun héros trouvé avec ces critères"
        )
    
    return heroes


# Endpoint pour obtenir des statistiques sur les héros
@app.get("/heroes/stats", tags=["Statistics"])
async def get_heroes_stats(db: Session = Depends(get_db)):
    from app.utils import get_database_statistics
    return get_database_statistics(db)


# Endpoint pour obtenir la liste des types de héros valides
@app.get("/heroes/types", tags=["Reference"])
async def get_valid_types():
    from app.utils import get_valid_hero_types
    return {
        "valid_types": get_valid_hero_types(),
        "total": len(get_valid_hero_types())
    }


# Endpoint pour récupérer les héros ayant un pouvoir spécifique
@app.get("/heroes/power/{power_name}", response_model=List[HeroResponse], tags=["Heroes"])
async def get_heroes_by_power(
    power_name: str = Path(..., description="Nom du pouvoir à rechercher"),
    db: Session = Depends(get_db)
):
    from app.utils import get_heroes_with_power
    
    heroes = get_heroes_with_power(db, power_name)
    
    if not heroes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aucun héros trouvé avec le pouvoir '{power_name}'"
        )
    
    return heroes


# Endpoint pour obtenir les héros avec les meilleurs ranks
@app.get("/heroes/top/{limit}", response_model=List[HeroResponse], tags=["Heroes"])
async def get_top_ranked_heroes(
    limit: int = Path(..., ge=1, le=50, description="Nombre de héros à retourner"),
    db: Session = Depends(get_db)
):
    from app.utils import get_top_heroes
    return get_top_heroes(db, limit)