#!/bin/env python

import eyed3
import pafy
import youtube_dl
import youtube_search

import argparse
import csv
import glob
import json
import os
import pathlib
import shutil
import time

import cfg


def csv_file_type(astring):
    if not os.path.exists(astring) or not astring.endswith(".csv"):
        raise argparse.ArgumentTypeError("Incorrect file")
    return astring


def get_arguments():
	parser = argparse.ArgumentParser()
	subparsers = parser.add_subparsers(help='Command to be executed')
	subparsers.required = True
	subparsers.dest = 'cmd'

	import_parser = subparsers.add_parser("import")
	import_parser.add_argument(
		'--file', dest='csv_file',
		type=csv_file_type, default=None, required=True,
		help='CSV file to import'
	)

	download_parser = subparsers.add_parser("download")
	download_parser.add_argument(
		'--artist', dest='artist_name',
		type=str, default=None, required=True,
		help='Name of the artist'
	)
	download_parser.add_argument(
		'--album', dest='album_name',
		type=str, default=None, required=True,
		help='Name of the album'
	)
	download_parser.add_argument(
		'--track', dest='track_name',
		type=str, default=None, required=True,
		help='Name of the track'
	)

	return parser.parse_args()


def get_search_query(csv_row):
	return " - ".join([
		csv_row["artist_name"], csv_row["song_name"]
	])


def parse_duration(duration):
	ftr = [3600,60,1]
	return sum([
		a * b
		for a,b in zip(ftr, map(int, duration.split(':')))
	]) / 60.0


def url_is_playlist(url):
	return "list=" in url


def take_best_result(search_result):
	for i, video_info in enumerate(search_result):
		print("Processing video ({}): {}".format(i, video_info))
		if not "link" in video_info:
			print("ERROR: URL not found in response")
			continue
		print("Video found: {}".format(video_info))

		print("Getting metadata...")
		video_url = cfg.base_url + video_info.get("link", "")

		if url_is_playlist(video_url):
			print("ERROR: url is a playlist")
			continue

		try:
			video = pafy.new(video_url)
			video_duration = parse_duration(video.duration)
			if video_duration > cfg.max_minutes:
				print("ERROR: video is too long: {} (max: {})".format(
					video_duration, cfg.max_minutes
				))
				continue

			print("Title: {}, Duration: {}".format(video.title, video.duration))
			return video_url
		except Exception as e:
			print("ERROR: couldn't get metadata: {}".format(str(e)))

		return None


def list_mp3_files(path):
	return [
		filename for filename in glob.glob(os.path.join(path, "*.mp3"))
	]


def get_mp3_file_name(row):
	return row['song_name'].replace("/", "-") + ".mp3"


def get_mp3_dir(row):
	return os.path.join(
		cfg.download_dir,
		row['artist_name'].replace("/", ""),
		row['album'].replace("/", "")
	)


def write_metadata(mp3_file_path, row):
	audiofile = eyed3.load(mp3_file_path)
	audiofile.tag.artist = row["artist_name"]
	audiofile.tag.album = row["album"]
	audiofile.tag.album_artist = row["artist_name"]
	audiofile.tag.title = row["song_name"]

	audiofile.tag.save()


def video_download(video_url):
	attempts = 1
	with youtube_dl.YoutubeDL(cfg.ydl_opts) as ydl:
		while attempts <= cfg.attempts:
			try:
				print("Attempt {}".format(attempts))
				ydl.download([video_url])
			except Exception as e:
				wait_time = cfg.wait_time[attempts - 1]
				print("ERROR: {}\nWaiting {} seconds".format(str(e), wait_time))
				time.sleep(wait_time)
			finally:
				return


def download_song(song_info):
	search_query = get_search_query(song_info)

	print("\n=== Searching {} ===".format(search_query))
	new_mp3_file_name = get_mp3_file_name(song_info)
	mp3_dir = get_mp3_dir(song_info)
	mp3_file_path = os.path.join(mp3_dir, new_mp3_file_name)
	if os.path.exists(mp3_file_path):
		print("ERROR: song {} already exists".format(mp3_file_path))
		return

	search_result = youtube_search.YoutubeSearch(
		search_query, max_results=10
	).to_json()
	search_result = json.loads(search_result)
	search_result = search_result.get("videos", [])
	if not search_result:
		print("Search results are empty")
		return

	video_url = take_best_result(search_result)
	if video_url is None:
		print("ERROR: no video found for search {} with results {}".format(
			search_query, search_result
		))
		return

	print("Downloading video: {}".format(video_url))
	video_download(video_url)

	mp3_files = list_mp3_files(".")
	if  not mp3_files or len(mp3_files) > 1:
		print("ERROR: more than one file (or none) in current directory")
		exit(1)
	mp3_file_name = mp3_files[0]
	print("Video downloaded: {}".format(mp3_file_name))

	print("Creating directories...")
	pathlib.Path(mp3_dir).mkdir(parents=True, exist_ok=True)

	print("Saving to {}".format(mp3_file_path))
	shutil.move(mp3_file_name, mp3_file_path)

	print("Updating file metadata...")
	write_metadata(mp3_file_path, song_info)


if __name__ == "__main__":
	args = get_arguments()
	mp3_files = list_mp3_files(".")
	if len(mp3_files) > 0:
		print("ERROR: please, remove all mp3 files from the current directory first")
		exit(1)

	if args.cmd == "import":
		print("Opening CSV: {}".format(args.csv_file))
		with open(args.csv_file, newline='') as csv_file:
			reader = csv.DictReader(csv_file)
			for song_info in reader:
				download_song(song_info)
	elif args.cmd == "download":
		song_info = {}
		song_info["artist_name"] = args.artist_name
		song_info["album"] = args.album_name
		song_info["song_name"] = args.track_name
		download_song(song_info)
