import argparse
import logging
import os
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from xml.dom import minidom
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

from lxml import etree, objectify


class Graph:
    def __init__(self, vertices):
        self.graph = defaultdict(list)  # dictionary containing adjacency List
        self.V = vertices  # No. of vertices

    # function to add an edge to graph
    def add_edge(self, u, v):
        self.graph[u].append(v)

    # A recursive function used by topologicalSort
    def topological_sort_util(self, v, visited, stack):

        # Mark the current node as visited.
        visited[v] = True

        # Recur for all the vertices adjacent to this vertex
        for i in self.graph[v]:
            if visited[i] is False:
                self.topological_sort_util(i, visited, stack)

        # Push current vertex to stack which stores result
        stack.insert(0, v)

    # The function to do Topological Sort. It uses recursive topologicalSortUtil()
    def topological_sort(self):
        # Mark all the vertices as not visited
        visited = [False] * self.V
        stack = []

        # Call the recursive helper function to store Topological Sort starting from all vertices one by one
        for i in range(self.V):
            if visited[i] is False:
                self.topological_sort_util(i, visited, stack)

        # return contents of stack
        return stack

    def is_cyclic_util(self, v, visited, recStack, cycle):

        # Mark current node as visited and adds to recursion stack
        visited[v] = True
        recStack[v] = True

        # Recur for all neighbours; if any neighbour is visited and in recStack then graph is cyclic
        for neighbour in self.graph[v]:
            cycle.append(neighbour)
            if v != neighbour:
                if visited[neighbour] is False:
                    if self.is_cyclic_util(neighbour, visited, recStack, cycle) is True:
                        return True
                elif recStack[neighbour] is True:
                    return True

        # The node needs to be poped from recursion stack before function ends
        recStack[v] = False
        return False

    def is_cyclic(self):
        visited = [False] * self.V
        recStack = [False] * self.V
        cycle = []
        for node in range(self.V):
            cycle.append(node)
            if visited[node] is False:
                if self.is_cyclic_util(node, visited, recStack, cycle) is True:
                    return cycle
        return False


def main():
    events = []
    aswcs = []
    swc_types = []
    # parsing the command line arguments
    parser = argparse.ArgumentParser()
    arg_parse(parser)
    args = parser.parse_args()
    input_cfg_path = args.inp
    aswc_path = args.aswc
    acme_path = args.acme
    rte_path =  args.rte
    input_path=[]
    input_path.append(aswc_path)
    input_path.append(acme_path)
    input_path.append(rte_path)
    composition_name = ""
    disable = False
    if args.dec:
        disable = True
    if args.compo:
        composition_name = args.compo
    mem_map = False
    if args.MemMap:
        mem_map = True
    if mem_map:
        if composition_name == "":
            print("Composition name must be set if MemMap parameter is present")
            sys.exit(1)
    rte = False
    if args.Rte:
        rte = True
    if rte:
        if composition_name == "":
            print("Composition name must be set if Rte parameter is present")
            sys.exit(1)
    if args.default_duration == '':
        default_duration = '0'
    else:
        default_duration = int(args.default_duration)
    error = False

    if mem_map == False and (aswc_path != '' and acme_path != '' and rte_path != ''):
        print("\nError MemMap parameter is not present but input path is!\n")
        error = True
        sys.exit(1)

    # if rte == False and input_cfg_path != '':
    #     print("\nError Rte parameter is  not present but input path is!\n")
    #     error = True
    #     sys.exit(1)

    path_list = []
    file_list = []
    entry_list = []
    config_path = args.osconfig
    config_path = config_path.replace("\\", "/")
    if mem_map:
        type=1
        for elem in input_path:
            for path in elem:
                if path.startswith('@'):
                    file = open(path[1:])
                    line_file = file.readline()
                    while line_file != "":
                        line_file = line_file.rstrip()
                        line_file = line_file.lstrip()
                        if "#" not in line_file:
                            if os.path.isdir(line_file):
                                obj = {}
                                obj['FILE'] = line_file
                                if type == 1:
                                    obj['TYPE'] = 'aswc'
                                if type == 2:
                                    obj['TYPE'] = 'acme'
                                if type == 3:
                                    obj['TYPE'] = 'rte'
                                path_list.append(obj)
                            elif os.path.isfile(line_file):
                                obj = {}
                                obj['FILE'] = line_file
                                if type == 1:
                                    obj['TYPE'] = 'aswc'
                                if type == 2:
                                    obj['TYPE'] = 'acme'
                                if type == 3:
                                    obj['TYPE'] = 'rte'
                                file_list.append(obj)
                            else:
                                print("\nError defining the input path: " + line_file + "\n")
                                error = True
                            line_file = file.readline()
                        else:
                            line_file = file.readline()
                    file.close()
                else:
                    if os.path.isdir(path):
                        obj = {}
                        obj['FILE'] = path
                        if type == 1:
                            obj['TYPE'] = 'aswc'
                        if type == 2:
                            obj['TYPE'] = 'acme'
                        if type == 3:
                            obj['TYPE'] = 'rte'
                        path_list.append(obj)
                    elif os.path.isfile(path):
                        obj = {}
                        obj['FILE'] = path
                        if type == 1:
                            obj['TYPE'] = 'aswc'
                        if type == 2:
                            obj['TYPE'] = 'acme'
                        if type == 3:
                            obj['TYPE'] = 'rte'
                        file_list.append(obj)
                    else:
                        print("\nError defining the input path: " + path + "\n")
                        error = True
            type = type + 1
        for path in path_list:
            for (dirpath, dirnames, filenames) in os.walk(path['FILE']):
                for file in filenames:
                    fullname = dirpath + '\\' + file
                    obj = {}
                    obj['FILE'] = fullname
                    obj['TYPE'] = path['TYPE']
                    file_list.append(obj)

        [entry_list.append(elem) for elem in file_list if elem['FILE'] not in entry_list]

    path_cfg_list = []
    file_cfg_list = []
    entry_cfg_list = []
    #if rte:
    for path in input_cfg_path:
        if path.startswith('@'):
            file = open(path[1:])
            line_file = file.readline()
            while line_file != "":
                line_file = line_file.rstrip()
                line_file = line_file.lstrip()
                if "#" not in line_file:
                    if os.path.isdir(line_file):
                        path_cfg_list.append(line_file)
                    elif os.path.isfile(line_file):
                        file_cfg_list.append(line_file)
                    else:
                        print("\nError defining the input path: " + line_file + "\n")
                        error = True
                    line_file = file.readline()
                else:
                    line_file = file.readline()
            file.close()
        else:
            if os.path.isdir(path):
                path_cfg_list.append(path)
            elif os.path.isfile(path):
                file_cfg_list.append(path)
            else:
                print("\nError defining the input path: " + path + "\n")
                error = True
    for path in path_cfg_list:
        for (dirpath, dirnames, filenames) in os.walk(path):
            for file in filenames:
                fullname = dirpath + '\\' + file
                file_cfg_list.append(fullname)
    [entry_cfg_list.append(elem) for elem in file_cfg_list if elem not in entry_cfg_list]

    total_list=[]
    total_list = entry_list + entry_cfg_list

    if error:
        sys.exit(1)
    output_path = args.out_epc
    #output_script = args.out_script
    output_epc = args.out_epc
    output_log = args.out_log
    swc_allocation=[]
    if output_path:
        if not os.path.isdir(output_path):
            print("\nError defining the output path!\n")
            sys.exit(1)
        if output_log:
            if not os.path.isdir(output_log):
                print("\nError defining the output log path!\n")
                sys.exit(1)
            logger = set_logger(output_log)
            debugger = set_debugger(output_log)
            swc_allocation,events,aswcs,swc_types = create_list(entry_list, entry_cfg_list, config_path, events, aswcs, swc_types, output_path, default_duration, logger, debugger)
            if mem_map:
                #create_mapping(entry_list, composition_name, output_path, logger, swc_allocation)
                create_mapping(entry_list,entry_cfg_list, composition_name, output_path, logger, swc_allocation)
            #create_script(events, aswcs, output_path)
            if rte:
                create_configuration(events, aswcs, swc_types, output_path)
        else:
            logger = set_logger(output_path)
            debugger = set_debugger(output_path)
            swc_allocation,events,aswcs,swc_types = create_list(entry_list, entry_cfg_list, config_path, events, aswcs, swc_types, output_path, default_duration, logger, debugger)
            if mem_map:
                #create_mapping(entry_list, composition_name, output_path, logger, swc_allocation)
                create_mapping(entry_list,entry_cfg_list, composition_name, output_path, logger, swc_allocation)
            #create_script(events, aswcs, output_path)
            if rte:
                create_configuration(events, aswcs, swc_types, output_path)
    elif not output_path:
        # if output_script:
        #     if not os.path.isdir(output_script):
        #         print("\nError defining the output configuration path!\n")
        #         sys.exit(1)
        #     if output_log:
        #         if not os.path.isdir(output_log):
        #             print("\nError defining the output log path!\n")
        #             sys.exit(1)
        #         logger = set_logger(output_log)
        #         if mem_map:
        #             create_mapping(entry_list, composition_name, output_script, logger)
        #     else:
        #         logger = set_logger(output_script)
        #         if mem_map:
        #             create_mapping(entry_list, composition_name, output_script, logger)
        if output_epc:
            if not os.path.isdir(output_epc):
                print("\nError defining the output configuration path!\n")
                sys.exit(1)
            if output_log:
                if not os.path.isdir(output_log):
                    print("\nError defining the output log path!\n")
                    sys.exit(1)
                logger = set_logger(output_log)
                debugger = set_debugger(output_log)
                swc_allocation,events,aswcs,swc_types = create_list(entry_list, entry_cfg_list, config_path, events, aswcs, swc_types, output_epc, default_duration, logger, debugger)
                if rte:
                    create_configuration(events, aswcs, swc_types, output_epc)
                if mem_map:
                    #create_mapping(entry_list, composition_name, output_epc, logger, swc_allocation)
                    create_mapping(entry_list,entry_cfg_list, composition_name, output_path, logger, swc_allocation)
            else:
                logger = set_logger(output_epc)
                debugger = set_debugger(output_epc)
                swc_allocation,events,aswcs,swc_types = create_list(entry_list, entry_cfg_list, config_path, events, aswcs, swc_types, output_epc, default_duration, logger, debugger)
                if rte:
                    create_configuration(events, aswcs, swc_types, output_epc)
                if mem_map:
                    #create_mapping(entry_list, composition_name, output_epc, logger, swc_allocation)
                    create_mapping(entry_list,entry_cfg_list, composition_name, output_path, logger, swc_allocation)
    else:
        print("\nNo output path defined!\n")
        sys.exit(1)


# def findMin(slot_list, frequency):
#     """
#     :param slot_list: list of slots to be filled (given as a list of lists)
#     :param frequency: the frequency of a given event
#     :return: position in the list that corresponds to the element with the least events already mapped
#     It takes the first <frequency> elements from the <slot_list> and return the position of the smallest length element
#     """
#     firstNSlots = slot_list[:frequency]
#     pos = firstNSlots.index(min(firstNSlots, key=len))
#     return pos
def findMin(slot_list, frequency):
    """
    :param slot_list: list of slots to be filled (given as a list of lists)
    :param frequency: the frequency of a given event
    :return: position in the list that corresponds to the element with the smallest duration of events already mapped
    It takes the first <frequency> elements from the <slot_list> and return the position of the smallest duration slot
    """
    firstNSlots = slot_list[:frequency]
    min_duration = 1000
    smallest_slot = 0
    for slot in firstNSlots:
        slot_duration = sum(float(event['DURATION']) for event in slot)
        if slot_duration < min_duration:
            min_duration = slot_duration
            smallest_slot = firstNSlots.index(slot)
    return smallest_slot

def findSlot(slot_list, frequency, limit):
    firstNSlots = slot_list[:frequency]
    min_duration = 1000
    smallest_slot = 0
    slot_not_found = True
    for slot in firstNSlots:
        slot_duration = sum(float(event['DURATION']) for event in slot)
        if slot_duration < limit:
            smallest_slot = firstNSlots.index(slot)
            slot_not_found = False
        else:
            slot_not_found = True
        if slot_not_found:
            if slot_duration < min_duration:
                min_duration = slot_duration
                smallest_slot = firstNSlots.index(slot)
    return smallest_slot



def insertElement(slot_list, position, frequency, element):
    """
    :param slot_list: list of slots to be filled (given as a list of lists)
    :param position:  the position of which the element will be inserted
    :param frequency: the frequency of a given event
    :param element: the element to be inserted
    :return: the modified list
    This function will insert the element <element> on the position <position> and on all other elements with frequency <frequency>
    """
    iteration = 0
    for sublist in slot_list:
        if iteration == position or iteration % frequency == position:
            sublist.append(element)
        iteration = iteration + 1
    return slot_list


def move_to_front(event_list):
    """
    :param event_list: the list of events to be computed
    :return: the modified list
    This function will move to the begginig of the list the events that have AFTER or BEFORE constraints
    """
    for elem in event_list:
        if elem['AFTER'] or elem['BEFORE']:
            event_list.insert(0, event_list.pop(event_list.index(elem)))
    return event_list


def merge_events(event_list, logger, output_path):
    event_names = []
    events = []
    for index1 in range(len(event_list)):
        if event_list[index1]['EVENT'] not in event_names:
            event_names.append(event_list[index1]['EVENT'])
            events.append(event_list[index1])
        else:
            for index2 in range(len(event_list)):
                if index1 != index2:
                    if event_list[index1]['EVENT'] == event_list[index2]['EVENT']:
                        index_of_events = events.index(event_list[index2])
                        # print(event_list[index1]['NAME'])
                        if events[index_of_events]['DURATION'] == '0':
                            events[index_of_events]['DURATION'] = event_list[index1]['DURATION']
                        if events[index_of_events]['SPECIFIC-TASK'] is None:
                            events[index_of_events]['SPECIFIC-TASK'] = event_list[index1]['SPECIFIC-TASK']
                        else:
                            if event_list[index2]['SPECIFIC-TASK'] != event_list[index1]['SPECIFIC-TASK']:
                                logger.error('The event with the name ' + event_list[index2]['NAME'] + ' and reference ' + event_list[index2]['EVENT'] + ' has multiple SPECIFIC-TASK allocated')
                                print('The event with the name ' + event_list[index2]['NAME'] + ' and reference ' + event_list[index2]['EVENT'] + ' has multiple SPECIFIC-TASK allocated')
                                #os.remove(output_path + '/RTE_Config.xml')
                                sys.exit(1)
                        if not events[index_of_events]['AFTER-EVENT']:
                            events[index_of_events]['AFTER-EVENT'] = event_list[index1]['AFTER-EVENT']
                        else:
                            if event_list[index1]['AFTER-EVENT']:
                                for elem in event_list[index1]['AFTER-EVENT']:
                                    if elem not in events[index_of_events]['AFTER-EVENT']:
                                        events[index_of_events]['AFTER-EVENT'].append(elem)
                        if not events[index_of_events]['BEFORE-EVENT']:
                            events[index_of_events]['BEFORE-EVENT'] = event_list[index1]['BEFORE-EVENT']
                        else:
                            if event_list[index1]['BEFORE-EVENT']:
                                for elem in event_list[index1]['BEFORE-EVENT']:
                                    if elem not in events[index_of_events]['BEFORE-EVENT']:
                                        events[index_of_events]['BEFORE-EVENT'].append(elem)
                        if events[index_of_events]['CATEGORY'] == 'DEFAULT':
                            events[index_of_events]['CATEGORY'] = event_list[index1]['CATEGORY']
                    # else:
                    #     events.append(event_list[index1])
    return events


def arg_parse(parser):
    parser.add_argument('-in', '--inp', nargs='*', help="Input path or file", required=False, default="")
    parser.add_argument('-osconfig', '--osconfig', help="Os configuration script", required=True, default="")
    #parser.add_argument('-out', '--out', help="Output path", required=False, default="")
    parser.add_argument('-default_duration', '--default_duration', help="event default duration (µs)", required=False, default="")
    #parser.add_argument('-out_script', '--out_script', help="output path for memory mapping script file", required=False, default="")
    parser.add_argument('-out_epc', '--out_epc', help="output path for RTE configuration file", required=False, default="")
    parser.add_argument('-out_log', '--out_log', help="output path for log file", required=False, default="")
    parser.add_argument('-MemMap', action="store_const", const="-MemMap", required=False, default="")
    parser.add_argument('-compo', '--compo', help="composition name", required=False, default="")
    parser.add_argument('-Rte', action="store_const", const="-Rte", required=False, default="")
    parser.add_argument('-in_aswc', '--aswc', nargs='*', help="Input aswc path or file", required=False, default="")
    parser.add_argument('-in_acme', '--acme', nargs='*', help="Input acme path or file", required=False, default="")
    parser.add_argument('-in_rte', '--rte', nargs='*', help="Input rte path or file", required=False, default="")
    parser.add_argument('-disable_error_check', '--dec', help="disables error check", required=False, default="")

def set_logger(path):
    # logger creation and setting
    logger = logging.getLogger('result')
    hdlr = logging.FileHandler(path + '/result_RTE.log')
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.INFO)
    open(path + '/result_RTE.log', 'w').close()
    return logger


def set_debugger(path):
    debugger = logging.getLogger('debug')
    hdlr = logging.FileHandler(path + '/debug_result.csv')
    debugger.addHandler(hdlr)
    debugger.setLevel(logging.INFO)
    open(path + '/debug_result.csv', 'w').close()
    return debugger


def create_list(file_arxml_list, files_list, config, events, aswcs, swc_types, output_path, default_duration, logger, debugger):
    events_rte = []
    events_aswc = []
    swc_allocation = []
    ibehaviors = []
    implementations = []
    compos = []
    error_no = 0
    warning_no = 0
    info_no = 0
    tasks_general = []
    file_list_complete=[]
    file_list_complete = file_arxml_list + files_list
    if default_duration is None:
        event_duration = 0.001
    else:
        event_duration = default_duration
    #try:
    # parse input files
    for file in file_arxml_list: 
        if file['FILE'].endswith('.arxml'):
            try:
                check_if_xml_is_wellformed(file['FILE'])
                logger.info(' The file ' + file['FILE'] + ' is well-formed')
                info_no = info_no + 1
            except Exception as e:
                logger.error(' The file ' + file['FILE'] + ' is not well-formed: ' + str(e))
                print(' The file ' + file['FILE'] + ' is not well-formed: ' + str(e))
                error_no = error_no + 1
            parser = etree.XMLParser(remove_comments=True)
            tree = objectify.parse(file['FILE'], parser=parser)
            root = tree.getroot()
            ascre_event = root.findall(".//{http://autosar.org/schema/r4.0}ASYNCHRONOUS-SERVER-CALL-RETURNS-EVENT")
            for elem in ascre_event:
                obj_event = {}
                obj_event['NAME'] = elem.find('{http://autosar.org/schema/r4.0}SHORT-NAME').text
                obj_event['EVENT-TYPE'] = elem.tag.split('}')[-1]
                obj_event['TYPE'] = "EVT"
                obj_event['START-ON-EVENT'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                obj_event['DURATION'] = event_duration
                obj_event['BEFORE-EVENT'] = []
                obj_event['AFTER-EVENT'] = []
                obj_event['REF'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                obj_event['EVENT-REF'] = ''
                obj_event['CORE'] = ""
                obj_event['PARTITION'] = ""
                obj_event['CATEGORY'] = "DEFAULT"
                obj_event['SPECIFIC-TASK'] = None
                if elem.find('{http://autosar.org/schema/r4.0}ACTIVATION') is not None:
                    obj_event['ACTIVATION'] = elem.find('{http://autosar.org/schema/r4.0}ACTIVATION').text
                else:
                    obj_event['ACTIVATION'] = None
                if elem.find('{http://autosar.org/schema/r4.0}PERIOD') is not None:
                    obj_event['PERIOD'] = elem.find('{http://autosar.org/schema/r4.0}PERIOD').text
                else:
                    obj_event['PERIOD'] = None
                obj_event['IB'] = elem.getparent().getparent().getchildren()[0].text
                obj_event['ASWC'] = elem.getparent().getparent().getparent().getparent().getchildren()[0].text
                obj_event['ROOT'] = elem.getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].text
                if elem.getparent().getparent().getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].tag == '{http://autosar.org/schema/r4.0}SHORT-NAME':
                    obj_event['ROOT'] = elem.getparent().getparent().getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].text + '/' + obj_event['ROOT']
                events_aswc.append(obj_event)
            be_event = root.findall(".//{http://autosar.org/schema/r4.0}BACKGROUND-EVENT")
            for elem in be_event:
                obj_event = {}
                obj_event['NAME'] = elem.find('{http://autosar.org/schema/r4.0}SHORT-NAME').text
                obj_event['EVENT-TYPE'] = elem.tag.split('}')[-1]
                obj_event['TYPE'] = "EVT"
                obj_event['START-ON-EVENT'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                obj_event['DURATION'] = event_duration
                obj_event['BEFORE-EVENT'] = []
                obj_event['AFTER-EVENT'] = []
                obj_event['REF'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                obj_event['EVENT-REF'] = ''
                obj_event['CORE'] = ""
                obj_event['PARTITION'] = ""
                obj_event['CATEGORY'] = "DEFAULT"
                obj_event['SPECIFIC-TASK'] = None
                if elem.find('{http://autosar.org/schema/r4.0}ACTIVATION') is not None:
                    obj_event['ACTIVATION'] = elem.find('{http://autosar.org/schema/r4.0}ACTIVATION').text
                else:
                    obj_event['ACTIVATION'] = None
                if elem.find('{http://autosar.org/schema/r4.0}PERIOD') is not None:
                    obj_event['PERIOD'] = elem.find('{http://autosar.org/schema/r4.0}PERIOD').text
                else:
                    obj_event['PERIOD'] = None
                obj_event['IB'] = elem.getparent().getparent().getchildren()[0].text
                obj_event['ASWC'] = elem.getparent().getparent().getparent().getparent().getchildren()[0].text
                obj_event['ROOT'] = elem.getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].text
                if elem.getparent().getparent().getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].tag == '{http://autosar.org/schema/r4.0}SHORT-NAME':
                    obj_event['ROOT'] = elem.getparent().getparent().getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].text + '/' + obj_event['ROOT']
                events_aswc.append(obj_event)
            dree_event = root.findall(".//{http://autosar.org/schema/r4.0}DATA-RECEIVE-ERROR-EVENT")
            for elem in dree_event:
                obj_event = {}
                obj_event['NAME'] = elem.find('{http://autosar.org/schema/r4.0}SHORT-NAME').text
                obj_event['EVENT-TYPE'] = elem.tag.split('}')[-1]
                obj_event['TYPE'] = "EVT"
                obj_event['START-ON-EVENT'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                obj_event['DURATION'] = event_duration
                obj_event['BEFORE-EVENT'] = []
                obj_event['AFTER-EVENT'] = []
                obj_event['REF'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                obj_event['EVENT-REF'] = ''
                obj_event['CORE'] = ""
                obj_event['PARTITION'] = ""
                obj_event['CATEGORY'] = "DEFAULT"
                obj_event['SPECIFIC-TASK'] = None
                if elem.find('{http://autosar.org/schema/r4.0}ACTIVATION') is not None:
                    obj_event['ACTIVATION'] = elem.find('{http://autosar.org/schema/r4.0}ACTIVATION').text
                else:
                    obj_event['ACTIVATION'] = None
                if elem.find('{http://autosar.org/schema/r4.0}PERIOD') is not None:
                    obj_event['PERIOD'] = elem.find('{http://autosar.org/schema/r4.0}PERIOD').text
                else:
                    obj_event['PERIOD'] = None
                obj_event['IB'] = elem.getparent().getparent().getchildren()[0].text
                obj_event['ASWC'] = elem.getparent().getparent().getparent().getparent().getchildren()[0].text
                obj_event['ROOT'] = elem.getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].text
                if elem.getparent().getparent().getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].tag == '{http://autosar.org/schema/r4.0}SHORT-NAME':
                    obj_event['ROOT'] = elem.getparent().getparent().getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].text + '/' + obj_event['ROOT']
                events_aswc.append(obj_event)
            dre_event = root.findall(".//{http://autosar.org/schema/r4.0}DATA-RECEIVED-EVENT")
            for elem in dre_event:
                obj_event = {}
                obj_event['NAME'] = elem.find('{http://autosar.org/schema/r4.0}SHORT-NAME').text
                obj_event['EVENT-TYPE'] = elem.tag.split('}')[-1]
                obj_event['TYPE'] = "EVT"
                obj_event['START-ON-EVENT'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                obj_event['DURATION'] = event_duration
                obj_event['BEFORE-EVENT'] = []
                obj_event['AFTER-EVENT'] = []
                obj_event['REF'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                obj_event['EVENT-REF'] = ''
                obj_event['CORE'] = ""
                obj_event['PARTITION'] = ""
                obj_event['CATEGORY'] = "DEFAULT"
                obj_event['SPECIFIC-TASK'] = None
                if elem.find('{http://autosar.org/schema/r4.0}ACTIVATION') is not None:
                    obj_event['ACTIVATION'] = elem.find('{http://autosar.org/schema/r4.0}ACTIVATION').text
                else:
                    obj_event['ACTIVATION'] = None
                if elem.find('{http://autosar.org/schema/r4.0}PERIOD') is not None:
                    obj_event['PERIOD'] = elem.find('{http://autosar.org/schema/r4.0}PERIOD').text
                else:
                    obj_event['PERIOD'] = None
                obj_event['IB'] = elem.getparent().getparent().getchildren()[0].text
                obj_event['ASWC'] = elem.getparent().getparent().getparent().getparent().getchildren()[0].text
                obj_event['ROOT'] = elem.getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].text
                if elem.getparent().getparent().getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].tag == '{http://autosar.org/schema/r4.0}SHORT-NAME':
                    obj_event['ROOT'] = elem.getparent().getparent().getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].text + '/' + obj_event['ROOT']
                events_aswc.append(obj_event)
            dsce_event = root.findall(".//{http://autosar.org/schema/r4.0}DATA-SEND-COMPLETED-EVENT")
            for elem in dsce_event:
                obj_event = {}
                obj_event['NAME'] = elem.find('{http://autosar.org/schema/r4.0}SHORT-NAME').text
                obj_event['EVENT-TYPE'] = elem.tag.split('}')[-1]
                obj_event['TYPE'] = "EVT"
                obj_event['START-ON-EVENT'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                obj_event['DURATION'] = event_duration
                obj_event['BEFORE-EVENT'] = []
                obj_event['AFTER-EVENT'] = []
                obj_event['REF'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                obj_event['EVENT-REF'] = ''
                obj_event['CORE'] = ""
                obj_event['PARTITION'] = ""
                obj_event['CATEGORY'] = "DEFAULT"
                obj_event['SPECIFIC-TASK'] = None
                if elem.find('{http://autosar.org/schema/r4.0}ACTIVATION') is not None:
                    obj_event['ACTIVATION'] = elem.find('{http://autosar.org/schema/r4.0}ACTIVATION').text
                else:
                    obj_event['ACTIVATION'] = None
                if elem.find('{http://autosar.org/schema/r4.0}PERIOD') is not None:
                    obj_event['PERIOD'] = elem.find('{http://autosar.org/schema/r4.0}PERIOD').text
                else:
                    obj_event['PERIOD'] = None
                obj_event['IB'] = elem.getparent().getparent().getchildren()[0].text
                obj_event['ASWC'] = elem.getparent().getparent().getparent().getparent().getchildren()[0].text
                obj_event['ROOT'] = elem.getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].text
                if elem.getparent().getparent().getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].tag == '{http://autosar.org/schema/r4.0}SHORT-NAME':
                    obj_event['ROOT'] = elem.getparent().getparent().getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].text + '/' + obj_event['ROOT']
                events_aswc.append(obj_event)
            dwce_event = root.findall(".//{http://autosar.org/schema/r4.0}DATA-WRITE-COMPLETED-EVENT")
            for elem in dwce_event:
                obj_event = {}
                obj_event['NAME'] = elem.find('{http://autosar.org/schema/r4.0}SHORT-NAME').text
                obj_event['EVENT-TYPE'] = elem.tag.split('}')[-1]
                obj_event['TYPE'] = "EVT"
                obj_event['START-ON-EVENT'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                obj_event['DURATION'] = event_duration
                obj_event['BEFORE-EVENT'] = []
                obj_event['AFTER-EVENT'] = []
                obj_event['REF'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                obj_event['EVENT-REF'] = ''
                obj_event['CORE'] = ""
                obj_event['PARTITION'] = ""
                obj_event['CATEGORY'] = "DEFAULT"
                obj_event['SPECIFIC-TASK'] = None
                if elem.find('{http://autosar.org/schema/r4.0}ACTIVATION') is not None:
                    obj_event['ACTIVATION'] = elem.find('{http://autosar.org/schema/r4.0}ACTIVATION').text
                else:
                    obj_event['ACTIVATION'] = None
                if elem.find('{http://autosar.org/schema/r4.0}PERIOD') is not None:
                    obj_event['PERIOD'] = elem.find('{http://autosar.org/schema/r4.0}PERIOD').text
                else:
                    obj_event['PERIOD'] = None
                obj_event['IB'] = elem.getparent().getparent().getchildren()[0].text
                obj_event['ASWC'] = elem.getparent().getparent().getparent().getparent().getchildren()[0].text
                obj_event['ROOT'] = elem.getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].text
                if elem.getparent().getparent().getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].tag == '{http://autosar.org/schema/r4.0}SHORT-NAME':
                    obj_event['ROOT'] = elem.getparent().getparent().getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].text + '/' + obj_event['ROOT']
                events_aswc.append(obj_event)
            etoe_event = root.findall(".//{http://autosar.org/schema/r4.0}EXTERNAL-TRIGGER-OCCURRED-EVENT")
            for elem in etoe_event:
                obj_event = {}
                obj_event['NAME'] = elem.find('{http://autosar.org/schema/r4.0}SHORT-NAME').text
                obj_event['EVENT-TYPE'] = elem.tag.split('}')[-1]
                obj_event['TYPE'] = "EVT"
                obj_event['START-ON-EVENT'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                obj_event['DURATION'] = event_duration
                obj_event['BEFORE-EVENT'] = []
                obj_event['AFTER-EVENT'] = []
                obj_event['REF'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                obj_event['EVENT-REF'] = ''
                obj_event['CORE'] = ""
                obj_event['PARTITION'] = ""
                obj_event['CATEGORY'] = "DEFAULT"
                obj_event['SPECIFIC-TASK'] = None
                if elem.find('{http://autosar.org/schema/r4.0}ACTIVATION') is not None:
                    obj_event['ACTIVATION'] = elem.find('{http://autosar.org/schema/r4.0}ACTIVATION').text
                else:
                    obj_event['ACTIVATION'] = None
                if elem.find('{http://autosar.org/schema/r4.0}PERIOD') is not None:
                    obj_event['PERIOD'] = elem.find('{http://autosar.org/schema/r4.0}PERIOD').text
                else:
                    obj_event['PERIOD'] = None
                obj_event['IB'] = elem.getparent().getparent().getchildren()[0].text
                obj_event['ASWC'] = elem.getparent().getparent().getparent().getparent().getchildren()[0].text
                obj_event['ROOT'] = elem.getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].text
                if elem.getparent().getparent().getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].tag == '{http://autosar.org/schema/r4.0}SHORT-NAME':
                    obj_event['ROOT'] = elem.getparent().getparent().getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].text + '/' + obj_event['ROOT']
                events_aswc.append(obj_event)
            ie_event = root.findall(".//{http://autosar.org/schema/r4.0}INIT-EVENT")
            for elem in ie_event:
                obj_event = {}
                obj_event['NAME'] = elem.find('{http://autosar.org/schema/r4.0}SHORT-NAME').text
                obj_event['EVENT-TYPE'] = elem.tag.split('}')[-1]
                obj_event['TYPE'] = "EVT"
                obj_event['START-ON-EVENT'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                obj_event['DURATION'] = event_duration
                obj_event['BEFORE-EVENT'] = []
                obj_event['AFTER-EVENT'] = []
                obj_event['REF'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                obj_event['EVENT-REF'] = ''
                obj_event['CORE'] = ""
                obj_event['PARTITION'] = ""
                obj_event['CATEGORY'] = "DEFAULT"
                obj_event['SPECIFIC-TASK'] = None
                if elem.find('{http://autosar.org/schema/r4.0}ACTIVATION') is not None:
                    obj_event['ACTIVATION'] = elem.find('{http://autosar.org/schema/r4.0}ACTIVATION').text
                else:
                    obj_event['ACTIVATION'] = None
                if elem.find('{http://autosar.org/schema/r4.0}PERIOD') is not None:
                    obj_event['PERIOD'] = elem.find('{http://autosar.org/schema/r4.0}PERIOD').text
                else:
                    obj_event['PERIOD'] = None
                obj_event['IB'] = elem.getparent().getparent().getchildren()[0].text
                obj_event['ASWC'] = elem.getparent().getparent().getparent().getparent().getchildren()[0].text
                obj_event['ROOT'] = elem.getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].text
                if elem.getparent().getparent().getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].tag == '{http://autosar.org/schema/r4.0}SHORT-NAME':
                    obj_event['ROOT'] = elem.getparent().getparent().getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].text + '/' + obj_event['ROOT']
                events_aswc.append(obj_event)
            itoe_event = root.findall(".//{http://autosar.org/schema/r4.0}INTERNAL-TRIGGER-OCCURRED-EVENT")
            for elem in itoe_event:
                obj_event = {}
                obj_event['NAME'] = elem.find('{http://autosar.org/schema/r4.0}SHORT-NAME').text
                obj_event['EVENT-TYPE'] = elem.tag.split('}')[-1]
                obj_event['TYPE'] = "EVT"
                obj_event['START-ON-EVENT'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                obj_event['DURATION'] = event_duration
                obj_event['BEFORE-EVENT'] = []
                obj_event['AFTER-EVENT'] = []
                obj_event['REF'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                obj_event['EVENT-REF'] = ''
                obj_event['CORE'] = ""
                obj_event['PARTITION'] = ""
                obj_event['CATEGORY'] = "DEFAULT"
                obj_event['SPECIFIC-TASK'] = None
                if elem.find('{http://autosar.org/schema/r4.0}ACTIVATION') is not None:
                    obj_event['ACTIVATION'] = elem.find('{http://autosar.org/schema/r4.0}ACTIVATION').text
                else:
                    obj_event['ACTIVATION'] = None
                if elem.find('{http://autosar.org/schema/r4.0}PERIOD') is not None:
                    obj_event['PERIOD'] = elem.find('{http://autosar.org/schema/r4.0}PERIOD').text
                else:
                    obj_event['PERIOD'] = None
                obj_event['IB'] = elem.getparent().getparent().getchildren()[0].text
                obj_event['ASWC'] = elem.getparent().getparent().getparent().getparent().getchildren()[0].text
                obj_event['ROOT'] = elem.getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].text
                if elem.getparent().getparent().getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].tag == '{http://autosar.org/schema/r4.0}SHORT-NAME':
                    obj_event['ROOT'] = elem.getparent().getparent().getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].text + '/' + obj_event['ROOT']
                events_aswc.append(obj_event)
            msae_event = root.findall(".//{http://autosar.org/schema/r4.0}MODE-SWITCHED-ACK-EVENT")
            for elem in msae_event:
                obj_event = {}
                obj_event['NAME'] = elem.find('{http://autosar.org/schema/r4.0}SHORT-NAME').text
                obj_event['EVENT-TYPE'] = elem.tag.split('}')[-1]
                obj_event['TYPE'] = "EVT"
                obj_event['START-ON-EVENT'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                obj_event['DURATION'] = event_duration
                obj_event['BEFORE-EVENT'] = []
                obj_event['AFTER-EVENT'] = []
                obj_event['REF'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                obj_event['EVENT-REF'] = ''
                obj_event['CORE'] = ""
                obj_event['PARTITION'] = ""
                obj_event['CATEGORY'] = "DEFAULT"
                obj_event['SPECIFIC-TASK'] = None
                if elem.find('{http://autosar.org/schema/r4.0}ACTIVATION') is not None:
                    obj_event['ACTIVATION'] = elem.find('{http://autosar.org/schema/r4.0}ACTIVATION').text
                else:
                    obj_event['ACTIVATION'] = None
                if elem.find('{http://autosar.org/schema/r4.0}PERIOD') is not None:
                    obj_event['PERIOD'] = elem.find('{http://autosar.org/schema/r4.0}PERIOD').text
                else:
                    obj_event['PERIOD'] = None
                obj_event['IB'] = elem.getparent().getparent().getchildren()[0].text
                obj_event['ASWC'] = elem.getparent().getparent().getparent().getparent().getchildren()[0].text
                obj_event['ROOT'] = elem.getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].text
                if elem.getparent().getparent().getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].tag == '{http://autosar.org/schema/r4.0}SHORT-NAME':
                    obj_event['ROOT'] = elem.getparent().getparent().getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].text + '/' + obj_event['ROOT']
                events_aswc.append(obj_event)
            oie_event = root.findall(".//{http://autosar.org/schema/r4.0}OPERATION-INVOKED-EVENT")
            for elem in oie_event:
                obj_event = {}
                obj_event['NAME'] = elem.find('{http://autosar.org/schema/r4.0}SHORT-NAME').text
                obj_event['EVENT-TYPE'] = elem.tag.split('}')[-1]
                obj_event['TYPE'] = "EVT"
                obj_event['START-ON-EVENT'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                obj_event['DURATION'] = event_duration
                obj_event['BEFORE-EVENT'] = []
                obj_event['AFTER-EVENT'] = []
                obj_event['REF'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                obj_event['EVENT-REF'] = ''
                obj_event['CORE'] = ""
                obj_event['PARTITION'] = ""
                obj_event['CATEGORY'] = "DEFAULT"
                obj_event['SPECIFIC-TASK'] = None
                if elem.find('{http://autosar.org/schema/r4.0}ACTIVATION') is not None:
                    obj_event['ACTIVATION'] = elem.find('{http://autosar.org/schema/r4.0}ACTIVATION').text
                else:
                    obj_event['ACTIVATION'] = None
                if elem.find('{http://autosar.org/schema/r4.0}PERIOD') is not None:
                    obj_event['PERIOD'] = elem.find('{http://autosar.org/schema/r4.0}PERIOD').text
                else:
                    obj_event['PERIOD'] = None
                obj_event['IB'] = elem.getparent().getparent().getchildren()[0].text
                obj_event['ASWC'] = elem.getparent().getparent().getparent().getparent().getchildren()[0].text
                obj_event['ROOT'] = elem.getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].text
                if elem.getparent().getparent().getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].tag == '{http://autosar.org/schema/r4.0}SHORT-NAME':
                    obj_event['ROOT'] = elem.getparent().getparent().getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].text + '/' + obj_event['ROOT']
                events_aswc.append(obj_event)
            smmee_event = root.findall(".//{http://autosar.org/schema/r4.0}SWC-MODE-MANAGER-ERROR-EVENT")
            for elem in smmee_event:
                obj_event = {}
                obj_event['NAME'] = elem.find('{http://autosar.org/schema/r4.0}SHORT-NAME').text
                obj_event['EVENT-TYPE'] = elem.tag.split('}')[-1]
                obj_event['TYPE'] = "EVT"
                obj_event['START-ON-EVENT'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                obj_event['DURATION'] = event_duration
                obj_event['BEFORE-EVENT'] = []
                obj_event['AFTER-EVENT'] = []
                obj_event['REF'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                obj_event['EVENT-REF'] = ''
                obj_event['CORE'] = ""
                obj_event['PARTITION'] = ""
                obj_event['CATEGORY'] = "DEFAULT"
                obj_event['SPECIFIC-TASK'] = None
                if elem.find('{http://autosar.org/schema/r4.0}ACTIVATION') is not None:
                    obj_event['ACTIVATION'] = elem.find('{http://autosar.org/schema/r4.0}ACTIVATION').text
                else:
                    obj_event['ACTIVATION'] = None
                if elem.find('{http://autosar.org/schema/r4.0}PERIOD') is not None:
                    obj_event['PERIOD'] = elem.find('{http://autosar.org/schema/r4.0}PERIOD').text
                else:
                    obj_event['PERIOD'] = None
                obj_event['IB'] = elem.getparent().getparent().getchildren()[0].text
                obj_event['ASWC'] = elem.getparent().getparent().getparent().getparent().getchildren()[0].text
                obj_event['ROOT'] = elem.getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].text
                if elem.getparent().getparent().getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].tag == '{http://autosar.org/schema/r4.0}SHORT-NAME':
                    obj_event['ROOT'] = elem.getparent().getparent().getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].text + '/' + obj_event['ROOT']
                events_aswc.append(obj_event)
            smse_event = root.findall(".//{http://autosar.org/schema/r4.0}SWC-MODE-SWITCH-EVENT")
            for elem in smse_event:
                obj_event = {}
                obj_event['NAME'] = elem.find('{http://autosar.org/schema/r4.0}SHORT-NAME').text
                obj_event['EVENT-TYPE'] = elem.tag.split('}')[-1]
                obj_event['TYPE'] = "PER"
                obj_event['START-ON-EVENT'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                obj_event['DURATION'] = event_duration
                obj_event['BEFORE-EVENT'] = []
                obj_event['AFTER-EVENT'] = []
                obj_event['REF'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                obj_event['EVENT-REF'] = ''
                obj_event['CORE'] = ""
                obj_event['PARTITION'] = ""
                obj_event['CATEGORY'] = "DEFAULT"
                obj_event['SPECIFIC-TASK'] = None
                if elem.find('{http://autosar.org/schema/r4.0}ACTIVATION') is not None:
                    obj_event['ACTIVATION'] = elem.find('{http://autosar.org/schema/r4.0}ACTIVATION').text
                else:
                    obj_event['ACTIVATION'] = None
                if elem.find('{http://autosar.org/schema/r4.0}PERIOD') is not None:
                    obj_event['PERIOD'] = elem.find('{http://autosar.org/schema/r4.0}PERIOD').text
                else:
                    obj_event['PERIOD'] = None
                obj_event['IB'] = elem.getparent().getparent().getchildren()[0].text
                obj_event['ASWC'] = elem.getparent().getparent().getparent().getparent().getchildren()[0].text
                obj_event['ROOT'] = elem.getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].text
                if elem.getparent().getparent().getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].tag == '{http://autosar.org/schema/r4.0}SHORT-NAME':
                    obj_event['ROOT'] = elem.getparent().getparent().getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].text + '/' + obj_event['ROOT']
                events_aswc.append(obj_event)
            te_event = root.findall(".//{http://autosar.org/schema/r4.0}TIMING-EVENT")
            for elem in te_event:
                obj_event = {}
                obj_event['NAME'] = elem.find('{http://autosar.org/schema/r4.0}SHORT-NAME').text
                obj_event['EVENT-TYPE'] = elem.tag.split('}')[-1]
                obj_event['TYPE'] = "PER"
                obj_event['START-ON-EVENT'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                obj_event['DURATION'] = event_duration
                obj_event['BEFORE-EVENT'] = []
                obj_event['AFTER-EVENT'] = []
                obj_event['REF'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                obj_event['EVENT-REF'] = ''
                obj_event['CORE'] = ""
                obj_event['PARTITION'] = ""
                obj_event['CATEGORY'] = "DEFAULT"
                obj_event['SPECIFIC-TASK'] = None
                if elem.find('{http://autosar.org/schema/r4.0}ACTIVATION') is not None:
                    obj_event['ACTIVATION'] = elem.find('{http://autosar.org/schema/r4.0}ACTIVATION').text
                else:
                    obj_event['ACTIVATION'] = None
                if elem.find('{http://autosar.org/schema/r4.0}PERIOD') is not None:
                    obj_event['PERIOD'] = elem.find('{http://autosar.org/schema/r4.0}PERIOD').text
                else:
                    obj_event['PERIOD'] = None
                obj_event['IB'] = elem.getparent().getparent().getchildren()[0].text
                obj_event['ASWC'] = elem.getparent().getparent().getparent().getparent().getchildren()[0].text
                obj_event['ROOT'] = elem.getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].text
                if elem.getparent().getparent().getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].tag == '{http://autosar.org/schema/r4.0}SHORT-NAME':
                    obj_event['ROOT'] = elem.getparent().getparent().getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].text + '/' + obj_event['ROOT']
                events_aswc.append(obj_event)
            thee_event = root.findall(".//{http://autosar.org/schema/r4.0}TRANSFORMER-HARD-ERROR-EVENT")
            for elem in thee_event:
                obj_event = {}
                obj_event['NAME'] = elem.find('{http://autosar.org/schema/r4.0}SHORT-NAME').text
                obj_event['EVENT-TYPE'] = elem.tag.split('}')[-1]
                obj_event['TYPE'] = "EVT"
                obj_event['START-ON-EVENT'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                obj_event['DURATION'] = event_duration
                obj_event['BEFORE-EVENT'] = []
                obj_event['AFTER-EVENT'] = []
                obj_event['REF'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                obj_event['EVENT-REF'] = ''
                obj_event['CORE'] = ""
                obj_event['PARTITION'] = ""
                obj_event['CATEGORY'] = "DEFAULT"
                obj_event['SPECIFIC-TASK'] = None
                if elem.find('{http://autosar.org/schema/r4.0}ACTIVATION') is not None:
                    obj_event['ACTIVATION'] = elem.find('{http://autosar.org/schema/r4.0}ACTIVATION').text
                else:
                    obj_event['ACTIVATION'] = None
                if elem.find('{http://autosar.org/schema/r4.0}PERIOD') is not None:
                    obj_event['PERIOD'] = elem.find('{http://autosar.org/schema/r4.0}PERIOD').text
                else:
                    obj_event['PERIOD'] = None
                obj_event['IB'] = elem.getparent().getparent().getchildren()[0].text
                obj_event['ASWC'] = elem.getparent().getparent().getparent().getparent().getchildren()[0].text
                obj_event['ROOT'] = elem.getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].text
                if elem.getparent().getparent().getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].tag == '{http://autosar.org/schema/r4.0}SHORT-NAME':
                    obj_event['ROOT'] = elem.getparent().getparent().getparent().getparent().getparent().getparent().getparent().getparent().getchildren()[0].text + '/' + obj_event['ROOT']
                events_aswc.append(obj_event)
            sw_compos = root.findall(".//{http://autosar.org/schema/r4.0}SW-COMPONENT-PROTOTYPE")
            for elemSW in sw_compos:
                objSw = {}
                objSw['NAME'] = str(elemSW.find("{http://autosar.org/schema/r4.0}SHORT-NAME").text)
                objSw['TYPE'] = elemSW.find("{http://autosar.org/schema/r4.0}TYPE-TREF").text
                temp = objSw['TYPE'].split('/')
                objSw['SWC'] = temp[-1]
                compos.append(objSw)
            behavior = root.findall(".//{http://autosar.org/schema/r4.0}SWC-INTERNAL-BEHAVIOR")
            for ib in behavior:
                objIB = {}
                objIB['NAME'] = ib.find("{http://autosar.org/schema/r4.0}SHORT-NAME").text
                objIB['ASWC'] = ib.getparent().getparent().getchildren()[0].text
                objIB['ROOT'] = ib.getparent().getparent().getparent().getparent().getchildren()[0].text
                ibehaviors.append(objIB)
            implementation = root.findall(".//{http://autosar.org/schema/r4.0}SWC-IMPLEMENTATION")
            for elem in implementation:
                objImp = {}
                objImp['NAME'] = elem.find("{http://autosar.org/schema/r4.0}SHORT-NAME").text
                objImp['BEHAVIOR'] = elem.find("{http://autosar.org/schema/r4.0}BEHAVIOR-REF").text
                objImp['ROOT'] = elem.getparent().getparent().getchildren()[0].text
                implementations.append(objImp)
    for file in files_list:
        if file.endswith('.xml'):
            try:
                check_if_xml_is_wellformed(file)
                logger.info(' The file ' + file + ' is well-formed')
                info_no = info_no + 1
            except Exception as e:
                logger.error(' The file ' + file + ' is not well-formed: ' + str(e))
                print(' The file ' + file + ' is not well-formed: ' + str(e))
                error_no = error_no + 1
            parser = etree.XMLParser(remove_comments=True)
            tree = objectify.parse(file, parser=parser)
            root = tree.getroot()
            event = root.findall(".//EVENT")
            for element in event:
                name = None
                obj_event = {}
                after_list = []
                before_list = []
                task = None
                category = 'DEFAULT'
                duration = '0'
                for child in element.iterchildren():
                    if child.tag == 'SHORT-NAME':
                        name = child.text
                    if child.tag == 'EVENT-REF':
                        obj_event['EVENT'] = child.text
                    if child.tag == 'DURATION':
                        duration = child.text
                    if child.tag == 'AFTER-EVENT-REF':
                        list_of_events = child.findall('.//EVENT-REF')
                        for elem in list_of_events:
                            if not elem.text.isspace():
                                after_list.append(elem.text)
                    if child.tag == 'BEFORE-EVENT-REF':
                        list_of_events = child.findall('.//EVENT-REF')
                        for elem in list_of_events:
                            if not elem.text.isspace():
                                before_list.append(elem.text)
                    if child.tag == 'SPECIFIC-TASK':
                        task = child.text
                    if child.tag == 'CATEGORY':
                        category = child.text
                obj_event['NAME'] = name
                obj_event['DURATION'] = duration
                obj_event['AFTER-EVENT'] = after_list
                obj_event['BEFORE-EVENT'] = before_list
                obj_event['SPECIFIC-TASK'] = task
                obj_event['CATEGORY'] = category
                events_rte.append(obj_event)
            swc = root.findall(".//SWC-ALLOCATION")
            for element in swc:
                obj_event = {}
                obj_event['SWC'] = element.find('SWC-REF').text
                obj_event['CORE'] = element.find('CORE').text
                obj_event['PARTITION'] = element.find('PARTITION').text
                swc_allocation.append(obj_event)
    try:
        check_if_xml_is_wellformed(config)
        logger.info(' The file ' + config + ' is well-formed')
        info_no = info_no + 1
    except Exception as e:
        logger.error(' The file ' + config + ' is not well-formed: ' + str(e))
        print(' The file ' + config + ' is not well-formed: ' + str(e))
        error_no = error_no + 1
    parser = etree.XMLParser(remove_comments=True)
    tree = objectify.parse(config, parser=parser)
    root = tree.getroot()
    elem_task = root.findall(".//TASK")
    for elem in elem_task:
        obj_task = {}
        obj_task['NAME'] = elem.find('NAME').text
        obj_task['CATEGORY'] = elem.find('CATEGORY').text
        if elem.find('PERIODICITY') is not None:
            obj_task['PERIODICITY'] = elem.find('PERIODICITY').text
        else:
            obj_task['PERIODICITY'] = None
        if elem.find('OFFSET') is not None:
            obj_task['OFFSET'] = elem.find('OFFSET').text
        else:
            obj_task['OFFSET'] = None
        obj_task['PARTITION'] = elem.getparent().getchildren()[0].text
        obj_task['CORE'] = elem.getparent().getparent().getchildren()[0].text
        tasks_general.append(obj_task)
    ###################################
    if error_no != 0:
        print("There is at least one blocking error! Check the generated log.")
        print("\nExecution stopped with: " + str(info_no) + " infos, " + str(warning_no) + " warnings, " + str(error_no) + " errors\n")
        try:
            os.remove(output_path + '/RTE_Config.xml')
        except OSError:
            pass
        sys.exit(1)

    # for elem in swc_allocation[:]:
    #     for elem2 in swc_allocation[:]:
    #         if swc_allocation.index(elem) != swc_allocation.index(elem2):
    #             if elem['SWC'] == elem2['SWC']:
    #                 if elem['CORE'] != elem2['CORE'] or elem['PARTITION'] != elem2['PARTITION']:
    #                     logger.error('The SWC ' + elem2['SWC'] + 'has multiple different allocations')
    #                     print('The SWC ' + elem2['SWC'] + 'has multiple different allocations')
    #                     os.remove(output_path + '/MemMap.epc')
    #                 else :
    #                     if elem['CORE'] == elem2['CORE'] or elem['PARTITION'] == elem2['PARTITION']:
    #                         swc_allocation.remove(elem2)

    copy_swc = swc_allocation[:]
    for index1 in range(len(copy_swc)):
        for index2 in range(len(copy_swc)):
            if index1 != index2 and index1 < index2:
                if copy_swc[index1]['SWC'] == copy_swc[index2]['SWC']:
                    if copy_swc[index1]['CORE'] != copy_swc[index2]['CORE'] or copy_swc[index1]['PARTITION'] != copy_swc[index2]['PARTITION']:
                        logger.error('The SWC ' + copy_swc[index1]['SWC'] + 'has multiple different allocations')
                        print('The SWC ' + copy_swc[index1]['SWC'] + 'has multiple different allocations')
                        os.remove(output_path + '/MemMap.epc')
                    else:
                        if copy_swc[index1]['CORE'] == copy_swc[index2]['CORE'] or copy_swc[index1]['PARTITION'] == copy_swc[index2]['PARTITION']:
                            swc_allocation.remove(copy_swc[index2])


    for implementation in implementations:
        for behavior in ibehaviors:
            if implementation['BEHAVIOR'].split("/")[-1] == behavior['NAME'] and implementation['BEHAVIOR'].split("/")[-2] == behavior['ASWC']:
                objTemp = {}
                objTemp['NAME'] = behavior['ASWC']
                objTemp['SWC-REF'] = "/" + behavior['ROOT'] + "/" + behavior['ASWC']
                objTemp['IMPLEMENTATION-REF'] = "/" + implementation['ROOT'] + "/" + implementation['NAME']
                if objTemp not in swc_types:
                    swc_types.append(objTemp)
                else:
                    continue

    events_rte = merge_events(events_rte, logger, output_path)

    for elem_rte in events_rte:
        for elem_aswc in events_aswc:
            if elem_rte['NAME'] == elem_aswc['NAME']:
                elem_aswc['BEFORE-EVENT'] = elem_rte['BEFORE-EVENT']
                elem_aswc['AFTER-EVENT'] = elem_rte['AFTER-EVENT']
                elem_aswc['CATEGORY'] = elem_rte['CATEGORY']
                elem_aswc['SPECIFIC-TASK'] = elem_rte['SPECIFIC-TASK']
                elem_aswc['EVENT-REF'] = elem_rte['EVENT']
                if elem_rte['DURATION'] != '0':
                    elem_aswc['DURATION'] = elem_rte['DURATION']
    for elem_swc in swc_allocation:
        for elem_aswc in events_aswc:
            if "/"+elem_aswc['ROOT'] + "/" + elem_aswc['ASWC'] in elem_swc['SWC']:
                elem_aswc['CORE'] = elem_swc['CORE']
                elem_aswc['PARTITION'] = elem_swc['PARTITION']

    # remove OIE events that have the DEFAULT category
    for event in events_aswc[:]:
        if event['EVENT-TYPE'] == "OPERATION-INVOKED-EVENT":
            if event['CATEGORY'] == "DEFAULT":
                events_aswc.remove(event)

    # compute max period of the timing events and transform it from s in ms
    max_period = 0
    for elem_aswc in events_aswc:
        if elem_aswc['EVENT-TYPE'] == 'TIMING-EVENT' and float(elem_aswc['PERIOD']) > max_period:
            max_period = float(elem_aswc['PERIOD'])
    max_period = max_period * 1000

    # TRS.RTECONFIG.FUNC.006
    for elem in events_aswc:
        if elem['ACTIVATION'] == "ON-ENTRY":
            for elem2 in events_aswc:
                if elem['CORE'] == elem2['CORE'] and elem['PARTITION'] == elem2['PARTITION'] and elem['TYPE'] == elem2['TYPE'] and elem['ASWC'] == elem2['ASWC'] and elem2['ACTIVATION'] == "ON-EXIT":
                    elem['AFTER-EVENT'].append(elem2['NAME'])

    g = Graph(len(events_aswc))
    order = []
    for elem in events_aswc:
        if elem['AFTER-EVENT']:
            i = events_aswc.index(elem)
            j = 0
            temp = elem['AFTER-EVENT']
            for t in temp:
                for element in events_aswc:
                    if element['NAME'] == t.split('/')[-1]:
                        j = events_aswc.index(element)
                        g.add_edge(j, i)
                        dictOrder = {}
                        dictOrder["BEFORE"] = element['NAME']
                        dictOrder["AFTER"] = elem["NAME"]
                        dictOrder["VISITED"] = False
                        order.append(dictOrder)
        if elem['BEFORE-EVENT']:
            i = events_aswc.index(elem)
            j = 0
            temp = elem['BEFORE-EVENT']
            for t in temp:
                for element in events_aswc:
                    if element['NAME'] == t.split('/')[-1]:
                        j = events_aswc.index(element)
                        g.add_edge(i, j)
                        dictOrder = {}
                        dictOrder["BEFORE"] = elem['NAME']
                        dictOrder["AFTER"] = element["NAME"]
                        dictOrder["VISITED"] = False
                        order.append(dictOrder)
    result = g.is_cyclic()
    error_cycle = []
    if result is not False:
        for index in range(len(result)):
            for elem in range(len(events_aswc)):
                if result[index] == elem:
                    error_cycle.append(events_aswc[elem]['NAME'])
        text = ""
        iter = -1
        for elem in error_cycle:
            iter = iter + 1
            if iter == len(error_cycle) - 1:
                text = text + elem
            else:
                text = text + elem + " => "
        logger.error('There is a cycle in task sequencing: ' + text)
        print('There is a cycle in task sequencing: ' + text)
        error_no = error_no + 1
    else:
        sequence = g.topological_sort()
        # setting the EventToTaskMapping parameter
        for index in range(len(sequence)):
            for elem in range(len(events_aswc)):
                if sequence[index] == elem:
                    obj_event = {}
                    obj_event['EVENT'] = events_aswc[elem]['NAME']
                    obj_event['TYPE'] = events_aswc[elem]['EVENT-TYPE']
                    obj_event['EVENT-REF'] = events_aswc[elem]['EVENT-REF']
                    obj_event['ACTIVATION-OFFSET'] = None
                    obj_event['POSITION-IN-TASK'] = None
                    obj_event['MAPPED-TO-TASK'] = ""
                    try:
                        if events_aswc[elem]['CORE'] == '' or events_aswc[elem]['CORE'] is None:
                            logger.error('CORE not set for SWC-REF:' + events_aswc[elem]['ASWC'])
                            print('CORE not set for SWC-REF:' + events_aswc[elem]['ASWC'])
                            error_no = error_no + 1
                        elif events_aswc[elem]['PARTITION'] == '' or events_aswc[elem]['PARTITION'] is None:
                            logger.error('PARTITION not set for SWC-REF:' + events_aswc[elem]['ASWC'])
                            print('PARTITION not set for SWC-REF:' + events_aswc[elem]['ASWC'])
                            error_no = error_no + 1
                        else:
                            if events_aswc[elem]['SPECIFIC-TASK'] is not None:
                                obj_event['MAPPED-TO-TASK'] = events_aswc[elem]['SPECIFIC-TASK']
                            else:
                                tasked = False
                                for task in tasks_general:
                                    if events_aswc[elem]['CATEGORY'] == "DEFAULT" and task['CATEGORY'] == "PERIODIC" and events_aswc[elem]['CORE'] == task['CORE'] and events_aswc[elem]['PARTITION'] == task['PARTITION']:
                                        obj_event['MAPPED-TO-TASK'] = task['NAME']
                                        tasked = True
                                        break
                                    elif events_aswc[elem]['CATEGORY'] == "PRIORITY_EVT" and task['CATEGORY'] == "EVENT" and events_aswc[elem]['CORE'] == task['CORE'] and events_aswc[elem]['PARTITION'] == task['PARTITION']:
                                        obj_event['MAPPED-TO-TASK'] = task['NAME']
                                        tasked = True
                                        break
                                    elif events_aswc[elem]['CATEGORY'] == "DIAG" and task['CATEGORY'] == "DIAG" and events_aswc[elem]['CORE'] == task['CORE'] and events_aswc[elem]['PARTITION'] == task['PARTITION']:
                                        obj_event['MAPPED-TO-TASK'] = task['NAME']
                                        tasked = True
                                        break
                                if not tasked:
                                    logger.error('The event ' + events_aswc[elem]['NAME'] + ' is mapped to a wrong CORE or PARTITION. Check the software allocation file!')
                                    print('The event ' + events_aswc[elem]['NAME'] + ' is mapped to a wrong CORE or PARTITION. Check the software allocation file!')
                                    error_no = error_no + 1
                    except Exception as e:
                        logger.error('CORE or PARTITION not set for SWC-REF:' + events_aswc[elem]['ASWC'] + " -> " + str(e))
                        print('CORE or PARTITION not set for SWC-REF:' + events_aswc[elem]['ASWC'] + " -> " + str(e))
                        error_no = error_no + 1
                    obj_event['REF'] = events_aswc[elem]['REF']
                    obj_event['PERIOD'] = events_aswc[elem]['PERIOD']
                    obj_event['DURATION'] = events_aswc[elem]['DURATION']
                    obj_event['AFTER-EVENT'] = events_aswc[elem]['AFTER-EVENT']
                    obj_event['BEFORE-EVENT'] = events_aswc[elem]['BEFORE-EVENT']
                    obj_event['ACTIVATION'] = events_aswc[elem]['ACTIVATION']
                    obj_event['IB'] = events_aswc[elem]['IB']
                    obj_event['ASWC'] = events_aswc[elem]['ASWC']
                    obj_event['ROOT'] = events_aswc[elem]['ROOT']
                    obj_event['CATEGORY'] = events_aswc[elem]['CATEGORY']
                    obj_event['SPECIFIC-TASK'] = events_aswc[elem]['SPECIFIC-TASK']
                    obj_event['CORE'] = None
                    obj_event['PARTITION'] = None
                    obj_event['INSTANCE'] = None
                    if obj_event not in events:
                        events.append(obj_event)
                        break
                    else:
                        continue

        index_exit = 0
        index_entry = 0
        for event in events:
            if event['ACTIVATION'] == "ON-EXIT":
                events.insert(0, events.pop(index_exit))
            index_exit = index_exit + 1
        reverse_events = list(reversed(events))
        for event in reverse_events:
            if event['ACTIVATION'] == "ON-ENTRY":
                reverse_events.insert(0, reverse_events.pop(index_entry))
            index_entry = index_entry + 1
        events = list(reversed(reverse_events))

        events = sorted(events, key=lambda x: x['MAPPED-TO-TASK'])
        # setting the PositionInTask parameter
        tasks = []
        for task in tasks_general:
            count = 1
            for elem in events:
                if elem['MAPPED-TO-TASK'] == task['NAME']:
                    elem['POSITION-IN-TASK'] = count
                    count = count + 1
        for event in events:
            if event['POSITION-IN-TASK'] is None:
                logger.error('The event ' + event['EVENT'] + ' is mapped to a task not present in the OsConfig file: ' + str(event['SPECIFIC-TASK']))
                print('The event ' + event['EVENT'] + ' is mapped to a task not present in the OsConfig file: ' + str(event['SPECIFIC-TASK']))
                error_no = error_no + 1
        # setting the RteActivationOffset parameter
        d = defaultdict(list)
        for item in events:
            if item['TYPE'] == 'TIMING-EVENT':
                if item['SPECIFIC-TASK'] is None and item['CATEGORY'] == 'DEFAULT':
                    obj_event = {}
                    obj_event['NAME'] = item['EVENT']
                    obj_event['REF'] = item['REF']
                    if float(item['DURATION']) == 0:
                        obj_event['DURATION'] = '0.0001'
                    else:
                        obj_event['DURATION'] = item['DURATION']
                    obj_event['PERIOD'] = item['PERIOD']
                    obj_event['AFTER'] = item['AFTER-EVENT']
                    obj_event['BEFORE'] = item['BEFORE-EVENT']
                    obj_event['COMPUTED'] = False
                    obj_event['OFFSET'] = None
                    d[item['MAPPED-TO-TASK']].append(obj_event)
        for task in d:
            # compute max period of the timing events and transform it from s in ms
            # compute min task peridicity to use in case of periodicity command line argument not defined
            max_period = 0
            task_periodicity = 1
            task_offset = 0
            for task_elem in tasks_general:
                if task_elem['NAME'] == task:
                    if task_elem['PERIODICITY'] is not None:
                        task_periodicity = task_elem['PERIODICITY'].replace(",", ".")
                        task_periodicity = float(task_periodicity)
                        task_periodicity = task_periodicity * 1000
                    if task_elem['OFFSET'] is not None:
                        task_offset = task_elem['OFFSET'].replace(",", ".")
                        task_offset = float(task_offset)
                        task_offset = task_offset * 1000
                    break
            medium_value = 0
            nb_of_events = 0
            for elem in d[task]:
                medium_value = medium_value + float(elem['DURATION'])
                nb_of_events = nb_of_events + 1
            if nb_of_events == 0:
                continue
            medium_value = (medium_value/nb_of_events) * 2
            for elem in d[task]:
                if float(elem['PERIOD']) > max_period:
                    max_period = float(elem['PERIOD'])
            max_period = max_period * 1000
            number_of_slots = max_period/task_periodicity
            slots = [[] for i in range(int(number_of_slots))]
            dprim_big = defaultdict(list)
            dprim_small = defaultdict(list)
            for te in d[task]:
                if float(te['DURATION']) >= medium_value:
                    dprim_big[te['PERIOD']].append(te)
                else:
                    dprim_small[te['PERIOD']].append(te)
            dprim_big = sorted(dprim_big.items())
            slot_limit = 0
            # for each period time, insert the event on the slot
            for period in dprim_big:
                slot_frequency = int((float(period[0]) * 1000) / task_periodicity)
                chain_duration = sum(float(event['DURATION']) for event in period[1])
                chain_limit = chain_duration / slot_frequency
                slot_limit = slot_limit + chain_limit
                for event in period[1]:
                    if event['COMPUTED'] is not True:
                        # pos = findMin(slots, slot_frequency)
                        pos = findSlot(slots, slot_frequency, slot_limit)
                        slots = insertElement(slots, pos, slot_frequency, event)
                        event['COMPUTED'] = True
            dprim_small = sorted(dprim_small.items())
            # for each period time, insert the event on the slot
            for period in dprim_small:
                slot_frequency = int((float(period[0]) * 1000) / task_periodicity)
                chain_duration = sum(float(event['DURATION']) for event in period[1])
                chain_limit = chain_duration / slot_frequency
                slot_limit = slot_limit + chain_limit
                for event in period[1]:
                    if event['COMPUTED'] is not True:
                        pos = findMin(slots, slot_frequency)
                        # pos = findSlot(slots, slot_frequency, slot_limit)
                        slots = insertElement(slots, pos, slot_frequency, event)
                        event['COMPUTED'] = True
            # dump data to debug file
            debugger.info("=============Schedule" + task + "==========")
            counter = 0
            debugger.info("Tick;Tick duration;Event list")
            for slot in slots:
                debugger.info(str(counter) + ";" + str(round(sum(float(event['DURATION']) for event in slot), 2)) + "(ms);" + ";".join([str(event['NAME']) for event in slot]))
                counter = counter + 1
            debugger.info("")
            # add the computed offset (first occurence in the slot table) to the main <event> list
            for elem in events:
                iterator = -1
                if elem['TYPE'] == 'TIMING-EVENT':
                    for slot in slots:
                        iterator = iterator + 1
                        event_slot = []
                        for event in slot:
                            event_slot.append(event['NAME'])
                        if elem['EVENT'] in event_slot:
                            elem['ACTIVATION-OFFSET'] = ((iterator * task_periodicity) + task_offset) / 1000
                            break
            ######
        for elemEv in events:
            for elemAlloc in swc_allocation:
                temp = elemAlloc['SWC'].split("/")
                if elemEv['ASWC'] == temp[-1]:
                    elemEv['CORE'] = elemAlloc['CORE']
                    elemEv['PARTITION'] = elemAlloc['PARTITION']
        for elemEv in events:
            for elemSw in compos:
                if elemEv['ASWC'] == elemSw['SWC']:
                    elemEv['INSTANCE'] = elemSw['NAME']
        swc_allocation = list(unique_items(swc_allocation))
        for elemSw in compos:
            for elemAlloc in swc_allocation:
                temp = elemAlloc['SWC'].split("/")
                if elemSw['SWC'] == temp[-1]:
                    objElem = {}
                    objElem['INSTANCE'] = elemSw['NAME']
                    objElem['CORE'] = elemAlloc['CORE']
                    objElem['PARTITION'] = elemAlloc['PARTITION']
                    if objElem not in aswcs:
                        aswcs.append(objElem)
                    else:
                        continue
    # # dump data to debug file
    debugger.info("=============Event order ===========")
    # for element in orderUnique:
    #     debugger.info(element["BEFORE"] + " => " + element["AFTER"])
    chains = []
    for index1 in range(len(order)):
        chain = []
        chain.append(order[index1]['BEFORE'])
        chain.append(order[index1]['AFTER'])
        for index2 in range(len(order)):
            if index2 != index1:
                if order[index1]["AFTER"] == order[index2]["BEFORE"] and order[index2]["VISITED"] is False:
                    chain.append(order[index2]["AFTER"])
        chains.append(chain)
    debugger.info("")

    # dump data to debug file
    debugger.info("=============Event detail===========")
    debugger.info("Event;Period;Offset;Duration;Task")
    for event in events:
        debugger.info(str(event['EVENT']) + ";" + str(event['PERIOD']) + ";" + str(event['ACTIVATION-OFFSET']) + ";" + str(event['DURATION']) + ";" + str(event['MAPPED-TO-TASK']))
    #################################
    if error_no != 0:
        print("There is at least one blocking error! Check the generated log.")
        print("\nRTE configuration file generation stopped with: " + str(info_no) + " infos, " + str(warning_no) + " warnings, " + str(error_no) + " errors\n")
        try:
            os.remove(output_path + '/RTE_Config.xml')
        except OSError:
            pass
        sys.exit(1)
    else:
        print("\nRTE configuration file generation finished with: " + str(info_no) + " infos, " + str(warning_no) + " warnings, " + str(error_no) + " errors\n")
    # except Exception as e:
    #     print("Unexpected error: " + str(e))
    #     print("\nRTE configuration file generation stopped with: " + str(info_no) + " infos, " + str(warning_no) + " warnings, " + str(error_no) + " errors\n")
    #     try:
    #         os.remove(output_path + '/RTE_Config.xml')
    #     except OSError:
    #         pass
    #     sys.exit(1)
    return swc_allocation,events,aswcs,swc_types


def create_script(events, aswcs, output_path):
    root_script = ET.Element('Script')
    root_script.set('xsi:noNamespaceSchemaLocation', "Scriptor.xsd")
    root_script.set('xmlns:xsi', "http://www.w3.org/2001/XMLSchema-instance")
    name = ET.SubElement(root_script, 'Name').text = "RTE_Config"
    decription = ET.SubElement(root_script, 'Decription').text = "Set the RTE parameters"
    expression = ET.SubElement(root_script, 'Expression').text = "as:modconf('Rte')[1]"
    operations_global = ET.SubElement(root_script, 'Operations')
    for aswc in aswcs:
        operation = ET.SubElement(operations_global, 'Operation')
        operation.set('Type', "ForEach")
        expression_global = ET.SubElement(operation, 'Expression')
        expression_global.text = "as:modconf('Rte')[1]/RteSwComponentInstance/" + aswc['INSTANCE'] + "/MappedToOsApplicationRef"
        operations = ET.SubElement(operation, 'Operations')
        operation_general = ET.SubElement(operations, "Operation")
        operation_general.set('Type', "SetEnabled")
        expression_general = ET.SubElement(operation_general, "Expression").text = 'boolean(1)'
        operation_appref = ET.SubElement(operations, 'Operation')
        operation_appref.set('Type', "SetValue")
        expression_appref = ET.SubElement(operation_appref, 'Expression')
        expression_appref.text = '"ASPath:/Os/Os/OsApp_' + aswc['CORE'] + '_' + aswc['PARTITION'] + '"'
    for event in events:
        operation_position = ET.SubElement(operations_global, 'Operation')
        operation_position.set('Type', "ForEach")
        expression_position = ET.SubElement(operation_position, 'Expression')
        expression_position.text = "as:modconf('Rte')[1]/RteSwComponentInstance/*/RteEventToTaskMapping/*/RteEventRef[.=" + '"ASPath:/'+event['ROOT']+'/'+event['ASWC']+'/'+event['IB']+'/'+event['EVENT']+'"]/../RtePositionInTask'
        operations_activation = ET.SubElement(operation_position, "Operations")
        operation_general = ET.SubElement(operations_activation, "Operation")
        operation_general.set('Type', "SetEnabled")
        expression_general = ET.SubElement(operation_general, "Expression").text = 'boolean(1)'
        operation_element = ET.SubElement(operations_activation, "Operation")
        operation_element.set('Type', "SetValue")
        expression_element = ET.SubElement(operation_element, "Expression").text = 'num:i(' + str(event['POSITION-IN-TASK']) + ')'
        operation_task = ET.SubElement(operations_global, 'Operation')
        operation_task.set('Type', "ForEach")
        expression_task = ET.SubElement(operation_task, 'Expression')
        expression_task.text = "as:modconf('Rte')[1]/RteSwComponentInstance/*/RteEventToTaskMapping/*/RteEventRef[.=" + '"ASPath:/'+event['ROOT']+'/'+event['ASWC']+'/'+event['IB']+'/'+event['EVENT']+'"]/../RteMappedToTaskRef'
        operations_activation = ET.SubElement(operation_task, "Operations")
        operation_general = ET.SubElement(operations_activation, "Operation")
        operation_general.set('Type', "SetEnabled")
        expression_general = ET.SubElement(operation_general, "Expression").text = 'boolean(1)'
        operation_element = ET.SubElement(operations_activation, "Operation")
        operation_element.set('Type', "SetValue")
        expression_element = ET.SubElement(operation_element, "Expression").text = '"ASPath:/Os/Os/' + str(event['MAPPED-TO-TASK'] + '"')
        operation_offset = ET.SubElement(operations_global, 'Operation')
        operation_offset.set('Type', "ForEach")
        expression_offset = ET.SubElement(operation_offset, 'Expression')
        expression_offset.text = "as:modconf('Rte')[1]/RteSwComponentInstance/*/RteEventToTaskMapping/*/RteEventRef[.=" + '"ASPath:/'+event['ROOT']+'/'+event['ASWC']+'/'+event['IB']+'/'+event['EVENT']+'"]/../RteActivationOffset'
        if event['ACTIVATION-OFFSET'] is not None:
            operations_activation = ET.SubElement(operation_offset, "Operations")
            operation_general = ET.SubElement(operations_activation, "Operation")
            operation_general.set('Type', "SetEnabled")
            expression_general = ET.SubElement(operation_general, "Expression").text = 'boolean(1)'
            operation_element = ET.SubElement(operations_activation, "Operation")
            operation_element.set('Type', "SetValue")
            expression_element = ET.SubElement(operation_element, "Expression").text = 'num:f(' + str(event['ACTIVATION-OFFSET']) + ')'
        else:
            operations_activation = ET.SubElement(operation_offset, "Operations")
            operation_element = ET.SubElement(operations_activation, "Operation")
            operation_element.set('Type', "SetEnabled")
            expression_element = ET.SubElement(operation_element, "Expression").text = 'boolean(0)'

    pretty_xml = prettify_xml(root_script)
    tree = ET.ElementTree(ET.fromstring(pretty_xml))
    tree.write(output_path + "/RTE_Config.xml", encoding="UTF-8", xml_declaration=True, method="xml")


def create_configuration(events, aswcs, swc_types, output_path):
    NSMAP = {None: 'http://autosar.org/schema/r4.0', "xsi": 'http://www.w3.org/2001/XMLSchema-instance'}
    attr_qname = etree.QName("http://www.w3.org/2001/XMLSchema-instance", "schemaLocation")
    rootRte = etree.Element('AUTOSAR', {attr_qname: 'http://autosar.org/schema/r4.0 AUTOSAR_4-2-2_STRICT_COMPACT.xsd'}, nsmap=NSMAP)
    packages = etree.SubElement(rootRte, 'AR-PACKAGES')
    package = etree.SubElement(packages, 'AR-PACKAGE')
    short_name = etree.SubElement(package, 'SHORT-NAME').text = "Rte"
    elements = etree.SubElement(package, 'ELEMENTS')
    ecuc_module = etree.SubElement(elements, 'ECUC-MODULE-CONFIGURATION-VALUES')
    short_name = etree.SubElement(ecuc_module, 'SHORT-NAME').text = "Rte"
    definition = etree.SubElement(ecuc_module, 'DEFINITION-REF')
    definition.attrib['DEST'] = "ECUC-MODULE-DEF"
    definition.text = "/AUTOSAR/EcuDefs/Rte"
    master_container = etree.SubElement(ecuc_module, 'CONTAINERS')
    for aswc in aswcs:
        container_aswc = etree.SubElement(master_container, 'ECUC-CONTAINER-VALUE')
        short_name = etree.SubElement(container_aswc, 'SHORT-NAME').text = aswc['INSTANCE']
        definition = etree.SubElement(container_aswc, 'DEFINITION-REF')
        definition.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition.text = "/AUTOSAR/EcuDefs/Rte/RteSwComponentInstance"
        references = etree.SubElement(container_aswc, 'REFERENCE-VALUES')
        reference1 = etree.SubElement(references, 'ECUC-REFERENCE-VALUE')
        definition = etree.SubElement(reference1, 'DEFINITION-REF')
        definition.attrib['DEST'] = "ECUC-REFERENCE-DEF"
        definition.text = "/AUTOSAR/EcuDefs/Rte/RteSwComponentInstance/MappedToOsApplicationRef"
        value = etree.SubElement(reference1, 'VALUE-REF')
        value.attrib['DEST'] = 'ECUC-CONTAINER-VALUE'
        value.text = "/Os/Os/OsApp_" + aswc['CORE'] + "_" + aswc['PARTITION']
        reference2 = etree.SubElement(references, 'ECUC-REFERENCE-VALUE')
        definition = etree.SubElement(reference2, 'DEFINITION-REF')
        definition.attrib['DEST'] = "ECUC-FOREIGN-REFERENCE-DEF"
        definition.text = "/AUTOSAR/EcuDefs/Rte/RteSwComponentInstance/RteSoftwareComponentInstanceRef"
        value = etree.SubElement(reference2, 'VALUE-REF')
        value.attrib['DEST'] = "SW-COMPONENT-PROTOTYPE"
        value.text = "/EcuExtract/TopLevelComposition/" + aswc['INSTANCE']
        subcontainers = etree.SubElement(container_aswc, 'SUB-CONTAINERS')
        for event in events:
            if aswc['INSTANCE'] == event['INSTANCE']:
                container_event = etree.SubElement(subcontainers, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container_event, 'SHORT-NAME').text = event['EVENT']
                definition = etree.SubElement(container_event, 'DEFINITION-REF')
                definition.attrib['DEST'] = 'ECUC-PARAM-CONF-CONTAINER-DEF'
                definition.text = "/AUTOSAR/EcuDefs/Rte/RteSwComponentInstance/RteEventToTaskMapping"
                parameters = etree.SubElement(container_event, 'PARAMETER-VALUES')
                numerical1 = etree.SubElement(parameters, 'ECUC-NUMERICAL-PARAM-VALUE')
                definition = etree.SubElement(numerical1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-FLOAT-PARAM-DEF"
                definition.text = "/AUTOSAR/EcuDefs/Rte/RteSwComponentInstance/RteEventToTaskMapping/RteActivationOffset"
                if event['ACTIVATION-OFFSET'] is None:
                    value = etree.SubElement(numerical1, 'VALUE').text = "0"
                else:
                    value = etree.SubElement(numerical1, 'VALUE').text = str(event['ACTIVATION-OFFSET'])
                numerical2 = etree.SubElement(parameters, 'ECUC-NUMERICAL-PARAM-VALUE')
                definition = etree.SubElement(numerical2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-BOOLEAN-PARAM-DEF"
                definition.text = "/AUTOSAR/EcuDefs/Rte/RteSwComponentInstance/RteEventToTaskMapping/RteImmediateRestart"
                value = etree.SubElement(numerical2, 'VALUE').text = "0"
                numerical3 = etree.SubElement(parameters, 'ECUC-NUMERICAL-PARAM-VALUE')
                definition = etree.SubElement(numerical3, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-INTEGER-PARAM-DEF"
                definition.text = "/AUTOSAR/EcuDefs/Rte/RteSwComponentInstance/RteEventToTaskMapping/RtePositionInTask"
                value = etree.SubElement(numerical3, 'VALUE').text = str(event['POSITION-IN-TASK'])
                references = etree.SubElement(container_event, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(references, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-FOREIGN-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/Rte/RteSwComponentInstance/RteEventToTaskMapping/RteEventRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "RTE-EVENT"
                value.text = '/' + event['ROOT'] + '/' + event['ASWC'] + '/' + event['IB'] + '/' + event['EVENT']
                reference2 = etree.SubElement(references, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/Rte/RteSwComponentInstance/RteEventToTaskMapping/RteMappedToTaskRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/Os/Os/" + event['MAPPED-TO-TASK']
    for swc in swc_types:
        container_swc = etree.SubElement(master_container, 'ECUC-CONTAINER-VALUE')
        short_name = etree.SubElement(container_swc, 'SHORT-NAME').text = "RteSwComponentType_" + swc['NAME']
        definition = etree.SubElement(container_swc, 'DEFINITION-REF')
        definition.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition.text = "/AUTOSAR/EcuDefs/Rte/RteSwComponentType"
        references = etree.SubElement(container_swc, 'REFERENCES-VALUES')
        reference1 = etree.SubElement(references, 'ECUC-REFERENCE-VALUE')
        definition = etree.SubElement(reference1, 'DEFINITION-REF')
        definition.attrib['DEST'] = "ECUC-FOREIGN-REFERENCE-DEF"
        definition.text = "/AUTOSAR/EcuDefs/Rte/RteSwComponentType/RteComponentTypeRef"
        value = etree.SubElement(reference1, 'VALUE-REF')
        value.attrib['DEST'] = "SW-COMPONENT-TYPE"
        value.text = swc['SWC-REF']
        reference2 = etree.SubElement(references, 'ECUC-REFERENCE-VALUE')
        definition = etree.SubElement(reference2, 'DEFINITION-REF')
        definition.attrib['DEST'] = "ECUC-FOREIGN-REFERENCE-DEF"
        definition.text = "/AUTOSAR/EcuDefs/Rte/RteSwComponentType/RteImplementationRef"
        value = etree.SubElement(reference2, 'VALUE-REF')
        value.attrib['DEST'] = "SWC-IMPLEMENTATION"
        value.text = swc['IMPLEMENTATION-REF']

    # generate data
    pretty_xml = prettify_xml(rootRte)
    output = etree.ElementTree(etree.fromstring(pretty_xml))
    output.write(output_path + '/Rte.epc', encoding='UTF-8', xml_declaration=True, method="xml", doctype="<!-- XML file generated by RTE_Configurator v1.0.1 -->")
    return


def create_mapping(files_list,files_cfg_list, composition, output_path, logger,swc_allocation):
    NSMAP = {None: 'http://autosar.org/schema/r4.0',
             "xsi": 'http://www.w3.org/2001/XMLSchema-instance'}
    attr_qname = etree.QName("http://www.w3.org/2001/XMLSchema-instance", "schemaLocation")
    info_no = 0
    warning_no = 0
    error_no = 0
    compositions = []
    behaviors = []
    memory_mappings = []
    #swc_allocation = []
    data_elements = []
    components_type=[]
    try:
        for file in files_list:
            if file['FILE'].endswith('.arxml'):
                try:
                    check_if_xml_is_wellformed(file['FILE'])
                    logger.info('The file: ' + file['FILE'] + ' is well-formed')
                    info_no = info_no + 1
                except Exception as e:
                    logger.error('The file: ' + file['FILE'] + ' is not well-formed: ' + str(e))
                    print('The file: ' + file['FILE'] + ' is not well-formed: ' + str(e))
                    error_no = error_no + 1
                parser = etree.XMLParser(remove_comments=True)
                tree = objectify.parse(file['FILE'], parser=parser)
                root = tree.getroot()
                sections = root.findall(".//{http://autosar.org/schema/r4.0}SWC-IMPLEMENTATION")
                for section in sections:
                    obj_section = {}
                    obj_section['IMPLEMENTATION'] = section.find(".//{http://autosar.org/schema/r4.0}SHORT-NAME").text
                    obj_section['BEHAVIOR'] = section.find(".//{http://autosar.org/schema/r4.0}BEHAVIOR-REF").text
                    obj_section['ROOT'] = section.getparent().getparent().getchildren()[0].text
                    if section.getparent().getparent().getparent().getparent().getchildren()[0].tag == '{http://autosar.org/schema/r4.0}SHORT-NAME':
                        obj_section['ROOT'] = section.getparent().getparent().getparent().getparent().getchildren()[0].text + "/" + obj_section['ROOT']
                    obj_section['RESSOURCE'] = section.find(".//{http://autosar.org/schema/r4.0}RESOURCE-CONSUMPTION/{http://autosar.org/schema/r4.0}SHORT-NAME").text
                    if section.find(".//{http://autosar.org/schema/r4.0}MEMORY-SECTION/{http://autosar.org/schema/r4.0}SHORT-NAME") is not None:
                        obj_section['NAME'] = section.find(".//{http://autosar.org/schema/r4.0}MEMORY-SECTION/{http://autosar.org/schema/r4.0}SHORT-NAME").text
                    else:
                        obj_section['NAME'] = None
                    if section.find(".//{http://autosar.org/schema/r4.0}MEMORY-SECTION/{http://autosar.org/schema/r4.0}SW-ADDRMETHOD-REF") is not None:
                        obj_section['METHOD'] = section.find(".//{http://autosar.org/schema/r4.0}MEMORY-SECTION/{http://autosar.org/schema/r4.0}SW-ADDRMETHOD-REF").text
                    else:
                        obj_section['METHOD'] = None
                    memory_mappings.append(obj_section)
                # components = root.findall(".//{http://autosar.org/schema/r4.0}SW-COMPONENT-PROTOTYPE")
                # for component in components:
                #     obj_component = {}
                #     obj_component['INSTANCE'] = component.find(".//{http://autosar.org/schema/r4.0}SHORT-NAME").text
                #     obj_component['SWC'] = component.find(".//{http://autosar.org/schema/r4.0}TYPE-TREF").text
                #     obj_component['COMPONENT'] = component.getparent().getparent().getchildren()[0].text
                #     obj_component['ROOT'] = component.getparent().getparent().getparent().getparent().getchildren()[0].text
                #     obj_component['DELETE'] = False
                #     obj_component['TYPE'] = file['TYPE']
                #     compositions.append(obj_component)
                ibs = root.findall(".//{http://autosar.org/schema/r4.0}SWC-INTERNAL-BEHAVIOR")
                for ib in ibs:
                    obj_behavior = {}
                    obj_behavior['NAME'] = ib.find(".//{http://autosar.org/schema/r4.0}SHORT-NAME").text
                    obj_behavior['ASWC'] = ib.getparent().getparent().getchildren()[0].text
                    obj_behavior['ROOT'] = ib.getparent().getparent().getparent().getparent().getchildren()[0].text
                    behaviors.append(obj_behavior)
                # component_type={}
                # component_type['NAME'] = root.find(".//{http://autosar.org/schema/r4.0}APPLICATION-SW-COMPONENT-TYPE")
                # component_type['TYPE'] = file['TYPE']
                # components_type.append(component_type)
                component_type = root.findall(".//{http://autosar.org/schema/r4.0}APPLICATION-SW-COMPONENT-TYPE")
                for elem in component_type:
                    obj={}
                    obj['ROOT'] = elem.getparent().getparent().getchildren()[0].text
                    obj['NAME'] = elem.find('.//{http://autosar.org/schema/r4.0}SHORT-NAME').text
                    obj['TYPE'] = file['TYPE']
                    components_type.append(obj)

        for file in files_cfg_list:
            if file.endswith('.arxml'):
                try:
                    check_if_xml_is_wellformed(file)
                    logger.info('The file: ' + file + ' is well-formed')
                    info_no = info_no + 1
                except Exception as e:
                    logger.error('The file: ' + file + ' is not well-formed: ' + str(e))
                    print('The file: ' + file + ' is not well-formed: ' + str(e))
                    error_no = error_no + 1
                parser = etree.XMLParser(remove_comments=True)
                tree = objectify.parse(file, parser=parser)
                root = tree.getroot()
                components = root.findall(".//{http://autosar.org/schema/r4.0}SW-COMPONENT-PROTOTYPE")
                for component in components:
                    obj_component = {}
                    obj_component['INSTANCE'] = component.find(".//{http://autosar.org/schema/r4.0}SHORT-NAME").text
                    obj_component['SWC'] = component.find(".//{http://autosar.org/schema/r4.0}TYPE-TREF").text
                    obj_component['COMPONENT'] = component.getparent().getparent().getchildren()[0].text
                    obj_component['ROOT'] = component.getparent().getparent().getparent().getparent().getchildren()[0].text
                    obj_component['DELETE'] = False
                    obj_component['TYPE'] = ""
                    compositions.append(obj_component)
            # if file['FILE'].endswith('.xml'):
            #     try:
            #         check_if_xml_is_wellformed(file['FILE'])
            #         logger.info('The file: ' + file['FILE'] + ' is well-formed')
            #         info_no = info_no + 1
            #     except Exception as e:
            #         logger.error('The file: ' + file['FILE'] + ' is not well-formed: ' + str(e))
            #         print('The file: ' + file['FILE'] + ' is not well-formed: ' + str(e))
            #         error_no = error_no + 1
            #     parser = etree.XMLParser(remove_comments=True)
            #     tree = objectify.parse(file['FILE'], parser=parser)
            #     root = tree.getroot()
            #     swc = root.findall(".//SWC-ALLOCATION")
            #     for element in swc:
            #         obj_event = {}
            #         obj_event['SWC'] = element.find('SWC-REF').text
            #         obj_event['CORE'] = element.find('CORE').text
            #         obj_event['PARTITION'] = element.find('PARTITION').text
            #         obj_event['TYPE'] = file['TYPE']
            #         swc_allocation.append(obj_event)

        for elem in compositions:
            for elem2 in components_type:
                if elem['SWC'] == '/' + elem2['ROOT'] + '/' + elem2['NAME']:
                    elem['TYPE'] = elem2['TYPE']



        copy_swc = swc_allocation[:]
        for index1 in range(len(copy_swc)):
            for index2 in range(len(copy_swc)):
                if index1 != index2 and index1 < index2:
                    if copy_swc[index1]['SWC'] == copy_swc[index2]['SWC']:
                        if copy_swc[index1]['CORE'] != copy_swc[index2]['CORE'] or copy_swc[index1]['PARTITION'] != \
                                copy_swc[index2]['PARTITION']:
                            logger.error('The SWC ' + copy_swc[index1]['SWC'] + 'has multiple different allocations')
                            print('The SWC ' + copy_swc[index1]['SWC'] + 'has multiple different allocations')
                            os.remove(output_path + '/MemMap.epc')
                        else:
                            if copy_swc[index1]['CORE'] == copy_swc[index2]['CORE'] or copy_swc[index1]['PARTITION'] == \
                                    copy_swc[index2]['PARTITION']:
                                swc_allocation.remove(copy_swc[index2])

        # remove duplicate compositions (from multiple input sources)
        compositions = list(remove_duplicates(compositions))
        # check if compositions respects the given path; if not, delete them from treatment list
        for compo in compositions:
            if compo['ROOT'] != composition.split("/")[-2] or compo['COMPONENT'] != composition.split("/")[-1]:
                logger.warning('SW-COMPONENT-PROTOTYPE ' + compo['INSTANCE'] + ' is not in the given composition; this element will not be mapped!')
                # print('SW-COMPONENT-PROTOTYPE ' + compo['INSTANCE'] + ' is not in the given composition; this element will not be mapped!')
                warning_no = warning_no + 1
                compo['DELETE'] = True
        for compo in compositions[:]:
            if compo['DELETE']:
                compositions.remove(compo)
        # create element list
        for compo in compositions:
            for swc in swc_allocation:
                if compo['SWC'] == swc['SWC']:
                    obj_elem = {}
                    obj_elem['INSTANCE'] = compo['INSTANCE']
                    obj_elem['SWC'] = compo['SWC']
                    obj_elem['CORE'] = swc['CORE']
                    obj_elem['PARTITION'] = swc['PARTITION']
                    obj_elem['BEHAVIOR'] = None
                    obj_elem['METHOD'] = None
                    obj_elem['ROOTP'] = None
                    obj_elem['IMPLEMENTATION'] = None
                    obj_elem['RESSOURCE'] = None
                    obj_elem['CODE'] = None
                    obj_elem['TYPE'] = compo['TYPE']
                    data_elements.append(obj_elem)

        # create swc list with no duplicates
        ok = 0
        obj_element={}
        obj_element['CORE'] = data_elements[0]['CORE']
        obj_element['PARTITION'] = data_elements[0]['PARTITION']
        obj_element['TYPE'] = data_elements[0]['TYPE']
        swc_no_duplicates =[]
        swc_no_duplicates.append(obj_element)
        for elem in data_elements:
            for elem2 in swc_no_duplicates:
                if elem['CORE'] == elem2['CORE'] and elem['PARTITION'] == elem2['PARTITION']:
                    ok = 1
                    break
            if ok == 0:
                obj_elem2 = {}
                obj_elem2['CORE'] = elem['CORE']
                obj_elem2['PARTITION'] = elem['PARTITION']
                obj_elem2['TYPE'] = elem['TYPE']
                swc_no_duplicates.append(obj_elem2)
            ok=0

        #create list of cores
        ok = 0
        obj_element = {}
        obj_element['CORE'] = data_elements[0]['CORE']
        list_cores = []
        list_cores.append(obj_element)
        for elem in data_elements:
            for elem2 in list_cores:
                if elem['CORE'] == elem2['CORE'] :
                    ok = 1
                    break
            if ok == 0:
                obj_elem2 = {}
                obj_elem2['CORE'] = elem['CORE']
                list_cores.append(obj_elem2)
            ok=0


        # add internal behavior to the element list:
        # for elem in swc_allocation:
        for elem in data_elements:
            for behavior in behaviors:
                if elem['SWC'].split("/")[-1] == behavior['ASWC'] and elem['SWC'].split("/")[-2] == behavior['ROOT']:
                    elem['BEHAVIOR'] = behavior['NAME']
        # add addressing method to the element list:
        for elem in data_elements:
            for mapping in memory_mappings:
                if mapping['BEHAVIOR'].split("/")[-1] == elem['BEHAVIOR'] and elem['SWC'] in mapping['BEHAVIOR']:
                    elem['ROOTP'] = mapping['ROOT']
                    elem['IMPLEMENTATION'] = mapping['IMPLEMENTATION']
                    elem['RESSOURCE'] = mapping['RESSOURCE']
                    elem['CODE'] = mapping['NAME']
                    elem['METHOD'] = mapping['METHOD']
        # delete elements without a valid addressing memory:
        for elem in data_elements[:]:
            if elem['METHOD'] is None:
                data_elements.remove(elem)
                logger.warning('There is no <SW-ADDRMETHOD-REF> given for ASWC ' + elem['SWC'])
                print('There is no <SW-ADDRMETHOD-REF> given for ASWC ' + elem['SWC'])
                warning_no = warning_no + 1
        for elem in data_elements[:]:
            swc_name = elem['SWC'].split("/")[-1].split("_")[-1]
            if swc_name != elem['METHOD'].split("/")[-1].split("_")[-1]:
                data_elements.remove(elem)
                logger.warning('The associated <SW-ADDRMETHOD-REF> given for ASWC ' + elem['SWC'] + ' does not respect the naming rule')
                print('The associated <SW-ADDRMETHOD-REF> given for ASWC ' + elem['SWC'] + ' does not respect the naming rule')
                warning_no = warning_no + 1

        # create output script
        rootScript = etree.Element('Script')
        name = etree.SubElement(rootScript, 'Name').text = "MemMapSectionSpecificMapping"
        description = etree.SubElement(rootScript, 'Decription').text = "Add MemMapSectionSpecificMapping for all code implementation"
        expression = etree.SubElement(rootScript, 'Expression').text = "as:modconf('Rte')[1]"
        operations = etree.SubElement(rootScript, 'Operations')
        for elem in data_elements:
            operation = etree.SubElement(operations, 'Operation')
            operation.attrib['Type'] = "ForEach"
            expression = etree.SubElement(operation, 'Expression')
            expression.text = "as:modconf('MemMap')[1]/MemMapAllocation/*/MemMapSectionSpecificMapping[not(*[@name=" + '"MemMapSectionSpecificMapping_' + elem['SWC'].split("/")[-1] + '"])]'
            operations2 = etree.SubElement(operation, 'Operations')
            operation_enable = etree.SubElement(operations2, 'Operation')
            operation_enable.attrib['Type'] = "Add"
            expression_enable = etree.SubElement(operation_enable, 'Expression').text = '"MemMapSectionSpecificMapping_' + elem['SWC'].split("/")[-1] + '"'
            operation2 = etree.SubElement(operations2, 'Operation')
            operation2.attrib['Type'] = "ForEach"
            expression2 = etree.SubElement(operation2, 'Expression').text = 'node:current()/MemMapSectionSpecificMapping_' + elem['SWC'].split("/")[-1] + '/MemMapMemorySectionRef'
            operations3 = etree.SubElement(operation2, 'Operations')
            operation3 = etree.SubElement(operations3, 'Operation')
            operation3.attrib['Type'] = "SetValue"
            expression3 = etree.SubElement(operation3, 'Expression').text = "'ASPath:/" + elem['ROOTP'] + '/' + elem['IMPLEMENTATION'] + '/' + elem['RESSOURCE'] + '/' + elem['CODE'] + "'"
            operation4 = etree.SubElement(operations2, 'Operation')
            operation4.attrib['Type'] = "ForEach"
            expression4 = etree.SubElement(operation4, 'Expression').text = 'node:current()/MemMapSectionSpecificMapping_' + elem['SWC'].split("/")[-1] + '/MemMapAddressingModeSetRef'
            operations3 = etree.SubElement(operation4, 'Operations')
            operation3 = etree.SubElement(operations3, 'Operation')
            operation3.attrib['Type'] = "SetValue"
            expression3 = etree.SubElement(operation3, 'Expression').text = "'ASPath:/MemMap/MemMap/MemMapAddressingModeSet_VSM_CODE_" + elem['CORE'] + "'"
        pretty_xml = prettify_xml(rootScript)
        tree = etree.ElementTree(etree.fromstring(pretty_xml))
        #tree.write(output_path + "/MemMapSectionSpecificMapping.xml", encoding="UTF-8", xml_declaration=True, method="xml")

        # create output script xml->epc
        rootSystem = etree.Element('AUTOSAR', {attr_qname: 'http://autosar.org/schema/r4.0 AUTOSAR_4-2-2_STRICT_COMPACT.xsd'}, nsmap=NSMAP)
        packages = etree.SubElement(rootSystem, 'AR-PACKAGES')
        package = ""
        compo = etree.SubElement(packages, 'AR-PACKAGE')
        short_name = etree.SubElement(compo, 'SHORT-NAME').text = "MemMap"
        elements = etree.SubElement(compo, 'ELEMENTS')
        moduleConfiguration = etree.SubElement(elements,'ECUC-MODULE-CONFIGURATION-VALUES')
        short_name = etree.SubElement(moduleConfiguration,'SHORT-NAME').text = 'MemMap'
        definition = etree.SubElement(moduleConfiguration, 'DEFINITION-REF')
        definition.attrib['DEST'] = "ECUC-MODULE-DEF"
        definition.text = "/AUTOSAR/EcuDefs/MemMap"
        configVariant = etree.SubElement(moduleConfiguration, 'IMPLEMENTATION-CONFIG-VARIANT').text = 'VARIANT-PRE-COMPILE'
        containers = etree.SubElement(moduleConfiguration,'CONTAINERS')

        container = etree.SubElement(containers, 'ECUC-CONTAINER-VALUE')
        short_name = etree.SubElement(container, 'SHORT-NAME').text = "MemMapAllocation_0"
        definition2 = etree.SubElement(container, 'DEFINITION-REF')
        definition2.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition2.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation"
        sub_container = etree.SubElement(container, 'SUB-CONTAINERS')

        for elem in data_elements:
            container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
            short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_' + elem['SWC'].split("/")[-1]
            definition = etree.SubElement(container2, 'DEFINITION-REF')
            definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
            definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
            reference_values = etree.SubElement(container2,'REFERENCE-VALUES')
            reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
            definition = etree.SubElement(reference1, 'DEFINITION-REF')
            definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
            definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
            value = etree.SubElement(reference1, 'VALUE-REF')
            value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
            value.text = "/" + elem['ROOTP'] + '/' + elem['IMPLEMENTATION'] + '/' + elem['RESSOURCE'] + '/' + elem['CODE'] + ""
            reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
            definition = etree.SubElement(reference2, 'DEFINITION-REF')
            definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
            definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
            value = etree.SubElement(reference2, 'VALUE-REF')
            value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
            value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_CODE_" + elem['CORE'] + ""

            if elem['TYPE'] == 'acme':
                container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_' + elem['SWC'].split("/")[-1] + '_START_SEC_INTER_NO_INIT_QM_VAR_8'
                definition = etree.SubElement(container2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
                reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/RootP_Implementation/Implementation_" + elem['CORE'] + '_' + elem['PARTITION']+ '/Resources/INTER_NO_INIT_QM_VAR_8'
                reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_NO_INIT_INTER_QM"

                container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_' + \
                                                                               elem['SWC'].split("/")[-1] + '_START_SEC_INTER_NO_INIT_QM_VAR_16'
                definition = etree.SubElement(container2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
                reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/RootP_Implementation/Implementation_" + elem['CORE'] + '_' + elem['PARTITION'] + '/Resources/INTER_NO_INIT_QM_VAR_16'
                reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_NO_INIT_INTER_QM"

                container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_' + \
                                                                               elem['SWC'].split("/")[-1] + '_START_SEC_INTER_NO_INIT_QM_VAR_32'
                definition = etree.SubElement(container2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
                reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/RootP_Implementation/Implementation_" + elem['CORE'] + '_' + elem['PARTITION'] + '/Resources/INTER_NO_INIT_QM_VAR_32'
                reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_NO_INIT_INTER_QM"

                container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_' + \
                                                                               elem['SWC'].split("/")[-1] + '_START_SEC_INTER_NO_INIT_QM_UNSPECIFIED'
                definition = etree.SubElement(container2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
                reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/RootP_Implementation/Implementation_" + elem['CORE'] + '_' + elem['PARTITION'] + '/Resources/INTER_NO_INIT_QM_UNSPECIFIED'
                reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_NO_INIT_INTER_QM"

                container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_' + \
                                                                               elem['SWC'].split("/")[-1] + '_START_SEC_INTER_INIT_' + elem['PARTITION'] + '_'+ elem['CORE'] +'_VAR_8'
                definition = etree.SubElement(container2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
                reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/RootP_Implementation/Implementation_" + elem['PARTITION'] + '_' + elem['CORE'] + '/Resources/INTER_INIT_' + elem['PARTITION'] + '_' + elem['CORE'] + '_VAR_8'
                reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_INIT_INTER_" + elem['PARTITION'] + '_' + elem['CORE']

                container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_' + \
                                                                               elem['SWC'].split("/")[-1] + '_START_SEC_INTER_INIT_' + elem['PARTITION'] + '_'+ elem['CORE'] +'_VAR_16'
                definition = etree.SubElement(container2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
                reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/RootP_Implementation/Implementation_" + elem['PARTITION'] + '_' + elem['CORE'] + '/Resources/INTER_INIT_' + elem['PARTITION'] + '_' + elem['CORE'] + '_VAR_16'
                reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_INIT_INTER_" + elem['PARTITION'] + '_' + elem['CORE']

                container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_' + \
                                                                               elem['SWC'].split("/")[-1] + '_START_SEC_INTER_INIT_' + elem['PARTITION'] + '_'+ elem['CORE'] +'_VAR_32'
                definition = etree.SubElement(container2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
                reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/RootP_Implementation/Implementation_" + elem['PARTITION'] + '_' + elem['CORE'] + '/Resources/INTER_INIT_' + elem['PARTITION'] + '_' + elem['CORE'] + '_VAR_32'
                reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_INIT_INTER_" + elem['PARTITION'] + '_' + elem['CORE']

                container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_' + \
                                                                               elem['SWC'].split("/")[-1] + '_START_SEC_INTER_INIT_' + \
                                                                               elem['PARTITION'] + '_' + elem['CORE'] + '_UNSPECIFIED'
                definition = etree.SubElement(container2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
                reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/RootP_Implementation/Implementation_" + elem['PARTITION'] + '_' + elem['CORE'] + '/Resources/INTER_INIT_' + elem['PARTITION'] + '_' + elem['CORE'] + '_UNSPECIFIED'
                reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_INIT_INTER_" + elem['PARTITION'] + '_' + elem['CORE']

                container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_' + \
                                                                               elem['SWC'].split("/")[-1] + '_START_SEC_INTER_CLEARED_' + elem['PARTITION'] + '_'+ elem['CORE'] +'_VAR_8'
                definition = etree.SubElement(container2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
                reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/RootP_Implementation/Implementation_" + elem['PARTITION'] + '_' + elem['CORE'] + '/Resources/INTER_CLEARED_' + elem['PARTITION'] + '_' + elem['CORE'] + '_VAR_8'
                reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_CLEARED_INTER_" + elem['PARTITION'] + '_' + elem['CORE']

                container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_' + \
                                                                               elem['SWC'].split("/")[-1] + '_START_SEC_INTER_CLEARED_' + elem['PARTITION'] + '_'+ elem['CORE'] +'_VAR_16'
                definition = etree.SubElement(container2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
                reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/RootP_Implementation/Implementation_" + elem['PARTITION'] + '_' + elem['CORE'] + '/Resources/INTER_CLEARED_' + elem['PARTITION'] + '_' + elem['CORE'] + '_VAR_16'
                reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_CLEARED_INTER_" + elem['PARTITION'] + '_' + elem['CORE']

                container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_' + \
                                                                               elem['SWC'].split("/")[-1] + '_START_SEC_INTER_CLEARED_' + elem['PARTITION'] + '_'+ elem['CORE'] +'_VAR_32'
                definition = etree.SubElement(container2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
                reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/RootP_Implementation/Implementation_" + elem['PARTITION'] + '_' + elem['CORE'] + '/Resources/INTER_CLEARED_' + elem['PARTITION'] + '_' + elem['CORE'] + '_VAR_32'
                reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_CLEARED_INTER_" + elem['PARTITION'] + '_' + elem['CORE']

                container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_' + \
                                                                               elem['SWC'].split("/")[-1] + '_START_SEC_INTER_CLEARED_' + \
                                                                               elem['PARTITION'] + '_' + elem['CORE'] + '_UNSPECIFIED'
                definition = etree.SubElement(container2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
                reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/RootP_Implementation/Implementation_" + elem['PARTITION'] + '_' + elem['CORE'] + '/Resources/INTER_CLEARED_' + elem['PARTITION'] + '_' + elem['CORE'] + '_UNSPECIFIED'
                reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_CLEARED_INTER_" + elem['PARTITION'] + '_' + elem['CORE']

            if elem['TYPE'] == 'acme' or elem['TYPE'] == 'aswc':
                container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_' + \
                                                                               elem['SWC'].split("/")[-1] + '_START_SEC_PRIVATE_INIT_VAR_8'
                definition = etree.SubElement(container2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
                reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/RootP_Implementation/Implementation_" + elem['CORE'] + '_' + elem['PARTITION'] + '/Resources/PRIVATE_INIT_VAR_8'
                reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_INIT_PRIVATE_" + elem['CORE'] + '_' + elem['PARTITION']

                container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_' + \
                                                                               elem['SWC'].split("/")[-1] + '_START_SEC_PRIVATE_INIT_VAR_16'
                definition = etree.SubElement(container2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
                reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/RootP_Implementation/Implementation_" + elem['CORE'] + '_' + elem['PARTITION'] + '/Resources/PRIVATE_INIT_VAR_16'
                reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_INIT_PRIVATE_" + elem['CORE'] + '_' + elem['PARTITION']

                container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_' + \
                                                                               elem['SWC'].split("/")[-1] + '_START_SEC_PRIVATE_INIT_VAR_32'
                definition = etree.SubElement(container2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
                reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/RootP_Implementation/Implementation_" + elem['CORE'] + '_' + elem['PARTITION'] + '/Resources/PRIVATE_INIT_VAR_32'
                reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_INIT_PRIVATE_" + elem['CORE'] + '_' + elem['PARTITION']

                container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_' + \
                                                                               elem['SWC'].split("/")[-1] + '_START_SEC_PRIVATE_INIT_VAR_UNSPECIFIED'
                definition = etree.SubElement(container2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
                reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/RootP_Implementation/Implementation_" + elem['CORE'] + '_' + elem['PARTITION'] + '/Resources/PRIVATE_INIT_VAR_UNSPECIFIED'
                reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_INIT_PRIVATE_" + elem['CORE'] + '_' + elem['PARTITION']

                container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_' + \
                                                                               elem['SWC'].split("/")[-1] + '_START_SEC_PRIVATE_CLEARED_VAR_8'
                definition = etree.SubElement(container2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
                reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/RootP_Implementation/Implementation_" + elem['CORE'] + '_' + elem['PARTITION'] + '/Resources/PRIVATE_CLEARED_VAR_8'
                reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_CLEARED_PRIVATE_" + elem['CORE'] + '_' + elem['PARTITION']

                container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_' + \
                                                                               elem['SWC'].split("/")[-1] + '_START_SEC_PRIVATE_CLEARED_VAR_16'
                definition = etree.SubElement(container2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
                reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/RootP_Implementation/Implementation_" + elem['CORE'] + '_' + elem['PARTITION'] + '/Resources/PRIVATE_CLEARED_VAR_16'
                reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_CLEARED_PRIVATE_" + elem['CORE'] + '_' + elem['PARTITION']

                container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_' + \
                                                                               elem['SWC'].split("/")[-1] + '_START_SEC_PRIVATE_CLEARED_VAR_32'
                definition = etree.SubElement(container2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
                reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/RootP_Implementation/Implementation_" + elem['CORE'] + '_' + elem['PARTITION'] + '/Resources/PRIVATE_CLEARED_VAR_32'
                reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_CLEARED_PRIVATE_" + elem['CORE'] + '_' + elem['PARTITION']

                container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_' + \
                                                                               elem['SWC'].split("/")[-1] + '_START_SEC_PRIVATE_CLEARED_VAR_UNSPECIFIED'
                definition = etree.SubElement(container2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
                reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/RootP_Implementation/Implementation_" + elem['CORE'] + '_' + elem['PARTITION'] + '/Resources/PRIVATE_CLEARED_VAR_UNSPECIFIED'
                reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_CLEARED_PRIVATE_" + elem['CORE'] + '_' + elem['PARTITION']

                container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_' + \
                                                                               elem['SWC'].split("/")[-1] + '_START_SEC_PUBLIC_INIT_VAR_8'
                definition = etree.SubElement(container2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
                reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/RootP_Implementation/Implementation_" + elem['CORE'] + '_' + elem['PARTITION'] + '/Resources/PUBLIC_INIT_VAR_8'
                reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_INIT_PUBLIC_" + elem['CORE'] + '_' + elem['PARTITION']

                container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_' + \
                                                                               elem['SWC'].split("/")[-1] + '_START_SEC_PUBLIC_INIT_VAR_16'
                definition = etree.SubElement(container2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
                reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/RootP_Implementation/Implementation_" + elem['CORE'] + '_' + elem['PARTITION'] + '/Resources/PUBLIC_INIT_VAR_16'
                reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_INIT_PUBLIC_" + elem['CORE'] + '_' + elem['PARTITION']

                container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_' + \
                                                                               elem['SWC'].split("/")[-1] + '_START_SEC_PUBLIC_INIT_VAR_32'
                definition = etree.SubElement(container2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
                reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/RootP_Implementation/Implementation_" + elem['CORE'] + '_' + elem['PARTITION'] + '/Resources/PUBLIC_INIT_VAR_32'
                reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_INIT_PUBLIC_" + elem['CORE'] + '_' + elem['PARTITION']

                container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_' + \
                                                                               elem['SWC'].split("/")[-1] + '_START_SEC_PUBLIC_INIT_VAR_UNSPECIFIED'
                definition = etree.SubElement(container2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
                reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/RootP_Implementation/Implementation_" + elem['CORE'] + '_' + elem['PARTITION'] + '/Resources/PUBLIC_INIT_VAR_UNSPECIFIED'
                reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_INIT_PUBLIC_" + elem['CORE'] + '_' + elem['PARTITION']

                container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_' + \
                                                                               elem['SWC'].split("/")[-1] + '_START_SEC_PUBLIC_CLEARED_VAR_8'
                definition = etree.SubElement(container2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
                reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/RootP_Implementation/Implementation_" + elem['CORE'] + '_' + elem['PARTITION'] + '/Resources/PUBLIC_CLEARED_VAR_8'
                reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_CLEARED_PUBLIC_" + elem['CORE'] + '_' + elem['PARTITION']

                container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_' + \
                                                                               elem['SWC'].split("/")[-1] + '_START_SEC_PUBLIC_CLEARED_VAR_16'
                definition = etree.SubElement(container2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
                reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/RootP_Implementation/Implementation_" + elem['CORE'] + '_' + elem['PARTITION'] + '/Resources/PUBLIC_CLEARED_VAR_16'
                reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_CLEARED_PUBLIC_" + elem['CORE'] + '_' + elem['PARTITION']

                container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_' + \
                                                                               elem['SWC'].split("/")[-1] + '_START_SEC_PUBLIC_CLEARED_VAR_32'
                definition = etree.SubElement(container2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
                reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/RootP_Implementation/Implementation_" + elem['CORE'] + '_' + elem['PARTITION'] + '/Resources/PUBLIC_CLEARED_VAR_32'
                reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_CLEARED_PUBLIC_" + elem['CORE'] + '_' + elem['PARTITION']

                container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_' + \
                                                                               elem['SWC'].split("/")[-1] + '_START_SEC_PUBLIC_CLEARED_VAR_UNSPECIFIED'
                definition = etree.SubElement(container2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
                reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/RootP_Implementation/Implementation_" + elem['CORE'] + '_' + elem['PARTITION'] + '/Resources/PUBLIC_CLEARED_VAR_UNSPECIFIED'
                reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_CLEARED_PUBLIC_" + elem['CORE'] + '_' + elem['PARTITION']


        for elem in swc_no_duplicates:
            if elem['TYPE'] == 'rte':
                container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_RTE_START_SEC_' + elem['CORE'] + '_' + elem['PARTITION'] + '_VAR_8'
                definition = etree.SubElement(container2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
                reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/EB_Rte/Implementations/BswImplementation_0/ResourceConsumption/OSAPP_" + elem['CORE'].upper() + "_" + elem['PARTITION'].upper() + "_VAR_8"
                reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_INIT_PRIVATE_" + elem['CORE'] + "_" + elem['PARTITION']

                container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_RTE_START_SEC_' + elem['CORE'] + '_' + elem['PARTITION'] + '_VAR_16'
                definition = etree.SubElement(container2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
                reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/EB_Rte/Implementations/BswImplementation_0/ResourceConsumption/OSAPP_" + elem['CORE'].upper() + "_" + \
                             elem['PARTITION'].upper() + "_VAR_16"
                reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_INIT_PRIVATE_" + elem['CORE'] + "_" + elem['PARTITION']

                container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_RTE_START_SEC_' + elem['CORE'] + '_' + elem['PARTITION'] + '_VAR_32'
                definition = etree.SubElement(container2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
                reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/EB_Rte/Implementations/BswImplementation_0/ResourceConsumption/OSAPP_" + elem['CORE'].upper() + "_" + \
                             elem['PARTITION'].upper() + "_VAR_32"
                reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_INIT_PRIVATE_" + elem['CORE'] + "_" + elem['PARTITION']

                container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_RTE_START_SEC_' + elem['CORE'] + '_' + elem['PARTITION'] + '_VAR_UNSPECIFIED'
                definition = etree.SubElement(container2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
                reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/EB_Rte/Implementations/BswImplementation_0/ResourceConsumption/OSAPP_" + elem['CORE'].upper() + "_" + \
                             elem['PARTITION'].upper() + "_UNSPECIFIED"
                reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_INIT_PRIVATE_" + elem['CORE'] + "_" + elem['PARTITION']

                container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_RTE_START_SEC_SHARED_' + elem['CORE'] + '_' + elem['PARTITION'] + '_VAR_8'
                definition = etree.SubElement(container2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
                reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/EB_Rte/Implementations/BswImplementation_0/ResourceConsumption/OSAPP_" + elem['CORE'].upper() + "_" + \
                             elem['PARTITION'].upper() + "_VAR_8"
                reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_INIT_PUBLIC_" + elem['CORE'] + "_" + elem['PARTITION']

                container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_RTE_START_SEC_SHARED_' + elem['CORE'] + '_' + elem['PARTITION'] + '_VAR_16'
                definition = etree.SubElement(container2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
                reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/EB_Rte/Implementations/BswImplementation_0/ResourceConsumption/OSAPP_" + elem['CORE'].upper() + "_" + \
                             elem['PARTITION'].upper() + "_VAR_16"
                reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_INIT_PUBLIC_" + elem['CORE'] + "_" + elem['PARTITION']

                container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_RTE_START_SEC_SHARED_' + elem['CORE'] + '_' + elem['PARTITION'] + '_VAR_32'
                definition = etree.SubElement(container2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
                reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/EB_Rte/Implementations/BswImplementation_0/ResourceConsumption/OSAPP_" + elem['CORE'].upper() + "_" + \
                             elem['PARTITION'].upper() + "_VAR_32"
                reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_INIT_PUBLIC_" + elem['CORE'] + "_" + elem['PARTITION']

                container2 = etree.SubElement(sub_container, 'ECUC-CONTAINER-VALUE')
                short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapSectionSpecificMapping_RTE_START_SEC_SHARED_' + elem['CORE'] + '_' + elem['PARTITION'] + '_UNSPECIFIED'
                definition = etree.SubElement(container2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
                reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
                reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference1, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
                value = etree.SubElement(reference1, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/EB_Rte/Implementations/BswImplementation_0/ResourceConsumption/OSAPP_" + elem['CORE'].upper() + "_" + \
                             elem['PARTITION'].upper() + "_UNSPECIFIED"
                reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
                definition = etree.SubElement(reference2, 'DEFINITION-REF')
                definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
                definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
                value = etree.SubElement(reference2, 'VALUE-REF')
                value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
                value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_INIT_PUBLIC_" + elem['CORE'] + "_" + elem['PARTITION']

        all_swcs=''
        for elem in swc_no_duplicates:
            all_swcs = all_swcs + elem['CORE'] + '_' + elem['PARTITION'] + '_'

        container2 = etree.SubElement(containers,'ECUC-CONTAINER-VALUE')
        short_name = etree.SubElement(container2,'SHORT-NAME').text = 'MemMapSectionSpecificMapping_RTE_START_SEC_' + all_swcs + 'VAR_8'
        definition = etree.SubElement(container2, 'DEFINITION-REF')
        definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
        definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
        reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
        reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
        definition = etree.SubElement(reference1, 'DEFINITION-REF')
        definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
        definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
        value = etree.SubElement(reference1, 'VALUE-REF')
        value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
        value.text = "/EB_Rte/Implementations/BswImplementation_0/ResourceConsumption/OSAPP_" + elem['CORE'].upper() + "_" + \
                     elem['PARTITION'].upper() + "_VAR_8"
        reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
        definition = etree.SubElement(reference2, 'DEFINITION-REF')
        definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
        definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
        value = etree.SubElement(reference2, 'VALUE-REF')
        value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
        value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_INIT_INTER_QM_CORE0"

        container2 = etree.SubElement(containers,'ECUC-CONTAINER-VALUE')
        short_name = etree.SubElement(container2,'SHORT-NAME').text = 'MemMapSectionSpecificMapping_RTE_START_SEC_' + all_swcs  + 'VAR_16'
        definition = etree.SubElement(container2, 'DEFINITION-REF')
        definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
        definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
        reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
        reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
        definition = etree.SubElement(reference1, 'DEFINITION-REF')
        definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
        definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
        value = etree.SubElement(reference1, 'VALUE-REF')
        value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
        value.text = "/EB_Rte/Implementations/BswImplementation_0/ResourceConsumption/OSAPP_" + elem['CORE'].upper() + "_" + \
                     elem['PARTITION'].upper() + "_VAR_16"
        reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
        definition = etree.SubElement(reference2, 'DEFINITION-REF')
        definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
        definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
        value = etree.SubElement(reference2, 'VALUE-REF')
        value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
        value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_INIT_INTER_QM_CORE0"

        container2 = etree.SubElement(containers,'ECUC-CONTAINER-VALUE')
        short_name = etree.SubElement(container2,'SHORT-NAME').text = 'MemMapSectionSpecificMapping_RTE_START_SEC_' + all_swcs + 'VAR_32'
        definition = etree.SubElement(container2, 'DEFINITION-REF')
        definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
        definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
        reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
        reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
        definition = etree.SubElement(reference1, 'DEFINITION-REF')
        definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
        definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
        value = etree.SubElement(reference1, 'VALUE-REF')
        value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
        value.text = "/EB_Rte/Implementations/BswImplementation_0/ResourceConsumption/OSAPP_" + elem['CORE'].upper() + "_" + \
                     elem['PARTITION'].upper() + "_VAR_32"
        reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
        definition = etree.SubElement(reference2, 'DEFINITION-REF')
        definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
        definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
        value = etree.SubElement(reference2, 'VALUE-REF')
        value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
        value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_INIT_INTER_QM_CORE0"

        container2 = etree.SubElement(containers,'ECUC-CONTAINER-VALUE')
        short_name = etree.SubElement(container2,'SHORT-NAME').text = 'MemMapSectionSpecificMapping_RTE_START_SEC_' + all_swcs +'_UNSPECIFIED'
        definition = etree.SubElement(container2, 'DEFINITION-REF')
        definition.attrib['DEST'] = "ECUC-CHOICE-CONTAINER-DEF"
        definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping"
        reference_values = etree.SubElement(container2, 'REFERENCE-VALUES')
        reference1 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
        definition = etree.SubElement(reference1, 'DEFINITION-REF')
        definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
        definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapMemorySectionRef"
        value = etree.SubElement(reference1, 'VALUE-REF')
        value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
        value.text = "/EB_Rte/Implementations/BswImplementation_0/ResourceConsumption/OSAPP_" + elem['CORE'].upper() + "_" + \
                     elem['PARTITION'].upper() + "_UNSPECIFIED"
        reference2 = etree.SubElement(reference_values, 'ECUC-REFERENCE-VALUE')
        definition = etree.SubElement(reference2, 'DEFINITION-REF')
        definition.attrib['DEST'] = "ECUC-SYMBOLIC-NAME-REFERENCE-DEF"
        definition.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAllocation/MemMapSectionSpecificMapping/MemMapAddressingModeSetRef"
        value = etree.SubElement(reference2, 'VALUE-REF')
        value.attrib['DEST'] = "ECUC-CONTAINER-VALUE"
        value.text = "/MemMap/MemMap/MemMapAddressingModeSet_VSM_INIT_INTER_QM_CORE0"

        for elem in swc_no_duplicates:
            container2 = etree.SubElement(containers,'ECUC-CONTAINER-VALUE')
            short_name = etree.SubElement(container2, 'SHORT-NAME').text = 'MemMapAddressingModeSet_VSM_CLEARED_INTER_' + elem['PARTITION'] + '_' + elem['CORE']
            definition2 = etree.SubElement(container2, 'DEFINITION-REF')
            definition2.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
            definition2.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet"
            sub_container2 = etree.SubElement(container2,'SUB-CONTAINERS')

            container_value= etree.SubElement(sub_container2,'ECUC-CONTAINER-VALUE')
            short_name_cv = etree.SubElement(container_value,'SHORT-NAME').text = 'MemMapAddressingMode_16bits'
            definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
            definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
            definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
            parameter_values = etree.SubElement(container_value,'PARAMETER-VALUES')
            textual_param = etree.SubElement(parameter_values,'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
            value_tp = etree.SubElement(textual_param,'VALUE').text = '#pragma section ".bss.inter.' + elem['PARTITION'].lower() + '.' + elem['CORE'].lower() +  '.VAR_16" aw 2'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '16'

            container_value = etree.SubElement(sub_container2, 'ECUC-CONTAINER-VALUE')
            short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_32bits'
            definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
            definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
            definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
            parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".bss.inter.' + elem['PARTITION'].lower() + '.' + elem['CORE'].lower() + '.VAR_32" aw 4'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '32'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = 'UNSPECIFIED'

            container_value = etree.SubElement(sub_container2, 'ECUC-CONTAINER-VALUE')
            short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_8bits'
            definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
            definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
            definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
            parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".bss.inter.' + elem['PARTITION'].lower() + '.' + elem['CORE'].lower() + '.VAR_8" aw 1'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '8'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = 'BOOLEAN'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = ''


            container3 = etree.SubElement(containers, 'ECUC-CONTAINER-VALUE')
            short_name_2 = etree.SubElement(container3,'SHORT-NAME').text = 'MemMapAddressingModeSet_VSM_INIT_INTER_' + elem['PARTITION'] + '_' + elem['CORE']
            definition3 = etree.SubElement(container3, 'DEFINITION-REF')
            definition3.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
            definition3.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet"
            sub_container3 = etree.SubElement(container3, 'SUB-CONTAINERS')

            container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
            short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_16bits'
            definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
            definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
            definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
            parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".data.inter.' + elem['PARTITION'].lower() + '.' + elem['CORE'].lower() + '.VAR_16" aw 2'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '16'

            container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
            short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_32bits'
            definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
            definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
            definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
            parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".data.inter.' + elem['PARTITION'].lower() + '.' + elem['CORE'].lower() + '.VAR_32" aw 4'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '32'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = 'UNSPECIFIED'

            container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
            short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_8bits'
            definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
            definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
            definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
            parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".data.inter.' + elem['PARTITION'].lower() + '.' + elem['CORE'].lower() + '.VAR_8" aw 1'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '8'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = 'BOOLEAN'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = ''




        container_inter_qm = etree.SubElement(containers,'ECUC-CONTAINER-VALUE')
        short_name = etree.SubElement(container_inter_qm, 'SHORT-NAME').text = 'MemMapAddressingModeSet_VSM_NO_INIT_INTER_QM'
        definition2 = etree.SubElement(container_inter_qm, 'DEFINITION-REF')
        definition2.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition2.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet"
        sub_container3 = etree.SubElement(container_inter_qm, 'SUB-CONTAINERS')

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_16bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".no_init.inter.qm.core0.VAR_16" aw 2'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '16'

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_32bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".no_init.inter.qm.core0.VAR_32" aw 4'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '32'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = 'UNSPECIFIED'

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_8bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".no_init.inter.qm.core0.VAR_8" aw 1'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '8'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = 'BOOLEAN'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = ''

        container_no_init = etree.SubElement(containers, 'ECUC-CONTAINER-VALUE')
        short_name = etree.SubElement(container_no_init,'SHORT-NAME').text = 'MemMapAddressingModeSet_VSM_NO_INIT'
        definition2 = etree.SubElement(container_no_init, 'DEFINITION-REF')
        definition2.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition2.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet"
        parameter_values2 = etree.SubElement(container_no_init,'PARAMETER-VALUES')
        textual_param2 = etree.SubElement(parameter_values2,'ECUC-TEXTUAL-PARAM-VALUE')
        definition3 = etree.SubElement(textual_param2, 'DEFINITION-REF')
        definition3.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition3.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapSupportedSectionInitializationPolicy"
        value2 = etree.SubElement(textual_param2,'VALUE').text ='NO-INIT'
        sub_container3 = etree.SubElement(container_no_init, 'SUB-CONTAINERS')

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_16bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param,'VALUE').text = '#pragma section ".no_init.inter.core0.VAR_NO_INIT_16" aw 2'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '16'

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_32bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param,'VALUE').text = '#pragma section ".no_init.core0.VAR_NO_INIT_32" aw 4'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '32'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = 'UNSPECIFIED'

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_8bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param,'VALUE').text = '#pragma section ".no_init.core0.VAR_NO_INIT_8" aw 1'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '8'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = 'BOOLEAN'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = ''

        container_power_on_init = etree.SubElement(containers, 'ECUC-CONTAINER-VALUE')
        short_name = etree.SubElement(container_power_on_init, 'SHORT-NAME').text = 'MemMapAddressingModeSet_VSM_POWER_ON_INIT'
        definition2 = etree.SubElement(container_power_on_init, 'DEFINITION-REF')
        definition2.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition2.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet"
        parameter_values2 = etree.SubElement(container_power_on_init, 'PARAMETER-VALUES')
        textual_param2 = etree.SubElement(parameter_values2, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition3 = etree.SubElement(textual_param2, 'DEFINITION-REF')
        definition3.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition3.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapSupportedSectionInitializationPolicy"
        value2 = etree.SubElement(textual_param2, 'VALUE').text = 'POWER-ON-INIT'
        sub_container3 = etree.SubElement(container_power_on_init, 'SUB-CONTAINERS')

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_16bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param,'VALUE').text = '#pragma section ".power_on_data.VAR_POWER_ON_INIT_16" aw 2'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '16'

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_32bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param,'VALUE').text = '#pragma section ".power_on_data.VAR_POWER_ON_INIT_32" aw 4'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '32'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = 'UNSPECIFIED'

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_8bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".power_on_data.VAR_POWER_ON_INIT_8" aw 1'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '8'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = 'BOOLEAN'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = ''

        container_vsm_cleared = etree.SubElement(containers, 'ECUC-CONTAINER-VALUE')
        short_name = etree.SubElement(container_vsm_cleared,'SHORT-NAME').text = 'MemMapAddressingModeSet_VSM_CLEARED'
        definition2 = etree.SubElement(container_vsm_cleared, 'DEFINITION-REF')
        definition2.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition2.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet"
        parameter_values2 = etree.SubElement(container_vsm_cleared, 'PARAMETER-VALUES')
        textual_param2 = etree.SubElement(parameter_values2, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition3 = etree.SubElement(textual_param2, 'DEFINITION-REF')
        definition3.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition3.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapSupportedSectionInitializationPolicy"
        value2 = etree.SubElement(textual_param2, 'VALUE').text = 'CLEARED'
        sub_container3 = etree.SubElement(container_vsm_cleared, 'SUB-CONTAINERS')

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_16bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param,'VALUE').text = '#pragma section ".bss.core0.VAR_CLEARED_16" awB 2'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '16'

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_256bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param,'VALUE').text = '#pragma section ".core0.VAR_CLEARED_256" awB 32'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '256'

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_32bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".bss.core0.VAR_CLEARED_32" awB 4'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '32'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = 'UNSPECIFIED'

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_8bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param,'VALUE').text = '#pragma section ".bss.core0.VAR_CLEARED_8" awB 1'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '8'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = 'BOOLEAN'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = ''

        container_power_on_cleared = etree.SubElement(containers, 'ECUC-CONTAINER-VALUE')
        short_name = etree.SubElement(container_power_on_cleared, 'SHORT-NAME').text = 'MemMapAddressingModeSet_VSM_POWER_ON_CLEARED'
        definition2 = etree.SubElement(container_power_on_cleared, 'DEFINITION-REF')
        definition2.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition2.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet"
        parameter_values2 = etree.SubElement(container_power_on_cleared, 'PARAMETER-VALUES')
        textual_param2 = etree.SubElement(parameter_values2, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition3 = etree.SubElement(textual_param2, 'DEFINITION-REF')
        definition3.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition3.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapSupportedSectionInitializationPolicy"
        value2 = etree.SubElement(textual_param2, 'VALUE').text = 'POWER-ON-CLEARED'
        sub_container3 = etree.SubElement(container_power_on_cleared, 'SUB-CONTAINERS')

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_16bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".power_on_bss.VAR_POWER_ON_CLEARED_16" aw 2'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '16'

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_32bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".power_on_bss.VAR_POWER_ON_CLEARED_32" aw 4'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '32'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = 'UNSPECIFIED'

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_8bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".power_on_bss.VAR_POWER_ON_CLEARED_8" aw 1'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '8'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = 'BOOLEAN'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = ''

        container_const = etree.SubElement(containers, 'ECUC-CONTAINER-VALUE')
        short_name = etree.SubElement(container_const,'SHORT-NAME').text = 'MemMapAddressingModeSet_VSM_CONST'
        definition2 = etree.SubElement(container_const, 'DEFINITION-REF')
        definition2.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition2.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet"
        sub_container3 = etree.SubElement(container_const, 'SUB-CONTAINERS')

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_16bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param,'VALUE').text = '#pragma section ".rodata.CONST_16" a 2'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '16'

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_32bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param,'VALUE').text = '#pragma section ".rodata.CONST_32" a 4'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '32'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = 'UNSPECIFIED'

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_8bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param,'VALUE').text = '#pragma section ".rodata.CONST_8" a 1'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '8'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = 'BOOLEAN'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = ''


        for elem in list_cores:
            container_code_core0 = etree.SubElement(containers, 'ECUC-CONTAINER-VALUE')
            short_name = etree.SubElement(container_code_core0, 'SHORT-NAME').text = 'MemMapAddressingModeSet_VSM_CODE_' + elem['CORE']
            definition2 = etree.SubElement(container_code_core0, 'DEFINITION-REF')
            definition2.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
            definition2.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet"
            parameter_values2 = etree.SubElement(container_code_core0, 'PARAMETER-VALUES')
            textual_param2 = etree.SubElement(parameter_values2, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition3 = etree.SubElement(textual_param2, 'DEFINITION-REF')
            definition3.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition3.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapSupportedSectionType"
            value2 = etree.SubElement(textual_param2, 'VALUE').text = 'MEMMAP_SECTION_TYPE_CODE'
            sub_container3 = etree.SubElement(container_code_core0, 'SUB-CONTAINERS')

            container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
            short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_code_app_' + elem['CORE'].lower()
            definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
            definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
            definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
            parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
            value_tp = etree.SubElement(textual_param,'VALUE').text = '#pragma section ".code_app.' + elem['CORE'].lower() + '" ax'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = ''


        for elem in list_cores:
            container_code_swp_core0 = etree.SubElement(containers, 'ECUC-CONTAINER-VALUE')
            short_name = etree.SubElement(container_code_swp_core0, 'SHORT-NAME').text = 'MemMapAddressingModeSet_VSM_CODE_SWP_' + elem['CORE']
            definition2 = etree.SubElement(container_code_swp_core0, 'DEFINITION-REF')
            definition2.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
            definition2.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet"
            parameter_values2 = etree.SubElement(container_code_swp_core0, 'PARAMETER-VALUES')
            textual_param2 = etree.SubElement(parameter_values2, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition3 = etree.SubElement(textual_param2, 'DEFINITION-REF')
            definition3.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition3.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapSupportedSectionType"
            value2 = etree.SubElement(textual_param2, 'VALUE').text = 'MEMMAP_SECTION_TYPE_CODE'
            sub_container3 = etree.SubElement(container_code_swp_core0, 'SUB-CONTAINERS')

            container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
            short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_code_swp_' + elem['CORE'].lower()
            definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
            definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
            definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
            parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".code_swp.' + elem['CORE'].lower() + '" ax'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = ''



        container_shared_init = etree.SubElement(containers, 'ECUC-CONTAINER-VALUE')
        short_name = etree.SubElement(container_shared_init, 'SHORT-NAME').text = 'MemMapAddressingModeSet_VSM_SHARED_INIT'
        definition2 = etree.SubElement(container_shared_init, 'DEFINITION-REF')
        definition2.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition2.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet"
        sub_container3 = etree.SubElement(container_shared_init, 'SUB-CONTAINERS')

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_16bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".shared_data.16" aw 2'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '16'

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_32bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".shared_data.32" aw 4'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '32'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = 'UNSPECIFIED'

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_8bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".shared_data.8" aw 1'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '8'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = 'BOOLEAN'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = ''

        container_shared_cleared = etree.SubElement(containers, 'ECUC-CONTAINER-VALUE')
        short_name = etree.SubElement(container_shared_cleared, 'SHORT-NAME').text = 'MemMapAddressingModeSet_VSM_SHARED_CLEARED'
        definition2 = etree.SubElement(container_shared_cleared, 'DEFINITION-REF')
        definition2.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition2.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet"
        sub_container3 = etree.SubElement(container_shared_cleared, 'SUB-CONTAINERS')

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_16bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".shared_bss.16" awB 2'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '16'

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_32bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".shared_bss.32" awB 4'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '32'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = 'UNSPECIFIED'

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_8bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".shared_bss.8" awB 1'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '8'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = 'BOOLEAN'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = ''

        container_shared_boot_cleared = etree.SubElement(containers, 'ECUC-CONTAINER-VALUE')
        short_name = etree.SubElement(container_shared_boot_cleared, 'SHORT-NAME').text = 'MemMapAddressingModeSet_VSM_SHARED_BOOT_CLEARED'
        definition2 = etree.SubElement(container_shared_boot_cleared, 'DEFINITION-REF')
        definition2.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition2.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet"
        sub_container3 = etree.SubElement(container_shared_boot_cleared, 'SUB-CONTAINERS')

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_16bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".shared_boot.16" awB 2'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '16'

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_32bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".shared_boot.32" awB 4'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '32'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = 'UNSPECIFIED'

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_8bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".shared_boot.8" awB 1'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '8'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = 'BOOLEAN'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = ''

        container_shared_factory_cleared = etree.SubElement(containers, 'ECUC-CONTAINER-VALUE')
        short_name = etree.SubElement(container_shared_factory_cleared, 'SHORT-NAME').text = 'MemMapAddressingModeSet_VSM_SHARED_FACTORY_CLEARED'
        definition2 = etree.SubElement(container_shared_factory_cleared, 'DEFINITION-REF')
        definition2.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition2.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet"
        sub_container3 = etree.SubElement(container_shared_factory_cleared, 'SUB-CONTAINERS')

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_16bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".shared_factory.16" awB 2'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '16'

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_32bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".shared_factory.32" awB 4'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '32'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = 'UNSPECIFIED'

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_8bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".shared_factory.8" awB 1'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '8'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = 'BOOLEAN'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = ''

        container_spi_cleared = etree.SubElement(containers, 'ECUC-CONTAINER-VALUE')
        short_name = etree.SubElement(container_spi_cleared, 'SHORT-NAME').text = 'MemMapAddressingModeSet_SPI_CLEARED'
        definition2 = etree.SubElement(container_spi_cleared, 'DEFINITION-REF')
        definition2.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition2.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet"
        parameter_values2 = etree.SubElement(container_spi_cleared, 'PARAMETER-VALUES')
        textual_param2 = etree.SubElement(parameter_values2, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition3 = etree.SubElement(textual_param2, 'DEFINITION-REF')
        definition3.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition3.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapSupportedSectionInitializationPolicy"
        value2 = etree.SubElement(textual_param2, 'VALUE').text = 'CLEARED'
        sub_container3 = etree.SubElement(container_spi_cleared, 'SUB-CONTAINERS')

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_256bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".core0.VAR_CLEARED_256" awB 32'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '256'

        container_vsm_data = etree.SubElement(containers, 'ECUC-CONTAINER-VALUE')
        short_name = etree.SubElement(container_vsm_data, 'SHORT-NAME').text = 'MemMapAddressingModeSet_VSM_DATA'
        definition2 = etree.SubElement(container_vsm_data, 'DEFINITION-REF')
        definition2.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition2.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet"
        sub_container3 = etree.SubElement(container_vsm_data, 'SUB-CONTAINERS')

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_32bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".variant_cfg" a 4'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = 'UNSPECIFIED'

        container_vsm_data_header = etree.SubElement(containers, 'ECUC-CONTAINER-VALUE')
        short_name = etree.SubElement(container_vsm_data_header, 'SHORT-NAME').text = 'MemMapAddressingModeSet_VSM_DATA_HEADER'
        definition2 = etree.SubElement(container_vsm_data_header, 'DEFINITION-REF')
        definition2.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition2.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet"
        sub_container3 = etree.SubElement(container_vsm_data_header, 'SUB-CONTAINERS')

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_32bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".variant_cfg_header" a 4'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = 'UNSPECIFIED'

        container_ssp_no_init = etree.SubElement(containers, 'ECUC-CONTAINER-VALUE')
        short_name = etree.SubElement(container_ssp_no_init, 'SHORT-NAME').text = 'MemMapAddressingModeSet_SSP_NO_INIT'
        definition2 = etree.SubElement(container_ssp_no_init, 'DEFINITION-REF')
        definition2.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition2.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet"
        parameter_values2 = etree.SubElement(container_ssp_no_init, 'PARAMETER-VALUES')
        textual_param2 = etree.SubElement(parameter_values2, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition3 = etree.SubElement(textual_param2, 'DEFINITION-REF')
        definition3.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition3.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapSupportedSectionInitializationPolicy"
        value2 = etree.SubElement(textual_param2, 'VALUE').text = 'INIT'
        sub_container3 = etree.SubElement(container_ssp_no_init, 'SUB-CONTAINERS')

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_16bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".data.core0.VAR_16" aw 2'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '16'

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_32bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".data.core0.VAR_32" aw 4'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '32'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = 'UNSPECIFIED'

        container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
        short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_8bits'
        definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
        definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
        definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
        parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".data.core0.VAR_8" aw 1'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = '8'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = 'BOOLEAN'
        textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
        definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
        definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
        definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
        value_tp = etree.SubElement(textual_param, 'VALUE').text = ''




        for elem in swc_no_duplicates:
            #if swc_no_duplicates['TYPE'] == 'aswc':
            container2 = etree.SubElement(containers, 'ECUC-CONTAINER-VALUE')
            short_name = etree.SubElement(container2,'SHORT-NAME').text = 'MemMapAddressingMode_VSM_CLEARED_PRIVATE_' + elem['CORE'] + '_' + elem['PARTITION']
            definition2 = etree.SubElement(container2, 'DEFINITION-REF')
            definition2.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
            definition2.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet"
            sub_container2 = etree.SubElement(container2, 'SUB-CONTAINERS')

            container_value = etree.SubElement(sub_container2, 'ECUC-CONTAINER-VALUE')
            short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_16bits'
            definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
            definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
            definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
            parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".bss.private.' + elem['PARTITION'].lower() + '.' + elem['CORE'].lower() + '.VAR_16" aw 2'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '16'

            container_value = etree.SubElement(sub_container2, 'ECUC-CONTAINER-VALUE')
            short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_32bits'
            definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
            definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
            definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
            parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".bss.private.' + elem['PARTITION'].lower() + '.' + elem['CORE'].lower() + '.VAR_32" aw 4'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '32'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = 'UNSPECIFIED'

            container_value = etree.SubElement(sub_container2, 'ECUC-CONTAINER-VALUE')
            short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_8bits'
            definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
            definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
            definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
            parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".bss.private.' + elem['PARTITION'].lower() + '.' + elem['CORE'].lower() + '.VAR_8" aw 1'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '8'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = 'BOOLEAN'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = ''

            container3 = etree.SubElement(containers, 'ECUC-CONTAINER-VALUE')
            short_name_2 = etree.SubElement(container3, 'SHORT-NAME').text = 'MemMapAddressingMode_VSM_INIT_PRIVATE_' + elem['CORE'] + '_' + elem['PARTITION']
            definition3 = etree.SubElement(container3, 'DEFINITION-REF')
            definition3.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
            definition3.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet"
            sub_container3 = etree.SubElement(container3, 'SUB-CONTAINERS')

            container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
            short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_16bits'
            definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
            definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
            definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
            parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".data.private.' + elem['PARTITION'].lower() + '.' + elem['CORE'].lower() + '.VAR_16" aw 2'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '16'

            container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
            short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_32bits'
            definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
            definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
            definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
            parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".data.private.' + elem['PARTITION'].lower() + '.' + elem['CORE'].lower() + '.VAR_32" aw 4'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '32'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = 'UNSPECIFIED'

            container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
            short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_8bits'
            definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
            definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
            definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
            parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".data.private.' + elem['PARTITION'].lower() + '.' + elem['CORE'].lower() + '.VAR_8" aw 1'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '8'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = 'BOOLEAN'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = ''



        for elem in swc_no_duplicates:
            #if swc_no_duplicates['TYPE'] == 'aswc':
            container2 = etree.SubElement(containers, 'ECUC-CONTAINER-VALUE')
            short_name = etree.SubElement(container2,'SHORT-NAME').text = 'MemMapAddressingMode_VSM_CLEARED_PUBLIC_' + elem['CORE'] + '_' + elem['PARTITION']
            definition2 = etree.SubElement(container2, 'DEFINITION-REF')
            definition2.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
            definition2.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet"
            sub_container2 = etree.SubElement(container2, 'SUB-CONTAINERS')

            container_value = etree.SubElement(sub_container2, 'ECUC-CONTAINER-VALUE')
            short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_16bits'
            definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
            definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
            definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
            parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".bss.public.' + elem['PARTITION'].lower() + '.' + elem['CORE'].lower() + '.VAR_16" aw 2'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '16'

            container_value = etree.SubElement(sub_container2, 'ECUC-CONTAINER-VALUE')
            short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_32bits'
            definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
            definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
            definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
            parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".bss.public.' + elem['PARTITION'].lower() + '.' + elem['CORE'].lower() + '.VAR_32" aw 4'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '32'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = 'UNSPECIFIED'

            container_value = etree.SubElement(sub_container2, 'ECUC-CONTAINER-VALUE')
            short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_8bits'
            definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
            definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
            definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
            parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".bss.public.' + elem['PARTITION'].lower() + '.' + elem['CORE'].lower() + '.VAR_8" aw 1'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '8'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = 'BOOLEAN'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = ''

            container3 = etree.SubElement(containers, 'ECUC-CONTAINER-VALUE')
            short_name_2 = etree.SubElement(container3, 'SHORT-NAME').text = 'MemMapAddressingMode_VSM_INIT_PUBLIC_' + elem['CORE'] + '_' + elem['PARTITION']
            definition3 = etree.SubElement(container3, 'DEFINITION-REF')
            definition3.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
            definition3.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet"
            sub_container3 = etree.SubElement(container3, 'SUB-CONTAINERS')

            container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
            short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_16bits'
            definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
            definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
            definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
            parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".data.public.' + elem['PARTITION'].lower() + '.' + elem['CORE'].lower() + '.VAR_16" aw 2'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '16'

            container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
            short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_32bits'
            definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
            definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
            definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
            parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".data.public.' + elem['PARTITION'].lower() + '.' + elem['CORE'].lower() + '.VAR_32" aw 4'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '32'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = 'UNSPECIFIED'

            container_value = etree.SubElement(sub_container3, 'ECUC-CONTAINER-VALUE')
            short_name_cv = etree.SubElement(container_value, 'SHORT-NAME').text = 'MemMapAddressingMode_8bits'
            definition_sc = etree.SubElement(container_value, 'DEFINITION-REF')
            definition_sc.attrib['DEST'] = "ECUC-PARAM-CONF-CONTAINER-DEF"
            definition_sc.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode"
            parameter_values = etree.SubElement(container_value, 'PARAMETER-VALUES')
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStart"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section ".data.public.' + elem['PARTITION'].lower() + '.' + elem['CORE'].lower() + '.VAR_8" aw 1'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-MULTILINE-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAddressingModeStop"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '#pragma section'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = '8'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = 'BOOLEAN'
            textual_param = etree.SubElement(parameter_values, 'ECUC-TEXTUAL-PARAM-VALUE')
            definition_tp = etree.SubElement(textual_param, 'DEFINITION-REF')
            definition_tp.attrib['DEST'] = "ECUC-STRING-PARAM-DEF"
            definition_tp.text = "/AUTOSAR/EcuDefs/MemMap/MemMapAddressingModeSet/MemMapAddressingMode/MemMapAlignmentSelector"
            value_tp = etree.SubElement(textual_param, 'VALUE').text = ''

        pretty_xml = prettify_xml(rootSystem)
        tree = etree.ElementTree(etree.fromstring(pretty_xml))
        #tree.write(output_path + "/MemMap.epc", encoding="UTF-8", xml_declaration=True, method="xml")
        tree.write(output_path + "/MemMap.epc", encoding="UTF-8", xml_declaration=True, method="xml", doctype="<!-- XML file generated by RTE_Configurator v1.0.1 -->")

    ###########################################
        if error_no != 0:
            print("There is at least one blocking error! Check the generated log.")
            print("\nMemory mapping creation script stopped with: " + str(info_no) + " infos, " + str(warning_no) + " warnings, " + str(error_no) + " errors\n")
            try:
                os.remove(output_path + '/MemMapSectionSpecificMapping.xml')
                os.remove(output_path + '/MemMap.epc')
            except OSError:
                pass
            sys.exit(1)
        else:
            print("\nMemory mapping creation script finished with: " + str(info_no) + " infos, " + str(warning_no) + " warnings, " + str(error_no) + " errors\n")
    except Exception as e:
        print("Unexpected error: " + str(e))
        print("\nMemory mapping creation script stopped with: " + str(info_no) + " infos, " + str(warning_no) + " warnings, " + str(error_no) + " errors\n")
        try:
            os.remove(output_path + '/MemMapSectionSpecificMapping.xml')
            os.remove(output_path + '/MemMap.epc')
        except OSError:
            pass
        sys.exit(1)








def unique_items(list_to_check):
    found = set()
    for item in list_to_check:
        if item['SWC'] not in found:
            yield item
            found.add(item['SWC'])


def remove_duplicates(list_to_be_checked):
    found = set()
    for item in list_to_be_checked:
        if item['INSTANCE'] not in found:
            yield item
            found.add(item['INSTANCE'])


def prettify_xml(elem):
    """Return a pretty-printed XML string for the Element."""
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="    ")


def check_if_xml_is_wellformed(file):
    parser = make_parser()
    parser.setContentHandler(ContentHandler())
    parser.parse(file)


if __name__ == "__main__":
    # cov = Coverage()
    # cov.start()
    # process = psutil.Process(os.getpid())
    # start_time = time.clock()
    main()
    # cov.stop()
    # cov.html_report(directory="coverage-html")
    # print(str(time.clock() - start_time) + " seconds")
    # print(str(process.memory_info()[0]/float(2**20)) + " MB")