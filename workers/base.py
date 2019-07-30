import functools
import logging

import tenacity

import logger

_LOGGER = logger.get(__name__)


class BaseWorker:
  def __init__(self, command_timeout, **args):
    self.command_timeout = command_timeout
    for arg, value in args.items():
      setattr(self, arg, value)
    self._setup()

  def _setup(self):
    return

  def format_discovery_topic(self, mac, *sensor_args):
    node_id = mac.replace(':', '-')
    object_id = '_'.join([repr(self), *sensor_args])
    return '{}/{}'.format(node_id, object_id)

  def format_discovery_id(self, mac, *sensor_args):
    return 'bt-mqtt-gateway/{}'.format(self.format_discovery_topic(mac, *sensor_args))

  def format_discovery_name(self, *sensor_args):
    return '_'.join([repr(self), *sensor_args])

  def format_topic(self, *topic_args):
    return '/'.join([self.topic_prefix, *topic_args])

  def __repr__(self):
    return self.__module__.split(".")[-1]


def retry(_func=None, *, exception_type=Exception):
  def log_retry(retry_state):
    _LOGGER.debug(
        'Call to %s failed the %s time (%s). Retrying in %s seconds',
        '.'.join((retry_state.fn.__module__, retry_state.fn.__name__)),
        retry_state.attempt_number,
        type(retry_state.outcome.exception()).__name__,
        getattr(retry_state.next_action, 'sleep'))

  def decorator_retry(func):
    @functools.wraps(func)
    def wrapped_retry(*args, **kwargs):
      retryer = tenacity.Retrying(
          wait=tenacity.wait_exponential(min=4),
          retry=tenacity.retry_if_exception_type(exception_type),
          stop=tenacity.stop_after_attempt(3),
          reraise=True,
          before_sleep=log_retry)
      return retryer(func, *args, **kwargs)
    return wrapped_retry

  if _func:
    return decorator_retry(_func)
  else:
    return decorator_retry
