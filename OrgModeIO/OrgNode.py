#-*-coding:utf-8-*-
from io import StringIO

class OrgHeadLine(object):
    def __init__(self, builder):
        self._level = builder.get_level()
        self._state = builder.get_state()
        self._priority = builder.get_priority()
        self._title = builder.get_title()
        self._tags = builder.get_tags()
        self._content = builder.get_content()
        self._content_buffer = StringIO(self._content)
        self._scheduled = builder.get_scheduled()
        self._deadline = builder.get_deadline()
        self._closed = builder.get_closed()
        self._properties = builder.get_properties()
        # TODO drawer
        # logbook

    def __str__(self):
        rtn = StringIO()
        sf = '{:*^' + str(self.get_level()) + 's}'
        rtn.write(sf.format(''))
        if self.get_state():
            rtn.write(' ' + self.get_state())
        if self.get_priority():
            rtn.write(' [#' + self.get_priority() + ']')
        if self.get_title():
            rtn.write(' ' + self.get_title())
        if self.get_tags():
            # TODO calc the space
            rtn.write(' :' + ':'.join(self.get_tags()) + ':')
        if self.get_closed():
            rtn.write('\nCLOSED:' + str(self.get_closed()))
        if self.get_scheduled():
            rtn.write(' SCHEDULED:' + str(self.get_scheduled()))
        if self.get_deadline():
            rtn.write(' DEADLINE:' + str(self.get_deadline()))
        # TODO properties
        return rtn.getvalue()

    def append_content(self, line):
        self._content_buffer.write(line)

    def get_content(self):
        return self._content_buffer.getvalue()

    def add_property(self, p):
        if self._properties:
            self._properties.append(p)
        else:
            self._properties = [p]

    def get_properties(self):
        return self._properties

    def get_level(self):
        return self._level

    def get_state(self):
        return self._state

    def get_priority(self):
        return self._priority

    def get_title(self):
        return self._title

    def get_tags(self):
        return self._tags

    def get_scheduled(self):
        return self._scheduled

    def get_deadline(self):
        return self._deadline

    def get_closed(self):
        return self._closed

    def set_scheduled(self, scheduled):
        self._scheduled = scheduled

    def set_deadline(self, deadline):
        self._deadline = deadline

    def set_closed(self, closed):
        self._closed = closed

    class OrgHeadBuild(object):
        def __init__(self):
            self._level = None
            self._state = None
            self._priority = None
            self._title = None
            self._tags = None
            self._content = None
            self._scheduled = None
            self._deadline = None
            self._closed = None
            self._properties = None

        def get_content(self):
            return self._content

        def get_level(self):
            return self._level

        def get_state(self):
            return self._state

        def get_priority(self):
            return self._priority

        def get_title(self):
            return self._title

        def get_tags(self):
            return self._tags

        def get_scheduled(self):
            return self._scheduled

        def get_deadline(self):
            return self._deadline

        def get_closed(self):
            return self._closed

        def get_properties(self):
            return self._properties

        def title(self, title):
            self._title = title
            return self

        def state(self, state):
            self._state = state
            return self

        def priority(self, priority):
            self._priority = priority
            return self

        def tags(self, tags):
            self._tags = tags
            return self

        def content(self, content):
            self._content = content
            return self

        def level(self, level):
            self._level = level
            return self

        def scheduled(self, scheduled):
            self._scheduled = scheduled
            return self

        def deadline(self, deadline):
            self._deadline = deadline
            return self

        def closed(self, closed):
            self._closed = closed
            return self

        def properties(self, properties):
            self._properties = properties
            return self

        def build(self):
            return OrgHeadLine(self) if self._level or self._state or self._priority or self._title or self._tags or self._content else None


class LogBook(object):
    def __init__(self):
        self._from_state = None
        self._to_state = None
        self._change_time = None
        self._note = None
    
    
