import sys

sys.path.insert(1, 'lsl_autocomplete')
import difflib
from datetime import datetime
import re
import cv2
import os
import requests
from paddleocr import PaddleOCR, draw_ocr


#########################
#         ocr           #
#########################


class OCREngine:

    def __init__(self):
        self.MODEL_DIR = "./models/"
        self.det_url = "https://paddleocr.bj.bcebos.com/PP-OCRv3/english/en_PP-OCRv3_det_infer.tar"
        self.rec_url = "https://paddleocr.bj.bcebos.com/PP-OCRv3/english/en_PP-OCRv3_rec_infer.tar"
        self.det_path = os.path.join(self.MODEL_DIR, "en_PP-OCRv3_det_infer.tar")
        self.rec_path = os.path.join(self.MODEL_DIR, "en_PP-OCRv3_rec_infer.tar")
        self.cls_path = self.rec_path
        self._download_models()
        self.engine = PaddleOCR(lang="en", use_angle_cls=False, inference_model_dir=self.MODEL_DIR,
                                det_model_dir=self.MODEL_DIR, rec_model_dir=self.MODEL_DIR,
                                cls_model_dir=self.MODEL_DIR,
                                show_log=False)  # need to run only once to download and load model into memory

    def _download_file(self, url, save_path):
        try:
            response = requests.get(url)
            open(save_path, "wb").write(response.content)
        except:
            print("Something went wrong downloading:", url)

    def _download_models(self):
        # create directory to store models if one doesn't already exist
        if not os.path.exists(self.MODEL_DIR):
            os.makedirs(self.MODEL_DIR)

        # download model weights if they are not already downloaded
        if not os.path.exists(self.det_path):
            self._download_file(self.det_url, self.MODEL_DIR)
        if not os.path.exists(self.rec_path):
            self._download_file(self.rec_url, self.MODEL_DIR)

    # https://github.com/PaddlePaddle/PaddleOCR/blob/release/2.6/doc/doc_en/models_list_en.md#1.2
    def scan_img(self, img):
        text_bounds = []

        result = self.engine.ocr(img, cls=False)
        for idx in range(len(result)):
            res = result[idx]
            for line in res:
                bound = line[0]
                x1 = min(bound[0][0], bound[1][0], bound[2][0], bound[3][0])
                x2 = max(bound[0][0], bound[1][0], bound[2][0], bound[3][0])

                y1 = min(bound[0][1], bound[1][1], bound[2][1], bound[3][1])
                y2 = max(bound[0][1], bound[1][1], bound[2][1], bound[3][1])

                text = line[1][0].lower()
                text_bounds.append((text, (x1, y1, x2, y2)))
        return text_bounds


#########################
#        gfycat         #
#########################


def get_data_url(gfycat_url):
    data_url = None
    error_msg = None

    url_split = gfycat_url.rsplit('/', 1)
    if len(url_split) > 0:
        data_url = "https://api.gfycat.com/v1/gfycats/" + url_split[-1]
    else:
        error_msg = "URL format not supported."
    return data_url, error_msg


def get_gif_info(url):
    data = None
    error_msg = None
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
        else:
            error_msg = f"Web response status code: {response.status_code}"
    except requests.exceptions.RequestException as e:
        error_msg = str(e)

    return data, error_msg


def get_image_from_url(mp4_url):
    image = None
    error_msg = None
    target_resolution = (1920, 1080)

    # capture the video
    cap = cv2.VideoCapture(mp4_url)

    # check if capture was successful
    if cap.isOpened():
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        center_frame = int(total_frames / 2)

        cap.set(cv2.CAP_PROP_POS_FRAMES, center_frame)

        # check if frame is readable
        if cap.grab():
            _, image = cap.retrieve()
            image = cv2.resize(image, target_resolution)
        else:
            error_msg = "Failed to read frame from video capture."
    else:
        error_msg = "Failed to open video capture."

    return image, error_msg


#########################
#      processing       #
#########################


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


#########################
#        MAIN           #
#########################


def parse_vsgm(text_bounds, map_decoder):
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
        try:
            target_line = target_line.replace(" ", "")
            season_encoded = target_line[-4]
            gamemode_encoded = target_line[-3]
            map_encoded = target_line[-2:]
            version = target_line[target_line.index('v'):-5]

            data["version"] = version
            data["season"] = decode_season(season_encoded)
            data["gamemode"] = decode_gamemode(gamemode_encoded)
            data["map"], error_msg = decode_map(map_decoder, map_encoded)
        except IndexError as e:
            error_msg = str(e)

    return data, error_msg


def parse_time(text):
    text = text.replace('o', "0")
    time = clean_time(text)
    return time


def parse_top_right(ocr_engine, image, map_decoder):
    top_right_img = crop_top_right(image)
    text_bounds = ocr_engine.scan_img(top_right_img)
    data, error_msg = parse_vsgm(text_bounds, map_decoder)
    return data, error_msg


def get_stats(gfycat_url):
    ocr_engine = OCREngine()
    map_decoder = Mapping("lsl_autocomplete/map_encodings.txt")
    mode_decoder = Mapping("lsl_autocomplete/map_gamemodes.txt")

    stats = {"version": None, "season": None, "gamemode": None, "map": None, "time": None, "message": None}

    timer = datetime.now()
    # parse gfycat url, convert to api url
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
    image, error_msg = get_image_from_url(data["gfyItem"]["mp4Url"])
    if error_msg is not None:
        stats["message"] = f"Could not frames from url: {data_url}. Error msg: \"{error_msg}\""
        return stats
    print("Timer - get_image_from_url:", datetime.now() - timer)

    timer = datetime.now()
    # get data from top-right part of image
    top_right_data, error_msg = parse_top_right(ocr_engine, image, map_decoder)
    stats["version"] = top_right_data["version"]
    stats["season"] = top_right_data["season"]
    stats["gamemode"] = top_right_data["gamemode"]
    stats["map"] = top_right_data["map"]
    if error_msg is not None:
        stats["message"] = f"Error reading top-right part of image: {data_url}. Error msg: \"{error_msg}\""
    print("Timer - parse_top_right:", datetime.now() - timer)

    return stats