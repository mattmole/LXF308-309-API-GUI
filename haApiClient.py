#! /usr/bin/python3
from requests import get
import json
from urllib.parse import urljoin 
from rich import print
import time
import configparser
import os

class HaApiClient:
    def __init__(self,uri="",apiKey=""):
        self.uri = uri
        self.headers = {}
        self.headers["Authorization"] = f"Bearer {apiKey}"
        self.headers["content-type"] = "application/json"
        self.data = {}
        self.response = {}
        self.getStatesEndpoint = 'api/states'
        self.responseCode = None
        self.responseJson = None
    def getRequest(self,endpoint):
        response = get(endpoint, headers=self.headers)
        self.response = response
        self.responseCode = response.status_code
        if response.status_code >= 200 and response.status_code < 400:
            self.responseJson = json.loads(response.text)
    def getStates(self):
        endpoint = '/'.join([self.uri,self.getStatesEndpoint])
        self.getRequest(endpoint)
    def returnStates(self):
        self.getStates()
        return self.responseCode, self.responseJson
    def getState(self,entity_id):
        endpoint = "/".join([self.uri, self.getStatesEndpoint, entity_id])
        self.getRequest(endpoint)
    def returnState(self, entity_id):
        self.getState(entity_id)
        return self.responseCode, self.responseJson

class HaEntityStatus():
    entities = {}
    entitiesList = []
    def __init__(self,uri,apiKey, entity_id = ""):
        self.uri = uri
        self.apiKey = apiKey
        self.entity = entity_id
        self.returnCode = 0
    def readAllEntities(self):
        apiCall = HaApiClient(uri = self.uri, apiKey = self.apiKey)
        entities = apiCall.returnStates()
        self.responseCode = apiCall.responseCode
        if entities[0] == 200 or entities[0] == 201:
            HaEntityStatus.entities = entities[1]
            #Now return a list of just the entity IDs
            for entity in entities[1]:
                HaEntityStatus.entitiesList.append(entity["entity_id"])

    def readEntity(self, entity_id = ""):
        if self.entity == "":
            self.entity = entity_id

        #Check to see if the entity_id exists in the list of entities
        if self.entity in HaEntityStatus.entitiesList:
            apiCall = HaApiClient(uri = self.uri, apiKey = self.apiKey)
            entity = apiCall.returnState(self.entity)
            if entity[0] == 200 or entity[0] == 201:
                return {"responseCode":entity[0], "responseJson": entity[1]}
            if entity[0] > 201:
                return {"responseCode":entity[0], "responseJson": {}}
        else:
            print("Entity does not exist")

if __name__ == '__main__':

    uri = None
    apiKey = None

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

    if uri == None:
        uri = input("Please enter your server address, including http:// or https:// at the start and the port")
    if apiKey == None:
        apiKey = input("Please enter your API key")


    allEntities = HaEntityStatus(uri, apiKey)
    allEntities.readAllEntities()
    entitiesJson = allEntities.entities

    # Sort the returned data 
    entitiesJson = sorted(entitiesJson, key=lambda x:x['entity_id'])

    counter = 0
    for entity in entitiesJson:
        if entity["entity_id"][0:7] == 'sensor.':
            print(counter, entity["entity_id"])
        counter += 1

    entityObjects = []
    entityList = []
    carryOn = True
    while carryOn:
        a = input("Enter entity id. (Enter q to finish entering list to check) ")
        if a == "q":
            carryOn = False
            break
        try:
            entityList.append(int(a))
            entityObjects.append(HaEntityStatus(uri, apiKey, entity_id=entitiesJson[int(a)]['entity_id']))
        except:
            print("Please try again")
    print(entityList)

    while 1:
    #    # Now print the entries
        for entityObject in entityObjects:
            response = entityObject.readEntity()
            print(response["responseCode"], response["responseJson"]["attributes"]["friendly_name"], response["responseJson"]["state"])
        time.sleep(10)