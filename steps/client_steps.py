import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from behave import given, when, then
from api.client_api import create_client, read_clients, delete_client, read_specific_client
from unittest.mock import patch

# Configuration de la base de données en fonction de la variable d'environnement ENV
if os.environ.get("ENV") == "test":
    DATABASE_URL = "sqlite:///./test_db.sqlite"
else:
    DATABASE_URL = "sqlite:///./client_api.db"

# Créez une session de base de données
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Initialisez la session de base de données pour les tests
@pytest.fixture(scope="function")
def db():
    db = SessionLocal()
    yield db
    db.close()

<<<<<<< HEAD
@given('je crée un client avec le nom "{name}" et la quantité {quantity:d}')
async def create_product(context, name, quantity):
    client_data = {"name": name, "quantity": quantity}
=======
@given('je crée un client avec le nom "{name}"')
async def create_product(context, name):
    client_data = {"name": name}
>>>>>>> origin/main
    context.client_created = await create_client(client_data, db())


@then('je récupère tous les clients')
async def get_all_products(context):
    context.clients = await read_clients(db())

@when('je supprime le client avec l\'ID {product_id:d}')
async def delete_product(context, product_id):
    await delete_client(product_id, db())


@then('le client est créé')
def check_product_created(context):
    assert read_clients().__sizeof__() > 0

@then('je reçois une liste de clients')
async def check_products_received(context):
    reponse = await read_clients(db())
    assert reponse == context.clients

@then('le client est supprimé avec succès')
async def check_product_deleted(context):
    assert await delete_client(context.clients[0], db()) is not None
@then('je reçois le client spécifique avec l\'ID {product_id:d}')
async def check_specific_product_received(context, product_id):
    assert read_specific_client(product_id) == context.clients[0]

<<<<<<< HEAD
@then('un message RabbitMQ est envoyé avec les détails du client "{name} {quantity}')
@patch('api.client_api.connect_rabbitmq')
async def check_rabbitmq_message_sent(mock_connect_rabbitmq, name, quantity):
    mock_channel = mock_connect_rabbitmq.return_value
    mock_channel.basic_get.return_value = (None, None, f"client créé: {name} avec quantité: {quantity}".encode('utf-8'))

    await create_client( client={"name": name, "quantity": quantity}, db=db())

    mock_connect_rabbitmq.assert_called_once()
    mock_channel.basic_publish.assert_called_once_with(exchange='', routing_key='client_queue', body=f"client créé: {name} avec quantité: {context.client_created.quantity}")
=======
@then('un message RabbitMQ est envoyé avec les détails du client "{name}')
@patch('api.client_api.connect_rabbitmq')
async def check_rabbitmq_message_sent(mock_connect_rabbitmq, name):
    mock_channel = mock_connect_rabbitmq.return_value
    mock_channel.basic_get.return_value = (None, None, f"client créé: {name}".encode('utf-8'))

    await create_client( client={"name": name}, db=db())

    mock_connect_rabbitmq.assert_called_once()
    mock_channel.basic_publish.assert_called_once_with(exchange='', routing_key='client_queue', body=f"client créé: {name}")
>>>>>>> origin/main
