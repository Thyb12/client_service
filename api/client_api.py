import os
from fastapi import FastAPI, HTTPException, Depends, Request, Response
from pydantic import BaseModel
from typing import List
<<<<<<< HEAD
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from prometheus_client import Summary, Counter, generate_latest, CONTENT_TYPE_LATEST
import pika
import logging
from datetime import datetime
=======
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
from prometheus_client import Summary, Counter, generate_latest, CONTENT_TYPE_LATEST
import pika
import logging
from datetime import datetime, timedelta
>>>>>>> origin/main

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

<<<<<<< HEAD
class Address(Base):
    __tablename__ = "address"
    id = Column(Integer, primary_key=True)
    postalCode = Column(String)
    city = Column(String)
    client_id = Column(Integer, ForeignKey('client.id'))

class Commande(Base):
    __tablename__ = "commande"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('client.id'))
    details = Column(String)

class Client(Base):
    __tablename__ = "client"
    id = Column(Integer, primary_key=True, index=True)
    createdAt = Column(DateTime, default=datetime.utcnow)
    name = Column(String, index=True)
    username = Column(String, index=True)
    firstName = Column(String)
    lastName = Column(String)
    companyName = Column(String)
    address = relationship("Address", backref="client", uselist=False)
    commandes = relationship("Commande", backref="client")
=======
class Client(Base):
    __tablename__ = "client"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    createdAt = Column(DateTime(timezone=True), server_default=func.now())
    adresse = Column(String)
>>>>>>> origin/main

# Création d'un modèle pydantic pour la création de client
class ClientCreate(BaseModel):
    name: str
<<<<<<< HEAD
    username: str
    firstName: str
    lastName: str
    companyName: str
    postalCode: str
    city: str
=======
>>>>>>> origin/main

# Création d'un modèle pydantic pour la réponse de client
class ClientResponse(ClientCreate):
    id: int
<<<<<<< HEAD
    createdAt: datetime
=======
>>>>>>> origin/main

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

<<<<<<< HEAD
# Route POST pour créer un nouveau client dans l'API
@app.post("/clients/create", response_model=ClientResponse)
async def create_client(client: ClientCreate, db: Session = Depends(get_db)):
    db_client = Client(name=client.name, username=client.username, firstName=client.firstName, lastName=client.lastName, companyName=client.companyName)
    db_address = Address(postalCode=client.postalCode, city=client.city, client=db_client)
    db.add(db_client)
    db.add(db_address)
=======
failed_attempts = {}

# Fonction pour vérifier et limiter les tentatives de connexion
def rate_limiting(ip_address: str):
    now = datetime.now()
    if ip_address in failed_attempts:
        attempt_info = failed_attempts[ip_address]
        last_attempt_time = attempt_info["timestamp"]
        attempts = attempt_info["count"]
        logger.info(f"IP {ip_address}: {attempts} attempts, last attempt at {last_attempt_time}")
        # Si moins de 60 secondes depuis la dernière tentative, augmenter le compteur de tentatives
        if now - last_attempt_time < timedelta(seconds=60):
            attempts += 1
            failed_attempts[ip_address] = {"count": attempts, "timestamp": now}
            # Si plus de 5 tentatives dans les 60 secondes, déclencher la limitation
            if attempts > 5:
                raise HTTPException(status_code=429, detail="Too many requests. Try again later.")
        else:
            # Réinitialiser après 60 secondes
            failed_attempts[ip_address] = {"count": 1, "timestamp": now}
    else:
        failed_attempts[ip_address] = {"count": 1, "timestamp": now}
    logger.info(f"IP {ip_address}: allowed")


# Route POST pour créer un nouveau client dans l'API
@app.post("/clients/create", response_model=ClientResponse)
async def create_client(request: Request, client: ClientCreate, db: Session = Depends(get_db)):
    client_ip = request.client.host
    rate_limiting(client_ip)  # Limiter les tentatives de connexion par adresse IP

    db_client = Client(name=client.name, adresse="", )
    db.add(db_client)
>>>>>>> origin/main
    db.commit()
    db.refresh(db_client)
    if os.getenv("ENV") == "prod":
        try:
            # Envoyer un message à RabbitMQ
            channel = connect_rabbitmq()
<<<<<<< HEAD
            message = f"Client créé: {client.name} avec adresse: {client.city}, {client.postalCode}"
=======
            message = f"Client créé: {client.name}"
>>>>>>> origin/main
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
<<<<<<< HEAD
async def delete_client(client_id: int, db: Session = Depends(get_db)):
=======
async def delete_client(request: Request, client_id: int, db: Session = Depends(get_db)):
    client_ip = request.client.host
    rate_limiting(client_ip)  # Limiter les tentatives de connexion par adresse IP

>>>>>>> origin/main
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
<<<<<<< HEAD
=======

>>>>>>> origin/main
