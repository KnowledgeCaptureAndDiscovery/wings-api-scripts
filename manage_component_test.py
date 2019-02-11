import wings.component
import json


server      = "http://ontosoft.isi.edu:7072/wings-portal"
exportURL   = "http://localhost:8080/wings-portal"
userid      = "admin"
password    = "4dm1n!23"
domain      = "CaesarCypher"



#create a new data
component = wings.ManageComponent(server, exportURL, userid, domain)
if not component.login(password):
    print("fail logging")
    exit(1)

#new component type
parent_type = None
component_id="sumRows"
component_type = component_id.capitalize()
component.new_component_type(component_type, parent_type)
component.new_component(component_id, component_type)


#Delete
component_type = "tododelete"
component.new_component_type(component_type, parent_type)
component_id="tododeleteComponent"
component.new_component(component_id, component_type)
component.del_component(component_id)
component.del_component_type(component_type)

#Get
component_type = "pihm"
component_id="sumRows"
print(component.get_component_description(component_id))
print(component.get_component_type_description(component_type))
print(component.get_all_items())


#upload
upload_component="assets/pihm.zip"
cid = component.get_component_id(component_id)
component.upload(upload_component, component_id)

save_json = "resources/component2.json"
#Save json
with open(save_json) as cfile:
    jsonobj = json.load(cfile)
    component.save_component(component_id, jsonobj)