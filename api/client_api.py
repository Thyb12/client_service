import os
from fastapi import FastAPI, HTTPException, Depends, Request, Response
from pydantic import BaseModel
from typing import List
from pymongo import MongoClient
from bson import ObjectId
from prometheus_client import Summary, Counter, generate_latest, CONTENT_TYPE_LATEST
import pika
import logging
from datetime import datetime

logger = logging.getLogger("uvicorn.error")

# Création de l'instance FastAPI pour initialiser l'application et permettre la définition des routes.
app = FastAPI()

# Configuration et mise en place de la connexion à la base de données avec MongoDB
MONGODB_URL = "mongodb://localhost:27017"
DATABASE_NAME = "MSPR_1"
CLIENT_COLLECTION_NAME = "clients"
ADDRESS_COLLECTION_NAME = "addresses"
COMMANDE_COLLECTION_NAME = "commandes"
RABBITMQ_HOST = "localhost"
RABBITMQ_QUEUE = "client_queue"

client = MongoClient(MONGODB_URL)
db = client[DATABASE_NAME]
client_collection = db[CLIENT_COLLECTION_NAME]
address_collection = db[ADDRESS_COLLECTION_NAME]
commande_collection = db[COMMANDE_COLLECTION_NAME]

# Création d'un modèle pydantic pour la création de client
class ClientCreate(BaseModel):
    name: str
    username: str
    firstName: str
    lastName: str
    companyName: str
    postalCode: str
    city: str

# Création d'un modèle pydantic pour la réponse de client
class ClientResponse(ClientCreate):
    id: str
    createdAt: datetime

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
async def create_client(client: ClientCreate):
    client_data = client.dict()
    client_data["createdAt"] = datetime.utcnow()
    result = client_collection.insert_one(client_data)
    client_data["id"] = str(result.inserted_id)

    address_data = {
        "client_id": client_data["id"],
        "postalCode": client.postalCode,
        "city": client.city
    }
    address_collection.insert_one(address_data)

    if os.getenv("ENV") == "prod":
        try:
            # Envoyer un message à RabbitMQ
            channel = connect_rabbitmq()
            message = f"Client créé: {client.name} avec adresse: {client.city}, {client.postalCode}"
            channel.basic_publish(exchange='', routing_key=RABBITMQ_QUEUE, body=message)
            channel.close()
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du message RabbitMQ : {e}")
            raise HTTPException(status_code=500, detail="Erreur interne du serveur")

    return client_data

# Route GET pour voir tous les clients
@app.get("/clients/all", response_model=List[ClientResponse])
async def read_clients(skip: int = 0, limit: int = 10):
    clients = list(client_collection.find().skip(skip).limit(limit))
    for client in clients:
        client["id"] = str(client["_id"])
        del client["_id"]
    return clients

# Route DELETE pour supprimer un client par son id
@app.delete("/clients/{client_id}")
async def delete_client(client_id: str):
    result = client_collection.delete_one({"_id": ObjectId(client_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Client not found")
    address_collection.delete_many({"client_id": client_id})
    commande_collection.delete_many({"client_id": client_id})
    return {"detail": "Client deleted"}

# Route GET pour voir un client spécifique par son id
@app.get("/client/{client_id}", response_model=ClientResponse)
async def read_specific_client(client_id: str):
    client = client_collection.find_one({"_id": ObjectId(client_id)})
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    client["id"] = str(client["_id"])
    del client["_id"]
    return client

# Route PUT pour modifier un client par son id
@app.put("/clients/{client_id}", response_model=ClientResponse)
async def update_client(client_id: str, client: ClientCreate):
    update_data = client.dict()
    result = client_collection.update_one({"_id": ObjectId(client_id)}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Client not found")

    address_data = {
        "postalCode": client.postalCode,
        "city": client.city
    }
    address_collection.update_one({"client_id": client_id}, {"$set": address_data})

    client = client_collection.find_one({"_id": ObjectId(client_id)})
    client["id"] = str(client["_id"])
    del client["_id"]
    return client