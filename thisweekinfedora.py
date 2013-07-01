#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""


This is the cron script querying the data of the past week and generating
the corresponding blog entry.
"""

import calendar
import json
import math
import os
import sys
from datetime import datetime
from datetime import timedelta
from multiprocessing import Pool

import pygal
import requests


DATAGREPPER = 'https://apps.fedoraproject.org/datagrepper/raw'
TOPICS = {
    'Updates to stable' : 'org.fedoraproject.prod.bodhi.update.request.stable',
    'Updates to testing' : 'org.fedoraproject.prod.bodhi.update.request.testing',
    'Builds': 'org.fedoraproject.prod.buildsys.build.state.change',
    'FAS user created': 'org.fedoraproject.prod.fas.user.create',
    'Meeting started': 'org.fedoraproject.prod.meetbot.meeting.start',
    'Meeting completed': 'org.fedoraproject.prod.meetbot.meeting.complete',
    'New packages': 'org.fedoraproject.prod.pkgdb.package.new',
    'Retired packages': 'org.fedoraproject.prod.pkgdb.package.retire',
    'Posts on the planet': 'org.fedoraproject.prod.planet.post.new',
    'Edit on the wiki': 'org.fedoraproject.prod.wiki.article.edit'
}
BLACK_LIST_USERS = ['zodbot', 'bodhi']


def query_datagrepper(start, end, topic, full=False):
    """ Query datagrepper for the provided time period and topic and
    returns the number of events that occured then.

    :arg start: a datetime object specifying when the time period to
        query started.
    :arg end: a datetime object specifying when the time period to
        query ended.
    :arg topic: the fedmsg topic to query.
    :kwarg full: a boolean specifying whether to retrieve all the
        messages or not.

    """
    if not full:
        params = {'start': calendar.timegm(start.timetuple()),
                  'end': calendar.timegm(end.timetuple()),
                  'topic': topic,
                  'meta': 'usernames',
                  }
        req = requests.get(DATAGREPPER, params=params)
        json_out = json.loads(req.text)
        info = '{0}\r'.format(topic)
        sys.stdout.write(info)
        sys.stdout.flush()
        json_out = json_out['total']
    else:
        messages = []
        cnt = 1
        while True:
            params = {'start': calendar.timegm(start.timetuple()),
                      'end': calendar.timegm(end.timetuple()),
                      'rows_per_page': 100,
                      'page': cnt,
                      'topic': topic,
                      'meta': 'usernames',
                  }
            req = requests.get(DATAGREPPER, params=params)
            json_out = json.loads(req.text)
            info = '{0} - page: {1}/{2}\r'.format(
                topic, cnt, json_out['pages'])
            sys.stdout.write(info)
            sys.stdout.flush()
            messages.extend(json_out['raw_messages'])
            cnt += 1
            if cnt > int(json_out['pages']):
                break
        json_out = messages
    return json_out


def get_fedora_contributors(datetime_to, datetime_from):
    """ Retrieve the top contributors for that week for each topics

    :arg datetime_to: a datetime object specifying the starting date and
        time of the week to retrieve.
    :arg datetime_from: a datetime object specifying the ending date and
        time of the week to retrieve.

    """
    contributors = {}
    topics = TOPICS.copy()
    # ignore user creation in top users
    if 'FAS user created' in topics:
        del(topics['FAS user created'])

    print 'Get contributions of week {0}'.format(datetime_from)

    for topic in topics:
        messages = query_datagrepper(
            datetime_from, datetime_to, TOPICS[topic], full=True)
        users = {}
        for msg in messages:
            for user in msg['meta']['usernames']:
                if user in BLACK_LIST_USERS:
                    continue
                if user in users:
                    users[user] += 1
                else:
                    users[user] = 1

        # invert dict
        ord_users = {}
        for key in users:
            if users[key] in ord_users:
                ord_users[users[key]].append(key)
            else:
                ord_users[users[key]] = [key]

        contributors[topic] = {}
        for key in sorted(ord_users.keys(), reverse=True)[:3]:
            contributors[topic][key] = ord_users[key]

    print '\n'

    return contributors


def get_fedora_activity(datetime_to, datetime_from):
    """ Retrieve the activity in Fedora over the week prior to the
    specified date.

    :arg datetime_to: a datetime object specifying the starting date and
        time of the week to retrieve.
    :arg datetime_from: a datetime object specifying the ending date and
        time of the week to retrieve.

    """
    print 'Get activities of week {0}'.format(datetime_from)

    activities = {}
    for topic in TOPICS:
        activities[topic] = query_datagrepper(datetime_from, datetime_to,
                                              TOPICS[topic])
    print '\n'

    return activities


def create_blog_post(datetime_to, datetime_from, activities,
        previous_activities, top_contributors):
    """ Create a new blog post.

    :arg datetime_to: a datetime object specifying the starting date and
        time of the week to retrieve.
    :arg datetime_from: a datetime object specifying the ending date and
        time of the week to retrieve.
    :arg activities: a dictionnary giving for each activity the number
        of time it occured in the period of time.
    :arg previous_activities: a dictionnary giving information about the
        information the week before.
    :arg top_contributors: a dictionnary giving information about the
        top contributors of the week.

    """

    blog_entry = ''
    for activity in sorted(activities.keys()):
        diff = 'NA'
        if activity in previous_activities:
            old_activity = previous_activities[activity]
            if old_activity == 0:
                diff = 'NA'
            else:
                pcent = activities[activity] * 100 / float(old_activity) - 100
                plus_sign = ['-', '+'][pcent > 0]
                diff = "{0}{1:05.2f}%".format(plus_sign, math.fabs(pcent))

        blog_entry += '{0} {1}  {2}\n'.format(
            activity.ljust(20),
            str(activities[activity]).rjust(10),
            diff.rjust(15))

    top_user_entry = ''
    for activity in sorted(top_contributors.keys()):
        entry = ''
        cnt = 0
        for top in sorted(top_contributors[activity].keys(), reverse=True):
            for contrib in sorted(top_contributors[activity][top]):
                if cnt >= 3:
                    break
                entry += '{0} ({1}), '.format(contrib, top)
                cnt += 1
        top_user_entry += '{0} {1} {2}\n'.format(
            activity.ljust(20),
            ' ' * 5,
            entry.rsplit(',', 1)[0].strip(),
        )

    content = """.. link:
.. description:
.. date: {date_now}
.. title: Activities from {date_from} to {date_to}
.. slug: {slug_date}

Activities
----------

======================    ========   ======================
Activities                 Amount     Diff to previous week
======================    ========   ======================
{content}
======================    ========   ======================

Top contributors of the week
----------------------------

======================    ==============
Activites                  Contributors
======================    ==============
{top_user}
======================    ==============

""".format(
    date_now=datetime_to.strftime('%Y/%m/%d %H:%M:%S'),
    date_from=datetime_from.strftime('%a, %d %b %Y'),
    date_to=datetime_to.strftime('%a, %d %b %Y'),
    slug_date=datetime_to.strftime('%Y_%m_%d'),
    content=blog_entry.strip(),
    top_user = top_user_entry.strip(),
    )

    file_name = '{0}.txt'.format(datetime_to.strftime('%Y_%m_%d'))
    with open(os.path.join('posts', file_name), 'w') as stream:
        stream.write(content)


def save_activities(datetime_to, activities):
    """ Add the activities of the week to the json string in the file
    `evolution.txt` which contains the activities week after week.

    :arg datetime_to: a datetime object specifying the starting date and
        time of the week to retrieve.
    :arg activities: a dictionnary giving for each activity the number
        of time it occured in the period of time.

    """

    date_str = datetime_to.strftime('%Y_%m_%d')
    file_name = 'evolution.txt'

    if os.path.exists(file_name):
        with open(file_name) as stream:
            output = json.loads(stream.read())
    else:
        output = {}

    for activity in sorted(activities.keys()):
        if activity not in output:
            output[activity] = {date_str: activities[activity]}
        else:
            output[activity][date_str] = activities[activity]

    with open(file_name, 'w') as stream:
        stream.write(json.dumps(output))

    return output


def generate_svg(evolution):
    """ Reads in the json string contained in `evolution.txt` and
    generate the evolution graph from it using pygal.

    :arg evolution: a dictionnary representing the evolution of the
        activities over time.

    """
    file_name = 'evolution.txt'

    line_chart = pygal.Line()
    line_chart.title = 'Evolution of the activities of the contributors over time'
    lbls = []
    for activity in sorted(evolution.keys()):
        values = []
        for key in sorted(evolution[activity].keys()):
            val = evolution[activity][key]
            if val == 0:
                values.append(val)
            else:
                values.append(math.log10(val))
        line_chart.add(activity, values)
        if not lbls:
            lbls = sorted(evolution[activity].keys())
    line_chart.x_labels = lbls
    line_chart.render_to_file(os.path.join('themes', 'thisweekinfedora',
                                           'assets', 'evolution.svg'))


def process_week(date_to):
    """ Main function.
    """
    datetime_to = datetime(date_to.year, date_to.month, date_to.day,
                           23, 59) - timedelta(days=1)
    datetime_from = datetime(date_to.year, date_to.month, date_to.day,
                             0, 0) - timedelta(days=7)
    print 'Process week of {0}'.format(datetime_from)

    activities = get_fedora_activity(datetime_to, datetime_from)

    top_contributors = get_fedora_contributors(
        datetime_to, datetime_from)

    evolution = save_activities(datetime_to, activities)

    generate_svg(evolution)

    previous_activities = get_fedora_activity(
        datetime_to - timedelta(days=7),
        datetime_from - timedelta(days=7)
    )


    create_blog_post(datetime_to, datetime_from, activities,
                     previous_activities, top_contributors)

def generate_history():
    """ Generate all the dates from December 31 2012 and process each
    week using multithreading to speed things up a little bit.
    """
    date_from = datetime(2012, 12, 31)
    date_to_process = date_from
    dates = []
    while date_to_process < datetime.today():
        dates.append(date_to_process)
        date_to_process = date_to_process + timedelta(days=7)
    p = Pool(5)
    p.map(process_week, dates)


if __name__ == '__main__':
    #generate_history()
    process_week(datetime(2013, 7, 1))
