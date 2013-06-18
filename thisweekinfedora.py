#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""


This is the cron script querying the data of the past week and generating
the corresponding blog entry.
"""

import calendar
import json
import os
from datetime import datetime
from datetime import timedelta

import requests


DATAGREPPER = 'https://apps.fedoraproject.org/datagrepper/raw'
TOPICS = {
    "Updates to stable" : 'org.fedoraproject.prod.bodhi.update.request.stable',
    "Updates to testing" : 'org.fedoraproject.prod.bodhi.update.request.testing',
    "Updates to testing" : 'org.fedoraproject.prod.bodhi.update.request.testing',
    "Builds": 'org.fedoraproject.prod.buildsys.build.state.change',
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



def get_fedora_activity(datetime_to, datetime_from):
    """ Retrieve the activity in Fedora over the week prior to the
    specified date.

    :arg datetime_to: a datetime object specifying the starting date and
        time of the week to retrieve.
    :arg datetime_from: a datetime object specifying the ending date and
        time of the week to retrieve.

    """
    #print datetime_from, datetime_to

    activities = {}
    for topic in TOPICS:
        activities[topic] = query_datagrepper(datetime_from, datetime_to,
                                              TOPICS[topic])

    return activities


def create_blog_post(datetime_to, datetime_from, activities,
        previous_activities):
    """ Create a new blog post.

    :arg datetime_to: a datetime object specifying the starting date and
        time of the week to retrieve.
    :arg datetime_from: a datetime object specifying the ending date and
        time of the week to retrieve.
    :arg activities: a dictionnary giving for each activity the number
        of time it occured in the period of time.
    :arg previous_activities: a dictionnary giving information about the
        information the week before.

    """

    blog_entry = ""
    for activity in sorted(activities.keys()):
        diff = 'NA'
        if activity in previous_activities:
            old_activity = previous_activities[activity]
            diff = "{0:5.2f}%".format(
                (activities[activity] * 100) / float(old_activity))

        blog_entry += "{0} {1}  {2}\n".format(
            activity.ljust(20),
            str(activities[activity]).rjust(10),
            diff.rjust(15))

    content = """.. link:
.. description:
.. date: {date_now}
.. title: Activities from {date_from} to {date_to}
.. slug: {slug_date}

======================    ========   ======================
Activities                 Amount     Diff to previous week
======================    ========   ======================
{content}
======================    ========   ======================

""".format(
    date_now=datetime.utcnow().strftime('%Y/%m/%d %H:%M:%S'),
    date_from=datetime_from.strftime('%a, %d %b %Y'),
    date_to=datetime_to.strftime('%a, %d %b %Y'),
    slug_date=datetime_to.strftime('%Y_%m_%d'),
    content=blog_entry.strip())

    file_name = '{0}.txt'.format(datetime_to.strftime('%Y_%m_%d'))
    with open(os.path.join('posts', file_name), 'w') as stream:
        stream.write(content)


def save_activities(datetime_to, activities):
    """ Save the activities of the week into a json string in a file in
    the `data` directory.

    :arg datetime_to: a datetime object specifying the starting date and
        time of the week to retrieve.
    :arg activities: a dictionnary giving for each activity the number
        of time it occured in the period of time.

    """
    if not os.path.exists('data'):
        os.mkdir('data')

    file_name = '{0}.txt'.format(datetime_to.strftime('%Y_%m_%d'))
    with open(os.path.join('data', file_name), 'w') as stream:
        stream.write(json.dumps(activities))


def main(date_to):
    """ Main function.
    """
    datetime_to = datetime(date_to.year, date_to.month, date_to.day,
                           23, 59) - timedelta(days=1)
    datetime_from = datetime(date_to.year, date_to.month, date_to.day,
                             0, 0) - timedelta(days=7)
    #print datetime_from, datetime_to

    activities = get_fedora_activity(datetime_to, datetime_from)

    save_activities(datetime_to, activities)

    previous_activities = get_fedora_activity(
        datetime_to - timedelta(days=7),
        datetime_from - timedelta(days=7)
    )

    create_blog_post(datetime_to, datetime_from, activities,
                     previous_activities)


if __name__ == '__main__':
    #date_to = datetime(2013, 6, 17)
    #date_to = datetime(2013, 6, 10)
    #date_to = datetime(2013, 6, 3)
    for date_to in [datetime(2013, 5, 27),
                    datetime(2013, 6, 3),
                    datetime(2013, 6, 10),
                    datetime(2013, 6, 17)]:
        main(date_to)
