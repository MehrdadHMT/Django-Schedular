from json_log_formatter import JSONFormatter
import time


class TaskSchedulerJsonFormatter(JSONFormatter):

    def json_record(self, message, extra, record):
        request = extra.pop('request', None)
        extra['time'] = time.time()
        return super(TaskSchedulerJsonFormatter, self).json_record(message, extra, record)
