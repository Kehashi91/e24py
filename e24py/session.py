import requests

import hmac, hashlib, base64
import json
import os

from email.utils import formatdate

APIKEY = os.getenv("E24_KEY")
APISECRET = os.getenv("E24_SECRET")

ENDPOINTS = {"dc1":"eu-poland-1poznan.api.e24cloud.com","dc2":"eu-poland-2poznan.api.e24cloud.com"}

"""
Poniższa stała rozwiązuje kwestie liczby pojedyńczej/mnogiej w wypadku requestów o listowanie zasobów vs requestów
ze wskazanym konkretnym ID
"""
TYPEMAP = {
    'virtual_machine':{'urlname':'virtual-machines', 'jsonname':'virtual_machines'},
    'storage_volume':{'urlname':'storage-volumes', 'jsonname':'storage_volumes'},
           }


class ApiRequestFailed(Exception):
    """Generic exception on non 2xx API response"""
    pass


class E24sess():
    """
    Session class encapsulating all methods tied to making actual requests and other non-resource tied utlilites.
    Registers all created API objects within a dictionary. Also creates a single requests.Session for use in all API 
    calls.
    """
    default_session = None

    def __init__(self, endpoint="dc1", set_default=True):
        self.session = requests.Session()  # request.Session() polaczona na stale z jednym obiektem
        self.endpoint = ENDPOINTS[endpoint]
        self.objects = {}
        if set_default:
            E24sess.default_session = self

    def api_request(self, method, path, data=None):

        url = "https://{}{}".format(self.endpoint, path)
        if data:
            rawauth = "{}\n{}\n{}\n{}\n{}".format(method, self.endpoint, formatdate(usegmt=True), path,
                                                  json.dumps(data))
        else:
            rawauth = "{}\n{}\n{}\n{}\n".format(method, self.endpoint, formatdate(usegmt=True), path)

        print(rawauth)
        rawauth = hmac.new(bytes(APISECRET, 'utf-8'), bytes(rawauth, 'utf-8'), hashlib.sha256).digest()
        authstring = (base64.b64encode(rawauth))

        complete = bytes(APIKEY, 'utf-8') + b':' + authstring

        headers = {'Content-type': 'application/json', 'X-Date': formatdate(usegmt=True), 'Authorization': complete}

        return self.request_dispatch(method, headers, url, data)

    def request_dispatch(self, method, headers, url, data):
        methods = {"GET", "POST", "PUT", "DELETE"}

        if not method in methods:
            raise ValueError("wrong method")
        request = requests.Request(method, url, headers=headers, json=data)
        request = self.session.prepare_request(request)
        request = self.session.send(request)
        
   
        #zapisywanie do pliku
        with open('data.json', 'a') as out:
            out.write("url:\n")
            out.write(url)
            out.write("Headers:\n")
            out.write(str(headers))
            out.write("status:\n")
            out.write(str(request.status_code))
            out.write("response:\n")
            #json.dump(request.json(), out)
            out.write("\n")


        if request.status_code == 404:  # konieczny dodatkowy warunek, w innym przypadku trzymamy JSON Decode error
            raise ApiRequestFailed("Status Code: {} \n No Json response".format(request.status_code))
        elif request.json()['success'] == False or not request.ok:
            raise ApiRequestFailed(("Status Code: {} \n Response: \n {}").format(request.json(), request.status_code))
        else:
            return request

    def resource_search(self, type, id=None, label=None):
        """
        Generic search function, returns uniformally formatted json responses independently.

        BUG: w przypadku wyszukiwania po labelu i istnieniu wielu elementów o tym samym labelu, zostanie zwrócony pierwszy z nich.
        """
        if id:
            url = "/v2/{}/{}".format(TYPEMAP[type]['urlname'], id)
            try:
                r = self.api_request('GET', url)

            except ApiRequestFailed:
                return False
            return r.json()[type]


        elif label:
            url = "/v2/{}".format(TYPEMAP[type]['urlname'])

            r = self.api_request('GET', url)

            for resource in r.json()[TYPEMAP[type]['jsonname']]:
                if resource['label'] == label:
                    return resource
            return False

        else:
            raise ValueError('No ID or label provided.')

    def create_vm(self, name, cpu, memory):

        params = {
            "create_vm": {
                "cpus": cpu,
                "ram": memory,
                "zone_id": "24e12e20-0851-5354-e2c3-04b16c4c9c45",
                "name": name,
                "boot_type": "image",
                "os": "2599",
                "password": "placeholder123placeholder123",
            }
        }

        r = self.api_request('PUT', "/v2/virtual-machines", params)
        print(r.json())
        return r.json()["virtual_machine"]["id"]



    def get_os(self):
        """
        Zwraca sformatowany słownik obrazów systemowych, gdzie kluczem jest id obrazu
        """
        r = self.api_request('GET', "/v2/templates", "kek")

        r = r.json()["templates"]

        rv = {template["id"]: template for template in r}
        for key, value in rv.items():
            del value["id"]

        return rv