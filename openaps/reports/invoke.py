
"""
invoke   - generate a report
"""
from __future__ import print_function
from openaps.reports.report import Report
from openaps.exceptions import RetryableCommsException
from openaps import uses

import reporters
import sys
import argparse
import time

# How many times should we retry in case of RetryableCommsException fails?
COMMS_EXCEPTION_RETRYCOUNT = 3
# How long should we wait after a RetryableCommsException, in seconds?
COMMS_RETRY_BACKOFF = 0

def configure_app (app, parser):
  """
  """
  parser._actions[-1].nargs = '+'

def main (args, app):
  # print args.report
  # print app.parser.parse_known_args( )
  requested = args.report[:]
  for spec in requested:
    report =  app.actions.selected(args).reports[spec]
    device = app.devices[report.fields['device']]
    task = app.actions.commands['add'].usages.commands[device.name].method.commands[report.fields['use']]
    # print task.name, task.usage, task.method
    # print device.name, device
    # print report.name, report.fields
    # XXX.bewest: very crude, need to prime the Use's args from the config
    app.parser.set_defaults(**task.method.from_ini(report.fields))
    args, extra = app.parser.parse_known_args( )
    """
    for k, v in report.fields.items( ):
      setattr(args, k, v)
    """
    # print args
    print(report.format_url( ))
    repo = app.git_repo( )

    for attempt in range(COMMS_EXCEPTION_RETRYCOUNT):
      try:
        output = task.method(args, app)
        reporters.Reporter(report, device, task)(output)
        print('reporting', report.name)
        repo.git.add([report.name])
        # XXX: https://github.com/gitpython-developers/GitPython/issues/265o
        # GitPython <  0.3.7, this can corrupt the index
        # repo.index.add([report.name])
        # Don't retry on success
        break
      except RetryableCommsException as e:
        message = 'Raised %s - retry %s of %s' % (e, attempt + 1, COMMS_EXCEPTION_RETRYCOUNT)
        print(report.name, message, file=sys.stderr)
        time.sleep(COMMS_RETRY_BACKOFF)
      except Exception as e:
        message = 'Raised %s' % e
        print(report.name, message, file=sys.stderr)
        # save prior progress in git
        app.epilog( )
        # ensure we still blow up with non-zero exit
        raise
