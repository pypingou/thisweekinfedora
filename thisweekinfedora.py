#!/usr/bin/env python

"""


This is the cron script querying the data of the past week and generating
the corresponding blog entry.
"""

import json
import calendar
from datetime import datetime
from datetime import timedelta

import requests


DATAGREPPER = 'https://apps.fedoraproject.org/datagrepper/raw'
TOPICS = {
    "update to stable" : 'org.fedoraproject.prod.bodhi.update.request.stable',
    "update to testing" : 'org.fedoraproject.prod.bodhi.update.request.testing',
    "update to testing" : 'org.fedoraproject.prod.bodhi.update.request.testing',
    "build": 'org.fedoraproject.prod.buildsys.build.state.change',
    "FAS user created": 'org.fedoraproject.prod.fas.user.create',
    "Meeting started": 'org.fedoraproject.prod.meetbot.meeting.start',
    "Meeting completed": 'org.fedoraproject.prod.meetbot.meeting.complete',
    "New packages": 'org.fedoraproject.prod.pkgdb.package.new',
    "Retired packages": 'org.fedoraproject.prod.pkgdb.package.retire',
    "Posts on the planet": 'org.fedoraproject.prod.planet.post.new',
    "Edit on the wiki": 'org.fedoraproject.prod.wiki.article.edit'
}

def query_datagrepper(start, end, topic):
    """ Query datagrepper for the provided time period and topic and
    returns the number of events that occured then.
    
    :arg start: a datetime object specifying when the time period to
        query started.
    :arg end: a datetime object specifying when the time period to
        query ended.
    :arg topic: the fedmsg topic to query.

    """
    params = {'start': calendar.timegm(start.timetuple()),
              'end': calendar.timegm(end.timetuple()),
              'topic': topic,
          }
    req = requests.get(DATAGREPPER, params=params)
    json_out = json.loads(req.text)
    return json_out['total']



def get_fedora_activity(date_to):
    """Retrieve the activity in Fedora over the week prior to the
    specified date.
    
    :arg date_to: a datetime object specifying the date and time from
        ending the week to retrieve.
    
    """
    datetime_to = datetime(date_to.year, date_to.month, date_to.day,
                           23, 59) - timedelta(days=1)
    datetime_from = datetime(date_to.year, date_to.month, date_to.day,
                             0, 0) - timedelta(days=7)

    activities = {}
    for topic in TOPICS:
        activities[topic] = query_datagrepper(datetime_from, datetime_to,
                                              TOPICS[topic])

    print "Between %s and %s the activity in Fedora was:" % (
        datetime_from.strftime('%a, %d %b %Y %H:%M:%S'),
        datetime_to.strftime('%a, %d %b %Y %H:%M:%S'))
    for activity in activities:
        print "%s : %s" % (activity.ljust(25),
                           str(activities[activity]).rjust(5))
    return activities


if __name__ == '__main__':
    date_to = datetime(2013, 6, 17)
    get_fedora_activity(date_to)
