# csv2yt2mp3 (CSV to YouTube to MP3)
## Description
Reads a CSV file containing a list of songs, search those songs on YouTube, download them and convert them to MP3 files.

## CSV file format
The CSV file is required to have 3 columns, exactly named: song_name, artist_name and album.

Example:
```
song_name,artist_name,album
Yesterday,"The Beatles",Help!
"The Kids Aren't Alright","The Offspring",Americana
```

## Install
1. cd csv2yt2mp3
1. python3 -m venv .venv
1. source .venv/bin/activate
1. pip install -r requirements

## Usage
```Usage:	python csv2yt2mp3.py CSV_FILE_PATH```