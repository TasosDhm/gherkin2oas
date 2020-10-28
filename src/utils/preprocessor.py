from gherkin.parser import Parser
import os
from os.path import basename
from collections import OrderedDict

# General comment: python dicts not perserving order matters here. Order is required.

def main(resources_path):
    parser = Parser()

    nlp_ready_resources = {}

    for root, dirs, files in os.walk(resources_path):
        for file_name in files:
            if file_name.endswith('.resource'):
                resource = os.path.splitext(basename(file_name))[0]
                resource = ' '.join(resource.split('-'))
                resource = ' '.join(resource.split('_'))
                parsed_resource_file = parser.parse(os.path.join(root, file_name))
                nlp_ready_resources[resource] = {}
                for child in parsed_resource_file['feature']['children']:
                    if child['type'] == 'Background':
                        nlp_ready_resources[resource]['background'] = {}
                        nlp_ready_resources[resource]['background']['Given'] = []
                        for step in child['steps']:
                            sentence = step['keyword'] + step['text']
                            nlp_ready_resources[resource]['background']['Given'].append({'sentence':sentence})
                    elif child['type'] == 'Scenario':
                        ordered_step_types = OrderedDict({'Given':[],'When':[],'Then':[]})
                        ordered_step_types.move_to_end('When')
                        ordered_step_types.move_to_end('Then')
                        nlp_ready_resources[resource][child['name']] = ordered_step_types
                        in_step = ''
                        for step in child['steps']:
                            data_table = []
                            sentence = step['keyword'] + step['text']
                            if step['keyword'] == 'When ' or step['keyword'] == 'Then ' or step['keyword'] == 'Given ': 
                                in_step = step['keyword'].strip() #note: there is a space here after the keyword                
                            if 'argument' in step:
                                if step['argument']['type'] == 'DataTable':
                                    data_table = parse_table(step)
                            if not in_step == 'Given':
                                nlp_ready_resources[resource][child['name']][in_step].append({'sentence':sentence,'data_table':data_table,'scenario_name':child['name']})
                                if 'description' in child:
                                    nlp_ready_resources[resource][child['name']]['Scenario Description'] = child['description']
                            else:
                                nlp_ready_resources[resource][child['name']][in_step].append({'sentence':sentence,'scenario_name':child['name']})
    return nlp_ready_resources

def parse_table(step):
    data_table = []
    for row in step['argument']['rows']:
        r = []
        for cell in row['cells']:
            r.append(cell['value'])
        data_table.append(r)
    return data_table