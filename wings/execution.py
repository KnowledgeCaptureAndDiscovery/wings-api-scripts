import os

import requests

from .auth import Auth
from .userop import UserOperation


class Execution(UserOperation):

    def __init__(self, server, exportURL, userid, domain):
        super(Execution, self).__init__(server, exportURL, userid, domain)

    def check_request(self, resp):
        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err)
        except requests.exceptions.RequestException as err:
            print(err)
        return resp


    def list_executions(self):
        resp = self.session.get(self.get_request_url() + 'executions/getRunList')
        return self.check_request(resp)

    def publish(self, execution_id):
        postdata = {'run_id': execution_id}
        resp = self.session.post(self.get_request_url() + 'executions/publishRun', data=postdata)
        return self.check_request(resp)
