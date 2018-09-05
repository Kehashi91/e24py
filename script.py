import e24py

from time import sleep


session = e24py.E24sess(endpoint="EU/POZ-1", set_default=False)

session.get_os()
vm = e24py.VirtualMachine(label="JurnyJanusz2", session=session)

"""
vm.power_on()
print (vm.state)
vm.update()
print (vm.state)


#vm = e24py.VirtualMachine(label="JurnyJanusz2")

os = d1.get_os()
for key in os:
	if os[key]['label'] == "Ubuntu 18.04":
		ubuntu = key


vm1 = e24py.VirtualMachine(label="mautic-test")
print (vm1.data)
#vm1.delete()

"""