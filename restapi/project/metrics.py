from json import dumps
from logging import getLogger
from threading import Thread
from django.utils.timezone import now
from prometheus_client.core import GaugeMetricFamily, GaugeHistogramMetricFamily, InfoMetricFamily, StateSetMetricFamily

logger = getLogger(__name__)


def generator_metrice_value(get_new_value):
    value = None

    def _set_value():
        nonlocal value
        try:
            value = get_new_value()
        except Exception as exception:
            logger.warning(exception)
            value = None

    def _get_value():
        nonlocal value
        _value = value
        Thread(target=_set_value, args=[], kwargs={}).start()
        return _value

    return _get_value


def gauge_metric_generator(get_value, name, documentation=None):
    class GaugeMetricCollector:
        def __init__(self):
            self.get_value = generator_metrice_value(get_value)

        def collect(self):
            gauge_metric = GaugeMetricFamily(f'pishkhan_restapi_{name}', documentation or f'Value of {name}')
            value = self.get_value()
            if value is not None:
                gauge_metric.add_metric(
                    labels=[f'pishkhan_restapi_{name}_gauge_metric'],
                    value=value,
                    timestamp=now().timestamp(),
                )
            yield gauge_metric

    return GaugeMetricCollector()


def gauge_histogram_metric_generator(get_values, name, documentation=None):
    class GaugeHistogramMetricCollector:
        def __init__(self):
            self.get_value = generator_metrice_value(get_values)

        def collect(self):
            gauge_histogram_metric = GaugeHistogramMetricFamily(f'pishkhan_restapi_{name}', documentation or f'Value of {name}')
            value = self.get_value()
            if value is not None:
                gauge_histogram_metric.add_metric(
                    labels=[f'pishkhan_restapi_{name}_gauge_histogram_metric'],
                    buckets=value,
                    gsum_value=sum(map(lambda item: item[1], value)),
                    timestamp=now().timestamp(),
                )
            yield gauge_histogram_metric

    return GaugeHistogramMetricCollector()


def info_metric_generator(get_info, name, documentation=None):
    class InfoMetricCollector:
        def __init__(self):
            self.get_value = generator_metrice_value(get_info)

        def collect(self):
            info_metric = InfoMetricFamily(f'pishkhan_restapi_{name}', documentation or f'Information of {name}')
            value = self.get_value()
            if value is not None:
                info_metric.add_metric(
                    labels=[f'pishkhan_restapi_{name}_info_metric'],
                    value={f'{k}': dumps(v) for k, v in value.items()},
                    timestamp=now().timestamp(),
                )
            yield info_metric

    return InfoMetricCollector()


def state_set_metric_generator(state_checker, name, documentation=None):
    class StateSetMetric:
        def __init__(self):
            self.get_value = generator_metrice_value(state_checker)

        def collect(self):
            set_state_metric = StateSetMetricFamily(f'pishkhan_restapi_{name}', documentation or f'State of {name}')
            value = self.get_value()
            if value is not None:
                set_state_metric.add_metric(
                    labels=[f'pishkhan_restapi_{name}_state_set_metric'],
                    value={f'{name}_state': value},
                    timestamp=now().timestamp(),
                )
            yield set_state_metric

    return StateSetMetric()



