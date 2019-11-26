import ntpath
import os
import os.path
import unittest

from lxml import etree


class FileCompare():
    def areSame(first_location, second_location):
        file1 = open(first_location)
        file2 = open(second_location)

        line_file1 = file1.readline()
        line_file2 = file2.readline()

        while line_file1 != "" or line_file2 != "":
            line_file1 = line_file1.rstrip()
            line_file1 = line_file1.lstrip()
            line_file2 = line_file2.rstrip()
            line_file2 = line_file2.lstrip()
            if line_file1 != line_file2:
                file1.close()
                file2.close()
                return False
            line_file1 = file1.readline()
            line_file2 = file2.readline()

        file1.close()
        file2.close()
        return True

    def matchLine(path, line_number, text):
        """
        path = used for defining the file to be checked
        line_number = used to identify the line that will be checked
        text = string containing the text to match
        """
        datafile = open(path)
        line_file = datafile.readline()
        line_file = line_file.rstrip()
        line_no = 1
        while line_file != "":
            if line_no == line_number:
                if line_file == text:
                    datafile.close()
                    return True
                else:
                    datafile.close()
                    return False
            line_no = line_no + 1
            line_file = datafile.readline()
            line_file = line_file.rstrip()

    def checkLog(path, level, message):
        """
        path = used for defining the file to be checked
        level = event name or criticity level :INFO, WARNING, ERROR
        message = string to be matched
        """
        datafile = open(path)
        line_file = datafile.readline()
        bool_message = []
        for elem in message:
            for elem2 in level:
                bool_message.append(False)
        i = 0
        while line_file != "":
            for text in message:
                for lvl in level:
                    if lvl in line_file:
                        if text in line_file:
                            # print(line_file)
                            bool_message[i] = True
                            i = i + 1
            line_file = datafile.readline()
        for elem in bool_message:
            if elem == False:
                datafile.close()
                return False
        datafile.close()
        return True

    def checkError(path, level, message):
        """
        path = used for defining the file to be checked
        level = criticity level :INFO, WARNING, ERROR
        message = string to be matched
        """
        datafile = open(path)
        line_file = datafile.readline()
        while line_file != "":
            for text in message:
                if level in line_file:
                    if text in line_file:
                        # print(line_file)
                        datafile.close()
                        return True
            line_file = datafile.readline()
        datafile.close()
        return False

    def checkParsing(path1, path2, extension, message):
        """
        path1 = used for taking the .arxml files name
        path2 = used for defining the file to be checked
        message = string to be matched
        extension = file extension
        """
        all_files = []
        for path, dirs, file in os.walk(path1):
            for f in file:
                if f.endswith(extension):
                    all_files.append(f)
        datafile = open(path2)
        line_file = datafile.readline()
        i = 0
        while line_file != "" and all_files:
            for files in all_files:
                if files + " " + message in line_file:
                    all_files.remove(files)
                    i = i + 1
            line_file = datafile.readline()
        if not all_files:
            datafile.close()
            return True
        else:
            datafile.close()
            return False

    def scriptParam(path1, path2, eventname, parameter, cicle):
        """
        path1 = used for defining the file from where to obtain CORE and PARTITION
        path2 = used for defining the file to be checked
        eventname = event short-name (ex: RUNA_GererAutomonieConso_Cyclic) or SWC short_name (ex: Instance_ASWC_A26)
        parameter = parameter name (ex: RteEventToTaskMapping)
        """
        swc_list = []

        tree1 = etree.parse(path1)
        root1 = tree1.getroot()
        swc = root1.findall("SWC-ALLOCATION")
        for elem in swc:
            obj_elem = {}
            obj_elem['ASWC'] = elem.find('.//SWC-REF').text
            obj_elem['CORE'] = elem.find('.//CORE').text
            obj_elem['PARTITION'] = elem.find('.//PARTITION').text
            swc_list.append(obj_elem)

        tree2 = etree.parse(path2)
        root2 = tree2.getroot()
        op = root2.find("Operations")
        for elem2 in op:
            if parameter in elem2.getchildren()[0].text and eventname in elem2.getchildren()[0].text:
                if elem2.getchildren()[1].getchildren()[1].getchildren()[0].tag == "Expression":
                    for elem_dict in swc_list:
                        if elem_dict['ASWC'] in elem2.getchildren()[0].text:
                            if elem_dict['CORE'] in elem2.getchildren()[1].getchildren()[1].getchildren()[0].text and \
                                    elem_dict['PARTITION'] in elem2.getchildren()[1].getchildren()[1].getchildren()[
                                0].text and cicle in elem2.getchildren()[1].getchildren()[1].getchildren()[0].text:
                                return True
        return False

    def scriptParamNew(path1, path2, eventname, parameter, cicle):
        """
        path1 = used for defining the file from where to obtain CORE and PARTITION
        path2 = used for defining the file to be checked
        eventname = event short-name (ex: RUNA_GererAutomonieConso_Cyclic) or SWC short_name (ex: Instance_ASWC_A26)
        parameter = parameter name (ex: RteEventToTaskMapping)
        """
        swc_list = []

        tree1 = etree.parse(path1)
        root1 = tree1.getroot()
        swc = root1.findall("SWC-ALLOCATION")
        for elem in swc:
            obj_elem = {}
            obj_elem['ASWC'] = elem.find('.//SWC-REF').text
            obj_elem['CORE'] = elem.find('.//CORE').text
            obj_elem['PARTITION'] = elem.find('.//PARTITION').text
            swc_list.append(obj_elem)

        tree2 = etree.parse(path2)
        root2 = tree2.getroot()
        op = root2.findall(".//ECUC-CONTAINER-VALUE")
        for elem2 in op:
            if elem2.getparent().tag == 'SUB-CONTAINERS':
                if elem2.getchildren()[0].text == eventname:
                    temps = elem2.findall(".//ECUC-REFERENCE-VALUE")
                    for temp in temps:
                        if parameter in temp.getchildren()[0].text:
                            for elem_dict in swc_list:
                                if elem_dict['CORE'] in temp.getchildren()[1].text and \
                                        elem_dict['PARTITION'] in temp.getchildren()[1].text and cicle in temp.getchildren()[1].text:
                                    return True

        return False

    def setParam(path1, path2, eventname, parameter):
        """
        path1 = used for defining the file from where to obtain CORE and PARTITION
        path2 = used for defining the file to be checked
        eventname = event short-name (ex: RUNA_GererAutomonieConso_Cyclic) or SWC short_name (ex: Instance_ASWC_A26)
        parameter = parameter name (ex: RteEventToTaskMapping)
        """
        swc_list = []

        tree1 = etree.parse(path1)
        root1 = tree1.getroot()
        swc = root1.findall("SWC-ALLOCATION")
        for elem in swc:
            obj_elem = {}
            obj_elem['CORE'] = elem.find('.//CORE').text
            obj_elem['PARTITION'] = elem.find('.//PARTITION').text
            swc_list.append(obj_elem)

        tree2 = etree.parse(path2)
        root2 = tree2.getroot()
        op = root2.find("Operations")
        for elem2 in op:
            if parameter in elem2.getchildren()[0].text and eventname in elem2.getchildren()[0].text:
                if elem2.getchildren()[1].getchildren()[1].getchildren()[0].tag == "Expression":
                    for elem_dict in swc_list:
                        if elem_dict['CORE'] in elem2.getchildren()[1].getchildren()[1].getchildren()[0].text and \
                                elem_dict['PARTITION'] in elem2.getchildren()[1].getchildren()[1].getchildren()[0].text:
                            return True
        return False

    def setParamNew(path1, path2, eventname, parameter):
        """
        path1 = used for defining the file from where to obtain CORE and PARTITION
        path2 = used for defining the file to be checked
        eventname = event short-name (ex: RUNA_GererAutomonieConso_Cyclic) or SWC short_name (ex: Instance_ASWC_A26)
        parameter = parameter name (ex: RteEventToTaskMapping)
        """
        swc_list = []

        tree1 = etree.parse(path1)
        root1 = tree1.getroot()
        swc = root1.findall("SWC-ALLOCATION")
        for elem in swc:
            obj_elem = {}
            obj_elem['CORE'] = elem.find('.//CORE').text
            obj_elem['PARTITION'] = elem.find('.//PARTITION').text
            swc_list.append(obj_elem)

        tree2 = etree.parse(path2)
        root2 = tree2.getroot()
        op = root2.findall(".//ECUC-CONTAINER-VALUE")
        for elem2 in op:
            if elem2.getparent().tag == 'CONTAINERS':
                if elem2.getchildren()[0].text == eventname:
                    temps = elem2.findall(".//ECUC-REFERENCE-VALUE")
                    for temp in temps:
                        if parameter in temp.getchildren()[0].text:
                            for elem_dict in swc_list:
                                if elem_dict['CORE'] in temp.getchildren()[1].text and \
                                        elem_dict['PARTITION'] in temp.getchildren()[1].text:
                                    return True
        return False

    def checkRteActivation(path1, path2, value):
        """
        path1 = used for defining the file from where to obtain events short-names
        path2 = used for defining the file to be checked
        value = used for defining the value of "Expression"
        """
        swc_list = []
        tree1 = etree.parse(path1)
        root1 = tree1.getroot()
        swc = root1.findall("EVENT")
        for elem in swc:
            short_name = elem.find('.//SHORT-NAME').text
            swc_list.append(short_name)

        tree2 = etree.parse(path2)
        root2 = tree2.getroot()
        op = root2.find("Operations")
        for elem2 in op:
            for name in swc_list:
                if name in elem2.getchildren()[0].text and "RteActivationOffset" in elem2.getchildren()[0].text:
                    if elem2.getchildren()[1].getchildren()[0].getchildren()[0].tag == "Expression":
                        if value in elem2.getchildren()[1].getchildren()[0].getchildren()[0].text:
                            return True
        return False

    def eventOrder(path, path1, eventposition, possible_order):
        """
        path = used for defining the file from where to obtain events name
        path2 = used for defining the file to be checked
        eventposition = a list of events positions
        """
        event_name = []
        tree = etree.parse(path)
        root = tree.getroot()
        swc = root.findall("EVENT")
        for elem in swc:
            short_name = elem.find('.//SHORT-NAME').text
            event_name.append(short_name)

        event_position = []
        position_list = []
        tree1 = etree.parse(path1)
        root1 = tree1.getroot()
        op = root1.find("Operations")
        for elem2 in op:
            for name in event_name:
                if name in elem2.getchildren()[0].text and "RtePositionInTask" in elem2.getchildren()[0].text:
                    event_position.append(name)
            for pos in event_position:
                if pos in elem2.getchildren()[0].text and "RtePositionInTask" in elem2.getchildren()[0].text:
                    if elem2.getchildren()[1].getchildren()[1].getchildren()[0].tag == "Expression":
                        position_list.append(elem2.getchildren()[1].getchildren()[1].getchildren()[0].text)
            for position in eventposition:
                if event_position == position:
                    for order in possible_order:
                        if position_list == order:
                            return True
        return False

    def isOutput(path):
        """
        path = used for defining the folder to be checked
        """
        if os.path.isfile(path):
            return True
        else:
            return False


class ConnectorDescriptor(unittest.TestCase):

    # def test_TRS_RTECONFIG_INOUT_001(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.INOUT.001\\input -out ' + head + '\\tests\\TRS.RTECONFIG.INOUT.001\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.checkParsing(head + '\\tests\\TRS.RTECONFIG.INOUT.001\\input', head + '\\tests\\TRS.RTECONFIG.INOUT.001\\output\\result_RTE.log','.arxml', 'is well-formed'))

    # def test_TRS_RTECONFIG_INOUT_002(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.INOUT.002\\input -out ' + head + '\\tests\\TRS.RTECONFIG.INOUT.002\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.checkParsing(head + '\\tests\\TRS.RTECONFIG.INOUT.002\\rte_config', head + '\\tests\\TRS.RTECONFIG.INOUT.002\\output\\result_RTE.log','.xml', 'is well-formed'))
    #
    # def test_TRS_RTECONFIG_INOUT_003(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.INOUT.003\\input -out ' + head + '\\tests\\TRS.RTECONFIG.INOUT.003\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.isOutput(head + '\\tests\\TRS.RTECONFIG.INOUT.003\output\Rte.epc'))
    #
    # def test_TRS_RTECONFIG_CHECK_001(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.CHECK.001\\input -out ' + head + '\\tests\\TRS.RTECONFIG.CHECK.001\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     # self.assertFalse(FileCompare.isOutput(head + '\\tests\\TRS.RTECONFIG.CHECK.001\output\RTE_Config.xml'))
    #     self.assertTrue(FileCompare.checkLog(head + '\\tests\TRS.RTECONFIG.CHECK.001\output\\result_RTE.log', ["ERROR"], ["cycle"]))
    #
    # def test_TRS_RTECONFIG_GEN_002_1(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.002.1\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.002.1\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.scriptParamNew(head + '\\tests\TRS.RTECONFIG.GEN.002.1\\input\\ExempleSwcAllocation.xml',head + '\\tests\TRS.RTECONFIG.GEN.002.1\output\\Rte.epc',"RUNA_GererAutomonieConso_Cyclic", "RteMappedToTaskRef", "PER"))
    #
    # def test_TRS_RTECONFIG_GEN_002_2(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.002.2\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.002.2\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     # self.assertFalse(FileCompare.isOutput(head + '\\tests\\TRS.RTECONFIG.GEN.002.2\output\RTE_Config.xml'))
    #     self.assertTrue(FileCompare.checkLog(head + '\\tests\TRS.RTECONFIG.GEN.002.2\output\\result_RTE.log', ["ERROR"], ["PARTITION not set"]))
    #
    # def test_TRS_RTECONFIG_GEN_002_3(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.002.3\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.002.3\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     # self.assertFalse(FileCompare.isOutput(head + '\\tests\\TRS.RTECONFIG.GEN.002.3\output\RTE_Config.xml'))
    #     self.assertTrue(FileCompare.checkLog(head + '\\tests\TRS.RTECONFIG.GEN.002.3\output\\result_RTE.log', ["ERROR"], ["CORE not set"]))
    #
    # def test_TRS_RTECONFIG_GEN_002_4(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.002.4\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.002.4\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     # self.assertFalse(FileCompare.isOutput(head + '\\tests\\TRS.RTECONFIG.GEN.002.4\output\RTE_Config.xml'))
    #     self.assertTrue(FileCompare.checkLog(head + '\\tests\TRS.RTECONFIG.GEN.002.4\output\\result_RTE.log', ["ERROR"], ["CORE not set"]))
    #
    # def test_TRS_RTECONFIG_CHECK_003(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.CHECK.003\\input -out ' + head + '\\tests\\TRS.RTECONFIG.CHECK.003\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     # self.assertFalse(FileCompare.isOutput(head + '\\tests\\TRS.RTECONFIG.CHECK.003\output\RTE_Config.xml'))
    #     self.assertTrue(FileCompare.checkLog(head + '\\tests\TRS.RTECONFIG.CHECK.003\output\\result_RTE.log', ["ERROR"], ["RUNI_A26_EXIT has an EVENTS-CALLED reference, and is referenced in EVENTS-CALLED of event"]))
    #
    # def test_TRS_RTECONFIG_FUNC_001(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.FUNC.001\\input -out ' + head + '\\tests\\TRS.RTECONFIG.FUNC.001\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.checkLog(head + '\\tests\TRS.RTECONFIG.FUNC.001\output\\RTE_Config.xml', ["Instance_ASWC_A26"],["MappedToOsApplicationRef"]))
    #
    # def test_TRS_RTECONFIG_GEN_0001(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.0001\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.0001\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.setParamNew(head + '\\tests\TRS.RTECONFIG.GEN.0001\\input\\ExempleSwcAllocation.xml',head + '\\tests\TRS.RTECONFIG.GEN.0001\output\\Rte.epc', "Instance_ASWC_A26", "MappedToOsApplicationRef"))
    #
    # def test_TRS_RTECONFIG_GEN_004(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.004\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.004\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.checkLog(head + '\\tests\TRS.RTECONFIG.GEN.004\output\\input.xml', ["RUNA_GererAutomonieConso_Cyclic"],["RtePositionInTask", "RteMappedToTaskRef", "RteActivationOffset"]))
    #
    # def test_TRS_RTECONFIG_GEN_0002_1(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.0002.1\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.0002.1\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.scriptParamNew(head + '\\tests\TRS.RTECONFIG.GEN.0002.1\\input\\ExempleSwcAllocation.xml', head + '\\tests\TRS.RTECONFIG.GEN.0002.1\output\\Rte.epc', "RUNA_GererAutomonieConso_Cyclic", "RteMappedToTaskRef", "PER"))
    #
    # def test_TRS_RTECONFIG_GEN_0002_2(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.0002.2\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.0002.2\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.scriptParamNew(head + '\\tests\\TRS.RTECONFIG.GEN.0002.2\\input\\ExempleSwcAllocation.xml', head + '\\tests\\TRS.RTECONFIG.GEN.0002.2\\output\\Rte.epc',"DataReceivedEvent", "RteMappedToTaskRef", "PER"))
    #
    # def test_TRS_RTECONFIG_GEN_0002_3(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.0002.3\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.0002.3\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.scriptParamNew(head + '\\tests\TRS.RTECONFIG.GEN.0002.3\\input\\ExempleSwcAllocation.xml', head + '\\tests\TRS.RTECONFIG.GEN.0002.3\output\\Rte.epc',"RUNA_GererAutomonieConso_Cyclic", "RteMappedToTaskRef", "PER"))
    #
    # def test_TRS_RTECONFIG_GEN_0002_4(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.0002.4\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.0002.4\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.scriptParamNew(head + '\\tests\TRS.RTECONFIG.GEN.0002.4\\input\\ExempleSwcAllocation.xml',head + '\\tests\TRS.RTECONFIG.GEN.0002.4\output\\Rte.epc',"DataReceivedEvent", "RteMappedToTaskRef", "PER"))
    #
    # def test_TRS_RTECONFIG_GEN_0002_5(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.0002.5\\input  -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.0002.5\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.scriptParam(head + '\\tests\TRS.RTECONFIG.GEN.0002.5\\input\\ExempleSwcAllocation.xml',head + '\\tests\TRS.RTECONFIG.GEN.0002.5\output\\RTE_Config.xml', "RUNI_A28_EXIT","RteMappedToTaskRef", "PER"))
    #
    # def test_TRS_RTECONFIG_GEN_0002_6(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.0002.6\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.0002.6\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.scriptParam(head + '\\tests\TRS.RTECONFIG.GEN.0002.6\\input\\ExempleSwcAllocation.xml',head + '\\tests\TRS.RTECONFIG.GEN.0002.6\output\\RTE_Config.xml',"DataReceivedEvent", "RteMappedToTaskRef", "PER"))
    #
    # def test_TRS_RTECONFIG_GEN_0002_7(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.0002.7\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.0002.7\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.scriptParam(head + '\\tests\TRS.RTECONFIG.GEN.0002.7\\input\\ExempleSwcAllocation.xml',head + '\\tests\TRS.RTECONFIG.GEN.0002.7\output\\RTE_Config.xml',"DataReceivedEvent", "RteMappedToTaskRef", "PER"))
    #
    # def test_TRS_RTECONFIG_GEN_006_1(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.006.1\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.006.1\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.eventOrder(head + '\\tests\TRS.RTECONFIG.GEN.006.1\\input\\ExempleEventsConstraints.xml', head + '\\tests\TRS.RTECONFIG.GEN.006.1\output\\RTE_Config.xml', [['DataReceivedEvent', 'RUNI_A26_EXIT', 'RUNPI_ASWC_A26_ENTRY'], ['RUNI_A26_EXIT', 'DataReceivedEvent', 'RUNPI_ASWC_A26_ENTRY']], [['num:i(1)', 'num:i(2)', 'num:i(3)'], ['num:i(1)', 'num:i(1)', 'num:i(2)']]))
    #
    # def test_TRS_RTECONFIG_GEN_006_2(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.006.2\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.006.2\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.eventOrder(head + '\\tests\TRS.RTECONFIG.GEN.006.2\\input\\ExempleEventsConstraints.xml', head + '\\tests\TRS.RTECONFIG.GEN.006.2\output\\RTE_Config.xml', [['DataReceived1Event', 'DataReceived3Event', 'DataReceived2Event'], ['DataReceived3Event', 'DataReceived1Event', 'DataReceived2Event']],[['num:i(1)', 'num:i(2)', 'num:i(3)'], ['num:i(1)', 'num:i(1)', 'num:i(2)']]))
    #
    # def test_TRS_RTECONFIG_GEN_006_3(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.006.3\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.006.3\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.eventOrder(head + '\\tests\TRS.RTECONFIG.GEN.006.3\\input\\ExempleEventsConstraints.xml', head + '\\tests\TRS.RTECONFIG.GEN.006.3\output\\RTE_Config.xml', [['DataReceived3Event', 'DataReceived1Event', 'DataReceived2Event'], ['DataReceived3Event', 'DataReceived2Event', 'DataReceived1Event']], [['num:i(1)', 'num:i(2)', 'num:i(3)'], ['num:i(1)', 'num:i(1)', 'num:i(2)']]))
    #
    # def test_TRS_RTECONFIG_GEN_005(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.005\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.005\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.eventOrder(head + '\\tests\TRS.RTECONFIG.GEN.005\\input\\ExempleEventsConstraints.xml', head + '\\tests\TRS.RTECONFIG.GEN.005\output\\RTE_Config.xml', [['DataReceived2Event', 'DataReceived3Event', 'DataReceived1Event'],['DataReceivedEvent1', 'DataReceivedEvent', 'DataReceivedEvent2']],[['num:i(1)', 'num:i(2)', 'num:i(3)'], ['num:i(1)', 'num:i(1)', 'num:i(2)']]))
    #
    # def test_TRS_RTECONFIG_FUNC_007(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.FUNC.007\\input -out ' + head + '\\tests\\TRS.RTECONFIG.FUNC.007\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.checkRteActivation(head + '\\tests\TRS.RTECONFIG.FUNC.007\\input\\ExempleEventsConstraints.xml',head + '\\tests\TRS.RTECONFIG.FUNC.007\output\\RTE_Config.xml', "0"))
    #
    # def test_TRS_RTECONFIG_FUNC_008(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.FUNC.008\\input -out ' + head + '\\tests\\TRS.RTECONFIG.FUNC.008\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.eventOrder(head + '\\tests\TRS.RTECONFIG.FUNC.008\\input\\ExempleEventsConstraints.xml',head + '\\tests\TRS.RTECONFIG.FUNC.008\output\\RTE_Config.xml', [['RUNI_A26_EXIT', 'RUNA_GererAutomonieConso_Cyclic', 'RUNI_A26_EXIT'], ['RUNI_A26_EXIT', 'RUNA_GererAutomonieConso_Cyclic', 'RUNPI_A26_ENTRY']],[['num:i(1)', 'num:i(2)', 'num:i(1)'], ['num:i(1)', 'num:i(2)', 'num:i(3)']]))
    #
    # def test_TRS_RTECONFIG_GEN_003_1(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.003.1\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.003.1\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.checkLog(head + '\\tests\TRS.RTECONFIG.GEN.003.1\output\\RTE_Config.xml', ["RUNA_GererAutomonieConso_Cyclic"],["RtePositionInTask", "RteMappedToTaskRef", "RteActivationOffset"]))
    #
    # def test_TRS_RTECONFIG_GEN_003_2(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.003.2\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.003.2\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.checkLog(head + '\\tests\TRS.RTECONFIG.GEN.003.2\output\\RTE_Config.xml', ["RUNA_GererAutomonieConso_Cyclic"], ["RtePositionInTask", "RteMappedToTaskRef", "RteActivationOffset"]))
    #
    # def test_TRS_RTECONFIG_GEN_003_3(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.003.3\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.003.3\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.checkLog(head + '\\tests\TRS.RTECONFIG.GEN.003.3\output\\RTE_Config.xml', ["RUNA_GererAutomonieConso_Cyclic"], ["RtePositionInTask", "RteMappedToTaskRef", "RteActivationOffset"]))
    #
    # def test_TRS_RTECONFIG_GEN_003_4(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.003.4\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.003.4\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.checkLog(head + '\\tests\TRS.RTECONFIG.GEN.003.4\output\\RTE_Config.xml', ["RUNA_GererAutomonieConso_Cyclic", "RUNA_GererCptTempVhl_Cyclic"], ["RtePositionInTask", "RteMappedToTaskRef", "RteActivationOffset"]))
    #
    # def test_TRS_RTECONFIG_GEN_003_5(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.003.5\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.003.5\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.checkLog(head + '\\tests\TRS.RTECONFIG.GEN.003.5\output\\RTE_Config.xml', ["RUNA_GererAutomonieConso_Cyclic", "RUNA_GererCptTempVhl_Cyclic"], ["RtePositionInTask", "RteMappedToTaskRef", "RteActivationOffset"]))
    #
    # def test_TRS_RTECONFIG_GEN_003_6(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.003.6\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.003.6\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.checkLog(head + '\\tests\TRS.RTECONFIG.GEN.003.6\output\\RTE_Config.xml', ["RUNA_GererAutomonieConso_Cyclic", "RUNA_GererCptTempVhl_Cyclic"], ["RtePositionInTask", "RteMappedToTaskRef", "RteActivationOffset"]))
    #
    # def test_TRS_RTECONFIG_GEN_003_7(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.003.7\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.003.7\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.checkLog(head + '\\tests\TRS.RTECONFIG.GEN.003.7\output\\RTE_Config.xml', ["RUNA_GererAutomonieConso_Cyclic", "RUNA_GererCptTempVhl_Cyclic"], ["RtePositionInTask", "RteMappedToTaskRef", "RteActivationOffset"]))
    #
    # def test_TRS_RTECONFIG_GEN_003_8(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.003.8\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.003.8\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertFalse(FileCompare.checkLog(head + '\\tests\TRS.RTECONFIG.GEN.003.8\output\\RTE_Config.xml', ["RUNA_GererAutomonieConso_Cyclic"], ["RtePositionInTask", "RteMappedToTaskRef", "RteActivationOffset"]))
    #
    # def test_TRS_RTECONFIG_GEN_003_9(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.003.9\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.003.9\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertFalse(FileCompare.checkLog(head + '\\tests\TRS.RTECONFIG.GEN.003.9\output\\RTE_Config.xml', ["RUNA_GererAutomonieConso_Cyclic"],["RtePositionInTask", "RteMappedToTaskRef", "RteActivationOffset"]))
    #
    # def test_RTECONFIG_1(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\RTECONFIG.1\\input -out ' + head + '\\tests\\RTECONFIG.1\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.checkLog(head + '\\tests\\RTECONFIG.1\output\\result_RTE.log', ["ERROR"], "mismatched tag"))
    #
    # def test_RTE_EXCEPT_OIE_1(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\RTE.EXCEPT.OIE_1\\input -out ' + head + '\\tests\\RTE.EXCEPT.OIE_1\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.areSame(head + '\\tests\\RTE.EXCEPT.OIE_1\\output.xml', head + '\\tests\\RTE.EXCEPT.OIE_1\\output\\RTE_Config.xml'))
    #
    # def test_RTE_EXCEPT_OIE_2(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\RTE.EXCEPT.OIE_2\\input -out ' + head + '\\tests\\RTE.EXCEPT.OIE_2\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.areSame(head + '\\tests\\RTE.EXCEPT.OIE_2\\output.xml', head + '\\tests\\RTE.EXCEPT.OIE_2\\output\\RTE_Config.xml'))

    # def test_RTECONFIG_GEN_010(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.010\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.010\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.areSame(head + '\\tests\\TRS.RTECONFIG.GEN.010\\output.epc', head + '\\tests\\TRS.RTECONFIG.GEN.010\\output\\MemMap.epc'))

    # def test_RTECONFIG_GEN_011(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.011\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.011\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.areSame(head + '\\tests\\TRS.RTECONFIG.GEN.011\\output.epc', head + '\\tests\\TRS.RTECONFIG.GEN.011\\output\\MemMap.epc'))

    # def test_RTECONFIG_GEN_012(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.012\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.012\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.areSame(head + '\\tests\\TRS.RTECONFIG.GEN.012\\output.epc', head + '\\tests\\TRS.RTECONFIG.GEN.012\\output\\MemMap.epc'))
    #
    # def test_RTECONFIG_GEN_013(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.012\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.012\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.areSame(head + '\\tests\\TRS.RTECONFIG.GEN.012\\output.epc', head + '\\tests\\TRS.RTECONFIG.GEN.012\\output\\MemMap.epc'))
    #
    # def test_RTECONFIG_GEN_014(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.012\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.012\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.areSame(head + '\\tests\\TRS.RTECONFIG.GEN.012\\output.epc', head + '\\tests\\TRS.RTECONFIG.GEN.012\\output\\MemMap.epc'))
    #
    # def test_RTECONFIG_GEN_015(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.012\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.012\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.areSame(head + '\\tests\\TRS.RTECONFIG.GEN.012\\output.epc', head + '\\tests\\TRS.RTECONFIG.GEN.012\\output\\MemMap.epc'))
    #
    # def test_RTECONFIG_GEN_016(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.012\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.012\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.areSame(head + '\\tests\\TRS.RTECONFIG.GEN.012\\output.epc', head + '\\tests\\TRS.RTECONFIG.GEN.012\\output\\MemMap.epc'))
    #
    # def test_RTECONFIG_GEN_017(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.012\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.012\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.areSame(head + '\\tests\\TRS.RTECONFIG.GEN.012\\output.epc', head + '\\tests\\TRS.RTECONFIG.GEN.012\\output\\MemMap.epc'))
    #
    # def test_RTECONFIG_GEN_018(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.012\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.012\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.areSame(head + '\\tests\\TRS.RTECONFIG.GEN.012\\output.epc', head + '\\tests\\TRS.RTECONFIG.GEN.012\\output\\MemMap.epc'))
    #
    # def test_RTECONFIG_GEN_019(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.012\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.012\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.areSame(head + '\\tests\\TRS.RTECONFIG.GEN.012\\output.epc', head + '\\tests\\TRS.RTECONFIG.GEN.012\\output\\MemMap.epc'))
    #
    # def test_RTECONFIG_GEN_020(self):
    #     current_path = os.path.realpath(__file__)
    #     head, tail = ntpath.split(current_path)
    #     os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.012\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.012\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
    #     self.assertTrue(FileCompare.areSame(head + '\\tests\\TRS.RTECONFIG.GEN.012\\output.epc', head + '\\tests\\TRS.RTECONFIG.GEN.012\\output\\MemMap.epc'))

    def test_RTECONFIG_GEN_021(self):
        current_path = os.path.realpath(__file__)
        head, tail = ntpath.split(current_path)
        os.system('coverage run RTE_Configurator.py -in ' + head + '\\tests\\TRS.RTECONFIG.GEN.012\\input -out ' + head + '\\tests\\TRS.RTECONFIG.GEN.012\\output -osconfig C:\\Users\\fcdirman\\PycharmProjects\\RTE_Configurator\\ConfigOs.xml -MemMap -compo /RootP_Composition/Compo_VSM')
        self.assertTrue(FileCompare.areSame(head + '\\tests\\TRS.RTECONFIG.GEN.012\\output.epc', head + '\\tests\\TRS.RTECONFIG.GEN.012\\output\\MemMap.epc'))



suite = unittest.TestLoader().loadTestsFromTestCase(ConnectorDescriptor)
unittest.TextTestRunner(verbosity=2).run(suite)

# current_path = os.path.realpath(__file__)
# head, tail = ntpath.split(current_path)
# if __name__ == "__main__":
#     unittest.main(testRunner=HtmlTestRunner.HTMLTestRunner(output=head + "\\tests"))
