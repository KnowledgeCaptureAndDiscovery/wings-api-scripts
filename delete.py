import json
import argparse
import os

import wings.component
import logging
import requests
import configparser
import csv
import concurrent.futures
from math import ceil

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



def delete_execution(execution_id):
    resp = wingsExecution.delete_run(execution_id).json()
    if resp["success"]:
        logger.info("delete execution {} success".format(execution_id))
    else:
        logger.error("delete execution {} failed".format(execution_id))


'''
read configuration
'''

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

    pattern = "cycles"
    status = "SUCCESS"
    executions_resp = wingsExecution.list_executions_by_page(0, pattern=pattern, status=status).json()
    executions = executions_resp["rows"]
    logger.warning("{} executions matches with the pattern {}".format(len(executions), pattern))

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        for execution in executions:
            execution_id = execution["id"]
            executor.submit(delete_execution, execution_id)


