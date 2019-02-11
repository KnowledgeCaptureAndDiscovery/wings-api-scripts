# wings-API-scripts

This project combines WINGS API and MINT Data Catalog using Python

## Features

- Implements auth, data, domain, planner, resource and user operations
- Get the input/output, parameters, and code using [the MINT Model Catalog Ontology](https://w3id.org/mint/modelCatalog#ModelConfiguration)
- Create the Data and data types in WINGS
- Create the components: Select the data types and upload the code (hasComponentLocation)

## How to use it?

First, install the required software components

```
pip install -r requirements.txt
```

Second, check the configuration **config.ini**

```
#Mint servers
serverMint      = http://ontosoft.isi.edu:8001/api/KnowledgeCaptureAndDiscovery/MINT-ModelCatalogQueries
endpointMint    = http://ontosoft.isi.edu:3030/ds/query

# Wings configuration
serverWings     = http://datascience4all.org/wings-portal
userWings       = user
passwordWings   = password
domainWings     = domain
# Workaround wings' bug
exportWingsURL  = http://ontosoft.isi.edu:8080/wings-portal
```
Finally, run it

```
$ python mint.py -r https://w3id.org/mint/instance/pihm
```