Feature: Gestion des clients dans l'API

  Scenario: Créer un nouveau client
    Given je crée un client avec le nom "1client" et la quantité 10
    Then le client est créé

  Scenario: Récupérer tous les clients
    Given je crée un client avec le nom "2client" et la quantité 10
    And je crée un client avec le nom "2.1client" et la quantité 10
    And je crée un client avec le nom "2.3client" et la quantité 10
    Then je reçois une liste de clients

  Scenario: Supprimer un client existant
    Given je crée un client avec le nom "3client" et la quantité 10
    When je supprime le client avec l'ID 1
    Then le client est supprimé avec succès

  Scenario: Récupérer un client spécifique par son ID
    Given je crée un client avec le nom "4client" et la quantité 10
    Then je reçois le client spécifique avec l'ID 1

  Scenario: Vérifier l'envoi d'un message RabbitMQ lors de la création d'un client
    Given je crée un client avec le nom "5client" et la quantité 10
    Then un message RabbitMQ est envoyé avec les détails du client "5client" 10
