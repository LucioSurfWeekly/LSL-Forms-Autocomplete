import difflib
from datetime import datetime
import numpy as np
import lsl_gfycat



def parse_vsgm(text_bounds):
    error_msg = None
    data = {"version": None, "season": None, "gamemode": None, "map": None}

    target_string = "lucio surf"
    target_line = None
    for text, bound in text_bounds:
        if string_difference(text, target_string) <= 2:
            target_line = text
            break

    if target_line is None:
        error_msg = "Could not locate verson, season, gamemode, map header."
    else:
        # target_line = target_line.replace(" ", "")

        try:
            # version = target_line.split(" ")[2][0:4]
            # season_encoded = target_line[-4]
            # gamemode_encoded = target_line[-3]
            # map_encoded = target_line[-2:]

            target_line = target_line.replace(" ", "")
            season_encoded = target_line[-4]
            gamemode_encoded = target_line[-3]
            map_encoded = target_line[-2:]
            version = target_line[target_line.index('v'):-5]

            data["version"] = version
            data["season"] = decode_season(season_encoded)
            data["gamemode"] = decode_gamemode(gamemode_encoded)
            data["map"], error_msg = decode_map(map_encoded)
        except IndexError as e:
            error_msg = str(e)

    return data, error_msg


def parse_time(text):
    text = text.replace('o', "0")
    time = clean_time(text)
    return time


def parse_top_right(images):
    img = images[-1]
    top_right_img = crop_top_right(img)
    # cv2_imshow(top_right_img)
    text_bounds = scan_img(top_right_img)
    data, error_msg = parse_vsgm(text_bounds)
    return data, error_msg


def get_stats(gfycat_url):
    stats = {"version": None, "season": None, "gamemode": None, "map": None, "time": None, "message": None}

    timer = datetime.now()
    # parse gfycat url, convret to api url
    data_url, error_msg = get_data_url(gfycat_url)
    if error_msg is not None:
        stats["message"] = f"Could not parse gyfcat url: {gfycat_url}. Error msg: \"{error_msg}\""
        return stats
    print("Timer - get_data_url:", datetime.now() - timer)

    timer = datetime.now()
    # request json info from api url
    data, error_msg = get_gif_info(data_url)
    if error_msg is not None:
        stats["message"] = f"Could not open gyfcat api url: {data_url}. Error msg: \"{error_msg}\""
        return stats
    print("Timer - get_gif_info:", datetime.now() - timer)

    timer = datetime.now()
    # download last from run submission video
    frames, error_msg = get_image_from_url(data["gfyItem"]["mp4Url"], num_frames=12, stride=10)
    if error_msg is not None:
        stats["message"] = f"Could not frames from url: {data_url}. Error msg: \"{error_msg}\""
        return stats
    print("Timer - get_image_from_url:", datetime.now() - timer)

    timer = datetime.now()
    # get data from top-right part of image
    top_right_data, error_msg = parse_top_right(frames)
    stats["version"] = top_right_data["version"]
    stats["season"] = top_right_data["season"]
    stats["gamemode"] = top_right_data["gamemode"]
    stats["map"] = top_right_data["map"]
    if error_msg is not None:
        stats["message"] = f"Error reading top-right part of image: {data_url}. Error msg: \"{error_msg}\""
    print("Timer - parse_top_right:", datetime.now() - timer)

    timer = datetime.now()
    # get data from top-left part of image
    top_left_data, error_msg = parse_top_center(frames, stats)
    stats["time"] = top_left_data["time"]
    if error_msg is not None:
        stats["message"] = f"Error reading top-center part of image: {data_url}. Error msg: \"{error_msg}\""
    print("Timer - parse_top_center:", datetime.now() - timer)

    return stats