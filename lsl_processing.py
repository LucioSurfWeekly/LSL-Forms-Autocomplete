import re


class Mapping:
    def __init__(self, path):
        self.mapping = self.load_mapping(path)

    def load_mapping(self, path):
        mapping = {}
        with open(path) as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                split = line.split(",")
                decoded = split[0].strip()
                encoded = split[1].strip().lower()
                mapping[encoded] = decoded
        return mapping


def crop_top_right(src_img):
    height, width, depth = src_img.shape

    y_start_percent = 0.03
    y_stop_percent = 0.065
    y_start = int(height * y_start_percent)
    y_stop = int(height * y_stop_percent)

    x_start_percent = 0.75
    x_stop_percent = 1.00
    x_start = int(width * x_start_percent)
    x_stop = int(width * x_stop_percent)

    return src_img[y_start:y_stop, x_start:x_stop, :]


def decode_season(season):
    if season.isnumeric():
        return int(season)
    else:
        # season = season.lower()
        if season == "i" or season == "l":
            return 1
        if season == "z":
            return 2
        if season == "e" or season == "m" or season == "w":
            return 3
        if season == "h" or season == "a" or season == "y":
            return 4
        if season == "s":
            return 5
        if season == "b" or season == "g":
            return 6
        if season == "t" or season == "j":
            return 7
    return None


def decode_gamemode(gamemode):
    gamemode = gamemode.lower()
    if gamemode == "g" or gamemode == "9" or gamemode == "c":
        return "Gravspeed"
    if gamemode == "s" or gamemode == "5":
        return "Standard"
    return None


def decode_map(map_mapping, map_encoded):
    map_name = None
    error_msg = None

    map_encoded = map_encoded.replace("0", "o")

    try:
        map_name = map_mapping[map_encoded]
    except KeyError as e:
        error_msg = "key error: " + str(e)

    return map_name, error_msg


def get_is_deathmatch(dm_mapping, stats):
    is_dm = None
    error_msg = None

    map_name = stats["map"]

    try:
        is_dm = dm_mapping[map_name] == "deathmatch"
    except KeyError as e:
        error_msg = "key error: " + str(e)

    return is_dm, error_msg


def clean_time(time_str):
    txt = re.findall(r"[-+]?(?:\d*\.\d+|\d+)", time_str)
    if len(txt) > 0:
        return abs(float(txt[0]))
    else:
        return None


def string_difference(src, target):
    output_list = [li for li in difflib.ndiff(src, target) if li[0] != ' ' and li[0] != '-']
    return len(output_list)

