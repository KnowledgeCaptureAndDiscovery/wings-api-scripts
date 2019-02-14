import requests
from urllib.parse import urlparse
import re


class Gather(object):
    def __init__(self, server, endpoint):
        self.session = requests.Session()
        self.server = server
        self.endpoint = endpoint

    def get_id(self, full_id):
        '''
        Wings does not accept domain outside of him. So,
        we remove the domain and get the id
        '''
        return full_id.split('#')[-1]

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
            param['prefix'] = '-p%d' % (idx + 1)
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

    def prepareInputOutput(self, instance, jsonRequest, dcdom):
        response = self.getInputOutput(instance)
        data_types = {}
        counterInput = 1
        for idx, item in enumerate(response['results']['bindings']):
            data_type = self.get_id(item['type']['value'])
            # ignore duplicate fields
            if data_type in data_types:
                continue
            # prepare json
            io = {}
            label = self.sanitize(item['iolabel']['value'])
            typeV = self.sanitize(data_type)
            io['role'] = label
            io['id'] = typeV
            io['dimensionality'] = item['dim']['value']
            io['type'] = dcdom + data_type
            io['isParam'] = False
            if item['prop']['value'] == 'https://w3id.org/mint/modelCatalog#hasInput':
                io['prefix'] = '-i%d' % (counterInput)
                jsonRequest['inputs'].append(io)
                counterInput += 1
            elif item['prop']['value'] == 'https://w3id.org/mint/modelCatalog#hasOutput':
                io['prefix'] = '-o%d' % (len(jsonRequest['outputs']) + 1)
                jsonRequest['outputs'].append(io)
            else:
                continue
            data_types[data_type] = True
        return jsonRequest, data_types
