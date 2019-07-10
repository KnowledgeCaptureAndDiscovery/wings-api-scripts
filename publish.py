import argparse
import concurrent.futures
import configparser
import csv
import logging
import time

import wings.component

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

config = configparser.ConfigParser()
config.read('config.ini')
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


def publish_page(execution):
    '''
    Publish the execution
    @param execution: the object returned by wings
    @type execution: string
    @return:
    @rtype:
    '''
    execution_id = execution["id"]
    execution_start = execution["runtimeInfo"]["startTime"]
    if execution_start:
        execution_start_time = time.ctime(execution_start)
    publish_output = wingsExecution.publish(execution_id).json()
    if "url" in publish_output.keys():
        logger.info("Published {} - {} ".format(execution_id, execution_start_time))
    else:
        logger.error("Unable to publish {}  - {}".format(execution_id, execution_start_time))



if args.server not in config:
    logger.error("Server configuration does not exist")
    exit(1)

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
    status = "SUCCESS"
    executions_resp = wingsExecution.list_executions_by_page(0, pattern=pattern, status=status).json()
    executions = executions_resp["rows"]
    logger.warning("{} executions matches with the pattern {}".format(len(executions), pattern))

    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        for execution in executions:
            submit = executor.submit(publish_page, execution)
            try:
                submit.result()
            except TypeError as e:
                print(e)


