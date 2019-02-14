import json
import argparse
import wings.planner
import wings.component
import mint.gather
import logging
import requests
import shutil
import configparser
import tempfile

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
parse arguments
'''
parser = argparse.ArgumentParser()
parser.add_argument("-r", "--resource", help="Resource URI")
parser.add_argument("-s", "--server", default="default", help="Server configuration (it must exist in the configfile)")
args = parser.parse_args()



'''
read configuration
'''
config = configparser.ConfigParser()
config.read('config.ini')

if not args.server in config:
    logger.error("Server configuration does not exist")
    exit(1)

serverMint = config['default']['serverMint']
serverWings = config['default']['serverWings']
exportWingsURL = config['default']['exportWingsURL']
userWings = config['default']['userWings']
passwordWings = config['default']['passwordWings']
domainWings = config['default']['domainWings']
endpointMint = config['default']['endpointMint']

logger.info("Server mint: %s", serverMint)
logger.info("Server wings: %s", serverWings)

logger.info("Export wings url: %s", exportWingsURL)
logger.info("User wings: %s", userWings)
logger.info("Domain wings: %s", domainWings)
logger.info("Endpoint mint: %s", endpointMint)

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
    return componentJSON

if __name__ == "__main__":
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
    componentJSON = createComponent(
        resource,
        wingsData,
        wingsComponent,
        data_type_name,
        component_type,
        component_id)
    print(json.dumps(componentJSON))