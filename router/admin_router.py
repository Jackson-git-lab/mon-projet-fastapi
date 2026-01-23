from fastapi import APIRouter,Path,HTTPException
from database import db_dependency
from starlette import status 
from models import Players
from router.autho_router import user_dependency

#  le routeur pour les actions administrateur
router = APIRouter(
    tags=["ADMIN"],
    prefix="/admin"
)

# récupère tous les joueurs de tous les utilisateurs (réservé admin)
@router.get("/Players",status_code=status.HTTP_200_OK)
async def get_all_payers(user:user_dependency,db:db_dependency):
    if user is None or user.get("user_role") != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="vous n'êtes pas autorisé")
    return db.query(Players).order_by(Players.id.asc()).all()


# supprime n'importe quel joueur sans vérifier le propriétaire (réservé admin)
@router.delete("/delete/{player_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_payer(user:user_dependency,db:db_dependency,player_id:int=Path(ge=1)):
    if user is None or user.get("user_role") != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="vous n'êtes pas autorisé")
    player_found = db.query(Players).filter(Players.id == player_id).first()
    if not player_found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="player n'existe pas")
    db.delete(player_found)
    db.commit()