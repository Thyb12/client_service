Feature: Gestion des clients dans l'API

  Scenario: Créer un nouveau client
    Given je crée un client avec le nom "1client"
    Then le client est créé

  Scenario: Récupérer tous les clients
    Given je crée un client avec le nom "2client"
    And je crée un client avec le nom "2.1client"
    And je crée un client avec le nom "2.3client"
    Then je reçois une liste de clients

  Scenario: Supprimer un client existant
    Given je crée un client avec le nom "3client"
    When je supprime le client avec l'ID 1
    Then le client est supprimé avec succès

  Scenario: Récupérer un client spécifique par son ID
    Given je crée un client avec le nom "4client"
    Then je reçois le client spécifique avec l'ID 1

  Scenario: Vérifier l'envoi d'un message RabbitMQ lors de la création d'un client
    Given je crée un client avec le nom "5client"
    Then un message RabbitMQ est envoyé avec les détails du client "5client"
