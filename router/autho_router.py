from fastapi import APIRouter,Body,Depends,HTTPException
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
from database import db_dependency
from typing import Annotated
from classes import UserValidation,Token
from models import Users
from starlette import status
from datetime import timedelta,datetime,timezone
from jose import jwt,JWTError
import os
from dotenv import load_dotenv

# charge les variables d'environnement
load_dotenv()

router = APIRouter(
   tags=["AUTH"],
    prefix="/auth"
)

# jwt config   ...... secret_key obtenir par : openssl rand -hex 64
SECRET_KEY = os.getenv("SECRET_KEY")
JWT_ALGO = "HS256"

# bcrypt config
bcrypt_context = CryptContext(schemes=["bcrypt"],deprecated="auto")

# declare oath2bearer
oauth2bearer = OAuth2PasswordBearer(tokenUrl="/auth/login")

# function authenticate
def user_authenticate(username:str,password:str,db):
    autho_found = db.query(Users).filter(Users.username == username).first()
    if  not autho_found:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="no authenticad")
    if not bcrypt_context.verify(password,autho_found.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="no authenticad")
    return autho_found

# function create token
def create_token(username:str,user_id:int,role:str,expires_delta:timedelta):
    token_db =  {"sub":username,"id":user_id,"user_role":role}
    expiration = datetime.now(timezone.utc)+expires_delta
    token_db.update({"exp":expiration.timestamp()}) 
    return jwt.encode(token_db,SECRET_KEY,algorithm=JWT_ALGO)

# mildoware function 
async def current_user(db:db_dependency,token:Annotated[str,Depends(oauth2bearer)]):
    try:
        user_load = jwt.decode(token,SECRET_KEY,algorithms=[JWT_ALGO])
        username = user_load.get("sub")
        user_id = user_load.get("id")
        user_role = user_load.get("user_role")
        if username is None or user_id is None or user_role is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="non autoriser")
        return {"username":username,"id":user_id,"user_role":user_role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="non autoriser")
    
# declaration de l utilisateur
user_dependency = Annotated[dict,Depends(current_user)]

# endpoint pour créer un nouveau compte utilisateur
@router.post("/register",status_code=status.HTTP_201_CREATED)
async def register_user(db:db_dependency,format_user:UserValidation=Body()):
    register_found = Users(
    nom = format_user.nom,
    email = format_user.email,
    username = format_user.username,
    hashed_password = bcrypt_context.hash(format_user.password),
    role = "user"
    )
    db.add(register_found)
    db.commit()


# endpoint pour se connecter et obtenir un token
@router.post("/login",response_model=Token,status_code=status.HTTP_200_OK)
async def login_user(db:db_dependency,format:Annotated[OAuth2PasswordRequestForm,Depends()]):
    user_authenticated = user_authenticate(format.username,format.password,db)
    if not user_authenticated:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="authentication non autoriser")
    token = create_token(user_authenticated.username,user_authenticated.id,user_authenticated.role,timedelta(minutes=30))
    return {"access_token":token,"token_type":"Bearer"}