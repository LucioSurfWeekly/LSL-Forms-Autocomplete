from urllib.error import HTTPError
import json
import requests
import cv2


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
        center_frame = int(total_frames/2)

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