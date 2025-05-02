# COAA Presentation Tech Notes

## Pre-setup
 - Load separate tabs for each survey question on presentation computer
### Onedrive setup
 - In teams, navigate to web page folder
 - Click 'Sync' button on top options bar
 - Onedrive VMDO folder should sync on local computer
 - Test opening html files from this location

## Web Browser (Chrome)
 - CTRL-Shift-B >>> hides bookmark bar
 - F11 >>> enter / exit full screen

## Auth and tokens
 - If authentication fails, try deleting `token.json`

## Running the script
 - turn on venv `venv/scripts/activate` before running script
 - run with automated data pull -   `python coaa_interactive.py <q1, q2, or q3>`
 - run with data from csv           `python coaa_interactive.py <q#> --csv=<filename.csv>`
 - run with excel data              `python coaa_interactive.py <q#> --excel=<filename.xlsx>`
