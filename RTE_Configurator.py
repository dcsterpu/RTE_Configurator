import argparse
import logging
import os
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from decimal import Decimal
from xml.dom import minidom
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

from lxml import etree


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
        if output_log:
            if not os.path.isdir(output_log):
                print("\nError defining the output log path!\n")
                sys.exit(1)
            logger = set_logger(output_log)
            create_list(entry_list, events, aswcs, output_path, logger)
            create_script(events, aswcs, output_path)
        else:
            logger = set_logger(output_path)
            create_list(entry_list, events, aswcs, output_path, logger)
            create_script(events, aswcs, output_path)
    elif not output_path:
        if output_script:
            if not os.path.isdir(output_script):
                print("\nError defining the output configuration path!\n")
                sys.exit(1)
            if output_log:
                if not os.path.isdir(output_log):
                    print("\nError defining the output log path!\n")
                    sys.exit(1)
                logger = set_logger(output_log)
                create_list(entry_list, events, aswcs, output_script, logger)
                create_script(events, aswcs, output_script)
            else:
                logger = set_logger(output_script)
                create_list(entry_list, events, aswcs, output_script, logger)
                create_script(events, aswcs, output_script)
    else:
        print("\nNo output path defined!\n")
        sys.exit(1)


def arg_parse(parser):
    parser.add_argument('-in', '--inp', nargs='*', help="input path or file", required=True, default="")
    parser.add_argument('-out', '--out', help="output path", required=False, default="")
    parser.add_argument('-out_script', '--out_script', help="output path for Scriptor script file(s)", required=False, default="")
    parser.add_argument('-out_log', '--out_log', help="output path for log file", required=False, default="")


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


def create_list(files_list, events, aswcs, output_path, logger):
    events_rte = []
    events_aswc = []
    swc_allocation = []
    compos = []
    error_no = 0
    warning_no = 0
    info_no = 0
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
                tree = etree.parse(file)
                root = tree.getroot()
                ascre_event = root.findall(".//{http://autosar.org/schema/r4.0}ASYNCHRONOUS-SERVER-CALL-RETURNS-EVENT")
                for elem in ascre_event:
                    obj_event = {}
                    obj_event['NAME'] = elem.find('{http://autosar.org/schema/r4.0}SHORT-NAME').text
                    obj_event['EVENT-TYPE'] = elem.tag.split('}')[-1]
                    obj_event['TYPE'] = "EVT"
                    obj_event['START-ON-EVENT'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                    obj_event['DURATION'] = "0.01"
                    obj_event['BEFORE-EVENT'] = []
                    obj_event['AFTER-EVENT'] = []
                    obj_event['REF'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                    obj_event['CONTAIN-IMPLICIT-ACCESS'] = ""
                    obj_event['UNMAPPED'] = ""
                    obj_event['CORE'] = ""
                    obj_event['PARTITION'] = ""
                    obj_event['EVENTS-CALLED'] = None
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
                    obj_event['DURATION'] = "0.01"
                    obj_event['BEFORE-EVENT'] = []
                    obj_event['AFTER-EVENT'] = []
                    obj_event['REF'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                    obj_event['CONTAIN-IMPLICIT-ACCESS'] = ""
                    obj_event['UNMAPPED'] = ""
                    obj_event['CORE'] = ""
                    obj_event['PARTITION'] = ""
                    obj_event['EVENTS-CALLED'] = None
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
                    obj_event['DURATION'] = "0.01"
                    obj_event['BEFORE-EVENT'] = []
                    obj_event['AFTER-EVENT'] = []
                    obj_event['REF'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                    obj_event['CONTAIN-IMPLICIT-ACCESS'] = ""
                    obj_event['UNMAPPED'] = ""
                    obj_event['CORE'] = ""
                    obj_event['PARTITION'] = ""
                    obj_event['EVENTS-CALLED'] = None
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
                    obj_event['DURATION'] = "0.01"
                    obj_event['BEFORE-EVENT'] = []
                    obj_event['AFTER-EVENT'] = []
                    obj_event['REF'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                    obj_event['CONTAIN-IMPLICIT-ACCESS'] = ""
                    obj_event['UNMAPPED'] = ""
                    obj_event['CORE'] = ""
                    obj_event['PARTITION'] = ""
                    obj_event['EVENTS-CALLED'] = None
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
                    obj_event['DURATION'] = "0.01"
                    obj_event['BEFORE-EVENT'] = []
                    obj_event['AFTER-EVENT'] = []
                    obj_event['REF'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                    obj_event['CONTAIN-IMPLICIT-ACCESS'] = ""
                    obj_event['UNMAPPED'] = ""
                    obj_event['CORE'] = ""
                    obj_event['PARTITION'] = ""
                    obj_event['EVENTS-CALLED'] = None
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
                    obj_event['DURATION'] = "0.01"
                    obj_event['BEFORE-EVENT'] = []
                    obj_event['AFTER-EVENT'] = []
                    obj_event['REF'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                    obj_event['CONTAIN-IMPLICIT-ACCESS'] = ""
                    obj_event['UNMAPPED'] = ""
                    obj_event['CORE'] = ""
                    obj_event['PARTITION'] = ""
                    obj_event['EVENTS-CALLED'] = None
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
                    obj_event['DURATION'] = "0.01"
                    obj_event['BEFORE-EVENT'] = []
                    obj_event['AFTER-EVENT'] = []
                    obj_event['REF'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                    obj_event['CONTAIN-IMPLICIT-ACCESS'] = ""
                    obj_event['UNMAPPED'] = ""
                    obj_event['CORE'] = ""
                    obj_event['PARTITION'] = ""
                    obj_event['EVENTS-CALLED'] = None
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
                    obj_event['DURATION'] = "0.01"
                    obj_event['BEFORE-EVENT'] = []
                    obj_event['AFTER-EVENT'] = []
                    obj_event['REF'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                    obj_event['CONTAIN-IMPLICIT-ACCESS'] = ""
                    obj_event['UNMAPPED'] = ""
                    obj_event['CORE'] = ""
                    obj_event['PARTITION'] = ""
                    obj_event['EVENTS-CALLED'] = None
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
                    obj_event['DURATION'] = "0.01"
                    obj_event['BEFORE-EVENT'] = []
                    obj_event['AFTER-EVENT'] = []
                    obj_event['REF'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                    obj_event['CONTAIN-IMPLICIT-ACCESS'] = ""
                    obj_event['UNMAPPED'] = ""
                    obj_event['CORE'] = ""
                    obj_event['PARTITION'] = ""
                    obj_event['EVENTS-CALLED'] = None
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
                    obj_event['DURATION'] = "0.01"
                    obj_event['BEFORE-EVENT'] = []
                    obj_event['AFTER-EVENT'] = []
                    obj_event['REF'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                    obj_event['CONTAIN-IMPLICIT-ACCESS'] = ""
                    obj_event['UNMAPPED'] = ""
                    obj_event['CORE'] = ""
                    obj_event['PARTITION'] = ""
                    obj_event['EVENTS-CALLED'] = None
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
                    obj_event['DURATION'] = "0.01"
                    obj_event['BEFORE-EVENT'] = []
                    obj_event['AFTER-EVENT'] = []
                    obj_event['REF'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                    obj_event['CONTAIN-IMPLICIT-ACCESS'] = ""
                    obj_event['UNMAPPED'] = ""
                    obj_event['CORE'] = ""
                    obj_event['PARTITION'] = ""
                    obj_event['EVENTS-CALLED'] = None
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
                    obj_event['DURATION'] = "0.01"
                    obj_event['BEFORE-EVENT'] = []
                    obj_event['AFTER-EVENT'] = []
                    obj_event['REF'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                    obj_event['CONTAIN-IMPLICIT-ACCESS'] = ""
                    obj_event['UNMAPPED'] = ""
                    obj_event['CORE'] = ""
                    obj_event['PARTITION'] = ""
                    obj_event['EVENTS-CALLED'] = None
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
                    obj_event['DURATION'] = "0.01"
                    obj_event['BEFORE-EVENT'] = []
                    obj_event['AFTER-EVENT'] = []
                    obj_event['REF'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                    obj_event['CONTAIN-IMPLICIT-ACCESS'] = ""
                    obj_event['UNMAPPED'] = ""
                    obj_event['CORE'] = ""
                    obj_event['PARTITION'] = ""
                    obj_event['EVENTS-CALLED'] = None
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
                    obj_event['DURATION'] = "0.01"
                    obj_event['BEFORE-EVENT'] = []
                    obj_event['AFTER-EVENT'] = []
                    obj_event['REF'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                    obj_event['CONTAIN-IMPLICIT-ACCESS'] = ""
                    obj_event['UNMAPPED'] = ""
                    obj_event['CORE'] = ""
                    obj_event['PARTITION'] = ""
                    obj_event['EVENTS-CALLED'] = None
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
                    obj_event['DURATION'] = "0.01"
                    obj_event['BEFORE-EVENT'] = []
                    obj_event['AFTER-EVENT'] = []
                    obj_event['REF'] = elem.find('{http://autosar.org/schema/r4.0}START-ON-EVENT-REF').text
                    obj_event['CONTAIN-IMPLICIT-ACCESS'] = ""
                    obj_event['UNMAPPED'] = ""
                    obj_event['CORE'] = ""
                    obj_event['PARTITION'] = ""
                    obj_event['EVENTS-CALLED'] = None
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
                tree = etree.parse(file)
                root = tree.getroot()
                event = root.findall(".//EVENT")
                for element in event:
                    obj_event = {}
                    after_list = []
                    before_list = []
                    duration = None
                    cia = None
                    unmap = None
                    name = None
                    event_called = []
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
                        if child.tag == 'CONTAIN-IMPLICIT-ACCESS':
                            cia = child.text
                        if child.tag == 'UNMAPPED':
                            unmap = child.text
                        if child.tag == 'EVENTS-CALLED':
                            list_of_events = child.findall('.//EVENT-REF')
                            for elem in list_of_events:
                                event_called.append(elem.text)
                            # event_called = child.text
                    obj_event['NAME'] = name
                    obj_event['DURATION'] = duration
                    obj_event['CIA'] = cia
                    obj_event['UNMAP'] = unmap
                    obj_event['EVENT-CALLED'] = event_called
                    obj_event['AFTER-EVENT'] = after_list
                    obj_event['BEFORE-EVENT'] = before_list
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
                    elem_aswc['CONTAIN-IMPLICIT-ACCESS'] = elem_rte['CIA']
                    elem_aswc['UNMAPPED'] = elem_rte['UNMAP']
                    elem_aswc['EVENTS-CALLED'] = elem_rte['EVENT-CALLED']
                    if elem_rte['DURATION'] is not None:
                        elem_aswc['DURATION'] = elem_rte['DURATION']
        for elem_swc in swc_allocation:
            for elem_aswc in events_aswc:
                if "/"+elem_aswc['ROOT'] + "/" + elem_aswc['ASWC'] in elem_swc['SWC']:
                    elem_aswc['CORE'] = elem_swc['CORE']
                    elem_aswc['PARTITION'] = elem_swc['PARTITION']

        # implement TRS.RTECONFIG.CHECK.003
        for elem in events_aswc:
            if elem['EVENTS-CALLED']:
                for element in elem['EVENTS-CALLED']:
                    temp = element.split('/')
                    for elem2 in events_aswc:
                        if elem2['NAME'] == temp[-1]:
                            if elem2['EVENTS-CALLED']:
                                logger.error('Event ' + elem2['NAME'] + " has an EVENTS-CALLED reference, and is referenced in EVENTS-CALLED of event: "+elem['NAME'])
                                print('Event ' + elem2['NAME'] + " has an EVENTS-CALLED reference, and is referenced in EVENTS-CALLED of event: "+elem['NAME'])
                                error_no = error_no + 1
        # all the events of type <OPERATION-INVOKED-EVENT> which belongs to ASWC IoHwAb  or ASWC Aswc_IntDcm mult not be mapped
        for elem in events_aswc[:]:
            if elem['EVENT-TYPE'] == "OPERATION-INVOKED-EVENT":
                if elem['ASWC'] == "IoHwAb" or elem['ASWC'] == "Aswc_IntDcm":
                    events_aswc.remove(elem)
                    # print(elem['NAME'])

        # TRS.RTECONFIG.GEN.003
        # for index1 in events_aswc[:]:
        #     value = True
        #     for index2 in events_aswc[:]:
        #         if index1 != index2:
        #             if index1['CONTAIN-IMPLICIT-ACCESS'] == "true" or index1['CONTAIN-IMPLICIT-ACCESS'] == "1":
        #                 pass
        #             else:
        #                 if index1["EVENTS-CALLED"]:
        #                     for element in index1["EVENTS-CALLED"]:
        #                         if element.split('/')[-1] == index2['NAME']:
        #                             if index1['CORE'] == index2['CORE'] and index1['PARTITION'] == index2['PARTITION']:
        #                                 #if index1['UNMAPPED'] == '1' or index1['UNMAPPED'] == 'true':
        #                                 value = False
        #                                 break
        #     if not value:
        #         events_aswc.remove(index1)
        for index1 in events_aswc[:]:
            if index1['EVENT-TYPE'] == "OPERATION-INVOKED-EVENT":
                map_elem = False
                if index1['CONTAIN-IMPLICIT-ACCESS'] == "true" or index1['CONTAIN-IMPLICIT-ACCESS'] == "1" or index1['CONTAIN-IMPLICIT-ACCESS'] == "True":
                    map_elem = True
                else:
                    if index1['EVENTS-CALLED']:
                        for element in index1['EVENTS-CALLED']:
                            for index2 in events_aswc[:]:
                                if index1 != index2:
                                    if element.split('/')[-1] == index2['NAME']:
                                        if index1['PARTITION'] != index2['PARTITION'] or index1['CORE'] != index2['CORE']:
                                            map_elem = True
                if not map_elem:
                    events_aswc.remove(index1)

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
                            # old way, according to the requirement in spec
                            #         if events_aswc[elem]['TYPE'] == 'PER':
                            #             obj_event['MAPPED-TO-TASK'] = 'TaskApp_' + events_aswc[elem]['CORE'] + '_' + events_aswc[elem]['PARTITION'] + '_PER'
                            #         else:
                            #             if events_aswc[elem]['EVENTS-CALLED']:
                            #                 for element in events_aswc[elem]['EVENTS-CALLED']:
                            #                     if not element.isspace():
                            #                         obj_event['MAPPED-TO-TASK'] = 'TaskApp_' + events_aswc[elem]['CORE'] + '_' + events_aswc[elem]['PARTITION'] + '_PER'
                            #             elif events_aswc[elem]['START-ON-EVENT']:
                            #                 found = False
                            #                 for index2 in range(len(events_aswc)):
                            #                     if elem != index2:
                            #                         if events_aswc[elem]['START-ON-EVENT'] == events_aswc[index2]['START-ON-EVENT']:
                            #                             obj_event['MAPPED-TO-TASK'] = 'TaskApp_' + events_aswc[index2]['CORE'] + '_' + events_aswc[index2]['PARTITION'] + '_' + events_aswc[index2]['TYPE']
                            #                             found = True
                            #                 if not found:
                            #                     obj_event['MAPPED-TO-TASK'] = 'TaskApp_' + events_aswc[elem]['CORE'] + '_' + events_aswc[elem]['PARTITION'] + '_EVT'
                            #             else:
                            #                 obj_event['MAPPED-TO-TASK'] = 'TaskApp_' + events_aswc[elem]['CORE'] + '_' + events_aswc[elem]['PARTITION'] + '_EVT'
                            # new way: all event are PER, except OPERATION-INVOKED-EVENT, which are EVT
                                if events_aswc[elem]['EVENT-TYPE'] == "OPERATION-INVOKED-EVENT":
                                    obj_event['MAPPED-TO-TASK'] = 'TaskApp_' + events_aswc[elem]['CORE'] + '_' + events_aswc[elem]['PARTITION'] + '_EVT'
                                else:
                                    obj_event['MAPPED-TO-TASK'] = 'TaskApp_' + events_aswc[elem]['CORE'] + '_' + events_aswc[elem]['PARTITION'] + '_PER'
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
            offset = 0
            for elem in events:
                elem['ACTIVATION-OFFSET'] = offset
                offset = offset + float(Decimal(elem['DURATION']))
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
        #################################
        if error_no != 0:
            print("There is at least one blocking error! Check the generated log.")
            print("\nExecution stopped with: " + str(info_no) + " infos, " + str(warning_no) + " warnings, " + str(error_no) + " errors\n")
            try:
                os.remove(output_path + '/RTE_Config.xml')
            except OSError:
                pass
            sys.exit(1)
        else:
            print("\nExecution finished with: " + str(info_no) + " infos, " + str(warning_no) + " warnings, " + str(error_no) + " errors\n")
    except Exception as e:
        print("Unexpected error: " + str(e))
        print("\nExecution stopped with: " + str(info_no) + " infos, " + str(warning_no) + " warnings, " + str(error_no) + " errors\n")
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
        operations_activation = ET.SubElement(operation_offset, "Operations")
        operation_element = ET.SubElement(operations_activation, "Operation")
        operation_element.set('Type', "SetEnabled")
        expression_element = ET.SubElement(operation_element, "Expression").text = 'boolean(0)'

    pretty_xml = prettify_xml(root_script)
    tree = ET.ElementTree(ET.fromstring(pretty_xml))
    tree.write(output_path + "/RTE_Config.xml", encoding="UTF-8", xml_declaration=True, method="xml")


def unique_items(list_to_check):
    found = set()
    for item in list_to_check:
        if item['SWC'] not in found:
            yield item
            found.add(item['SWC'])


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
