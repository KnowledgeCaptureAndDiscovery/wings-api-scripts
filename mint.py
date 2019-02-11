import re
import json
import argparse
import wings.planner
import wings.component
import mint.gather
import logging
import requests
import shutil

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

serverMint      = 'http://ontosoft.isi.edu:8001/api/KnowledgeCaptureAndDiscovery/MINT-ModelCatalogQueries'
serverWings     = "http://ontosoft.isi.edu:7072/wings-portal"
exportWingsURL  = "http://localhost:8080/wings-portal"
userIdWings      = "admin"
passwordWings    = "4dm1n!23"
domainWings      = "CaesarCypher"
endpointMint = 'http://ontosoft.isi.edu:3030/ds/query'

def createDataWings(datatypes, parent_type, wings):
    for data_type, value in datatypes.items():
        logger.debug("Creating data %s", data_type)
        wings.new_data_type(data_type, parent_type)

def exists(json, key):
    if key in json:
        return json[key]
    else:
        return ''

def generateData(instance, wingsData, data_type_id):
    jsonRequest = {}
    jsonRequest['inputs'] = []
    jsonRequest['outputs'] = []
    data_type_id = wingsData.new_data_type(data_type_name, None)
    description = mint.describeURI(instance)
    jsonRequest['rulesText'] = exists(description, 'hasRule')
    jsonRequest['documentation'] = exists(description, 'description')
    jsonRequest = mint.prepareParameters(instance, jsonRequest)
    
    jsonRequest, datatypes = mint.prepareInputOutput(instance, data_type_id, jsonRequest, wingsData.dcdom)
    createDataWings(datatypes, instance_name, wingsData)
    return jsonRequest


def downloadFile(url):
    local_filename = url.split('/')[-1]
    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        shutil.copyfileobj(r.raw, f)
    return local_filename

def uploadComponent(instance):
    description = mint.describeURI(instance)
    url = exists(description, 'hasComponentLocation')
    if url:
        return downloadFile(url)
    return None

if __name__ == "__main__":
    mint = mint.Gather(serverMint, endpointMint)
    wingsData = wings.ManageData(serverWings, exportWingsURL, userIdWings, domainWings)
    wingsComponent = wings.ManageComponent(serverWings, exportWingsURL, userIdWings, domainWings)
    if not wingsData.login(passwordWings):
        print("fail logging")
        exit(1)
    wingsComponent.session = wingsData.session

    instance = 'https://w3id.org/mint/instance/pihm'
    instance_name = instance.split('/')[-1]
    data_type_name = instance_name
    component_id = instance_name
    component_type = component_id.capitalize()
    parent_type = None


    componentJSON = generateData(instance, wingsData, data_type_name)
    uploadDataPath = uploadComponent(instance)
    wingsComponent.new_component_type(component_type, parent_type)
    wingsComponent.new_component(component_id, component_type)
    wingsComponent.save_component(component_id, componentJSON)
    if uploadDataPath:
        logger.info("Uploading zip file for %s", instance)
        wingsComponent.upload(uploadDataPath, component_id)
    