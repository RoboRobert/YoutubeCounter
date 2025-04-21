import requests
import aniso8601
import datetime
import argparse
from dotenv import load_dotenv
import os

load_dotenv()

api_key: str = os.getenv("API_KEY")

game_grumps_id: str = "UC9CuvdOVfMPvKCiwdGKL3cQ"  # Game grumps channel ID

critical_role_id: str = "UCpXBGqwsBkpvcYjsJBQ7LEQ"  # Critical Role channel ID

big_a_id: str = "UCdBXOyqr8cDshsp7kcKDAkg"  # Big A channel ID

yt_api: str = "https://www.googleapis.com/youtube/v3"  # Youtube search API


# Gets the total amount of playtime for a specified channel ID or playlist ID
def get_total_playtime(type: str, id: str):
    total_playtime = datetime.timedelta(seconds=0)

    playlist_id: str = id
    # If a channel is specified, query the channel to get the ID of its uploads playlist
    if type == "c":
        # Gets the contentDetails for a specified channel ID
        uploads_response: list = requests.get(
            f"{yt_api}/channels",
            params={
                "key": api_key,
                "id": id,
                "part": "contentDetails",
            },
        ).json()

        # Gets the ID of the uploads playlist from the contentDetails of the specified channel.
        playlist_id = uploads_response["items"][0]["contentDetails"][
            "relatedPlaylists"
        ]["uploads"]

    # Queries the specified playlist for the first 50 videos
    uploads_page: list = requests.get(
        f"{yt_api}/playlistItems",
        params={
            "key": api_key,
            "playlistId": playlist_id,
            "part": "contentDetails",
            "maxResults": 50,
        },
    ).json()

    # Extract all the video IDs and put them into a comma separated list
    videos: str = ""
    for video_item in uploads_page["items"]:
        videos += video_item["contentDetails"]["videoId"] + ","
    # Trim the trailing comma
    videos = videos[:-1]

    # Get the data for the videos from the first request
    videos_page: list = requests.get(
        f"{yt_api}/videos",
        params={
            "key": api_key,
            "part": "contentDetails",
            "id": videos,
        },
    ).json()

    # Add the duration of the returned videos to the running total.
    for video in videos_page["items"]:
        total_playtime += aniso8601.parse_duration(video["contentDetails"]["duration"])

    # Get the token for the next page of the data.
    try:
        next_page: str = uploads_page["nextPageToken"]
    except KeyError:
        next_page: str = ""

    # Loop until there is no next page.
    while next_page != "":
        # Usese the next page token to get the next batch of video IDs to process
        uploads_page = requests.get(
            f"{yt_api}/playlistItems",
            params={
                "key": api_key,
                "playlistId": playlist_id,
                "pageToken": next_page,
                "part": "contentDetails",
                "maxResults": 50,
            },
        ).json()

        # Extract all the video IDs and put them into a comma separated list
        videos = ""
        for video_item in uploads_page["items"]:
            videos += video_item["contentDetails"]["videoId"] + ","
        # Trim the trailing comma
        videos = videos[:-1]

        # Get the data for all the videos
        videos_page: list = requests.get(
            f"{yt_api}/videos",
            params={
                "key": api_key,
                "part": "contentDetails",
                "id": videos,
            },
        ).json()

        # Add the duration of the returned videos to the running total.
        for video in videos_page["items"]:
            total_playtime += aniso8601.parse_duration(
                video["contentDetails"]["duration"]
            )

        print(total_playtime)

        # Try to get the next page to read from the returned data.
        try:
            next_page: str = uploads_page["nextPageToken"]
        # If the nextPageToken doesn't exist, break out of the loop.
        except KeyError:
            break

    return str(total_playtime)


# If there are fewer than two arguments specified, throw an error.
parser = argparse.ArgumentParser(
    prog="YoutubeLengthCount",
    description="This program takes in either a Youtube Channel ID or playlist ID and counts the total length of all the videos contained within.",
    epilog="Test",
)

parser.add_argument(
    "type",
    choices=["c", "p"],
    help="Specifies whether a channel or playlist ID will be entered. c for channel, p for playlist.",
)
parser.add_argument("id", help="Specifies the ID entered.")
args = parser.parse_args()

print(args)

type: str = args.type
id: str = args.id

print(f"Total Playtime: {get_total_playtime(args.type, args.id)}")
