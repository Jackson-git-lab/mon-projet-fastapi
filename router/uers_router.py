from fastapi import APIRouter,Path,HTTPException,Body
from database import db_dependency
from starlette import status 
from models import Users
from router.autho_router import user_dependency,bcrypt_context
from classes import Reset_password


# crée le routeur pour les actions utilisateurs
router = APIRouter(
    tags=["USERS"],
    prefix="/user"
)

# récupère les informations de l'utilisateur connecté
@router.get("/me", status_code=status.HTTP_200_OK)
async def get_current_user_info(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="vous n'êtes pas autorisé")
    user_info = db.query(Users).filter(Users.id == user.get("user_id")).first()
    if not user_info:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="utilisateur non trouvé")
    return {
        "id": user_info.id,
        "nom": user_info.nom,
        "email": user_info.email,
        "username": user_info.username,
        "role": user_info.role
    }

# permet à l'utilisateur connecté de modifier son mot de passe
@router.put("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(user: user_dependency,  db: db_dependency,passwords: Reset_password = Body()):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="vous n'êtes pas autorisé")
    user_found = db.query(Users).filter(Users.id == user.get("user_id")).first()
    if not user_found:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="utilisateur non trouvé")
    if not bcrypt_context.verify(passwords.old_password, user_found.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="ancien mot de passe incorrect")
    if bcrypt_context.verify(passwords.new_password, user_found.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="le nouveau mot de passe doit être différent de l'ancien")
    user_found.hashed_password = bcrypt_context.hash(passwords.new_password)
    db.add(user_found)
    db.commit()