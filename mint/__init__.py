from .gather import Gather

def check_request(self, resp):
    try:
        resp.raise_for_status()
    except requests.exceptions.HTTPError as err:
        print(err)   
    except requests.exceptions.RequestException as err:
        print(err)
    return resp