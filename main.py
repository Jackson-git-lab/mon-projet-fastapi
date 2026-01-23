from fastapi import FastAPI 
import models
from database import engine
from router import players_router,uers_router,autho_router,admin_router

# crée l'instance de l'application FastAPI
app = FastAPI()

# crée toutes les tables dans la base de données
models.Base.metadata.create_all(bind=engine)

# inclut le routeur des joueurs
app.include_router(players_router.router)

# inclut le routeur des utilisateurs
app.include_router(uers_router.router)

# inclut le routeur d authentification
app.include_router(autho_router.router)

# inclut le routeur de l admin
app.include_router(admin_router.router)




