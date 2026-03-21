@echo off
REM Scheduled task script - pushes TSM data to the cloud every 30 minutes
REM Set up via Windows Task Scheduler

set TSM_PUSH_API_KEY=TQoc8Z2x1JRqzMc7KsrTtoLAdQlwDs9LemdvTsQ3Aqk
set TSM_CLOUD_URL=https://tsm-tracker.up.railway.app

cd /d D:\Projects\tsm-tracker
python pusher.py >> D:\Projects\tsm-tracker\push.log 2>&1
