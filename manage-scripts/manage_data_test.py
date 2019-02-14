import wings.data
import json
data_id="test"
data_type="DataObject5"
parent_type=None

server      = "http://ontosoft.isi.edu:7072/wings-portal"
exportURL   = "http://localhost:8080/wings-portal"
userid      = "admin"
password    = "4dm1n!23"
domain      = "CaesarCypher"



#create a new data
data = wings.ManageData(server, exportURL, userid, domain)
if not data.login(password):
    print("fail logging")
    exit(1)

#New Datatype and create Data
data.new_data_type(data_type, None)

#New Data 
data.add_data_for_type(data_id, data_type)

#Get description Dataid
data.get_data_description(data_id)
data.get_datatype_description(data_type)
print(data.get_all_items())

# #Upload data from type
upload_data='assets/test.txt'
upload_data_type='dataFile'
data.new_data_type(upload_data_type, None)
upload_data_id = data.upload_data_for_type(upload_data, upload_data_type)
#add medata to the file
save_metadata = 'resources/metadata1.json'
with open(save_metadata) as dfile:
    jsonobj = json.load(dfile)
    data.save_metadata(upload_data_id, jsonobj)

#Delete data
data.del_data(data_id)
data.del_data_type(data_type)
