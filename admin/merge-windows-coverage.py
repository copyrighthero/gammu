#!/usr/bin/env python

# The coverage merge code is based on
# https://github.com/x3mSpeedy/Flow123d-python-utils/blob/master/src/coverage/coverage_merge_module.py


import sys
import xml.etree.cElementTree as ET
import re
import glob

# constants
PACKAGES_LIST = 'packages/package'
PACKAGES_ROOT = 'packages'
CLASSES_LIST = 'classes/class'
CLASSES_ROOT = 'classes'
METHODS_LIST = 'methods/method'
METHODS_ROOT = 'methods'
LINES_LIST = 'lines/line'
LINES_ROOT = 'lines'


class CoverageMerge(object):
    def __init__(self, filename, xmlfiles):
        self.xmlfiles = xmlfiles
        self.finalxml = filename
        self.filtersuffix = ''

    def execute_merge(self):
        # merge all given files
        totalfiles = len(self.xmlfiles)

        self.merge_xml(self.xmlfiles[0], self.xmlfiles[1], self.finalxml)

        for i in range(totalfiles - 2):
            xmlfile = self.xmlfiles[i + 2]
            self.merge_xml(self.finalxml, xmlfile, self.finalxml)

    def merge_xml(self, xmlfile1, xmlfile2, outputfile):
        # parse
        xml1 = ET.parse(xmlfile1)
        xml2 = ET.parse(xmlfile2)

        # get packages
        packages1 = self.filter_xml(xml1)
        packages2 = self.filter_xml(xml2)

        # find root
        packages1root = xml1.find(PACKAGES_ROOT)

        # merge packages
        self.merge(
            packages1root,
            packages1,
            packages2,
            'name',
            self.merge_packages
        )

        # write result to output file
        xml1.write(outputfile, encoding="UTF-8", xml_declaration=True)

    def filter_xml(self, xmlfile):
        xmlroot = xmlfile.getroot()
        return xmlroot.findall(PACKAGES_LIST)

    def get_attributes_chain(self, obj, attrs):
        """Return a joined arguments of object based on given arguments"""

        if type(attrs) is list:
            result = ''
            for attr in attrs:
                result += obj.attrib[attr]
            return result
        else:
            return obj.attrib[attrs]

    def merge(self, root, list1, list2, attr, merge_function):
        """ Groups given lists based on group attributes.
        Process of merging items with same key is handled by
        passed merge_function. Returns list1.
        """
        for item2 in list2:
            found = False
            for item1 in list1:
                if self.get_attributes_chain(item1, attr) == self.get_attributes_chain(item2, attr):
                    item1 = merge_function(item1, item2)
                    found = True
                    break
            if found:
                continue
            else:
                root.append(item2)

    def merge_packages(self, package1, package2):
        """Merges two packages. Returns package1."""
        classes1 = package1.findall(CLASSES_LIST)
        classes2 = package2.findall(CLASSES_LIST)
        if classes1 or classes2:
            self.merge(
                package1.find(CLASSES_ROOT),
                classes1,
                classes2,
                ['filename', 'name'],
                self.merge_classes
            )

        return package1

    def merge_classes(self, class1, class2):
        """Merges two classes. Returns class1."""

        lines1 = class1.findall(LINES_LIST)
        lines2 = class2.findall(LINES_LIST)
        if lines1 or lines2:
            self.merge(
                class1.find(LINES_ROOT),
                lines1,
                lines2,
                'number',
                self.merge_lines
            )

        methods1 = class1.findall(METHODS_LIST)
        methods2 = class2.findall(METHODS_LIST)
        if methods1 or methods2:
            self.merge(
                class1.find(METHODS_ROOT),
                methods1,
                methods2,
                'name',
                self.merge_methods
            )

        return class1

    def merge_methods(self, method1, method2):
        """Merges two methods. Returns method1."""

        lines1 = method1.findall(LINES_LIST)
        lines2 = method2.findall(LINES_LIST)
        self.merge(
            method1.find(LINES_ROOT),
            lines1,
            lines2,
            'number',
            self.merge_lines
        )

    def merge_lines(self, line1, line2):
        """Merges two lines by summing their hits. Returns line1."""

        # merge hits
        value = int(line1.get('hits')) + int(line2.get('hits'))
        line1.set('hits', str(value))

        # merge conditionals
        con1 = line1.get('condition-coverage')
        con2 = line2.get('condition-coverage')
        if con1 is not None and con2 is not None:
            con1value = int(con1.split('%')[0])
            con2value = int(con2.split('%')[0])
            # bigger coverage on second line, swap their conditionals
            if con2value > con1value:
                line1.set('condition-coverage', str(con2))
                line1.__setitem__(0, line2.__getitem__(0))

        return line1


COVERAGE_XML = 'c:\\projects\\gammu\\coverage.xml'
COVERAGE_MASK = 'c:\\projects\\gammu\\coverage\\*.*'


def main():
    matches = glob.glob(COVERAGE_MASK)
    if matches:
        CoverageMerge(COVERAGE_XML, matches).execute_merge()
    else:
        print 'No files matched: {0}'.format(COVERAGE_MASK)


if __name__ == '__main__':
    main()
