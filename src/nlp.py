import nltk
from nltk.corpus import treebank
import re
# from nltk.tag import StanfordPOSTagger
# from nltk.tag import SennaTagger
from textblob import TextBlob
import inflect
import re
import ast
import sys
from dateutil.parser import parse

HTTP_verbs = {
'post': ["create", "add", "produce", "make", "put", "write", "pay", "send", "build", 
"raise", "develop", "register", "post", "submit", "apply", "order", "insert","comment"],

'get': ["retrieve", "check", "choose", "request", "search", "contact", "get", 
"take", "see", "ask", "show", "watch", "read", "open", "reach", "return",
"receive", "view", "load", "review", "select"],

'put': ["perform", "mark", "evaluate", "update", "set", "change", "edit"],

'delete': ["delete", "destroy", "kill", "remove","cancel"]}

# response code lists
L404 = ['not found','doesn\'t exist','does not exist','unable to find','can\'t find','no', 'didn\'t find', 'did not find', 'none found', 'none was found']
L401 = ['unauthorized','not allowed','rejected','denied']
L400 = ['failed','unsuccessful','wrong','mistake','error','not']
L200 = ['success','ok','updated','deleted','retrieved','canceled']
L201 = ['created']
L202 = ['accepted']

# phrase lists
maximum_phrases = ['max', 'maximum', 'cannot be more than',\
 'can\'t be more than', 'ceiling', 'can\'t be greater than', 'cannot be greater than']
minimum_phrases = ['min', 'minimum', 'cannot be less than', \
'can\'t be less than', 'floor', 'can\'t be less than', 'cannot be less than']
exclusive_phrases = ['exclusive','including']

# st = StanfordPOSTagger("/path/to/stanfordtagger")

# senna_tagger = SennaTagger("path/to/sennatagger")
p = inflect.engine()

def resource_analysis(resources,resource_names):
    model = {}
    resource_graph = {}
    state_graph = {}
    table_parameter_occurence = {}
    plain_parameter_occurence = {}
    put_non_body_par_occurence = {}
    operation_occurence = {}
    for resource,scenarios in resources.items():
        resource_graph[resource] = []
        model[resource]= {'get':{'request_params':[],'request_examples':[],'responses':{'default':{'params':[],'links':[],'param_examples':[],'message':''}}, 'description':''},
        'post':{'request_params':[],'request_examples':[],'responses':{'default':{'params':[],'links':[],'param_examples':[],'message':''}},'description':''},
        'put':{'request_params':[],'non_body_params':[],'request_examples':[],'responses':{'default':{'params':[],'links':[],'param_examples':[],'message':''}},'description':''},
        'delete':{'request_params':[],'request_examples':[],'responses':{'default':{'params':[],'links':[],'param_examples':[],'message':''}},'description':''},'resource_hierarchy':{},'resource_roles':{}}
        table_parameter_occurence[resource] = {}
        plain_parameter_occurence[resource] = {}
        put_non_body_par_occurence[resource] = {}
        operation_occurence[resource] = {}
        resource_roles = []
        #----------------- Analyze Given steps in Background and scenarios
        for scenario,steps_types in scenarios.items():
            if scenario == 'background':
                for steps_type,steps in steps_types.items():
                     if steps_type == 'Given':
                        for step in steps:
                            resource_hierarchy = detect_other_resources(step['sentence'],resource,resource_names)
                            r_roles = detect_roles(step['sentence'],resource_names,resource_roles)
                            if resource_hierarchy:
                                hierarchy_parameter = detect_parameters(step['sentence'],resource_names)
                                if len(hierarchy_parameter) == 1:
                                    model[resource]['resource_hierarchy'] = {'hierarchy_resource':resource_hierarchy, 'linking_parameter':hierarchy_parameter[0]}
                                else:
                                    sys.exit("Please specify one and only one hierarchy linking parameter between the resources '" + resource + "' and '" + resource_hierarchy + "' in the sentence: "\
                                        + "'"+step['sentence']+"'")
                            elif r_roles:
                                for r_role in r_roles:
                                    resource_roles.append(r_role)
                                    model[resource]['resource_roles'][r_role] = []
        for scenario,steps_types in scenarios.items():                            
            if scenario != 'background':
                when_ops = []
                scenario_roles = []
                for steps_type,steps in steps_types.items():
                    if steps_type == 'Given':    
                        for step in steps:
                            s_roles = detect_roles(step['sentence'],resource_names,resource_roles)
                            if s_roles:
                                for s_role in s_roles:
                                    if s_role not in scenario_roles:
                                        scenario_roles.append(s_role)
        #----------------- Analyze When & Then Steps                            
                for steps_type,steps in steps_types.items():
                    if steps_type == 'When': # 'When' comes always before 'Then', because the dictionary is ordered from the preprocessor
                        plain_when_params = []
                        for step in steps:
                            if 'When' in step['sentence']:
                                plain_when_params = detect_parameters(step['sentence'],resource_names)
                                when_ops = detect_operations(step['sentence'],resource_names,steps_type)
                        for op in when_ops:
                            if op not in operation_occurence[resource]:
                                operation_occurence[resource][op] = {'request_count':1}
                            else:
                                operation_occurence[resource][op]['request_count'] += 1
                        for step in steps:
                            if step['data_table']:
                                processed_data_table = {}  
                                if ('query' in step['sentence'] and len(when_ops)==1 and when_ops[0]=='put'):                           
                                    processed_data_table = analyze_data_table(step['data_table'],'put_non_body')
                                    if 'put' not in operation_occurence[resource].keys():
                                        put_non_body_par_occurence[resource]['put'] = {'request': {}}
                                    elif 'request' not in operation_occurence[resource]['put']:
                                        put_non_body_par_occurence[resource]['put']['request'] = {}
                                    if not processed_data_table['domain'] in model[resource]['put']['non_body_params']:
                                        model[resource]['put']['non_body_params'].append(processed_data_table['domain'])
                                        for param in processed_data_table['domain']:
                                            if not param['name'] in put_non_body_par_occurence[resource]['put']['request'].keys():
                                                put_non_body_par_occurence[resource]['put']['request'][param['name']] = {'count':1}
                                            else:
                                                put_non_body_par_occurence[resource]['put']['request'][param['name']]['count'] += 1                
                                elif step['sentence'].endswith(':'):
                                    for op in when_ops:
                                        processed_data_table = analyze_data_table(step['data_table'],op)
                                        if (op == 'post' or op == 'put'):
                                            model_name = detect_model_name(step['sentence'])
                                            if not model_name:
                                                model_name = 'Uknown_Model'
                                            if not any(model_name == param['name'] for param in model[resource][op]['request_params']):
                                                if processed_data_table['example']:
                                                    model[resource][op]['request_params'].append({'name':model_name, 'model_type':True, 'properties':processed_data_table['domain'], 'example':processed_data_table['example']})
                                                else:
                                                    model[resource][op]['request_params'].append({'name':model_name, 'model_type':True, 'properties':processed_data_table['domain']})
                                            if op not in plain_parameter_occurence[resource].keys():
                                                plain_parameter_occurence[resource][op] = {'request': {}}
                                            if not model_name in plain_parameter_occurence[resource][op]['request']:
                                                plain_parameter_occurence[resource][op]['request'][model_name] = {'count':1}
                                            else:
                                                plain_parameter_occurence[resource][op]['request'][model_name]['count'] += 1
                                else:
                                    for op in when_ops:
                                        processed_data_table = analyze_data_table(step['data_table'],op)
                                        if op not in table_parameter_occurence[resource]:
                                            table_parameter_occurence[resource][op] = {'request': {}}
                                        elif 'request' not in table_parameter_occurence[resource][op]:
                                            table_parameter_occurence[resource][op]['request'] = {}
                                        if not processed_data_table['domain'] in model[resource][op]['request_params']:
                                            model[resource][op]['request_params'].append(processed_data_table['domain'])
                                            if processed_data_table['example']:
                                                model[resource][op]['request_examples'].append(processed_data_table['example'])
                                            for param in processed_data_table['domain']:
                                                if not param['name'] in table_parameter_occurence[resource][op]['request'].keys():
                                                    table_parameter_occurence[resource][op]['request'][param['name']] = {'count':1}
                                                else:
                                                    table_parameter_occurence[resource][op]['request'][param['name']]['count'] += 1
                                    if ('When' in step['sentence']):
                                        if len(when_ops) == 1 and (when_ops[0] == 'put' or when_ops[0] == 'delete' or when_ops[0] == 'get'):
                                            if len(plain_when_params) == 1:
                                                if len(processed_data_table['domain']) == 1:
                                                    for i, table in enumerate(model[resource][when_ops[0]]['request_params']):
                                                        if type(table) is list:
                                                            if len(table) == 1:
                                                                for j, param in enumerate(table):
                                                                    if param['name'] != plain_when_params[0] and param == processed_data_table['domain'][0]:
                                                                        print(param['name'],plain_when_params[0],processed_data_table['domain'],resource)
                                                                        sys.exit('In resource file ' + resource + ' and operation ' + when_ops[0] + ' a single parameter in the sentence and a single parameter \
                                                                            in the data table were specified with different names, exiting')
                                                                    elif param['name'] == plain_when_params[0] and param == processed_data_table['domain'][0]:
                                                                        model[resource][when_ops[0]]['request_params'][i][j]['path_param'] = True
                            else:                           
                                for op in when_ops: 
                                    if op not in plain_parameter_occurence:
                                        plain_parameter_occurence[resource][op] = {'request': {}}
                                    elif 'request' not in plain_parameter_occurence[resource][op]:
                                        plain_parameter_occurence[resource][op]['request'] = {}
                                    if (op == 'put' or op == 'get' or op == 'delete') and ('When' in step['sentence']) and (len(plain_when_params) == 1 or len(plain_when_params) == 0):
                                        if len(plain_when_params) == 1:
                                            param = plain_when_params[0]
                                            duplicate_path_param = False
                                            for i, parameters in enumerate(model[resource][op]['request_params']):
                                                if type(parameters) is list:
                                                    for j, parameter in enumerate(parameters):
                                                        if 'path_param' in parameter and parameter['name'] != param and parameter['name']:
                                                            print('Warning found duplicate path parameters: \'' + parameter['name'] + '\' and \'' + parameter['name'] + '\' in resource \'' + resource\
                                                                + '\' and operation \'' + operation + '\'')
                                                            print('A random path parameter will be chosen')
                                                            duplicate_path_param = True
                                                            break
                                                        elif 'path_param' in parameter and parameter['name'] == param:
                                                            duplicate_path_param = True
                                                        elif 'path_param' in parameter and not parameter['name']:
                                                            duplicate_path_param = True
                                                            model[resource][op]['request_params'][i][j]['name'] = param
                                            for i, parameter in enumerate(model[resource][op]['request_params']):
                                                if type(parameter) is not list:
                                                    if 'path_param' in parameter and parameter['name'] != param and parameter['name']:
                                                        print('Warning found duplicate path parameters: \'' + parameter['name'] + '\' and \'' + parameter['name'] + '\' in resource \'' + resource\
                                                            + '\' and operation \'' + operation + '\'')
                                                        print('A random path parameter will be chosen')
                                                        duplicate_path_param = True
                                                    elif 'path_param' in parameter and parameter['name'] == param:
                                                        duplicate_path_param = True
                                                    elif 'path_param' in parameter and not parameter['name']:
                                                        duplicate_path_param = True
                                                        model[resource][op]['request_params'][i]['name'] = param
                                            if duplicate_path_param == False:
                                                model[resource][op]['request_params'].append({'name':param,'path_param':True})
                                    else:
                                        plain_params = detect_parameters(step['sentence'],resource_names)
                                        for param in plain_params:
                                            if not param in plain_parameter_occurence[resource][op]['request']:
                                                plain_parameter_occurence[resource][op]['request'][param] = {'count':1}
                                            else:
                                                plain_parameter_occurence[resource][op]['request'][param]['count'] += 1
                                            duplicate = False
                                            for p in model[resource][op]['request_params']:
                                                if not type(p) is list and 'name' in p:
                                                    if p['name'] == param:
                                                        duplicate = True
                                            if duplicate == False:
                                                model[resource][op]['request_params'].append({'name':param})
                        for op in when_ops:
                            # roles apply to either the entire resource or a specific scenario
                            for resource_role in resource_roles:
                                scope = {'operation':op, 'resource':resource}
                                if not scope in model[resource]['resource_roles'][resource_role]:
                                    model[resource]['resource_roles'][resource_role].append(scope)
                            for scenario_role in scenario_roles:
                                if scenario_role not in model[resource]['resource_roles']:
                                    model[resource]['resource_roles'][scenario_role] = []
                                scope = {'operation':op, 'resource':resource}
                                if scope not in model[resource]['resource_roles'][scenario_role]:
                                    model[resource]['resource_roles'][scenario_role].append(scope)
                    elif steps_type == 'Then':
                        #preprocessing makes sure that 'when' is analyzed before 'then', so by now we know the scenario operations
                        steps_message_type = ''
                        steps_message_text = ''
                        for step in steps:
                            message = detect_messages(step['sentence'])
                            if message['text']:
                                steps_message_type = message['type']
                                steps_message_text = message['text']
                                if message['type'] == 'default':
                                    print('Warning, could not figure a status code from the phrase \'' + message['text'] + '\', the \'default\' be used as a status code')
                        if not steps_message_type:
                            steps_message_type = 'default'
                        for op in when_ops:
                            if steps_message_type not in model[resource][op]['responses']: # unique response types
                                model[resource][op]['responses'][steps_message_type] = {'params':[],'links':[],'param_examples':[],'message':steps_message_text}
                            if not steps_message_type+'_count' in operation_occurence[resource][op]:
                                operation_occurence[resource][op][steps_message_type+'_count'] = 1
                            else:
                                operation_occurence[resource][op][steps_message_type+'_count'] += 1
                        for step in steps:
                            message = detect_messages(step['sentence'])
                            if not message['text']:
                                if step['data_table']:
                                    processed_data_table = analyze_data_table(step['data_table'],None)
                                    if step['sentence'].endswith(':'): # sentence that describes a model
                                        model_name = detect_model_name(step['sentence'])
                                        if not model_name:
                                            model_name = 'Uknown_Model'
                                        for op in when_ops:
                                            if not any(model_name == param['name'] for param in model[resource][op]['responses'][steps_message_type]['params']):
                                                if processed_data_table['example']:
                                                    model[resource][op]['responses'][steps_message_type]['params'].append({'name':model_name, 'model_type':True, 'properties':processed_data_table['domain'], 'example':processed_data_table['example']})
                                                else:
                                                    model[resource][op]['responses'][steps_message_type]['params'].append({'name':model_name, 'model_type':True, 'properties':processed_data_table['domain']})
                                            if op not in plain_parameter_occurence[resource].keys():                                     
                                                plain_parameter_occurence[resource][op] = {steps_message_type+'_params':{}}                   
                                            else:
                                                if steps_message_type+'_params' not in plain_parameter_occurence[resource][op]:
                                                    plain_parameter_occurence[resource][op][steps_message_type+'_params'] = {}   
                                            if not model_name in plain_parameter_occurence[resource][op][steps_message_type+'_params']:
                                                plain_parameter_occurence[resource][op][steps_message_type+'_params'][model_name] = {'count':1}
                                            else:
                                                plain_parameter_occurence[resource][op][steps_message_type+'_params'][model_name]['count'] += 1 
                                    else:
                                        for op in when_ops:                                    
                                            if op not in table_parameter_occurence[resource]:            
                                                table_parameter_occurence[resource][op] = {steps_message_type+'_params':{}}                   
                                            elif (steps_message_type+'_params') not in table_parameter_occurence[resource][op]: 
                                                table_parameter_occurence[resource][op][steps_message_type+'_params'] = {}                                 
                                            if not processed_data_table['domain'] in model[resource][op]['responses'][steps_message_type]['params']:
                                                model[resource][op]['responses'][steps_message_type]['params'].append(processed_data_table['domain'])
                                                if processed_data_table['example']:
                                                    model[resource][op]['responses'][steps_message_type]['param_examples'].append(processed_data_table['example'])
                                                for param in processed_data_table['domain']:
                                                    if not param['name'] in table_parameter_occurence[resource][op][steps_message_type+'_params']:
                                                        table_parameter_occurence[resource][op][steps_message_type+'_params'][param['name']] = {'count':1}
                                                    else:
                                                        table_parameter_occurence[resource][op][steps_message_type+'_params'][param['name']]['count'] += 1
                                else:
                                    links = detect_operations(step['sentence'],resource_names,steps_type)
                                    if links:
                                        for op in when_ops:
                                            state = ''
                                            if steps_message_text:
                                                state = step['scenario_name'] + ' ('  + steps_message_text + ')'
                                            else:
                                                state = step['scenario_name'] + ' (' + 'default response' + ')'
                                            if resource+' '+state not in state_graph:
                                                state_graph[resource+' '+state] = {'operation':op,'resource':resource,'links':[],\
                                                'http_state':step['scenario_name'] + ' ('  + steps_message_type + ')','natural_state':state,\
                                                'code':steps_message_type} 
                                            for link in links:  
                                                if not ({'operation':link['operation'],'resource':link['path']} in model[resource][op]['responses'][steps_message_type]['links']):
                                                    flag = False
                                                    for oper in model[resource]:
                                                        if 'responses' in model[resource][oper]:
                                                            for message_type in model[resource][oper]['responses']:
                                                                if {'operation':link['operation'],'resource':link['path']} in model[resource][oper]['responses'][message_type]['links']: # make sure the link between the resources is not already registered
                                                                    flag = True
                                                    if flag == False:
                                                        resource_graph[resource].append({'operation':link['natural_verb'],'resource':link['natural_resource_name']})
                                                if link not in state_graph[resource+' '+state]['links']:
                                                    state_graph[resource+' '+state]['links'].append(link)                                           
                                                model[resource][op]['responses'][steps_message_type]['links'].append({'operation':link['operation'],'resource':link['path']})
                                    else:                                
                                        params = detect_parameters(step['sentence'],resource_names)
                                        for op in when_ops:
                                            if op not in plain_parameter_occurence[resource]:                                     
                                                plain_parameter_occurence[resource][op] = {steps_message_type+'_params':{}}                   
                                            elif steps_message_type+'_params' not in plain_parameter_occurence[resource][op]:
                                                plain_parameter_occurence[resource][op][steps_message_type+'_params'] = {}                           
                                            for param in params:
                                                if not param in plain_parameter_occurence[resource][op][steps_message_type+'_params']:
                                                    plain_parameter_occurence[resource][op][steps_message_type+'_params'][param] = {'count':1}
                                                else:
                                                    plain_parameter_occurence[resource][op][steps_message_type+'_params'][param]['count'] += 1
                                                duplicate = False
                                                for p in model[resource][op]['responses'][steps_message_type]['params']:
                                                    if not type(p) is list and 'name' in p:
                                                        if p['name'] == param:
                                                            duplicate = True
                                                if duplicate == False:
                                                    model[resource][op]['responses'][steps_message_type]['params'].append({'name':param})
                    elif steps_type == 'Scenario Description':
                        if not model[resource][op]['description']:
                            model[resource][op]['description'] = '- ' + steps
                        else:
                            model[resource][op]['description'] += "\n- " + steps
    model = set_parameter_requirements(table_parameter_occurence,operation_occurence,model,0)
    model = set_parameter_requirements(plain_parameter_occurence,operation_occurence,model,1)
    model = set_parameter_requirements(put_non_body_par_occurence,operation_occurence,model,2)

    # there can't be spaces in URIs so we replace spaces in resource names with underscores
    for resource in resources:
        compact_resource_name = '_'.join(resource.split(' '))
        model[compact_resource_name] = model.pop(resource)

    return {'model':model,'resource_graph':resource_graph, 'state_graph':state_graph}

def detect_other_resources(sentence,resource,resource_names):
    for resource_name in resource_names:
        if resource_name != resource and resource_name != p.plural(resource):
            if re.search(resource_name, sentence):
                return resource_name

def detect_roles(sentence,resource_names,resource_roles):
    tagged_tokens = TextBlob(sentence).tags
    roles = []
    has_resources = any(re.search(r'\b' + resource_name + r'\b',sentence) for resource_name in resource_names)
    if not has_resources: 
        for tagged_token in tagged_tokens:
            if tagged_token[0] not in resource_roles:
                if tagged_token[1][0:2] == 'NN':
                    roles.append(tagged_token[0])
    elif has_resources:
        if detect_http_verbs(sentence):
            for tagged_token in tagged_tokens:
                if tagged_token[0] not in resource_roles:
                    if tagged_token[1][0:2] == 'NN':
                        roles.append(tagged_token[0])
    return roles

def detect_messages(sentence):
    message = {'text':'','type':''}
    quoted_phrase = find_quoted_text(sentence)

    #assuming there is only one quoted phrase atm
    if quoted_phrase:
        plain_phrase = quoted_phrase[0].lower()
        message['text'] = quoted_phrase[0]
        if ([text for text in L404 if re.search(text,plain_phrase)]):
            message['type'] = 'Not Found'
        elif ([text for text in L401 if re.search(text,plain_phrase)]):
            message['type'] = 'Unauthorized'
        elif ([text for text in L400 if re.search(text,plain_phrase)]):
            message['type'] = 'Bad Request'
        elif ([text for text in L200 if re.search(text,plain_phrase)]):
            message['type'] = 'OK'
        elif ([text for text in L201 if re.search(text,plain_phrase)]):
            message['type'] = 'Created'
        elif ([text for text in L202 if re.search(text,plain_phrase)]):
            message['type'] = 'Accepted'
        if not message['type']:
            message['type'] = 'default'
    return message

def detect_operations(sentence,resource_names,step_type):
    # by convention a when_step can have ops and params in the same sentence
    # on the contrary a then_step sentence that describes operations is hateoas and cannot also have params
    tokenized_sentence = nltk.word_tokenize(sentence)
    if step_type == 'When':
        detected_verbs = detect_http_verbs(sentence)
        operations = []
        for detected_verb in detected_verbs:
            operations.append(detected_verb['http'])
        return operations
    elif step_type == 'Then':
        detected_verbs = detect_http_verbs(sentence)
        for resource_name in resource_names:
            resource_name_parts = resource_name.split(' ')
            if len(resource_name_parts) > 1:
                if all(re.search(r'\b' + part + r'\b',sentence) for part in resource_name_parts):
                    hateoas_links = []
                    for detected_verb in detected_verbs:
                        compact_resource_name = '_'.join(resource_name.split(' ')) # paths can't have spaces in them
                        hateoas_links.append({'natural_resource_name':resource_name,'path':compact_resource_name,'natural_verb':detected_verb['natural'], 'operation':detected_verb['http']})
                    return hateoas_links
        for resource_name in resource_names:
            if re.search(r'\b' + resource_name + r'\b',sentence) and not any(verb['natural'] == resource_name for verb in detected_verbs):
                hateoas_links = []
                for detected_verb in detected_verbs:
                    compact_resource_name = '_'.join(resource_name.split(' ')) # paths can't have spaces in them
                    hateoas_links.append({'natural_resource_name':resource_name,'path':compact_resource_name,'natural_verb':detected_verb['natural'], 'operation':detected_verb['http']})
                return hateoas_links

def detect_parameters(sentence,resource_names):
    tagged_tokens = TextBlob(sentence).tags
    parameters = []
    for tagged_token in tagged_tokens: # a tagged token has the word at position 0 and the tag at position 1
        if tagged_token[1][0:2] == 'NN':
            if not tagged_token[0] in resource_names:
                parameters.append(tagged_token[0])

    return parameters

def detect_model_name(sentence):
    tagged_tokens = TextBlob(sentence).tags
    for tagged_token in tagged_tokens: # a tagged token has the word at position 0 and the tag at position 1
        if tagged_token[1][0:2] == 'NN':
            return tagged_token[0]

def detect_http_verbs(sentence):
    tagged_tokens = TextBlob(sentence).tags
    verbs = []
    for tagged_token in tagged_tokens: # a tagged token has the word at position 0 and the tag at position 1
        if tagged_token[1][0:2] == 'VB':           
            for http_verb, language_verbs in HTTP_verbs.items():
                if tagged_token[0] in language_verbs:
                   verbs.append({'http': http_verb, 'natural': tagged_token[0]})

    return verbs

def plural_extend(words_in_dict_keys):
    return list(words_in_dict_keys) + [p.plural(word) for word in list(words_in_dict_keys)]

def analyze_data_table(table,operation):
    domain = []
    example = {}
    numrows = len(table)
    numcolumns = len(table[0])   
    most_left_column = []
    second_row = []
    second_column = []
    third_row = []
    third_column = []
    fourth_row = []
    fourth_column  = []
    top_row = table[0]
    for row in table:
        most_left_column.append(row[0])
    if not any(is_data_type(cell) for cell in top_row): #domain is on the top row
        if numrows == 2:
            second_row = table[1]
        elif numrows == 3:
            second_row = table[1]
            third_row = table[2]
        elif numrows == 4:
            second_row = table[1]
            third_row = table[2]
            fourth_row = table[3]
        if second_row:
            if all(is_data_type(cell) for cell in second_row):
                for top_row_cell,second_row_cell in zip(top_row,second_row):
                    cell_type = figure_cell_type(top_row_cell,second_row_cell,operation)
                    domain.append(cell_type['domain'])
                    if cell_type['example']:
                        example[cell_type['example']['name']] = cell_type['example']['value']
                if third_row:
                    for top_row_cell,third_row_cell in zip(top_row,third_row):
                        domain = detect_min_max_cell(top_row_cell,third_row_cell,domain)
                if fourth_row:
                    for top_row_cell,fourth_row_cell in zip(top_row,fourth_row):
                        domain = detect_min_max_cell(top_row_cell,fourth_row_cell,domain)
            else:
                print('asasdsad')
                sys.exit("Incorrect table format")
        else:
            for cell in top_row:
                domain.append({'name':cell,'type':'string'})
    elif not any(is_data_type(cell) for cell in most_left_column): #domain is on the most left column  
        if numcolumns == 1:
            if len(table[0]) > 1:
                second_column.append(table[0][1])
        elif numcolumns == 2:
            for row in table:
                second_column.append(row[1])
        elif numcolumns == 3:
            for row in table:
                second_column.append(row[1])
                third_column.append(row[2])
        elif numcolumns == 4:
            for row in table:
                second_column.append(row[1])
                third_column.append(row[2])
                fourth_column.append(row[3])       
        if second_column:
            if all(is_data_type(cell) for cell in second_column):
                for most_left_column_cell,second_column_cell in zip(most_left_column,second_column):
                    cell_type = figure_cell_type(most_left_column_cell,second_column_cell,operation)
                    domain.append(cell_type['domain'])
                    if cell_type['example']:
                        example[cell_type['example']['name']] = cell_type['example']['value']
            else:
                sys.exit("Incorrect table format")
            if third_column:
                for most_left_column_cell,third_column_cell in zip(most_left_column,third_column):
                    domain = detect_min_max_cell(most_left_column_cell,third_column_cell,domain)
            if fourth_column:
                for most_left_column_cell,fourth_column_cell in zip(most_left_column,fourth_column):
                    domain = detect_min_max_cell(most_left_column_cell,fourth_column_cell,domain) 
        else:
            for cell in most_left_column:
                domain.append({'name':cell,'type':'string'})
    else:
        sys.exit("Incorrect table format")
    
    return {'domain':domain,'example':example}

def figure_cell_type(parameter_cell,type_cell,operation):
    domain_type = type_of_value(type_cell)
    domain = {}
    example = {}
    if domain_type is float:
        domain = {'name':parameter_cell,'type':'number','format':'float'}
        example = {'name':parameter_cell, 'value':ast.literal_eval(type_cell)}
    elif domain_type is int:
        domain = {'name':parameter_cell,'type':'integer','format':'int32'}
        example = {'name':parameter_cell, 'value':ast.literal_eval(type_cell)}
    elif domain_type is bool:
        domain = {'name':parameter_cell,'type':'boolean'}
        if type_cell == 'true':
            example = {'name':parameter_cell, 'value':True}
        else:
            example = {'name':parameter_cell, 'value':False}
    elif is_array(type_cell):                     
        content = is_array(type_cell)[0]
        values = []
        collection_format = ''
        if ',' in content:
            collection_format = 'csv'
            values = content.split(',')                            
        elif ' ' in content:
            collection_format = 'ssv'
            values = content.split(' ')
        elif '\t' in content:
            collection_format = 'tsv'
            values = content.split('\t')
        elif '|' in content:
            collection_format = 'pipes'
            values = content.split('|')
        else:
            collection_format = 'unknown'
            values = content
        types = type_of_value(values[0]) # assuming that user did not submit an array with different data types
        example = {'name':parameter_cell, 'value':[]}
        if types is float:
            domain = {'name':parameter_cell,'type':'array','collectionFormat':collection_format,'items':{'type':'number','format':'float'}}
            for item in values:
                example['value'].append(ast.literal_eval(item))
        elif types is int:
            domain = {'name':parameter_cell,'type':'array','collectionFormat':collection_format,'items':{'type':'integer','format':'int32'}}
            for item in values:
                example['value'].append(ast.literal_eval(item))
        elif types is bool:
            domain = {'name':parameter_cell,'type':'array','collectionFormat':collection_format,'items':{'type':'boolean'}}
            for item in values:
                if item == 'true':
                    example['value'].append(True)
                else:
                    example['value'].append(False)
        else:
            domain = {'name':parameter_cell,'type':'array','collectionFormat':collection_format,'items':{'type':'string'}}
            for item in values:
                example['value'].append(item[1:-1]) # strip quotes
    else:
        if is_password(type_cell) and\
        (operation != 'delete' and operation != 'get'):
            domain = {'name':parameter_cell,'type':'string','format':'password'}
        elif not is_quoted_text(type_cell):
            if domain_type == 'file':
                domain = {'name':parameter_cell,'type':'file'}
            elif is_date(type_cell) and (operation != 'delete' or operation != 'get' or operation =='put_non_body'):
                if ':' in type_cell:
                    domain = {'name':parameter_cell,'type':'string','format':'date-time'} # "2017-02-19T20:51:09.0+02:00Z"                    
                else:
                    domain = {'name':parameter_cell,'type':'string','format':'date'} # "2017-02-19"
                example =  {'name':parameter_cell, 'value': type_cell}
        else:
            domain = {'name':parameter_cell,'type':'string'}
            example = {'name':parameter_cell, 'value':type_cell[1:-1]} #strip quotes
    return {'domain':domain, 'example':example}

def detect_numbers(text):
    numbers = []
    for word in text.split(' '):
        if type_of_value(word) is float or type_of_value(word) is int:
            numbers.append(ast.literal_eval(word))
    return numbers

def detect_min_max_cell(parameter_cell,type_cell,domain):
    numbers = detect_numbers(type_cell)
    if numbers:
        if len(numbers) == 2:
            minimum = numbers[0]
            maximum = numbers[1]
            if numbers[0] > numbers[1]:
                minimum = numbers[1]
                maximum = numbers[0]                                
            for i,param in enumerate(domain):
                if param['name'] == parameter_cell:
                    if param['type'] == 'string' or param['type'] == 'password':
                        domain[i]['minLength'] = minimum
                        domain[i]['maxLength'] = maximum
                    elif param['type'] == 'number' or param['type'] == 'integer':
                        domain[i]['minimum'] = minimum
                        domain[i]['maximum'] = maximum
                    elif param['type'] == 'array':
                        domain[i]['minItems'] = minimum
                        domain[i]['maxItems'] = maximum 
        elif len(numbers) == 1:
            if detect_phrase(type_cell,maximum_phrases):
                for i,param in enumerate(domain):
                    if param['name'] == parameter_cell:
                        if param['type'] == 'string' or param['type'] == 'password':
                            domain[i]['maxLength'] = numbers[0]
                        elif param['type'] == 'number' or param['type'] == 'integer':
                            domain[i]['maximum'] = numbers[0]
                        elif param['type'] == 'array':
                            domain[i]['maxItems'] = numbers[0]
            elif detect_phrase(type_cell,minimum_phrases):
                for i,param in enumerate(domain):
                    if param['name'] == parameter_cell:
                        if param['type'] == 'string' or param['type'] == 'password':
                            domain[i]['minLength'] = numbers[0]
                        elif param['type'] == 'number' or param['type'] == 'integer':
                            domain[i]['minimum'] = numbers[0]
                        elif param['type'] == 'array':
                            domain[i]['minItems'] = numbers[0]
    else:
        for i,param in enumerate(domain):
            if param['name'] == parameter_cell:
                if type_cell:
                    domain[i]['description'] = type_cell
    return domain

def set_parameter_requirements(param_occurences,operation_occurence,model,mode):
    #mode 0 = data table parameters
    #mode 1 = plain parameters
    #mode 2 = put non_body parameters
    if mode == 0:
        for resource,operations in param_occurences.items():
            for operation, occurences in operations.items():
                # set all parameters as not required
                for i, params in enumerate(model[resource][operation]['request_params']):
                    if type(params) is list:
                        for j, param in enumerate(params):
                            if not 'required' in model[resource][operation]['request_params'][i][j]:
                                model[resource][operation]['request_params'][i][j]['required'] = False
                for message_type in model[resource][operation]['responses']:
                    for i, params in enumerate(model[resource][operation]['responses'][message_type]['params']):
                        if type(params) is list:
                            for j, param in enumerate(params):
                                if not 'required' in model[resource][operation]['responses'][message_type]['params'][i][j]:
                                    model[resource][operation]['responses'][message_type]['params'][i][j]['required'] = False
                # find which are required
            for operation, occurences in operations.items():
                if 'request' in occurences:
                    for this_param_name in occurences['request'].keys():
                        if param_occurences[resource][operation]['request'][this_param_name]['count'] == operation_occurence[resource][operation]['request_count']:
                            for i, params in enumerate(model[resource][operation]['request_params']):
                                if type(params) is list:
                                    for j, param in enumerate(params):
                                        if param['name'] == this_param_name and\
                                        (param_occurences[resource][operation]['request'][this_param_name]['count'] == operation_occurence[resource][operation]['request_count']):
                                            model[resource][operation]['request_params'][i][j]['required'] = True
                for message_type in model[resource][operation]['responses']:
                    if message_type+'_params' in occurences:
                        for this_param_name in occurences[message_type+'_params'].keys():
                            for i, params in enumerate(model[resource][operation]['responses'][message_type]['params']):
                                if type(params) is list:
                                    for j, param in enumerate(params):
                                        if param['name'] == this_param_name and \
                                        (param_occurences[resource][operation][message_type+'_params'][this_param_name]['count'] == operation_occurence[resource][operation][message_type+'_count']):
                                            model[resource][operation]['responses'][message_type]['params'][i][j]['required'] = True
    elif mode == 1:
        for resource,operations in param_occurences.items():
            for operation, occurences in operations.items():
                # set all parameters as not required
                for i, param in enumerate(model[resource][operation]['request_params']):
                    if type(param) is not list:
                        if not 'required' in model[resource][operation]['request_params'][i]:
                            model[resource][operation]['request_params'][i]['required'] = False
                for message_type in model[resource][operation]['responses']:
                    for i, param in enumerate(model[resource][operation]['responses'][message_type]['params']):
                        if type(param) is not list:
                            if not 'required' in model[resource][operation]['responses'][message_type]['params'][i]:
                                model[resource][operation]['responses'][message_type]['params'][i]['required'] = False
                # find which are required
            for operation, occurences in operations.items():
                if 'request' in occurences:
                    for this_param_name in occurences['request'].keys():
                        if param_occurences[resource][operation]['request'][this_param_name]['count'] == operation_occurence[resource][operation]['request_count']:
                            for i, param in enumerate(model[resource][operation]['request_params']):
                                if type(param) is not list:
                                    if param['name'] == this_param_name and\
                                    (param_occurences[resource][operation]['request'][this_param_name]['count'] == operation_occurence[resource][operation]['request_count']):
                                        model[resource][operation]['request_params'][i]['required'] = True
                for message_type in model[resource][operation]['responses']:
                    if message_type+'_params' in occurences:
                        for this_param_name in occurences[message_type+'_params'].keys():
                            for i, param in enumerate(model[resource][operation]['responses'][message_type]['params']):
                                if type(param) is not list:
                                    if param['name'] == this_param_name and \
                                    (param_occurences[resource][operation][message_type+'_params'][this_param_name]['count'] == operation_occurence[resource][operation][message_type+'_count']):
                                        model[resource][operation]['responses'][message_type]['params'][i]['required'] = True
    elif mode == 2:
        for resource,operations in param_occurences.items():
            for operation, occurences in operations.items():
                # set all parameters as not required
                if operation == 'put':
                    for i, params in enumerate(model[resource][operation]['non_body_params']):
                        if type(params) is list:
                            for j, param in enumerate(params):
                                if not 'required' in model[resource][operation]['non_body_params'][i][j]:
                                    model[resource][operation]['non_body_params'][i][j]['required'] = False
            for operation, occurences in operations.items():
                # find which are required
                if operation == 'put':
                    # find which are required
                    if 'request' in occurences:
                        for this_param_name in occurences['request'].keys():
                            if param_occurences[resource][operation]['request'][this_param_name]['count'] == operation_occurence[resource][operation]['request_count']:
                                for i, params in enumerate(model[resource][operation]['request_params']):
                                    if type(params) is list:
                                        for j, param in enumerate(params):
                                            if param['name'] == this_param_name and\
                                            (param_occurences[resource][operation]['request'][this_param_name]['count'] == operation_occurence[resource][operation]['request_count']):
                                                model[resource][operation]['non_body_params'][i][j]['required'] = True

    return model

def detect_phrase(text,phrases):
    for phrase in phrases:
        if re.search(phrase,text):
            return True
    return False

def type_of_value(var):
    try:
       return type(ast.literal_eval(var))
    except Exception:
        if var == 'true' or var == 'false':
            return bool
        elif var == 'file':
            return 'file'
        else:
            return str

def is_date(string):
    try: 
        parse(string)
        return True
    except ValueError:
        return False

def find_quoted_text(string):
    return re.findall(r'\"(.+?)\"',string) or re.findall(r'\'(.+?)\'',string)

def is_array(string):
    return re.findall(r'\[(.+?)\]',string)

def is_quoted_text(string):
    if re.findall(r'\"(.+?)\"',string) or re.findall(r'\'(.+?)\'',string):
        return True
    else:
        return False

def is_data_type(string):
    if is_quoted_text(string):
        return True
    value_type = type_of_value(string)
    if (value_type is float) or (value_type is int) or (value_type is bool) or (value_type is list) or (value_type == 'file')\
     or is_array(string) or is_password(string):
        return True
    elif is_date(string):
        return True
    else:
        return False

def is_password(string):
    for character in string:
        if character != '*':
            return False    
    return True
