#-*-coding:utf-8-*-
from io import StringIO
import re


class OrgDoc(object):

    def __init__(self):
        self._doc = None
        # Text before the first heading.

    def get_doc_iterator(self):
        return self._doc


class OrgDocFile(OrgDoc):

    def __init__(self, file):
        self._doc = file
        self._doc_setting = None
        # Text before the first heading.
        self._preface = StringIO()


class OrgDocString(OrgDoc):

    def __init__(self, string):
        self._doc = StringIO(string)
        self._doc_setting = None
        # Text before the first heading.
        self._preface = StringIO()


class OrgParsedDoc(object):

    def __init__(self):
        self._buffer_settings = None
        self._preface = StringIO()
        self._nodes = None

    def get_buffer_settings(self):
        if self._buffer_settings is None:
            self._buffer_settings = OrgBufferSettings()
        return self._buffer_settings

    def set_nodes(self, nodes):
        self._nodes = nodes

    def get_preface(self):
        return self._preface.getvalue()

    def append_preface(self, line):
        self._preface.write(line)

    def get_nodes(self):
        return self._nodes

    def __str__(self):
        # TODO
        pass

    def to_html(self):
        # TODO
        pass


class OrgBufferSettings(object):
    __BUFFER_SETTINGS_TITLE = '#+TITLE:'
    __BUFFER_SETTINGS_SEQ_TODO = '#+SEQ_TODO:'
    __BUFFER_SETTINGS_TAG = '#+TAGS:'

    def __init__(self):
        self.__title = None
        self.__tags = []
        self.__states = []

    def get_title(self):
        return self.__title

    def set_title(self, title):
        self.__title = title

    def add_tags(self, tags):
        self.__tags.append(tags)

    def get_tags(self):
        return self.__tags

    def add_states(self, states):
        self.__states.append(states)

    def get_states(self):
        return self.__states

    def parse(self, line):
        if line.startswith(self.__BUFFER_SETTINGS_TITLE):
            self.set_title(
                line[len(self.__BUFFER_SETTINGS_TITLE): len(line)].strip())
            return True
        if line.startswith(self.__BUFFER_SETTINGS_TAG):
            self.add_tags(line[len(self.__BUFFER_SETTINGS_TAG)
                          :len(line)].strip().split(' '))
            return True
        # TODO  http://orgmode.org/manual/TODO-types.html#TODO-types
        # DONE  http://orgmode.org/manual/Workflow-states.html#Workflow-states
        if line.startswith(self.__BUFFER_SETTINGS_SEQ_TODO):
            self.add_states(re.split(r'\s+', re.sub(r'\([^()]*\)\s*|\|\s*', ' ', line[len(
                self.__BUFFER_SETTINGS_SEQ_TODO): len(line)].strip(), count=0).strip()))
            return True
