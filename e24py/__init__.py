try:
    import requests
except ImportError:
    print ("request module not found - import it!")
    exit(1)

from e24py.e24pyall import E24sess, VirtualMachine, StorageVolume



