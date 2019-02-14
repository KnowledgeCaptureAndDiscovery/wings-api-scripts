import requests
from urllib.parse import urlparse
import re

class Gather(object):
    def __init__(self, server, endpoint):
        self.session = requests.Session()
        self.server = server
        self.endpoint = endpoint
    
    def sanitize(self, resource):
        return re.sub(r"(^\d.+$)", r"_\1", resource)

    def check_request(self, resp):
        try:
            resp.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err)
        except requests.exceptions.RequestException as err:
            print(err)
        return resp

    def describeURI(self, resource):

        query = 'DESCRIBE <' + resource + '>'
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        payload = {'query': query, 'format': "application/ld+json"}
        resp = self.session.post(self.endpoint,
                                 headers=headers,
                                 data=payload
                                 )
        self.check_request(resp)
        return resp.json()

    def getParameters(self, instance):
        params = {'config': instance, 'endpoint': self.endpoint}
        resp = self.session.get(
            self.server +
            '/getConfigIParameters',
            params=params)
        self.check_request(resp)
        return resp.json()

    def prepareParameters(self, instance, jsonRequest):
        response = self.getParameters(instance)
        for idx, item in enumerate(response['results']['bindings']):
            param = {}
            param['role'] = item['paramlabel']['value']
            param['type'] = "xsd:%s" % (item['pdatatype']['value'])
            param['prefix'] = '-p%d' % (idx)
            param['id'] = item['p']['value']
            param['isParam'] = True
            param['paramDefaultValue'] = item['defaultvalue']['value']
            jsonRequest['inputs'].append(param)
        return jsonRequest

    def getInputOutput(self, instance):
        params = {'config': instance, 'endpoint': self.endpoint}
        resp = self.session.get(
            self.server +
            '/getConfigI_OVariablesAndStandardNames',
            params=params)
        self.check_request(resp)
        return resp.json()

    def prepareInputOutput(self, instance, data_type, jsonRequest, dcdom):
        response = self.getInputOutput(instance)
        selected = {}

        for idx, item in enumerate(response['results']['bindings']):
            if item['iolabel']['value'] in selected:
                continue
            io = {}
            label =  self.sanitize(item['iolabel']['value'])
            typeV =  self.sanitize(item['type']['value'])
            io['role'] = label
            io['id'] = typeV
            io['dimensionality'] = item['dim']['value']
            io['type'] = dcdom + item['iolabel']['value']
            io['isParam'] = False
            if item['prop']['value'] == 'https://w3id.org/mint/modelCatalog#hasInput':
                io['prefix'] = '-i%d' % (len(jsonRequest['inputs']) + 1)
                jsonRequest['inputs'].append(io)
            elif item['prop']['value'] == 'https://w3id.org/mint/modelCatalog#hasOutput':
                io['prefix'] = '-o%d' % (len(jsonRequest['outputs']) + 1)
                jsonRequest['outputs'].append(io)
            else:
                continue
            selected[item['iolabel']['value']] = True
        return jsonRequest, selected
