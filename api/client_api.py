import os
from fastapi import FastAPI, HTTPException, Depends, Request, Response
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from prometheus_client import Summary, Counter, generate_latest, CONTENT_TYPE_LATEST
import pika
import logging

logger = logging.getLogger("uvicorn.error")

# Création de l'instance FastAPI pour initialiser l'application et permettre la définition des routes.
app = FastAPI()

# Configuration et mise en place de la connexion à la base de données avec SQLAlchemy
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./client_api.db")
DATABASE_URL_TEST = "sqlite:///./test_db.sqlite"
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "client_queue")

def get_engine(env: str = "prod"):
    if env == "test":
        return create_engine(DATABASE_URL_TEST)
    else:
        return create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Définition d'une fonction pour obtenir une session de base de données en fonction de l'environnement
def get_db(env: str = "prod"):
    engine = get_engine(env)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    if env == "prod":
        Base.metadata.create_all(bind=engine)
    try:
        yield db
    finally:
        db.close()

# Définition d'un modèle de données pour un client dans la base de données
Base = declarative_base()

class Client(Base):
    __tablename__ = "client"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    quantity = Column(Integer, index=True)

# Création d'un modèle pydantic pour la création de client
class ClientCreate(BaseModel):
    name: str
    quantity: int

# Création d'un modèle pydantic pour la réponse de client
class ClientResponse(ClientCreate):
    id: int

    class Config:
        orm_mode = True

# Définir des métriques Prometheus
REQUEST_TIME = Summary('request_processing_seconds', 'Time spent processing request')
REQUEST_COUNT = Counter('request_count', 'Total count of requests')

# Middleware pour mesurer le temps de traitement des requêtes
@app.middleware("http")
async def add_prometheus_metrics(request: Request, call_next):
    with REQUEST_TIME.time():
        response = await call_next(request)
        REQUEST_COUNT.inc()
    return response

# Route pour exposer les métriques
@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

def connect_rabbitmq():
    try:
        parameters = pika.ConnectionParameters(RABBITMQ_HOST)
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue=RABBITMQ_QUEUE)
        return channel
    except pika.exceptions.AMQPConnectionError as e:
        logger.error(f"Failed to connect to RabbitMQ: {e}")
        raise HTTPException(status_code=500, detail="Could not connect to RabbitMQ")


# Route POST pour créer un nouveau client dans l'API
@app.post("/clients/create", response_model=ClientResponse)
async def create_client(client: ClientCreate, db: Session = Depends(get_db)):
    db_client = Client(name=client.name, quantity=client.quantity)
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    if os.getenv("ENV") == "prod":
        try:
            # Envoyer un message à RabbitMQ
            channel = connect_rabbitmq()
            message = f"Client créé: {client.name} avec quantité: {client.quantity}"
            channel.basic_publish(exchange='', routing_key=RABBITMQ_QUEUE, body=message)
            channel.close()
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du message RabbitMQ : {e}")
            raise HTTPException(status_code=500, detail="Erreur interne du serveur")

    return db_client

# Route GET pour voir tous les clients
@app.get("/clients/all", response_model=List[ClientResponse])
async def read_clients(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    clients = db.query(Client).offset(skip).limit(limit).all()
    return clients

# Route DELETE pour supprimer un client par son id
@app.delete("/clients/{client_id}")
async def delete_client(client_id: int, db: Session = Depends(get_db)):
    db_client = db.query(Client).filter(Client.id == client_id).first()
    if db_client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    db.delete(db_client)
    db.commit()
    return {"detail": "Client deleted"}

# Route GET pour voir un client spécifique par son id
@app.get("/client/{client_id}", response_model=ClientResponse)
async def read_specific_client(client_id: int, db: Session = Depends(get_db)):
    db_client = db.query(Client).filter(Client.id == client_id).first()
    if db_client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return db_client

