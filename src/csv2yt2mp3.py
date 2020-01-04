#!/bin/env python

import eyed3
import pafy
import youtube_dl
import youtube_search

import csv
import glob
import json
import os
import pathlib
import sys

import cfg


def usage():
	print("Usage:\tpython csv2yt2mp3.py CSV_FILE_PATH DEST_FOLDER")


def get_arguments():
	if len(sys.argv) < 2:
		usage()
		exit(1)
	csv_file_path = sys.argv[1]
	if not os.path.exists(csv_file_path) or not csv_file_path.endswith(".csv"):
		usage()
		exit(1)
	return csv_file_path


def get_search_query(csv_row):
	return " - ".join([
		csv_row["artist_name"], csv_row["album"], csv_row["song_name"]
	])


def parse_duration(duration):
	ftr = [3600,60,1]
	return sum([
		a * b
		for a,b in zip(ftr, map(int, duration.split(':')))
	]) / 60.0


def take_best_result(search_result):
	for i, video_info in enumerate(search_result):
		print("Processing video ({}): {}".format(i, video_info))
		if not "link" in video_info:
			print("ERROR: URL not found in response")
			continue
		print("Video found: {}".format(video_info))

		print("Getting metadata...")
		video_url = cfg.base_url + video_info.get("link", "")

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
	return row['song_name'] + ".mp3"


def write_metadata(mp3_file_path, row):
	audiofile = eyed3.load(mp3_file_path)
	audiofile.tag.artist = row["artist_name"]
	audiofile.tag.album = row["album"]
	audiofile.tag.album_artist = row["artist_name"]
	audiofile.tag.title = row["song_name"]

	audiofile.tag.save()


def main():
	with youtube_dl.YoutubeDL(cfg.ydl_opts) as ydl:
		csv_file_path = get_arguments()
		mp3_files = list_mp3_files(".")
		if len(mp3_files) > 0:
			print("ERROR: please, remove all mp3 files from the current directory first")
			exit(1)
		print("Opening CSV: {}".format(csv_file_path))
		with open(csv_file_path, newline='') as csv_file:
			reader = csv.DictReader(csv_file)
			for row in reader:
				search_query = get_search_query(row)

				print("\n=== Searching {} ===".format(search_query))
				new_mp3_file_name = get_mp3_file_name(row)
				mp3_dir = os.path.join(
					cfg.download_dir, row['artist_name'], row['album']
				)
				mp3_file_path = os.path.join(mp3_dir, new_mp3_file_name)
				if os.path.exists(mp3_file_path):
					print("ERROR: song {} already exists".format(mp3_file_path))
					continue

				search_result = youtube_search.YoutubeSearch(
					search_query, max_results=10
				).to_json()
				search_result = json.loads(search_result)
				search_result = search_result.get("videos", [])
				if not search_result:
					print("Search results are empty")
					continue

				video_url = take_best_result(search_result)
				if video_url is None:
					print("ERROR: no video found for search {} with results {}".format(
						search_query, search_result
					))
					continue

				print("Downloading video: {}".format(video_url))
				ydl.download([video_url])
				mp3_files = list_mp3_files(".")
				if  not mp3_files or len(mp3_files) > 1:
					print("ERROR: more than one file (or none) in current directory")
					exit(1)
				mp3_file_name = mp3_files[0]
				print("Video downloaded: {}".format(mp3_file_name))

				print("Creating directories...")
				pathlib.Path(mp3_dir).mkdir(parents=True, exist_ok=True)

				print("Saving to {}".format(mp3_file_path))
				os.rename(mp3_file_name, os.path.join(mp3_file_path))

				print("Updating file metadata...")
				write_metadata(mp3_file_path, row)


if __name__ == "__main__":
	main()
