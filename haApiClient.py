#! /usr/bin/python3
from requests import get
import json
from urllib.parse import urljoin 
from rich import print
import time
import configparser
import os

# Class used to interact directly with the API
class HaApiClient:
    #Initialise the class
    def __init__(self,uri="",apiKey=""):
        self.uri = uri
        # Headers are used for authentication
        self.headers = {}
        self.headers["Authorization"] = f"Bearer {apiKey}"
        self.headers["content-type"] = "application/json"
        # Store returned data in these variables
        self.data = {}
        self.response = {}
        # Address at the server to provide details about entities and states
        self.getStatesEndpoint = 'api/states'
        # Store response code and JSON from the API
        self.responseCode = None
        self.responseJson = None

    # Function the get data from an API endpoint
    def getRequest(self,endpoint):
        response = get(endpoint, headers=self.headers)
        self.response = response
        self.responseCode = response.status_code
        if response.status_code >= 200 and response.status_code < 400:
            self.responseJson = json.loads(response.text)
    
    # Function to get a list of endtityIds from the API 
    def getStates(self):
        endpoint = '/'.join([self.uri,self.getStatesEndpoint])
        self.getRequest(endpoint)

    # Function to return the entityIds in a more usable form
    def returnStates(self):
        self.getStates()
        return self.responseCode, self.responseJson
    
    # Function to get the state of an entity from the API
    def getState(self,entity_id):
        endpoint = "/".join([self.uri, self.getStatesEndpoint, entity_id])
        self.getRequest(endpoint)

    # Function to return the state of an entity in a more usable form
    def returnState(self, entity_id):
        self.getState(entity_id)
        return self.responseCode, self.responseJson

# Define a class to essentially format data in a more usable way and provide a way of centrally holding entityIds if more than one instance is defined
class HaEntityStatus():
    #Class variables to store all entities and entityIds
    entities = {}
    entitiesList = []
    # Initialise the function
    def __init__(self,uri,apiKey, entity_id = ""):
        # Instance variables to store URI, APIKey and entity to query
        self.uri = uri
        self.apiKey = apiKey
        self.entity = entity_id
        # Variable to store return code after data is requested
        self.returnCode = 0

    # Function to read all entities from the API and format data
    def readAllEntities(self):
        apiCall = HaApiClient(uri = self.uri, apiKey = self.apiKey)
        entities = apiCall.returnStates()
        self.responseCode = apiCall.responseCode
        # Make sure the return code shows success before going further
        if entities[0] == 200 or entities[0] == 201:
            # Add entities to a class variable to allow all instances to refer to the data
            HaEntityStatus.entities = entities[1]
            #Now return a list of just the entity IDs and store in a class variable
            for entity in entities[1]:
                HaEntityStatus.entitiesList.append(entity["entity_id"])
    
    # Request the state of a single entityId and return if possible
    def readEntity(self, entity_id = ""):
        if self.entity == "":
            self.entity = entity_id

        #Check to see if the entity_id exists in the list of entities
        if self.entity in HaEntityStatus.entitiesList:
            apiCall = HaApiClient(uri = self.uri, apiKey = self.apiKey)
            entity = apiCall.returnState(self.entity)
            # Format the data accordingly, based on success or failure from the API
            if entity[0] == 200 or entity[0] == 201:
                return {"responseCode":entity[0], "responseJson": entity[1]}
            if entity[0] > 201:
                return {"responseCode":entity[0], "responseJson": {}}
        else:
            print("Entity does not exist")

# Only run the code if called directly
if __name__ == '__main__':

    # Variables to hold the URI and API keys
    uri = None
    apiKey = None

    # Use the configparser library to read data from a config file, if it exists
    configFile = "haApiConfig.conf"
    configFilePath = os.path.join(os.path.dirname(__file__), configFile)
    config = configparser.ConfigParser()

    if os.path.exists(configFilePath):
        config.read(configFilePath)
        if "Server" in config and "Address" in config["Server"]:
            uri = config["Server"]["Address"]
        if "Server" in config and "ApiKey" in config["Server"]:
            apiKey = config["Server"]["ApiKey"]
    else:
        print("Config file does not exist or is incorrectly formatted! You will be asked to enter details next...")

    # If the config file does not exist or is incorrectly formatted, request the user to enter the URI and / or API Key
    if uri == None:
        uri = input("Please enter your server address, including http:// or https:// at the start and the port")
    if apiKey == None:
        apiKey = input("Please enter your API key")

    # Request all entities from the API
    allEntities = HaEntityStatus(uri, apiKey)
    allEntities.readAllEntities()
    entitiesJson = allEntities.entities

    # Sort the returned data 
    entitiesJson = sorted(entitiesJson, key=lambda x:x['entity_id'])

    # Print a list of all of the entities of type sensor along with a number that can be used to refer to them
    counter = 0
    for entity in entitiesJson:
        if entity["entity_id"][0:7] == 'sensor.':
            print(counter, entity["entity_id"])
        counter += 1

    # Create a list to store any items that we want to check
    entityObjects = []
    entityList = []
    # Use a while loop to query the user for any entities they want to check. When Q is pressed, move on
    carryOn = True
    while carryOn:
        # Request a number to be entered
        a = input("Enter entity id number. (Enter q to finish entering list to check) ")
        if a == "q":
            carryOn = False
            break
        # Add the number entered to the entity list and create a reference to an instance of the HaEntityStatus class that can be called multiple times to return new data
        try:
            entityList.append(int(a))
            entityObjects.append(HaEntityStatus(uri, apiKey, entity_id=entitiesJson[int(a)]['entity_id']))
        except:
            print("Please try again")

    # Now, each time the loop runs, iterate through our list of entity IDs and HaEntityStatus items and return an updated number. Finally, sleep for ten seconds before repeating
    while 1:
        # Now print the entries
        for entityObject in entityObjects:
            response = entityObject.readEntity()
            print(response["responseCode"], response["responseJson"]["attributes"]["friendly_name"], response["responseJson"]["state"])
        time.sleep(10)