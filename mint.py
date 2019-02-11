import re
import json
import argparse
import wings.planner
import wings.component
import mint.gather
import logging
import requests
import shutil
import configparser

'''
logging
'''
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

'''
read configuration
'''
config = configparser.ConfigParser()
config.read('config.ini')
serverMint = config['datascience']['serverMint']
serverWings = config['datascience']['serverWings']
exportWingsURL = config['datascience']['exportWingsURL']
userWings = config['datascience']['userWings']
passwordWings = config['datascience']['passwordWings']
domainWings = config['datascience']['domainWings']
endpointMint = config['datascience']['endpointMint']

'''
parse resource
'''
parser = argparse.ArgumentParser()
parser.add_argument("-r", "--resource", help="Resource URI")


def createDataWings(datatypes, parent_type, wings):
    for data_type, value in datatypes.items():
        logger.debug("Creating data %s", data_type)
        wings.new_data_type(data_type, parent_type)


def exists(json, key):
    if key in json:
        return json[key]
    else:
        return None


def generateData(resource, wingsData, data_type_id):
    jsonRequest = {}
    jsonRequest['inputs'] = []
    jsonRequest['outputs'] = []
    data_type_id = wingsData.new_data_type(data_type_name, None)
    description = mint.describeURI(resource)
    jsonRequest['rulesText'] = exists(description, 'hasRule')
    jsonRequest['documentation'] = exists(description, 'description')
    jsonRequest = mint.prepareParameters(resource, jsonRequest)

    jsonRequest, datatypes = mint.prepareInputOutput(
        resource, data_type_id, jsonRequest, wingsData.dcdom)
    createDataWings(datatypes, resource_name, wingsData)
    return jsonRequest


def downloadFile(url):
    local_filename = url.split('/')[-1]
    r = requests.get(url, stream=True)
    with open(local_filename, 'wb') as f:
        shutil.copyfileobj(r.raw, f)
    return local_filename


def uploadComponent(resource):
    description = mint.describeURI(resource)
    url = exists(description, 'hasComponentLocation')
    if url:
        return downloadFile(url)
    return None


def createComponent(resource, wingsData, wingsComponent,
                    data_type_name, component_type, component_id):
    componentJSON = generateData(resource, wingsData, data_type_name)
    uploadDataPath = uploadComponent(resource)
    wingsComponent.new_component_type(component_type, parent_type)
    wingsComponent.new_component(component_id, component_type)
    wingsComponent.save_component(component_id, componentJSON)
    if uploadDataPath:
        wingsComponent.upload(uploadDataPath, component_id)
    else:
        logger.info("Zip file is missing %s", resource)


if __name__ == "__main__":
    args = parser.parse_args()
    # todo: check if it is a ModelConfiguration
    mint = mint.Gather(serverMint, endpointMint)
    wingsData = wings.ManageData(
        serverWings,
        exportWingsURL,
        userWings,
        domainWings)
    wingsComponent = wings.ManageComponent(
        serverWings, exportWingsURL, userWings, domainWings)
    if not wingsData.login(passwordWings):
        logger.error("Login failed")
        exit(1)
    wingsComponent.session = wingsData.session

    resource = args.resource
    resource_name = resource.split('/')[-1]
    data_type_name = resource_name
    component_id = resource_name
    component_type = component_id.capitalize()
    parent_type = None
    createComponent(
        resource,
        wingsData,
        wingsComponent,
        data_type_name,
        component_type,
        component_id)
