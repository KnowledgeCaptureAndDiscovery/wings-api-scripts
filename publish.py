import json
import argparse
import os

import wings.planner
import wings.component
import mint.gather
import logging
import requests
import configparser
import csv


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
parser.add_argument(
    "-s",
    "--server",
    default="default",
    help="Server configuration (it must exist in the configfile)")
args = parser.parse_args()


'''
read configuration
'''
config = configparser.ConfigParser()
config.read('config.ini')

if args.server not in config:
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

def get_sparql_info(execution):
    headers = {
        'Accept': 'application/sparql-results+json',
    }

    query = '''
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX provModel: <http://openprovenance.org/model/opmo#>
PREFIX opmw: <https://www.opmw.org/ontology/>
SELECT DISTINCT ?filename ?unique ?location ?workflow from <''' + execution + '''> {
?param a opmw:WorkflowExecutionArtifact ;
    rdfs:label "unique_id";
    provModel:account ?workflow; 
    opmw:hasValue ?unique .
?file provModel:account ?workflow;
    rdfs:label ?filename; 
    opmw:hasLocation ?location .   
}'''

    data = {
        'query': query
    }

    response = requests.post('https://endpoint.mint.isi.edu/provenance/sparql', headers=headers, data=data)
    return response


def prepare_files(json_response):
    try:
        print("Writing file " + execution_id)

        unique = json_response['results']['bindings'][0]['unique']['value']
        filename_unique = "csv/" + unique + '.csv'
        if os.path.exists(filename_unique):
            print("Skipping file " + execution_id)
            return

        with open(filename_unique, mode='w') as csv_file:
            fs = {}
            fieldnames = ['id', 'filename', 'location']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            for i in json_response['results']['bindings']:
                filename = (i["filename"]["value"])
                #hack1: remove new line
                location = (i["location"]["value"]).replace("\n", "")
                #hack2: avoid duplicate link
                if not filename in fs.keys():
                    fs[filename] = True
                else:
                    continue
                writer.writerow({'id': unique, 'filename': filename, 'location': location})
    except:
        print("Error")

if __name__ == "__main__":
    wingsExecution = wings.Execution(
        serverWings,
        exportWingsURL,
        userWings,
        domainWings)
    if not wingsExecution.login(passwordWings):
        logger.error("Login failed")
        exit(1)
    executions = wingsExecution.list_executions().json()
    for execution in executions:
        if execution["runtimeInfo"]["status"] == "SUCCESS":
            execution_id = execution["id"]
            print("Exporting " + execution_id)
            publish_output = wingsExecution.publish(execution_id).json()
            if publish_output["url"]:
                output = get_sparql_info(publish_output["url"])
                prepare_files(output.json())
            else:
                print("Error")
