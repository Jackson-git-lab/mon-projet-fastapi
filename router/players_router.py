from fastapi import APIRouter,Path,HTTPException,Query,Body
from database import db_dependency
from sqlalchemy import text
from starlette import status 
from models import Players
from classes import PlayerValidation
from router.autho_router import user_dependency

# crée le routeur pour les joueurs
router = APIRouter(
    tags=["PLAYER"],
    prefix="/player"
)

# endpoint de bienvenue avec test de connexion à la base de données
@router.get("/",status_code=status.HTTP_200_OK)
async def bienvenue_message(user:user_dependency,db:db_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="vous n'êtes pas autorisé")
    try:
        db.execute(text("SELECT 1"))
        return {"Message":"Bienvenue Sur Notre Api"}
    except Exception as e:
        return {"Error":str(e)}

# récupère tous les joueurs appartenant à l'utilisateur connecté
@router.get("/Players",status_code=status.HTTP_200_OK)
async def get_all_payers(user:user_dependency,db:db_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="vous n'êtes pas autorisé")
    return db.query(Players).filter(user.get("id")==Players.owner_id).order_by(Players.id.asc()).all()

# récupère un joueur par son id (seulement si il appartient à l'utilisateur)
@router.get("/{player_id}",status_code=status.HTTP_200_OK)
async def get_player_by_id(user:user_dependency,db:db_dependency,player_id:int=Path(ge=1)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="vous n'êtes pas autorisé")
    player_found = db.query(Players).filter(player_id == Players.id).filter(user.get("id")==Players.owner_id).first()
    if not player_found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="l'id que vous avez saisi n'existe pas")
    return player_found

# récupère un joueur par son nom (seulement parmi les joueurs de l'utilisateur)
@router.get("/nom",status_code=status.HTTP_200_OK)
async def get_player_by_nom(user:user_dependency,db:db_dependency,nom:str=Query(min_length=3)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="vous n'êtes pas autorisé")
    player_found = db.query(Players).filter(Players.nom.ilike(f"%{nom}%")).filter(user.get("id")==Players.owner_id).all()
    if not player_found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="le nom n'a pas été trouvé")
    return player_found

# crée un nouveau joueur lié à l'utilisateur connecté
@router.post("/create",status_code=status.HTTP_201_CREATED)
async def create_player(user:user_dependency,db:db_dependency, format_player:PlayerValidation = Body()):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="vous n'êtes pas autorisé")
    player_found = Players(**format_player.model_dump(exclude="id"),owner_id = user.get("id"))
    db.add(player_found)
    db.commit()

# met à jour un joueur existant (seulement si il appartient à l'utilisateur)
@router.put("/update/{player_id}",status_code=status.HTTP_204_NO_CONTENT)
async def update_payer(user:user_dependency,db:db_dependency,player_id:int=Path(ge=1),format_player:PlayerValidation=Body()):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="vous n'êtes pas autorisé")
    player_found = db.query(Players).filter(Players.id == player_id).filter(user.get("id")== Players.owner_id).first()
    if not player_found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ce player n'existe pas")
    player_found.nom = format_player.nom
    player_found.actif = format_player.actif
    player_found.niveau = format_player.niveau
    player_found.classe = format_player.classe
    player_found.trophe = format_player.trophe
    db.add(player_found)
    db.commit()

# supprime un joueur (seulement si il appartient à l'utilisateur)
@router.delete("/delete/{player_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_payer(user:user_dependency,db:db_dependency,player_id:int=Path(ge=1)):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="vous n'êtes pas autorisé")
    player_found = db.query(Players).filter(Players.id == player_id).filter(user.get("id")== Players.owner_id).first()
    if not player_found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="player n'existe pas")
    db.delete(player_found)
    db.commit()