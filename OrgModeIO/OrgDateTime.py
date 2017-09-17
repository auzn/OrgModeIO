#-*-coding:utf-8-*-

from enum import Enum
import re
from datetime import datetime
from io import StringIO


class OrgRange(object):

    ORG_DATETIME_PSTR = "(([\\[<])[0-9]{4,}-[0-9]{2}-[0-9]{2} ?[^]\r\n>]*?[\\]>])"
    ORG_DT_OR_RANGE_PATTERN = re.compile(
        "(%s(--?-?%s)?)" % (ORG_DATETIME_PSTR, ORG_DATETIME_PSTR))

    def __init__(self):
        self.__start_time = None
        self.__end_time = None

    @staticmethod
    def parse(time_str):
        range = OrgRange()
        m = OrgRange.ORG_DT_OR_RANGE_PATTERN.search(time_str)
        if m:
            if len(m.groups()) == 6 and m.group(6) != None:
                range.set_start_time(OrgDateTime.parse(m.group(2)))
                range.set_end_time(OrgDateTime.parse(m.group(5)))
            else:
                range.set_start_time(OrgDateTime.parse(m.group(2)))
        return range

    def set_start_time(self, start_time):
        self.__start_time = start_time

    def set_end_time(self, end_time):
        self.__end_time = end_time

    def get_start_time(self):
        return self.__start_time

    def get_end_time(self):
        return self.__end_time

    def __str__(self):
        return str(self.get_start_time()) + ('--' + str(self.get_end_time()) if self.get_end_time() else '')


class IntervalUnit(Enum):
    HOUR = 'h'
    DAY = 'd'
    WEEK = 'w'
    MONTH = 'm'
    YEAR = 'y'


class OrgInterval(object):

    def __init__(self):
        self._interval_value = None
        self._interval_unit = None

    def set_value(self, interval_value):
        self._interval_value = interval_value

    def set_unit_with_str(self, interval_unit_str):
        self._interval_unit = IntervalUnit(interval_unit_str)

    def get_value(self):
        return self._interval_value

    def get_unit(self):
        return self._interval_unit

    def __str__(self):
        return str(self.get_value()) + self.get_unit()


class DelayType(Enum):
    """ ALL:In case the task contains a repeater, the delay is considered to affect all occurrences
    FIRST:In case the task contains a repeater,the delay  only affect the first scheduled occurrence of the task
    """
    ALL = '-'
    FIRST = '--'


class OrgDelay(OrgInterval):
    """Delay the display of the task in the agenda from the scheduled time,
    or lead time for warnings for a specific deadline
    http://orgmode.org/manual/Deadlines-and-scheduling.html
    """

    DELAY_PATTERN = re.compile('([-]{1,2})([0-9]+)([hdwmy])')

    def __init__(self):
        super(OrgDelay, self).__init__()
        self.__delay_type = None

    def set_delay_type(self, delay_type):
        self.__delay_type = delay_type

    def get_delay_type(self):
        return self.__delay_type

    @staticmethod
    def parse(time_str):
        delay = OrgDelay()
        m = OrgDelay.DELAY_PATTERN.search(time_str)
        if m:
            if len(m.groups()) == 3:
                delay.set_delay_type(DelayType(m.group(1)))
                delay.set_value(int(m.group(2)))
                delay.set_unit_with_str(m.group(3))
                return delay
        return None

    def shift(self):
        # TODO 根据delay type 、 schedule/deadline 生成预期时间
        pass

    def __str__(self):
        return self.get_delay_type().value + str(self.get_value()) + self.get_unit().value


class RepeaterType(Enum):
    # will shift the date by N hdwmy, uniformly-spaced
    UNIFORMLY_SPACED = '+'
    # will shift the date by at least N hdwmy,but also by as many N hdwmy as it takes to get this date into the future
    CATCH_UP = '++'
    # shift the date to N hdwmy after today.
    AFTER_TODAY = '.+'


class OrgRepeater(OrgInterval):
    """Some tasks need to be repeated again and again. 
    Org mode helps to organize such tasks using a so-called repeater in a DEADLINE, SCHEDULED, or plain timestamp. 
    http://orgmode.org/manual/Repeated-tasks.html
    """
    REPEATER_PATTERN = re.compile(
        '(([.+]?\\+)([0-9]+)([hdwmy]))(/([0-9]+)([hdwmy]))?')

    def __init__(self):
        super(OrgRepeater, self).__init__()
        self.__repeater_type = None
        self.__habit = None

    def set_repeater_type(self, repeater_type):
        self.__repeater_type = repeater_type

    def get_repeater_type(self):
        return self.__repeater_type

    def set_habit(self, habit):
        """
        http://orgmode.org/manual/Tracking-your-habits.html
        """
        self.__habit = habit

    def get_habit(self):
        return self.__habit

    @staticmethod
    def parse(time_str):
        repeater = OrgRepeater()
        m = OrgRepeater.REPEATER_PATTERN.search(time_str)
        if m:
            if len(m.groups()) == 7:
                repeater.set_repeater_type(RepeaterType(m.group(2)))
                repeater.set_value(int(m.group(3)))
                repeater.set_unit_with_str(m.group(4))
                if m.group(7):
                    habit = OrgInterval()
                    habit.set_value(int(m.group(6)))
                    habit.set_unit_with_str(m.group(7))
                    repeater.set_habit(habit)
            return repeater

        return None

    def __str__(self):
        return self.get_repeater_type().value + str(self.get_value()) + self.get_unit().value + ('/' + str(self.get_habit())
                                                                                                 if self.get_habit() else '')


class OrgDateTime(object):
    """A timestamp is a specification of a date (possibly with a time or a range of times) in a special format.
    http://orgmode.org/manual/Timestamps.html
    """
    DATE_MAYBE_WITH_TIME_PATTERN = re.compile(
        '(([0-9]{4,})-([0-9]{2})-([0-9]{2})( +[^]+0-9>\r\n -]+)?( +([0-9]{1,2}):([0-9]{2}))?)')
    TIME_MAYBE_TIME_RANGE = re.compile(
        '(([012]?[0-9]):([0-5][0-9]))(-(([012]?[0-9]):([0-5][0-9])))?')

    def __init__(self):
        self.__is_active = None
        self.__has_time = False
        self.__repeater = None
        self.__delay = None
        self.__time_str = None
        self.__s_dt = None
        self.__e_dt = None

    @staticmethod
    def parse(time_str):
        dt = OrgDateTime()
        if time_str.startswith('<'):
            dt.set_active(True)
        elif time_str.startswith('['):
            dt.set_active(False)
        md = OrgDateTime.DATE_MAYBE_WITH_TIME_PATTERN .search(time_str)
        if md:
            year = int(md.group(2))
            month = int(md.group(3))
            day = int(md.group(4))
            if md.group(6):
                mt = OrgDateTime.TIME_MAYBE_TIME_RANGE.search(
                    md.string[md.start(6):-1].strip())
                hour = int(mt.group(2))
                minute = int(mt.group(3))
                dt.set_has_time(True)
                dt.set_start_time(datetime(year, month, day, hour, minute))
                if mt.group(4):
                    end_hour = int(mt.group(6))
                    end_minute = int(mt.group(7))
                    dt.set_end_time(datetime(
                        year, month, day, end_hour, end_minute))
            else:
                dt.set_start_time(datetime(year, month, day, 0, 0))
                dt.set_has_time(False)
        dt.set_repeater(OrgRepeater.parse(time_str))
        dt.set_delay(OrgDelay.parse(time_str))
        return dt

    def get_start_time(self):
        return self.__s_dt

    def set_start_time(self, st):
        self.__s_dt = st

    def get_end_time(self):
        return self.__e_dt

    def set_end_time(self, et):
        self.__e_dt = et

    def is_active(self):
        return self.__is_active

    def set_active(self, active):
        self.__is_active = active

    def has_time(self):
        return self.__has_time

    def set_has_time(self, has_time):
        self.__has_time = has_time

    def get_repeater(self):
        return self.__repeater

    def set_repeater(self, repeater):
        self.__repeater = repeater

    def get_delay(self):
        return self.__delay

    def set_delay(self, delay):
        self.__delay = delay

    def __str__(self):
        s = StringIO()
        s.write('<' if self.is_active() else '[')
        if self.get_start_time():
            s.write(self.get_start_time().strftime('%Y-%m-%d %H:%M'))
        if self.get_end_time:
            s.write('-' + self.get_end_time().strftime('%H:%M')
                    if self.get_end_time() else '')
        s.write(' ' + str(self.get_repeater()) if self.get_repeater() else '')
        s.write(' ' + str(self.get_delay()) if self.get_delay() else '')
        s.write('>' if self.is_active() else ']')

        return s.getvalue()
