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
    # parsing the command line arguments
    parser = argparse.ArgumentParser()
    arg_parse(parser)
    args = parser.parse_args()
    input_path = args.inp
    composition_name = ""
    if args.compo:
        composition_name = args.compo
    mem_map = False
    if args.MemMap:
        mem_map = True
    if mem_map:
        if composition_name == "":
            print("Composition name must be set if MemMap parameter is present")
            sys.exit(1)
    task_periodicity = args.app_task_periodicity
    if task_periodicity == '':
        task_periodicity = 0
    else:
        task_periodicity = int(task_periodicity)
    if args.default_duration == '':
        default_duration = None
    else:
        default_duration = int(args.default_duration)
    error = False
    path_list = []
    file_list = []
    entry_list = []
    for path in input_path:
        if path.startswith('@'):
            file = open(path[1:])
            line_file = file.readline()
            while line_file != "":
                line_file = line_file.rstrip()
                line_file = line_file.lstrip()
                if "#" not in line_file:
                    if os.path.isdir(line_file):
                        path_list.append(line_file)
                    elif os.path.isfile(line_file):
                        file_list.append(line_file)
                    else:
                        print("\nError defining the input path: " + line_file + "\n")
                        error = True
                    line_file = file.readline()
                else:
                    line_file = file.readline()
            file.close()
        else:
            if os.path.isdir(path):
                path_list.append(path)
            elif os.path.isfile(path):
                file_list.append(path)
            else:
                print("\nError defining the input path: " + path + "\n")
                error = True
    for path in path_list:
        for (dirpath, dirnames, filenames) in os.walk(path):
            for file in filenames:
                fullname = dirpath + '\\' + file
                file_list.append(fullname)
    [entry_list.append(elem) for elem in file_list if elem not in entry_list]
    if error:
        sys.exit(1)
    output_path = args.out
    output_script = args.out_script
    output_log = args.out_log
    if output_path:
        if not os.path.isdir(output_path):
            print("\nError defining the output path!\n")
            sys.exit(1)
        debugger = set_debugger(output_path)
        if output_log:
            if not os.path.isdir(output_log):
                print("\nError defining the output log path!\n")
                sys.exit(1)
            logger = set_logger(output_log)
            if mem_map:
                create_mapping(entry_list, composition_name, output_path, logger)
            create_list(entry_list, events, aswcs, output_path, task_periodicity, default_duration, logger, debugger)
            create_script(events, aswcs, output_path)
        else:
            logger = set_logger(output_path)
            if mem_map:
                create_mapping(entry_list, composition_name, output_path, logger)
            create_list(entry_list, events, aswcs, output_path, task_periodicity, default_duration, logger, debugger)
            create_script(events, aswcs, output_path)
    elif not output_path:
        if output_script:
            if not os.path.isdir(output_script):
                print("\nError defining the output configuration path!\n")
                sys.exit(1)
            debugger = set_debugger(output_script)
            if output_log:
                if not os.path.isdir(output_log):
                    print("\nError defining the output log path!\n")
                    sys.exit(1)
                logger = set_logger(output_log)
                if mem_map:
                    create_mapping(entry_list, composition_name, output_script, logger)
                create_list(entry_list, events, aswcs, output_script, task_periodicity, default_duration, logger, debugger)
                create_script(events, aswcs, output_script)
            else:
                logger = set_logger(output_script)
                if mem_map:
                    create_mapping(entry_list, composition_name, output_script, logger)
                create_list(entry_list, events, aswcs, output_script, task_periodicity, default_duration, logger, debugger)
                create_script(events, aswcs, output_script)
    else:
        print("\nNo output path defined!\n")
        sys.exit(1)


def findMin(slot_list, frequency):
    """
    :param slot_list: list of slots to be filled (given as a list of lists)
    :param frequency: the frequency of a given event
    :return: position in the list that corresponds to the element with the least events already mapped
    It takes the first <frequency> elements from the <slot_list> and return the position of the smallest length element
    """
    firstNSlots = slot_list[:frequency]
    pos = firstNSlots.index(min(firstNSlots, key=len))
    return pos


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


def arg_parse(parser):
    parser.add_argument('-in', '--inp', nargs='*', help="input path or file", required=True, default="")
    parser.add_argument('-out', '--out', help="output path", required=False, default="")
    parser.add_argument('-app_task_periodicity', '--app_task_periodicity', help="task periodicity (ms)", required=False, default="")
    parser.add_argument('-default_duration', '--default_duration', help="event default duration (µs)", required=False, default="")
    parser.add_argument('-out_script', '--out_script', help="output path for Scriptor script file(s)", required=False, default="")
    parser.add_argument('-out_log', '--out_log', help="output path for log file", required=False, default="")
    parser.add_argument('-MemMap', action="store_const", const="-MemMap", required=False, default="")
    parser.add_argument('-compo', '--compo', help="composition name", required=False, default="")


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
    hdlr = logging.FileHandler(path + '/debug_result.log')
    debugger.addHandler(hdlr)
    debugger.setLevel(logging.INFO)
    open(path + '/debug_result.log', 'w').close()
    return debugger


def create_list(files_list, events, aswcs, output_path, periodicity, default_duration, logger, debugger):
    events_rte = []
    events_aswc = []
    swc_allocation = []
    compos = []
    error_no = 0
    warning_no = 0
    info_no = 0
    if default_duration is None:
        event_duration = 1
    else:
        event_duration = default_duration
    try:
        for file in files_list:
            if file.endswith('.arxml'):
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
                    duration = None
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
        ###################################
        if error_no != 0:
            print("There is at least one blocking error! Check the generated log.")
            print("\nExecution stopped with: " + str(info_no) + " infos, " + str(warning_no) + " warnings, " + str(error_no) + " errors\n")
            try:
                os.remove(output_path + '/RTE_Config.xml')
            except OSError:
                pass
            sys.exit(1)

        for elem_rte in events_rte:
            for elem_aswc in events_aswc:
                if elem_rte['NAME'] == elem_aswc['NAME']:
                    elem_aswc['BEFORE-EVENT'] = elem_rte['BEFORE-EVENT']
                    elem_aswc['AFTER-EVENT'] = elem_rte['AFTER-EVENT']
                    elem_aswc['CATEGORY'] = elem_rte['CATEGORY']
                    elem_aswc['SPECIFIC-TASK'] = elem_rte['SPECIFIC-TASK']
                    if elem_rte['DURATION'] is not None:
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
            if elem_aswc['EVENT-TYPE'] == 'TIMING-EVENT':
                if float(elem_aswc['PERIOD']) > max_period:
                    max_period = float(elem_aswc['PERIOD'])
        max_period = max_period * 1000

        # TRS.RTECONFIG.FUNC.006
        for elem in events_aswc:
            if elem['ACTIVATION'] == "ON-ENTRY":
                for elem2 in events_aswc:
                    if elem['CORE'] == elem2['CORE'] and elem['PARTITION'] == elem2['PARTITION'] and elem['TYPE'] == elem2['TYPE'] and elem['ASWC'] == elem2['ASWC']:
                        if elem2['ACTIVATION'] == "ON-EXIT":
                            elem['AFTER-EVENT'].append(elem2['NAME'])

        g = Graph(len(events_aswc))
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
            if elem['BEFORE-EVENT']:
                i = events_aswc.index(elem)
                j = 0
                temp = elem['BEFORE-EVENT']
                for t in temp:
                    for element in events_aswc:
                        if element['NAME'] == t.split('/')[-1]:
                            j = events_aswc.index(element)
                    g.add_edge(i, j)
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
                        obj_event['ACTIVATION-OFFSET'] = None
                        obj_event['POSITION-IN-TASK'] = None
                        try:
                            if events_aswc[elem]['CORE'] == '':
                                logger.error('CORE not set for SWC-REF:' + events_aswc[elem]['ASWC'])
                                print('CORE not set for SWC-REF:' + events_aswc[elem]['ASWC'])
                                error_no = error_no + 1
                            elif events_aswc[elem]['PARTITION'] == '':
                                logger.error('PARTITION not set for SWC-REF:' + events_aswc[elem]['ASWC'])
                                print('PARTITION not set for SWC-REF:' + events_aswc[elem]['ASWC'])
                                error_no = error_no + 1
                            else:
                                if events_aswc[elem]['SPECIFIC-TASK'] is not None:
                                    obj_event['MAPPED-TO-TASK'] = events_aswc[elem]['SPECIFIC-TASK']
                                else:
                                    if events_aswc[elem]['CATEGORY'] == "DEFAULT":
                                        obj_event['MAPPED-TO-TASK'] = 'TaskApp_' + events_aswc[elem]['CORE'] + '_' + events_aswc[elem]['PARTITION'] + '_PER'
                                    elif events_aswc[elem]['CATEGORY'] == "PRIORITY_EVT":
                                        obj_event['MAPPED-TO-TASK'] = 'TaskApp_' + events_aswc[elem]['CORE'] + '_' + events_aswc[elem]['PARTITION'] + '_EVT'
                                    elif events_aswc[elem]['CATEGORY'] == "DIAG":
                                        obj_event['MAPPED-TO-TASK'] = 'TaskDiag_' + events_aswc[elem]['CORE'] + '_' + events_aswc[elem]['PARTITION'] + '_EVT'
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
                        events.append(obj_event)

            for event in events:
                if event['ACTIVATION'] == "ON-EXIT":
                    events.insert(0, events.pop(events.index(event)))
            reverse_events = list(reversed(events))
            for event in reverse_events:
                if event['ACTIVATION'] == "ON-ENTRY":
                    reverse_events.insert(0, reverse_events.pop(reverse_events.index(event)))
            events = list(reversed(reverse_events))
            events = sorted(events, key=lambda x: x['MAPPED-TO-TASK'])
            # setting the PositionInTask parameter
            tasks = []
            for elem in events:
                if elem['MAPPED-TO-TASK'] not in tasks:
                    tasks.append(elem['MAPPED-TO-TASK'])
            for task in tasks:
                count = 1
                for elem in events:
                    if elem['MAPPED-TO-TASK'] == task:
                        elem['POSITION-IN-TASK'] = count
                        count = count + 1
            # setting the RteActivationOffset parameter
            d = defaultdict(list)
            for item in events:
                d[item['MAPPED-TO-TASK']].append(item)
            for task in d:
                # dump data to debug file
                debugger.info("=============Event order: " + task + "===========")
                for event in d[task]:
                    debugger.info(str(event['POSITION-IN-TASK']) + ";" + str(event['EVENT']))
                debugger.info("")

                timing_events = []
                # search and add only TIMING-EVENTS
                for event in d[task]:
                    if event['TYPE'] == 'TIMING-EVENT':
                        if event['SPECIFIC-TASK'] is None and event['CATEGORY'] == 'DEFAULT':
                            obj_event = {}
                            obj_event['NAME'] = event['EVENT']
                            obj_event['DURATION'] = event['DURATION']
                            obj_event['PERIOD'] = event['PERIOD']
                            obj_event['AFTER'] = event['AFTER-EVENT']
                            obj_event['BEFORE'] = event['BEFORE-EVENT']
                            obj_event['COMPUTED'] = False
                            obj_event['OFFSET'] = None
                            timing_events.append(obj_event)
                # compute max period of the timing events and transform it from s in ms
                # compute min task peridicity to use in case of periodicity command line argument not defined
                max_period = 0
                task_periodicity = 1
                for elem in timing_events:
                    if float(elem['PERIOD']) > max_period:
                        max_period = float(elem['PERIOD'])
                    if float(elem['PERIOD']) < task_periodicity:
                        task_periodicity = float(elem['PERIOD'])
                max_period = max_period * 1000
                if periodicity == 0:
                    task_periodicity = task_periodicity * 1000
                else:
                    task_periodicity = periodicity
                number_of_slots = max_period/task_periodicity
                slots = [[] for i in range(int(number_of_slots))]
                dprim = defaultdict(list)
                for te in timing_events:
                    dprim[te['PERIOD']].append(te)
                dprim = sorted(dprim.items())
                # for each period time, insert the event on the slot
                for period in dprim:
                    if periodicity == 0:
                        slot_frequency = int((max_period/1000)/float(period[0]))
                    else:
                        slot_frequency = int((float(period[0]) * 1000) / task_periodicity)
                    if slot_frequency < 1:
                        logger.error('Periodicity('+str(periodicity)+'ms) too small for event ' + period[1][0]['NAME'] + ' with period ' + str(float(period[0])*1000) + 'ms')
                        print('Periodicity('+str(periodicity)+'ms) too small for event ' + period[1][0]['NAME'] + ' with period ' + str(float(period[0])*1000) + 'ms')
                        sys.exit(1)
                    event_list = move_to_front(period[1])
                    for event in event_list:
                        if event['COMPUTED'] is not True:
                            pos = findMin(slots, slot_frequency)
                            slots = insertElement(slots, pos, slot_frequency, event)
                            event['COMPUTED'] = True
                            if event['AFTER']:
                                for event_constr in event['AFTER']:
                                    for event_tbd in event_list:
                                        if event_tbd['NAME'] == event_constr.split('/')[-1]:
                                            slots = insertElement(slots, pos, slot_frequency, event_tbd)
                                            event_tbd['COMPUTED'] = True
                            if event['BEFORE']:
                                for event_constr in event['BEFORE']:
                                    for event_tbd in event_list:
                                        if event_tbd['NAME'] == event_constr.split('/')[-1]:
                                            slots = insertElement(slots, pos, slot_frequency, event_tbd)
                                            event_tbd['COMPUTED'] = True
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
                            if elem['EVENT'] in slot:
                                elem['ACTIVATION-OFFSET'] = iterator * task_periodicity / 1000
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
                        aswcs.append(objElem)
        # dump data to debug file
        debugger.info("=============Event detail===========")
        debugger.info("Event;Period;Offset;Duration;Task")
        for event in events:
            debugger.info(str(event['EVENT']) + ";" + str(event['PERIOD']) + ";" + str(event['ACTIVATION-OFFSET']) + ";" + str(event['DURATION']) + ";" + str(event['MAPPED-TO-TASK']))

        #################################
        if error_no != 0:
            print("There is at least one blocking error! Check the generated log.")
            print("\nRTE configuration script stopped with: " + str(info_no) + " infos, " + str(warning_no) + " warnings, " + str(error_no) + " errors\n")
            try:
                os.remove(output_path + '/RTE_Config.xml')
            except OSError:
                pass
            sys.exit(1)
        else:
            print("\nRTE configuration script finished with: " + str(info_no) + " infos, " + str(warning_no) + " warnings, " + str(error_no) + " errors\n")
    except Exception as e:
        print("Unexpected error: " + str(e))
        print("\nRTE configuration script stopped with: " + str(info_no) + " infos, " + str(warning_no) + " warnings, " + str(error_no) + " errors\n")
        try:
            os.remove(output_path + '/RTE_Config.xml')
        except OSError:
            pass
        sys.exit(1)


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
            expression_element = ET.SubElement(operation_element, "Expression").text = 'num:i(' + str(event['ACTIVATION-OFFSET']) + ')'
        else:
            operations_activation = ET.SubElement(operation_offset, "Operations")
            operation_element = ET.SubElement(operations_activation, "Operation")
            operation_element.set('Type', "SetEnabled")
            expression_element = ET.SubElement(operation_element, "Expression").text = 'boolean(0)'

    pretty_xml = prettify_xml(root_script)
    tree = ET.ElementTree(ET.fromstring(pretty_xml))
    tree.write(output_path + "/RTE_Config.xml", encoding="UTF-8", xml_declaration=True, method="xml")


def create_mapping(files_list, composition, output_path, logger):
    NSMAP = {None: 'http://autosar.org/schema/r4.0',
             "xsi": 'http://www.w3.org/2001/XMLSchema-instance'}
    attr_qname = etree.QName("http://www.w3.org/2001/XMLSchema-instance", "schemaLocation")
    info_no = 0
    warning_no = 0
    error_no = 0
    compositions = []
    behaviors = []
    memory_mappings = []
    swc_allocation = []
    data_elements = []
    try:
        for file in files_list:
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
                components = root.findall(".//{http://autosar.org/schema/r4.0}SW-COMPONENT-PROTOTYPE")
                for component in components:
                    obj_component = {}
                    obj_component['INSTANCE'] = component.find(".//{http://autosar.org/schema/r4.0}SHORT-NAME").text
                    obj_component['SWC'] = component.find(".//{http://autosar.org/schema/r4.0}TYPE-TREF").text
                    obj_component['COMPONENT'] = component.getparent().getparent().getchildren()[0].text
                    obj_component['ROOT'] = component.getparent().getparent().getparent().getparent().getchildren()[0].text
                    obj_component['DELETE'] = False
                    compositions.append(obj_component)
                ibs = root.findall(".//{http://autosar.org/schema/r4.0}SWC-INTERNAL-BEHAVIOR")
                for ib in ibs:
                    obj_behavior = {}
                    obj_behavior['NAME'] = ib.find(".//{http://autosar.org/schema/r4.0}SHORT-NAME").text
                    obj_behavior['ASWC'] = ib.getparent().getparent().getchildren()[0].text
                    obj_behavior['ROOT'] = ib.getparent().getparent().getparent().getparent().getchildren()[0].text
                    behaviors.append(obj_behavior)
            if file.endswith('.xml'):
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
                swc = root.findall(".//SWC-ALLOCATION")
                for element in swc:
                    obj_event = {}
                    obj_event['SWC'] = element.find('SWC-REF').text
                    obj_event['CORE'] = element.find('CORE').text
                    obj_event['PARTITION'] = element.find('PARTITION').text
                    swc_allocation.append(obj_event)
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
                    data_elements.append(obj_elem)
        # add internal behavior to the element list:
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
        tree.write(output_path + "/MemMapSectionSpecificMapping.xml", encoding="UTF-8", xml_declaration=True, method="xml")
    ###########################################
        if error_no != 0:
            print("There is at least one blocking error! Check the generated log.")
            print("\nMemory mapping creation script stopped with: " + str(info_no) + " infos, " + str(warning_no) + " warnings, " + str(error_no) + " errors\n")
            try:
                os.remove(output_path + '/MemMapSectionSpecificMapping.xml')
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
