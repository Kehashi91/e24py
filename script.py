import e24py

from time import sleep


d1 = e24py.E24sess(endpoint="EU/POZ-1")
#vm = e24py.VirtualMachine(label="JurnyJanusz2")


d1.create_vm("nohej2", 1, 512)
d1.create_vm("nohej", 1, 512)
