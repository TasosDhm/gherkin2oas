from graphviz import Digraph
import os

def draw(resource_graph,state_graph,fixgraph,resources_folder):
    #---------------resource graph
    dot = Digraph(comment='')
    edgs = {}
    for resource,links in resource_graph.items():
        dot.node(resource,resource)
        for link in links:
            edgs[resource+link['resource']] = {'start':resource,'end':link['resource'],'lbl':''}
        for link in links:
            edgs[resource+link['resource']]['lbl'] += link['operation'] + ', '
    for name,e in edgs.items():
        e['lbl'] = e['lbl'].rstrip(', ')
        dot.edge(e['start'],e['end'],label=e['lbl'])
    dot.render(resources_folder + '/output_files/resource_graph.gv', view=True)
    os.remove(resources_folder + '/output_files/resource_graph.gv')

    #---------------state graph natural
    to_be_deleted = []
    dot = Digraph(comment='')
    edgs = {}
    for state in state_graph:
        dot.node(state_graph[state]['natural_state'],state_graph[state]['natural_state'])
        for link in state_graph[state]['links']:
            for new_state in state_graph:
                if state != new_state:
                    if link['operation'] == state_graph[new_state]['operation'] and link['natural_resource_name'] == state_graph[new_state]['resource']:
                            edge = state_graph[state]['natural_state']+state_graph[new_state]['natural_state']+ link['natural_verb'] + ' ' + link['natural_resource_name']
                            edgs[edge] = {'start':state_graph[state]['natural_state'], 'end':state_graph[new_state]['natural_state'], 'lbl':link['natural_verb'] + ' ' + link['natural_resource_name'],\
                                            'color':'black','end_code':state_graph[new_state]['code'],'end_resource':state_graph[new_state]['resource']}
                else:
                    if link['operation'] == state_graph[state]['operation'] and link['natural_resource_name'] == state_graph[state]['resource']:
                        edge = state_graph[state]['natural_state']+state_graph[state]['natural_state']+ link['natural_verb'] + ' ' + link['natural_resource_name']
                        edgs[edge] = {'start':state_graph[state]['natural_state'], 'end':state_graph[state]['natural_state'], 'lbl':link['natural_verb'] + ' ' + link['natural_resource_name'],\
                                        'color':'black','end_code':state_graph[state]['code'],'end_resource':state_graph[state]['resource']}
    if fixgraph == True:
        for edg in edgs:
            for scnd_edg in edgs:
                if edgs[edg] != edgs[scnd_edg]:
                    if edgs[edg]['start'] == edgs[scnd_edg]['start'] and edgs[edg]['lbl'] == edgs[scnd_edg]['lbl'] and edgs[edg]['end'] != edgs[scnd_edg]['end']\
                    and edgs[edg]['end_code'] == edgs[scnd_edg]['end_code'] and edgs[edg]['end_resource'] == edgs[scnd_edg]['end_resource']:
                        if (not edg in to_be_deleted) and (not scnd_edg in to_be_deleted):
                            if edgs[edg]['start'] == edgs[edg]['end']:
                                to_be_deleted.append(scnd_edg)
                            else:
                                print("Given I am on state " + edgs[edg]['start'] + " I want to transition to 1) " + edgs[edg]['end'] + " or 2) " + edgs[scnd_edg]['end'] + "?")
                                correct_state = 0
                                while correct_state != "1" and correct_state != "2" and correct_state != "both":
                                    correct_state = input('Correct transition (1, 2 or "both"): ')
                                if correct_state == "2":
                                    to_be_deleted.append(edg)
                                elif correct_state == "1":
                                    to_be_deleted.append(scnd_edg)
        for edg in to_be_deleted:
            silent_pop = edgs.pop(edg)
    else:
        for edg in edgs:
            for scnd_edg in edgs:
                if edgs[edg] != edgs[scnd_edg]:
                    if edgs[edg]['start'] == edgs[scnd_edg]['start'] and edgs[edg]['lbl'] == edgs[scnd_edg]['lbl'] and edgs[edg]['end'] != edgs[scnd_edg]['end']\
                    and edgs[edg]['end_code'] == edgs[scnd_edg]['end_code'] and edgs[edg]['end_resource'] == edgs[scnd_edg]['end_resource']:
                        edgs[edg]['color'] = 'red'
                        edgs[scnd_edg]['color'] = 'red'
        for edg in edgs:
            if edgs[edg]['start'] == edgs[edg]['end']:
                edgs[edg]['color'] = 'black'
    for name,e in edgs.items():
        dot.edge(e['start'],e['end'],label=e['lbl'],color=e['color'])
    dot.render(resources_folder + '/output_files/state_graph.gv', view=True)
    os.remove(resources_folder + '/output_files/state_graph.gv')

    #---------------state graph technical
    dot = Digraph(comment='')
    edgs = {}
    for state in state_graph:
        dot.node(state_graph[state]['http_state'],state_graph[state]['http_state'])
        for link in state_graph[state]['links']:
            for new_state in state_graph:
                if state != new_state:
                    if link['operation'] == state_graph[new_state]['operation'] and link['natural_resource_name'] == state_graph[new_state]['resource']:
                        edge = state_graph[state]['natural_state']+state_graph[new_state]['natural_state']+ link['natural_verb'] + ' ' + link['natural_resource_name']
                        edgs[edge] = {'start':state_graph[state]['http_state'], 'end':state_graph[new_state]['http_state'], 'lbl':link['operation'] + ' ' + link['natural_resource_name'],\
                        'color':'black','end_code':state_graph[new_state]['code'],'end_resource':state_graph[new_state]['resource']}
                else:
                    if link['operation'] == state_graph[state]['operation'] and link['natural_resource_name'] == state_graph[state]['resource']:
                        edge = state_graph[state]['natural_state']+state_graph[state]['natural_state']+ link['natural_verb'] + ' ' + link['natural_resource_name']
                        edgs[edge] = {'start':state_graph[state]['http_state'], 'end':state_graph[state]['http_state'], 'lbl':link['operation'] + ' ' + link['natural_resource_name'],\
                                        'color':'black','end_code':state_graph[state]['code'],'end_resource':state_graph[state]['resource']}
    if fixgraph == True:
        for edg in to_be_deleted:
            silent_pop = edgs.pop(edg)
    else:
        for edg in edgs:
            for scnd_edg in edgs:
                if edgs[edg] != edgs[scnd_edg]:
                    if edgs[edg]['start'] == edgs[scnd_edg]['start'] and edgs[edg]['lbl'] == edgs[scnd_edg]['lbl'] and edgs[edg]['end'] != edgs[scnd_edg]['end']\
                    and edgs[edg]['end_code'] == edgs[scnd_edg]['end_code'] and edgs[edg]['end_resource'] == edgs[scnd_edg]['end_resource']:
                        edgs[edg]['color'] = 'red'
                        edgs[scnd_edg]['color'] = 'red'
        for edg in edgs:
            if edgs[edg]['start'] == edgs[edg]['end']:
                edgs[edg]['color'] = 'black'
    for name,e in edgs.items():
        dot.edge(e['start'],e['end'],label=e['lbl'],color=e['color'])
    dot.render(resources_folder + '/output_files/http_state_graph.gv', view=True)
    os.remove(resources_folder + '/output_files/http_state_graph.gv')