import preprocessor
import nlp
import json
from collections import OrderedDict
import sys
import time
import nltk
import formatter
import yaml
from openapi_spec_validator import validate_spec
import graph
import argparse
import configparser
import os
import traceback

start_time = time.time()

parser = argparse.ArgumentParser(description='Gherkin2OAS')
parser.add_argument('-f','--folder', help='Resource folder path', required=False)
parser.add_argument('-m','--model', help='Model file path', required=False)
parser.add_argument('-fg','--fixgraph', action='store_true', help='Enable graph fixing', required=False)
parser.add_argument('-apiinfo','--apiinfo', help='api.info file path', required=False)
args = vars(parser.parse_args())
if not args['folder'] and not args['model']:
    sys.exit("Need one input file, type -h for help")
if args['folder'] and args['model']:
    sys.exit("Choose either folder or model")

oas_settings = configparser.ConfigParser()
oas_settings.read(args['folder'] + '/api_info.ini')
if not oas_settings:
    sys.exit("Something went wrong when reading api info file")
try:
    if not os.path.isdir(args['folder'] + '/output_files'):
        os.makedirs(args['folder'] + '/output_files')
    if not os.path.isdir(args['folder'] + '/output_files/swagger-oas2'):
        os.makedirs(args['folder'] + '/output_files/swagger-oas2')
    if not os.path.isdir(args['folder'] + '/output_files/oas3'):
        os.makedirs(args['folder'] + '/output_files/oas3')
except:
    print(traceback.format_exc())
model = {}
resource_graph = {}
state_graph = {}
if args['model']:
    print('Loading model...')
    nlp_model = {}
    with open(args['model']) as data_file:    
        nlp_model = json.load(data_file)
    model = nlp_model['model']
    resource_graph = nlp_model['resource_graph']
    state_graph = nlp_model['state_graph']
elif args['folder']:
    print('Parsing resources...')
    resources = preprocessor.main(args['folder'])
    if not resources:
        print('No resources found, did you insert the correct resources folder?')
        sys.exit()
    resource_names = nlp.plural_extend(resources)
    print('Processing resources...')
    nlp_model = nlp.resource_analysis(resources,resource_names)
    model = nlp_model['model']
    resource_graph = nlp_model['resource_graph']
    state_graph = nlp_model['state_graph']
    with open(args['folder'] + '/output_files/nlp_model.json', 'w') as outfile:
        json.dump(nlp_model, outfile, indent=4)

print('Generating files...')
graph.draw(resource_graph,state_graph,args['fixgraph'], args['folder'])
oas_schema = formatter.generate_swagger(model, oas_settings['SECURITY']['type'])
oas_schema['swagger'] = '2.0'
oas_schema['info'] = {  "title":            oas_settings['INFO']['title'],
                        "description":      oas_settings['INFO']['description'],
                        "version":          oas_settings['INFO']['version'],
                        "termsOfService":   oas_settings['INFO']['termsOfService']
}
oas_schema['host'] = oas_settings['HOST']['host']
oas_schema['schemes'] = ['https','http']
oas_schema['basePath'] = oas_settings['BASEPATH']['basePath']
oas_schema['produces'] = ['application/json']
# validator20.validate_spec(oas_schema)

with open(args['folder'] + '/output_files/swagger-oas2/swagger.json', 'w') as outfile:
    json.dump(oas_schema, outfile, indent=4)

# with open(args['folder'] + '/output_files/swagger-oas2/swagger.yaml', 'w') as outfile:
#     yaml.dump(oas_schema, outfile, indent=4)

import subprocess
subprocess.run(["swagger2openapi.cmd", args['folder'] + '/output_files/swagger-oas2/swagger.json', "-o", args['folder'] + '/output_files/oas3/swagger.json'])
with open(args['folder'] + '/output_files/oas3/swagger.json', 'r', encoding='utf-8') as inputfile:
    # spec = json.load(inputfile)
    # for oas_field in spec:
    #     i
    validate_spec(json.load(inputfile))
# subprocess.run(["swagger2openapi.cmd", args['folder'] + '/output_files/swagger-oas2/swagger.yaml', "-o", args['folder'] + '/output_files/oas3/swagger.yaml'])

elapsed_time = time.time() - start_time
print("Successfully generated valid swagger")
print(elapsed_time)

