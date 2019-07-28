import json
import argparse
import os

import wings.component
import logging
import requests
import configparser
import csv
import concurrent.futures
import urllib.parse

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


def show_failed(execution_selected):
    logger.info("publishing {}".format(execution_selected))


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


def write_csv_file(filename, list_dict):
    '''

    @param json_response:
    @type json_response:
    @param execution_id:
    @type execution_id:
    @return:
    @rtype:
    '''
    try:
        filename_unique = "csv/" + filename + '.csv'
        with open(filename_unique, mode='w') as csv_file:
            fs = {}
            fieldnames = ['id', 'link']
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            for dict in list_dict:
                writer.writerow(dict)
    except Exception as error:
        logger.error("error write the file {} \n {}".format(filename, error))


def details_files(files):
    all_files = []
    for input in files:
        if "datatype" in input['binding'].keys():
            logger.info("ignore parameter")
        else:
            execution_file = {}
            id_file = input['id']
            download_file = input['binding']['id']
            prefix_link = "https://wings.mint.isi.edu/users/mint/MINT-production/data/fetch?data_id="
            download_link = prefix_link + urllib.parse.quote(download_file)
            execution_file["id"] = id_file.split('#')[-1]
            execution_file["link"] = download_link
            all_files.append(execution_file)

    return all_files


def download_files(inputs_links, execution_name, session, pattern):
    logger.info("Downloading the file for the pattern {} ".format(pattern))
    all_files = []
    dst = 'files/{}/{}'.format(pattern, execution_name)
    os.mkdir(dst)
    for i in inputs_links:
        logger.info("Downloading file {} {}".format(pattern, i["id"]))
        dst_file = '{}/{}'.format(dst, i["id"])
        r = session.get(i["link"], allow_redirects=True)
        open(dst_file, 'wb').write(r.content)

    return all_files

def run(execution, pattern):
    if execution["runtimeInfo"]["status"] == "SUCCESS":
        execution_id = execution["id"]
        execution_name = execution_id.split('#')[-1]
        execution_details = wingsExecution.get_run_details(execution_id).json()
        variables = execution_details["variables"]
        inputs = variables["input"] + variables["output"]

        inputs_links = details_files(inputs)
        write_csv_file(execution_name, inputs_links)
        download_files(inputs_links, execution_name, wingsExecution.session, pattern)

if __name__ == "__main__":
    wingsExecution = wings.Execution(
        serverWings,
        exportWingsURL,
        userWings,
        domainWings)
    if not wingsExecution.login(passwordWings):
        logger.error("Login failed")
        exit(1)
    pattern = "economic"
    executions = wingsExecution.list_executions(pattern=pattern).json()
    executions_done = wingsExecution.list_executions(pattern=pattern, done=True).json()

    logger.info("{} executions matches with the pattern {}".format(len(executions), pattern))
    logger.info("{} executions matches with the pattern {} and successful".format(len(executions_done), pattern))


    #Tuesday, July 2, 2019 10:30:00 AM GMT-07:00
    start_time_pattern = 1562131800
    for execution in executions:
        status = execution["runtimeInfo"]["status"]
        start_time = execution["runtimeInfo"]["startTime"]
        if execution["runtimeInfo"]["status"] == "SUCCESS" and (start_time > start_time_pattern):
            print(execution)
            #run(execution, pattern)

    # with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
    #     for execution in executions:
    #         executor.submit(run, execution, pattern)



    # for execution in executions:
    #     if execution["runtimeInfo"]["status"] == "SUCCESS":
    #         execution_id = execution["id"]
    #         execution_name = execution_id.split('#')[-1]
    #         execution_details = wingsExecution.get_run_details(execution_id).json()
    #         variables = execution_details["variables"]
    #         inputs = variables["input"]
    #         inputs_links = details_files(inputs)
    #         write_csv_file(execution_name, inputs_links)
    #         download_files(inputs_links, execution_name, wingsExecution.session, pattern)
    exit(1)
