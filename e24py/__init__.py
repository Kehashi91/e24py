"""
TODO:
Fix ApiObject.update() - it works but is convoluted and unreadable.
Make proper methods for handling OS templates
Try to make create_vm method more generic and able to create all resource types

FUTURE:
Configuration options and managment
Threaded auto-update on request
Debug mode with logging
Live tests?
Safer secret key storage (env -> hash -> save to env?)
"""
import logging


try:
    import requests
except ImportError:
    print ("request module not found - import it!")
    exit(1)

logging.basicConfig(filename='debug.log', format='%(asctime)s: %(message)s', level=logging.INFO)
from e24py.apiobjects import E24sess, VirtualMachine, StorageVolume, DiscImage





