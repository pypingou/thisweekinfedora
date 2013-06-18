#!/bin/sh

# Run the python worked
/usr/bin/python ./thisweekinfedora.py

# Remove old files
rm -rf output/

# Rebuild the website
nikola build

