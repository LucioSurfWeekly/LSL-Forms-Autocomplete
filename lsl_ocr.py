import os
import requests
import paddleocr
from paddleocr.paddleocr import MODEL_URLS
from paddleocr import PaddleOCR, draw_ocr


class PaddleOCR:

    def __init__(self, params):
        self.params = params
        self.MODEL_DIR = "models/"
        self.det_url = "https://paddleocr.bj.bcebos.com/PP-OCRv3/english/en_PP-OCRv3_det_infer.tar"
        self.rec_url = "https://paddleocr.bj.bcebos.com/PP-OCRv3/english/en_PP-OCRv3_rec_infer.tar"
        self.det_path = os.path.join(self.MODEL_DIR, "en_PP-OCRv3_det_infer")
        self.rec_path = os.path.join(self.MODEL_DIR, "en_PP-OCRv3_rec_infer")
        self.cls_path = self.rec_path
        self._download_models()
        self.engine = PaddleOCR(lang="en", use_angle_cls=False, inference_model_dir="./models/",
                                det_model_dir=self.det_path, rec_model_dir=self.rec_path, cls_model_dir=self.cls_path,
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
            self._download_file(self.det_url, self.det_path)
        if not os.path.exists(self.rec_path):
            self._download_file(self.rec_url, self.rec_path)

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
