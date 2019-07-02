import json
import argparse
import os

import wings.component
import logging
import requests
import configparser
import csv
import concurrent.futures


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


def write_csv_file(json_response, execution_id):
    '''

    @param json_response:
    @type json_response:
    @param execution_id:
    @type execution_id:
    @return:
    @rtype:
    '''
    try:
        unique = json_response['results']['bindings'][0]['unique']['value']
        filename_unique = "csv/" + unique + '.csv'
        if os.path.exists(filename_unique):
            logger.info("skipping {}, the file exists".format(execution_id))
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
    except Exception as error:
        logger.error("error {} \n {}".format(execution_id, error))


def publisher_execution(execution_selected):
    execution_id = execution_selected["id"]
    logger.info("publishing {}".format(execution_id))
    publish_output = wingsExecution.publish(execution_id).json()
    if publish_output["url"]:
        output = get_sparql_info(publish_output["url"])
        write_csv_file(output.json(), execution_id)
    else:
        print("Error")

'''
read configuration
'''
config = configparser.ConfigParser()
config.read('config.ini')

if args.server not in config:
    logger.error("Server configuration does not exist")
    exit(1)


config_selected = config['default']
serverMint = config_selected['serverMint']
serverWings = config_selected['serverWings']
exportWingsURL = config_selected['exportWingsURL']
userWings = config_selected['userWings']
passwordWings = config_selected['passwordWings']
domainWings = config_selected['domainWings']
endpointMint = config_selected['endpointMint']

logger.info("Server mint: %s", serverMint)
logger.info("Server wings: %s", serverWings)

logger.info("Export wings url: %s", exportWingsURL)
logger.info("User wings: %s", userWings)
logger.info("Domain wings: %s", domainWings)
logger.info("Endpoint mint: %s", endpointMint)



if __name__ == "__main__":
    wingsExecution = wings.Execution(
        serverWings,
        exportWingsURL,
        userWings,
        domainWings)
    if not wingsExecution.login(passwordWings):
        logger.error("Login failed")
        exit(1)
    pattern = "cycles"
    executions = wingsExecution.list_executions(pattern=pattern, done=True).json()
    logger.info("{} executions matches with the pattern {}".format(len(executions), pattern))

    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        for execution in executions:
            executor.submit(publisher_execution, execution)
