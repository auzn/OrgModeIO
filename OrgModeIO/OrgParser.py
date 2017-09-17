#-*-coding:utf-8-*-
import re
import logging
from .OrgDoc import OrgParsedDoc
from .OrgNode import OrgHeadLine
from .OrgDateTime import OrgRange

logging.basicConfig(level=logging.DEBUG)


class OrgParser(object):
    """ parse org mode file or String
    """

    _HEADLINE_PROPERTY_PATTERN = re.compile("^:([^:\\s]+):\\s+(.*)\\s*$")

    def __init__(self, org_doc):
        self._org_doc = org_doc

    def parse(self):
        parsed_doc = OrgParsedDoc()
        headline_parser = None
        current_node = None
        root_node = OrgHeadLine.OrgHeadBuild().level(0).title('ROOT').build()
        org_nodes = [{
            'level': 0,
            'lft': 0,
            'rgt': None,
            'head': root_node
        }]
        stack_node = [{
            'id': 0,
            'level': 0
        }]
        interval = 1
        pref_level = 0
        sequence = 0
        is_in_properties = False

        for line in self._org_doc.get_doc_iterator():
            if current_node is None:
                if parsed_doc.get_buffer_settings().parse(line):
                    continue
            states = parsed_doc.get_buffer_settings().get_states()
            s = []
            for ss in states:
                s.append('|'.join(ss))
            if len(s) > 0:
                headline_parser = HeadLineParser(re.compile(
                    '^(' + '|'.join(s) + ')(.*)')
                )
            else:
                headline_parser = HeadLineParser(
                    re.compile('^(TODO|CLOSED)(.*)'))

            head = headline_parser.parse_headline(line)
            if head:
                if current_node != None:
                    # not a new head  , dealing with the relationship
                    # TODO find new head listener
                    # trim content line
                    if pref_level < head.get_level():
                        # *------
                        # **----- <---
                        # child node insert with lft
                        sequence += interval
                        self.__append_node(
                            org_nodes, stack_node, sequence, head)
                    elif pref_level == head.get_level():
                        # **---- on node
                        # **---- <---
                        # neighbor node close with rgt
                        sequence += interval
                        org_nodes[stack_node.pop()['id']]['rgt'] = sequence
                        sequence += interval
                        self.__append_node(
                            org_nodes, stack_node, sequence, head)
                    else:
                        # *-----
                        # **----
                        # *---
                        # new node level close all the neighbor node tree
                        while len(stack_node) > 0:
                            if stack_node[-1]['level'] >= head.get_level():
                                sequence += interval
                                org_nodes[stack_node.pop()['id']
                                          ]['rgt'] = sequence
                            else:
                                break
                        sequence += interval
                        self.__append_node(
                            org_nodes, stack_node, sequence, head)
                else:
                    # first head
                    sequence += interval
                    self.__append_node(org_nodes, stack_node, sequence, head)
                pref_level = head.get_level()
                current_node = head
            else:
                # not a head
                if current_node != None:
                    # belongs to pre head
                    if headline_parser.parse_plan(line, org_nodes[-1]):
                        pass
                    else:
                        if not is_in_properties and line.strip() == ':PROPERTIES:':
                            is_in_properties = True
                        elif is_in_properties:
                            is_in_properties = headline_parser.parse_properties(
                                line, org_nodes[-1])
                        else:
                            headline_parser.parse_content(line, org_nodes[-1])
                else:
                    parsed_doc.append_preface(line)
        # close all the node with rgt
        while len(stack_node) > 0:
            sequence += interval
            org_nodes[stack_node.pop()['id']
                      ]['rgt'] = sequence

        parsed_doc.set_nodes(org_nodes)
        return parsed_doc

    def _pass_head_other(self, line):
        pass

    def __append_node(self, org_node, stack_node, sequence, head):
        org_node.append({
            'level': head.get_level(),
            'lft': sequence,
            'rgt': None,
            'head': head
        })
        stack_node.append({
            'id': len(org_node) - 1,
            'level': head.get_level()
        })


class HeadLineParser(object):
    _HEADLINE_PATTERN = re.compile('^([\\*]+)\\s+(.*)\\s*$')
    _HEADLINE_PRIORITY_PATTEN = re.compile('^\\s*\\[#([A-Z])\\](.*)')
    _HEADLINE_TAG_PATTERN = re.compile('^(.*)\\s+:(\\S+):\\s*$')
    _HEADLINE_STATE_PATTERN = re.compile('^(TODO|CLOSED)(.*)')
    _PLAN_PATTERN = re.compile(
        "(SCHEDULED:|CLOSED:|DEADLINE:) *" + OrgRange.ORG_DT_OR_RANGE_PATTERN.pattern)
    _HEADLINE_PROPERTY_PATTERN = re.compile("^:([^:\\s]+):\\s+(.*)\\s*$")
    # TODO
    _LOGBOOK_PATTERN = re.compile(
        '\s*- State\s\"(.*)?\"\s*from\s*\"(.*)?\"\s*' + OrgRange.ORG_DT_OR_RANGE_PATTERN.pattern)

    def __init__(self, state_pattern):
        self._HEADLINE_STATE_PATTERN = state_pattern

    def parse_headline(self, line):
        hb = OrgHeadLine.OrgHeadBuild()
        m = self._HEADLINE_PATTERN.search(line)
        head_str = ''
        if m:
            hb.level(len(m.group(1)))
            head_str = m.group(2).strip()
        m = self._HEADLINE_STATE_PATTERN.search(head_str)
        if m:
            if len(m.group(2)) == 0 or m.group(2).startswith(' '):
                hb.state(m.group(1))
                head_str = m.group(2).strip()
        m = self._HEADLINE_PRIORITY_PATTEN.search(head_str)
        if m:
            hb.priority(m.group(1))
            head_str = m.group(2).strip()
        m = self._HEADLINE_TAG_PATTERN.search(head_str)
        if m:
            hb.tags(m.group(2).split(':'))
            hb.title(m.group(1).strip())
        else:
            # TODO last only title
            hb.title(head_str.strip())
        return hb.build()

    def parse_plan(self, line, org_node):
        times_matchs = self._PLAN_PATTERN.findall(line)
        found = False
        if times_matchs:
            for t in times_matchs:
                time_key = t[0]
                time_str = t[1]
                if time_key == 'SCHEDULED:':
                    org_node['head'].set_scheduled(
                        OrgRange.parse(time_str))
                elif time_key == 'CLOSED:':
                    org_node['head'].set_closed(
                        OrgRange.parse(time_str))
                elif time_key == 'DEADLINE:':
                    org_node['head'].set_deadline(
                        OrgRange.parse(time_str))
            found = True
        return found

    def parse_properties(self, line, org_node):
        if line.strip() == ':END:':
            return False
        else:
            property_match = self._HEADLINE_PROPERTY_PATTERN.search(
                line.strip())
            if property_match:
                    # TODO add properties
                org_node['head'].add_property({
                    'name': property_match.group(1),
                    'value': property_match.group(2)
                })
                return True

    def parse_content(self, line, org_node):
        org_node['head'].append_content(line)
