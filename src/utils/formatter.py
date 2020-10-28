import re
import sys

http_codes = {'OK': '200', 'Created':'201', 'Accepted':'202', 'Bad Request': '400', 'Unauthorized': '401', 'Not Found': '404', 'Forbidden': '403', 'default': 'default'}
ids=[]

def generate_swagger(model, security):
    global ids
    paths_object = {}
    definitions_object = {}
    security_definitions_object = {}
    security_object = []
    all_paths = {}
    empty = {'get':{'request_params':[],'request_examples':[],'responses':{'default':{'params':[],'links':[],'param_examples':[],'message':''}}, 'description':''},
        'post':{'request_params':[],'request_examples':[],'responses':{'default':{'params':[],'links':[],'param_examples':[],'message':''}},'description':''},
        'put':{'request_params':[],'non_body_params':[],'request_examples':[],'responses':{'default':{'params':[],'links':[],'param_examples':[],'message':''}},'description':''},
        'delete':{'request_params':[],'request_examples':[],'responses':{'default':{'params':[],'links':[],'param_examples':[],'message':''}},'description':''}}
    path_hierarchy = {}
    roles = {}
    for resource,operations in model.items():
        path_hierarchy[resource] = model[resource].pop('resource_hierarchy')
        roles[resource] = model[resource].pop('resource_roles')
        # ---------------path seeds--------------------        
        collection_path = '/' + resource
        single_resource_path = ''
        get_query_path = False
        delete_query_path = False
        all_paths[resource] = {}
        # ---------------resource identifications--------------------
        for operation,op_model in operations.items():
            if op_model != empty[operation] and (operation != 'post'):        
                if operation == 'get' or operation == 'delete' or operation == 'put':   
                    flattened_params = list(flatten(op_model['request_params']))
                    if len(flattened_params) == 1:
                        param = flattened_params[0]
                        if not (operation == 'put' and 'model_type' in param): 
                            if param['name']:
                                single_resource_path = collection_path + '/{'+param['name']+'}'
                                all_paths[resource][operation] = single_resource_path 
                                if not single_resource_path in paths_object:
                                    paths_object[single_resource_path] = {}
                                if not operation in paths_object[single_resource_path]:
                                    paths_object[single_resource_path][operation] = {'parameters':[]}
                                paths_object[single_resource_path][operation]['parameters'].append(constr_path(param))
                    else:
                        if len(flattened_params) != 0:
                            all_paths[resource][operation] = collection_path
                            path_param = {}
                            for param in flattened_params:
                                if not (operation == 'put' and 'model_type' in param):  
                                    if 'path_param' in param and param['name']:
                                        path_param = param
                                        single_resource_path =  collection_path + '/{'+param['name']+'}'
                                        all_paths[resource][operation] =  single_resource_path
                                        if not single_resource_path in paths_object:
                                            paths_object[single_resource_path] = {}
                                        if not operation in paths_object[single_resource_path]:
                                            paths_object[single_resource_path][operation] = {'parameters':[]} 
                                        paths_object[single_resource_path][operation]['parameters'].append(constr_path(param))
        for operation,op_model in operations.items():
            if op_model != empty[operation] and (operation != 'post'):                 
                if len(op_model['request_params']) == 0:
                    if not single_resource_path:
                        single_resource_path = collection_path + '/{' + 'id}'
                        all_paths[resource][operation] = single_resource_path
                        paths_object[single_resource_path] = {}
                        paths_object[single_resource_path][operation] = {'parameters':[]}                     
                        paths_object[single_resource_path][operation]['parameters'].append({'name':'id','type':'integer','format':'int32','in':'path','required':True})
                    else: # assign a random, already found, single resource path
                        all_paths[resource][operation] = single_resource_path
                        if not operation in paths_object[single_resource_path]:
                            paths_object[single_resource_path][operation] = {'parameters':[]}
                        p = {}
                        for op,o_m in paths_object[single_resource_path].items():
                            for param in o_m['parameters']:
                                if param['in'] == 'path':
                                    p = param
                                    break
                        paths_object[single_resource_path][operation]['parameters'].append(p) 
        # ---------------queries--------------------             
        for operation,op_model in operations.items():
            if op_model != empty[operation] and (operation == 'get' or operation == 'delete'):        
                flattened_params = list(flatten(op_model['request_params']))
                if len(flattened_params) > 1:
                    if not all_paths[resource][operation]:
                        all_paths[resource][operation] = collection_path
                    if not collection_path in paths_object:
                        paths_object[collection_path] = {}
                    if not operation in paths_object[all_paths[resource][operation]]:
                        paths_object[all_paths[resource][operation]][operation] = {'parameters':[]}
                    for param in flattened_params:
                        if 'path_param' not in param and param['name']:
                            paths_object[all_paths[resource][operation]][operation]['parameters'].append(constr_query(param))            
                            if operation == 'get':
                                get_query_path = True
                            elif operation == 'delete':
                                delete_query_path = True                                                   
        for operation,op_model in operations.items():
            if op_model != empty[operation] and operation == 'put':
                if op_model['non_body_params']:
                    flattened_params = list(flatten(op_model['non_body_params']))
                    if not all_paths[resource][operation]:
                        all_paths[resource][operation] = collection_path
                    if not collection_path in paths_object:
                        paths_object[collection_path] = {}
                    if not operation in paths_object[all_paths[resource][operation]]:
                        paths_object[all_paths[resource][operation]][operation] = {'parameters':[]}
                    for param in flattened_params:
                        paths_object[all_paths[resource][operation]][operation]['parameters'].append(constr_query(param))                    
        # ---------------bodies--------------------   
        for operation,op_model in operations.items():
            if op_model != empty[operation] and (operation == 'post' or operation == 'put'):             
                object_name = ''
                if not operation in all_paths[resource]:
                    all_paths[resource][operation] = collection_path
                    this_path = collection_path
                else:
                    this_path = all_paths[resource][operation]
                if not this_path in paths_object:
                    paths_object[this_path] = {}
                if not operation in paths_object[this_path]:
                    paths_object[this_path][operation] = {'parameters':[]}
                if op_model['request_params']:
                    has_file = False
                    for param in op_model['request_params']:
                        if type(param) is list:
                            for domain_param in param:
                                if domain_param['type'] == 'file': # cannot have body AND formData parameters at the same time 
                                    paths_object[this_path][operation]['consumes'] = ["multipart/form-data","application/x-www-form-urlencoded"]
                                    paths_object[this_path][operation]['parameters'].append({'name':domain_param['name'],'in':'formData','type':domain_param['type'],'required':True}) 
                                    has_file = True
                    if not has_file:
                        object_name = resource + '_' + operation + '_request_body'
                        definitions_object[object_name] = {}
                        definitions_object[object_name]['type'] = 'object'
                        definitions_object[object_name]['properties'] = {}
                        if all(param['required'] == True for param in list(flatten(op_model['request_params']))):
                            paths_object[this_path][operation]['parameters'].append({'name':object_name,'in':'body','schema':{'$ref':'#/definitions/' + object_name},'required':True})
                        else:
                            paths_object[this_path][operation]['parameters'].append({'name':object_name,'in':'body','schema':{'$ref':'#/definitions/' + object_name}})
                        for param in op_model['request_params']:
                            if type(param) is list:
                                for domain_param in param:
                                    if 'required' in domain_param:
                                            if domain_param['required'] == True:
                                                if 'required' not in definitions_object[object_name].keys():
                                                    definitions_object[object_name]['required'] = [domain_param['name']]
                                                elif domain_param['name'] not in definitions_object[object_name]['required']:
                                                    definitions_object[object_name]['required'].append(domain_param['name'])  
                                    definitions_object[object_name]['properties'][domain_param['name']] = constr_schema(domain_param)              
                            elif 'model_type' in param:
                                model_definition_name = param['name']
                                if not model_definition_name in definitions_object:
                                    definitions_object[model_definition_name] = {}
                                    definitions_object[model_definition_name]['type'] = 'object'
                                    definitions_object[model_definition_name]['properties'] = {}
                                if 'required' in param:
                                    if param['required'] == True:
                                        if 'required' not in definitions_object[object_name].keys():
                                            definitions_object[object_name]['required'] = [param['name']]
                                        elif param['name'] not in definitions_object[object_name]['required']:
                                            definitions_object[object_name]['required'].append(param['name'])
                                definitions_object[object_name]['properties'][param['name']] = {'$ref':'#/definitions/' + param['name']}
                                for model_property in param['properties']:                                
                                    definitions_object[model_definition_name]['properties'][model_property['name']] = constr_schema(model_property)
                                    if param['example']:
                                        definitions_object[model_definition_name]['example'] = [param['example']]       
                            else:
                                if 'path_param' not in param:
                                    definitions_object[object_name]['properties'][param['name']] = {'type':'string'}
                        for example in op_model['request_examples']:
                            if not 'example' in definitions_object[object_name]:
                                definitions_object[object_name]['example'] = [example]
                            else:
                                definitions_object[object_name]['example'].append(example)
                elif not op_model['request_params'] and operation == 'post':
                    sys.exit('A unique post operation inside a resource file must ALWAYS specify at least one body parameter', resource, operation)
        for operation,op_model in operations.items():
            if op_model['description']:
                this_path = all_paths[resource][operation]
                if operation == 'post' or (operation == 'get' and get_query_path) or (operation == 'delete' and delete_query_path):
                    paths_object[this_path][operation]['description'] = op_model['description']
                else:
                   paths_object[this_path][operation]['description'] = op_model['description']
    # ---------------path hierarchies--------------------
    hierarchy_levels = [[]]
    total_paths_count = len(list(paths_object))
    completed_paths_count = 0
    new_paths = []
    done_resources = {}
    for resource,operations in model.items():
        done_resources[resource] = False
        if not path_hierarchy[resource]:
            done_resources[resource] = True
            for operation in operations:
                if operations[operation] != empty[operation]:
                    if not any(all_paths[resource][operation] == registered_path['path'] for registered_path in hierarchy_levels[0]):
                        path_params = []
                        if paths_object[all_paths[resource][operation]][operation]['parameters']:
                            for parameter in paths_object[all_paths[resource][operation]][operation]['parameters']:
                                if parameter['in'] == 'path':
                                    path_params.append(parameter)            
                        hierarchy_levels[0].append({'path':all_paths[resource][operation], 'path_params':path_params})
                        new_paths.append({'new_path':all_paths[resource][operation],'old_path':all_paths[resource][operation], 'path_params':[]})
                        completed_paths_count += 1
    # if not hierarchy_levels[0]:
    #     sys.exit('It seems that a path hierarchy was specified in every resource file. For path hierarchies to make sense, at least one resource file must have no hierarchies')
    if hierarchy_levels[0]:
        high_hierarchy_level = 0
        low_hierarchy_level = 1
        hierarchy_levels.append([])
        while completed_paths_count != len(list(paths_object)):
            for resource in model:
                if path_hierarchy[resource] and not done_resources[resource]:
                    inherited_path_params = []
                    if path_hierarchy[resource]['linking_parameter']:
                        found_link = False
                        for higher_hierarchy_path in hierarchy_levels[high_hierarchy_level]:
                            if re.search(r'\b' + path_hierarchy[resource]['hierarchy_resource'] + r'\b',higher_hierarchy_path['path']):
                                if higher_hierarchy_path['path_params']:
                                    for path_param in higher_hierarchy_path['path_params']:
                                        if path_param['name'] == path_hierarchy[resource]['linking_parameter'] and re.search(path_param['name'] + '}$', higher_hierarchy_path['path']):
                                            found_link = True
                                            done_resources[resource] = True
                                    if found_link == True:
                                        for path_param in higher_hierarchy_path['path_params']:
                                            if path_param not in inherited_path_params:
                                                inherited_path_params.append(path_param)
                                        for operation in model[resource]:
                                            if model[resource][operation] != empty[operation]:
                                                if (operation == 'get' or operation == 'delete' or operation == 'put'):
                                                    for parameter in paths_object[all_paths[resource][operation]][operation]['parameters']:
                                                        if parameter['in'] == 'path' and parameter not in inherited_path_params:
                                                            inherited_path_params.append(parameter)
                                                new_path = higher_hierarchy_path['path'] + all_paths[resource][operation]
                                                if not any(registered_path['path'] == new_path for registered_path in hierarchy_levels[low_hierarchy_level]):
                                                    new_paths.append({'new_path':new_path, 'old_path':all_paths[resource][operation],'path_params':inherited_path_params})
                                                    hierarchy_levels[low_hierarchy_level].append({'path':new_path, 'path_params':inherited_path_params})
                                                    completed_paths_count += 1
                                        break                       
            high_hierarchy_level += 1
            low_hierarchy_level += 1
            hierarchy_levels.append([])

        for path in new_paths:
            new_path = path['new_path']
            old_path = path['old_path']
            if old_path in paths_object:
                paths_object[new_path] = paths_object.pop(old_path)
                for parameter in path['path_params']:
                    for operation in paths_object[new_path]:
                        if parameter not in paths_object[new_path][operation]['parameters']:
                            paths_object[new_path][operation]['parameters'].append(parameter)
    

        for resource in model:
            for operation in model[resource]:
                if model[resource][operation] != empty[operation]:
                    for path in new_paths:
                        if all_paths[resource][operation] == path['old_path']:
                            all_paths[resource][operation] = path['new_path']
                            break
    # ---------------responses--------------------
    for resource,operations in model.items():
        for operation,op_model in operations.items():
            if op_model != empty[operation]:
                this_path = all_paths[resource][operation]
                object_name = ''
                for response_type in op_model['responses']:
                    if op_model['responses'][response_type]['params'] or op_model['responses'][response_type]['links'] or op_model['responses'][response_type]['message']:
                        status_message = op_model['responses'][response_type]['message']
                        if not status_message:
                            status_message = 'None'
                        # create definition object entry
                        if op_model['responses'][response_type]['params'] or op_model['responses'][response_type]['links']:
                            object_name = resource + '_' + operation + '_' + http_codes[response_type] + '_response'
                            definitions_object[object_name] = {}
                            definitions_object[object_name]['type'] = 'object'
                        # create path object entry
                        if not 'responses' in paths_object[this_path][operation]:
                            paths_object[this_path][operation]['responses'] = {}
                        if not response_type in paths_object[this_path][operation]['responses']:
                            if op_model['responses'][response_type]['params'] or op_model['responses'][response_type]['links']:
                                if response_type in http_codes:
                                    paths_object[this_path][operation]['responses'][http_codes[response_type]] = {'description':status_message,'schema':{'$ref':'#/definitions/' + object_name}}
                                else:
                                    paths_object[this_path][operation]['responses']['default'] = {'description':'None','schema':{'$ref':'#/definitions/' + object_name}} 
                            elif op_model['responses'][response_type]['message']:
                                if response_type in http_codes:
                                    paths_object[this_path][operation]['responses'][http_codes[response_type]] = {'description':status_message}
                                else:
                                    paths_object[this_path][operation]['responses']['default'] = {'description':'None'}
                    if op_model['responses'][response_type]['params']: 
                        if not 'properties' in definitions_object[object_name]:                 
                            definitions_object[object_name]['properties'] = {}     
                        for param in op_model['responses'][response_type]['params']:
                            if type(param) is list:
                                for domain_param in param:             
                                    if 'required' in domain_param:
                                        if domain_param['required'] == True:
                                            if 'required' not in definitions_object[object_name]:
                                                definitions_object[object_name]['required'] = [domain_param['name']]
                                            elif domain_param['name'] not in definitions_object[object_name]['required']:
                                                definitions_object[object_name]['required'].append(domain_param['name'])
                                    definitions_object[object_name]['properties'][domain_param['name']] = constr_schema(domain_param)
                            elif 'model_type' in param:
                                model_definition_name = param['name']
                                if not model_definition_name in definitions_object:
                                    definitions_object[model_definition_name] = {}
                                    definitions_object[model_definition_name]['type'] = 'object'
                                    definitions_object[model_definition_name]['properties'] = {}
                                if 'required' in param:
                                    if param['required'] == True:
                                        if 'required' not in definitions_object[object_name].keys():
                                            definitions_object[object_name]['required'] = [param['name']]
                                        elif param['name'] not in definitions_object[object_name]['required']:
                                            definitions_object[object_name]['required'].append(param['name'])
                                definitions_object[object_name]['properties'][param['name']] = {'$ref':'#/definitions/' + model_definition_name}
                                for model_property in param['properties']:
                                    definitions_object[model_definition_name]['properties'][model_property['name']] = constr_schema(model_property)
                                if param['example']:
                                    definitions_object[model_definition_name]['example'] = [param['example']]  
                            else:
                                definitions_object[object_name]['properties'][param['name']] = {'type':'string'}
                        for example in op_model['responses'][response_type]['param_examples']:
                            if not 'example' in definitions_object[object_name]:
                                definitions_object[object_name]['example'] = [example]
                            else:
                                definitions_object[object_name]['example'].append(example)   
                    if op_model['responses'][response_type]['links']:
                        if not 'x-links' in definitions_object[object_name]:
                            definitions_object[object_name]['x-links'] = []                         
                        for link in op_model['responses'][response_type]['links']:
                            if link['resource'] in all_paths:
                                if link['operation'] in all_paths[link['resource']]:
                                    hateoas_link = {'path':all_paths[link['resource']][link['operation']],'operation':link['operation']}
                                    if hateoas_link not in definitions_object[object_name]['x-links']:
                                        definitions_object[object_name]['x-links'].append(hateoas_link) 
                                else:
                                    print('No ' + link['operation'] + ' operation found in resource file ' + link['resource'] + ' but such a hateoas link was described in ' + resource + ' resource file')
                            else:
                                print('No ' + link['operation'] + ' operation found in resource file ' + link['resource'] + ' but such a hateoas link was described in ' + resource + ' resource file')
    # ---------------security--------------------
    found_paths = list(paths_object.keys())
    flag_0 = False
    if security == 'access_token':   
        for resource,operations in model.items():
            security_definitions_object = {"cookieAuth" : {"type": "apiKey", "in" : "cookie", "name" : "access_token"}}
            for role,scopes in roles[resource].items():
                for scope in scopes:
                    paths_object[all_paths[resource][scope['operation']]][scope['operation']]["security"] = [{"cookieAuth" : []}]
                    flag_0 = True 
        if flag_0 == False:
            security_object = [{"cookieAuth" : []}]
    else:
        for resource,operations in model.items():
            for role,scopes in roles[resource].items():
                security_definitions_object[role] = {'type':'oauth2','flow':'implicit',"authorizationUrl": "http://swagger.io/api/oauth/dialog",'scopes':{}}
                for scope in scopes:
                    security_definitions_object[role]['scopes'][scope['operation']+':'+all_paths[resource][scope['operation']]] = 'No description'
                    if not 'security' in paths_object[all_paths[resource][scope['operation']]][scope['operation']].keys():
                        paths_object[all_paths[resource][scope['operation']]][scope['operation']]['security'] = [{role:[scope['operation']+':'+all_paths[resource][scope['operation']]]}]
                    else:
                        flag = False
                        for i, security_requirement in enumerate(paths_object[all_paths[resource][scope['operation']]][scope['operation']]['security']):
                            if role in paths_object[all_paths[resource][scope['operation']]][scope['operation']]['security'][i].keys():
                                paths_object[all_paths[resource][scope['operation']]][scope['operation']]['security'][i][role].append(scope['operation']+':'+all_paths[resource][scope['operation']])
                                flag = True
                        if flag == False:
                            paths_object[all_paths[resource][scope['operation']]][scope['operation']]['security'] = [{role:[scope['operation']+':'+all_paths[resource][scope['operation']]]}]
    # ---------------do some cleaning--------------------                            
    empty_defs = []
    for definition, definition_object in definitions_object.items():
        if 'properties' in definition_object:
            if not definition_object['properties']:
                empty_defs.append(definition)
    for empty_def in empty_defs:
        silence = definitions_object.pop(empty_def)
    # ---------------create unique path ids and update paths and params everywhere in the specification--------------------  
    generic_id_param = -1
    new_paths = []
    old_paths = paths_object.keys()
    for path in old_paths:
        new_path = re.sub(r'([^/]+)/{id}', rep, path)
        for operation in paths_object[path]:
            for i,parameter in enumerate(paths_object[path][operation]['parameters']):
                if parameter['in'] == 'path' and parameter['name'] == 'id' and ids:
                    generic_id_param = i
                    for new_id in ids:
                        paths_object[path][operation]['parameters'].append({'type':'integer','name':new_id,'required':True,'format':'int32','in':'path'})
            if generic_id_param != -1:
                silence = paths_object[path][operation]['parameters'].pop(generic_id_param)
            generic_id_param = -1
        ids = []
        if path in paths_object:
            paths_object[new_path] = paths_object.pop(path)

    for definition in definitions_object:
        if 'x-links' in definitions_object[definition]:
            new_x_links = []
            for x_link in definitions_object[definition]['x-links']:
                new_x_links.append({'path':re.sub(r'([^/]+)/{id}', rep, x_link['path']),'operation':x_link['operation']})
            definitions_object[definition]['x-links'] = new_x_links

    # remove duplicate parameters from queries, if any
    for path in paths_object:
        for operation in paths_object[path]:
            if operation == "get":
                unique_parameter_list = []
                for parameter in paths_object[path][operation]['parameters']:
                    if parameter not in unique_parameter_list:
                        unique_parameter_list.append(parameter)
                paths_object[path][operation]['parameters'] = unique_parameter_list
            

    return {'paths':paths_object,'definitions':definitions_object,'securityDefinitions':security_definitions_object, 'security':security_object}

def flatten(container):
    for i in container:
        if isinstance(i, (list,tuple)):
            for j in flatten(i):
                yield j
        else:
            yield i

def constr_path(param):
    param_properties = {}
    for param_property_name,param_property_value in param.items():
        if param_property_name in ['name','type','format','maxItems','minItems','minimum','maximum','minLength','maxLength','description']:
            param_properties[param_property_name] = param_property_value
    param_properties['required'] = True
    param_properties['in'] = 'path'
    if 'type' not in param_properties:
        if param['name'] == 'id':
            param_properties['type'] = 'integer'
            param_properties['format'] = 'int32'
        else:
            param_properties['type'] = 'string'
    return param_properties

def constr_query(param):
    param_properties = {}
    for param_property_name,param_property_value in param.items():
        if param_property_name in ['name','type','format','maxItems','minItems','minimum','maximum','minLength','maxLength','required','description']:
            param_properties[param_property_name] = param_property_value
    param_properties['in'] = 'query'
    if 'type' not in param_properties:
        if param['name'] == 'id':
            param_properties['type'] = 'integer'
            param_properties['format'] = 'int32'
        else:
            param_properties['type'] = 'string'
    return param_properties

def constr_schema(param):
    param_properties = {}
    for param_property_name,param_property_value in param.items():
        if param_property_name in ['type','format','maxItems','minItems','minimum','maximum','minLength','maxLength','items','description']:
            if param_property_name == 'type' and param_property_value == 'file':
                print('File type in response is bugged, see https://github.com/OAI/OpenAPI-Specification/issues/260')
            else:
                param_properties[param_property_name] = param_property_value
    return param_properties 

def rep(m):
    global ids
    ids.append('{}_id'.format(m.group(1)))
    return '{0}/{{{0}_id}}'.format(m.group(1))


