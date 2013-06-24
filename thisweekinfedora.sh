#!/bin/sh

# Run the python worked
python ./thisweekinfedora.py

# Remove old files
rm -rf output/

# Rebuild the website
nikola build

