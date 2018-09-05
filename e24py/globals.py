"""File for all constants and enviroment-dependent data.
"""
import os

APIKEY = os.getenv("E24_KEY")
APISECRET = os.getenv("E24_SECRET")

ENDPOINTS = {"EU/POZ-1":"eu-poland-1poznan.api.e24cloud.com","EU/POZ-2":"eu-poland-1poznan2.api.e24cloud.com"}
# Endpoints keys are meant to be consistent with /v2/zones labels

"""
TYPEMAP solves discrepectancy in singular/plural resources names when we use GET methods with ID (singular)
or without ID (plural). It also helps remediate diffrennce in url (using "-" as whitespace) and json where
we have "_".
"""
TYPEMAP = {
    'virtual_machine':{'urlname':'virtual-machines', 'jsonname':'virtual_machines'},
    'storage_volume':{'urlname':'storage-volumes', 'jsonname':'storage_volumes'},
    'disk_image':{'urlname':'disk-images', 'jsonname':'disk_images'},
           }