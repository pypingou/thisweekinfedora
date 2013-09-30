#!/bin/sh

git pull --rebase

# Run the python worked
python ./thisweekinfedora.py

# Remove old files
rm -rf output/

# Rebuild the website
nikola build

DATE=`date +"%Y_%m_%d" --date "now - 1 day"`

git add posts/$DATE.txt
git add evolution.txt
git add themes/thisweekinfedora/assets/evolution.svg
git commit -m "Weekly update"
git push

