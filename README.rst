This week in Fedora
===================

:Author: Pierre-Yves Chibon <pingou@pingoured.fr>


.. _datagrepper: https://apps.fedoraproject.org/datagrepper/

This week in Fedora is a website providing weekly news about the activities of
the contributors to the `Fedora project <http://fedoraproject.org>`_ using
the information collected by `fedmsg <http://www.fedmsg.com>`_ and made
available via `datagrepper`_


Get this project:
-----------------
Source:  https://github.com/pypingou/thisweekinfedora


Dependencies:
-------------
.. _python: http://www.python.org
.. _python-requests: http://docs.python-requests.org/en/latest/
.. _nikola: http://nikola.ralsina.com.ar/
.. _pygal: http://pygal.org/

The project is a website providing weekly updates and statistics about the
activity of the contributors of the community. The website is built using
`nikola`_ and the data is aggregated from `datagrepper`_ using
`python-requests`_.

The svg graph representing the evolution of the activities is generated using
the `pygal`_ library.


The dependency list is therefore:

- `python`_ (tested on 2.6 and 2.7)
- `python-requests`_
- `nikola`_
- `pygal`_


License:
--------

This project is licensed GPLv3+.
