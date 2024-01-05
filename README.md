# South Dakota Legislature data archive
This repo has data files sourced from the [South Dakota Legislature website](https://sdlegislature.gov/) with information on sessions, bills, legislators, committees, subcommittees, votes, audio files, documents, etc., from 1997 to present.

_Updated January 05, 2024_

## The data

### Sessions (40)
JSON files with details about each session, slugged by session ID, live in [`data/sessions`](data/sessions).

See also [`crawler/session-dates.json`](crawler/session-dates.json), a file I made with the start and end dates for each legislative session.

### Bills (16,069)
JSON files with details about each bill, slugged by bill ID and including full text of each version and data on votes, live in [`data/bills`](data/bills).

### Legislator Profiles (4,223)
JSON files with details about each legislator profile, slugged by the legislator's session profile ID, live in [`data/legislators`](data/legislators). This is data on a legislator's profile during a particular session; legislators who serve for more than one session are represented in more than one file.

See also [`data/legislators/legislators-historical.json`](data/legislators/legislators-historical.json), which pulls data from the canonical ["Historical Listing"](https://sdlegislature.gov/Legislators/Historical) page for legislators, and [`crawler/sd-legislator-xwalk.csv`](crawler/sd-legislator-xwalk.csv), a file I made to map each legislator session profile ID to that legislator's canonical record. (The value attached to the `legislator_canonical_id` key in each JSON file is derived from this lookup.)

### Committees (1,014)
JSON files with details about each committee, slugged by committee ID, live in [`data/committees`](data/committees).

## Running the crawler
Object classes -- `Session` `Bill`, `LegislatorProfile` and `Committee` -- are defined in [`crawler/models.py`](crawler/models.py).

The code to crawl each session and conditionally write data to file is in [`main.py`](crawler/main.py). (Only new data, or data about the current session, is written to file.)

To run the script, you'll first need to install two dependencies, `requests` and `bs4`, into a virtual environment using your favorite dependency management tools.