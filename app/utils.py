# Imports pour les types et les requêtes SQL
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from app.models import Hero


# Obtenir le prochain ID disponible (informatif, PostgreSQL gère auto)
def get_next_hero_id(db: Session) -> int:
    max_id = db.query(func.max(Hero.id)).scalar()
    return 1 if max_id is None else max_id + 1


# Vérifier si un héros avec ce nom existe déjà
def hero_exists_by_name(db: Session, name: str) -> bool:
    return db.query(Hero).filter(Hero.name.ilike(name)).first() is not None


# Vérifier si un héros avec cet ID existe
def hero_exists_by_id(db: Session, hero_id: int) -> bool:
    return db.query(Hero).filter(Hero.id == hero_id).first() is not None


# Compter le nombre total de héros dans la base
def get_heroes_count(db: Session) -> int:
    return db.query(Hero).count()


# Récupérer les héros dans une plage de rank (min à max)
def get_heroes_by_rank_range(
    db: Session,
    min_rank: int = 0,
    max_rank: int = 100,
    limit: int = 100
) -> List[Hero]:
    return db.query(Hero).filter(
        and_(Hero.rank >= min_rank, Hero.rank <= max_rank)
    ).order_by(Hero.rank.desc()).limit(limit).all()


# Recherche avancée avec plusieurs critères combinables
def search_heroes_advanced(
    db: Session,
    name: Optional[str] = None,
    first_name: Optional[str] = None,
    type: Optional[str] = None,
    min_rank: Optional[int] = None,
    max_rank: Optional[int] = None,
    powers: Optional[List[str]] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Hero]:
    query = db.query(Hero)
    
    # Ajouter les filtres textuels si fournis
    if name:
        query = query.filter(Hero.name.ilike(f"%{name}%"))
    
    if first_name:
        query = query.filter(Hero.first_name.ilike(f"%{first_name}%"))
    
    if type:
        query = query.filter(Hero.type.ilike(f"%{type}%"))
    
    # Ajouter les filtres numériques si fournis
    if min_rank is not None:
        query = query.filter(Hero.rank >= min_rank)
    
    if max_rank is not None:
        query = query.filter(Hero.rank <= max_rank)
    
    # Filtrer par pouvoirs (au moins un doit correspondre)
    if powers:
        power_conditions = [Hero.powers.contains([power]) for power in powers]
        query = query.filter(or_(*power_conditions))
    
    return query.offset(skip).limit(limit).all()


# Obtenir les héros avec les meilleurs ranks
def get_top_heroes(db: Session, limit: int = 10) -> List[Hero]:
    return db.query(Hero).order_by(Hero.rank.desc()).limit(limit).all()


# Compter le nombre de héros par type
def get_heroes_by_type_stats(db: Session) -> Dict[str, int]:
    stats = db.query(
        Hero.type,
        func.count(Hero.id).label('count')
    ).group_by(Hero.type).all()
    
    return {stat.type: stat.count for stat in stats}


# Calculer le rank moyen par type de héros
def get_average_rank_by_type(db: Session) -> Dict[str, float]:
    stats = db.query(
        Hero.type,
        func.avg(Hero.rank).label('avg_rank')
    ).group_by(Hero.type).all()
    
    return {stat.type: round(float(stat.avg_rank), 2) for stat in stats if stat.avg_rank}


# Valider qu'un type de héros est dans la liste autorisée
def validate_hero_type(hero_type: str) -> bool:
    valid_types = [
        'vigilante', 'alien', 'amazon', 'mutated', 'tech',
        'enhanced', 'god', 'mutant', 'magic', 'cosmic'
    ]
    return hero_type.lower() in valid_types


# Retourner la liste des types de héros valides
def get_valid_hero_types() -> List[str]:
    return [
        'vigilante', 'alien', 'amazon', 'mutated', 'tech',
        'enhanced', 'god', 'mutant', 'magic', 'cosmic'
    ]


# Formater un résumé textuel d'un héros
def format_hero_summary(hero: Hero) -> str:
    powers_str = ", ".join(hero.powers[:3]) if hero.powers else "None"
    if hero.powers and len(hero.powers) > 3:
        powers_str += f" (+{len(hero.powers) - 3} more)"
    
    return (
        f"{hero.name} ({hero.first_name}) - Type: {hero.type}, "
        f"Rank: {hero.rank}, Powers: {powers_str}"
    )


# Mettre à jour les ranks de plusieurs héros en une transaction
def bulk_update_ranks(db: Session, rank_adjustments: Dict[int, int]) -> int:
    updated_count = 0
    
    try:
        for hero_id, new_rank in rank_adjustments.items():
            hero = db.query(Hero).filter(Hero.id == hero_id).first()
            if hero and 0 <= new_rank <= 100:
                hero.rank = new_rank
                updated_count += 1
        
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    
    return updated_count


# Récupérer tous les héros ayant un pouvoir spécifique
def get_heroes_with_power(db: Session, power: str) -> List[Hero]:
    return db.query(Hero).filter(Hero.powers.contains([power])).all()


# Obtenir des statistiques complètes sur la base de données
def get_database_statistics(db: Session) -> Dict[str, Any]:
    total_heroes = db.query(Hero).count()
    
    if total_heroes == 0:
        return {
            "total_heroes": 0,
            "message": "Base de données vide"
        }
    
    # Calculer les statistiques globales
    avg_rank = db.query(func.avg(Hero.rank)).scalar()
    max_rank = db.query(func.max(Hero.rank)).scalar()
    min_rank = db.query(func.min(Hero.rank)).scalar()
    
    # Trouver le meilleur héros
    top_hero = db.query(Hero).order_by(Hero.rank.desc()).first()
    
    # Récupérer les statistiques par type
    type_stats = get_heroes_by_type_stats(db)
    avg_rank_by_type = get_average_rank_by_type(db)
    
    return {
        "total_heroes": total_heroes,
        "ranks": {
            "average": round(float(avg_rank), 2) if avg_rank else 0,
            "max": max_rank,
            "min": min_rank
        },
        "top_hero": {
            "name": top_hero.name,
            "rank": top_hero.rank
        } if top_hero else None,
        "heroes_by_type": type_stats,
        "average_rank_by_type": avg_rank_by_type
    }


# Nettoyer et valider une chaîne de caractères
def sanitize_string_input(input_str: str) -> str:
    if not input_str:
        return ""
    
    # Supprimer les espaces en début et fin
    cleaned = input_str.strip()
    
    # Limiter la longueur maximale à 200 caractères
    if len(cleaned) > 200:
        cleaned = cleaned[:200]
    
    return cleaned