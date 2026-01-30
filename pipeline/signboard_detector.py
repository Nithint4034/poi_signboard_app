# from ultralytics import YOLO
# import cv2

# class SignboardDetector:
#     def __init__(self):
#         self.model = YOLO("yolov8n.pt")  # temporary

#     def detect(self, image):
#         results = self.model(image, conf=0.3, verbose=False)
#         boxes = []

#         for r in results:
#             for box in r.boxes:
#                 x1, y1, x2, y2 = map(int, box.xyxy[0])
#                 boxes.append((x1, y1, x2, y2))

#         return boxes


# from ultralytics import YOLO
# import cv2
# import os

# class SignboardDetector:
#     def __init__(self):
#         self.model = YOLO(r"runs\detect\train6\weights\best.pt")  # temporary model

#     def detect_and_crop(self, image, image_name, save_dir="output/crops"):
#         os.makedirs(save_dir, exist_ok=True)
#         results = self.model(image, conf=0.3, verbose=False)

#         crops = []

#         for r in results:
#             for i, box in enumerate(r.boxes):
#                 x1, y1, x2, y2 = map(int, box.xyxy[0])
#                 crop = image[y1:y2, x1:x2]

#                 crop_path = os.path.join(
#                     save_dir, f"{image_name}_crop_{i}.jpg"
#                 )
#                 cv2.imwrite(crop_path, crop)

#                 crops.append(crop_path)

#         return crops



# import cv2

# class SignboardDetector:
#     def __init__(self):
#         from ultralytics import YOLO
#         self.model = YOLO(r"runs\detect\train7\weights\best.pt")
#         self.conf_thres = 0.4

#     def detect(self, img):
#         results = self.model(img, conf=self.conf_thres)
#         boxes = []

#         for r in results:
#             for box in r.boxes:
#                 boxes.append(box.xyxy[0].cpu().numpy())

#         return boxes



import cv2

# class SignboardDetector:
#     def __init__(self):
#         from ultralytics import YOLO
#         self.model = YOLO(r"runs\detect\train7\weights\best.pt")
#         self.conf_thres = 0.08        # LOWER confidence
#         self.min_area_ratio = 0.01   # Ignore tiny boxes
#         self.poi_class_id = 0        # signboard class index

#     def detect(self, img):
#         h, w = img.shape[:2]
#         img_area = h * w

#         results = self.model(img, conf=self.conf_thres, iou=0.5)
#         valid_boxes = []

#         for r in results:
#             for box in r.boxes:
#                 cls_id = int(box.cls[0])

#                 # ONLY POI SIGNBOARD
#                 if cls_id != self.poi_class_id:
#                     continue

#                 x1, y1, x2, y2 = map(int, box.xyxy[0])
#                 area = (x2 - x1) * (y2 - y1)

#                 # Ignore very small detections
#                 if area / img_area < self.min_area_ratio:
#                     continue

#                 valid_boxes.append((x1, y1, x2, y2))

#         return valid_boxes





# # Final
# class SignboardDetector:
#     def __init__(self):
#         from ultralytics import YOLO

#         self.model = YOLO(r"runs\detect\train\weights\best.pt")

#         # thresholds
#         self.low_conf = 0.01      # detect everything
#         self.medium_conf = 0.15
#         self.strong_conf = 0.35

#         self.poi_class_id = 0     # signboard class index

#     def detect(self, img):
#         results = self.model(img, conf=self.low_conf, iou=0.45)

#         detections = []

#         for r in results:
#             if r.boxes is None:
#                 continue

#             for box in r.boxes:
#                 cls_id = int(box.cls[0])
#                 if cls_id != self.poi_class_id:
#                     continue

#                 conf = float(box.conf[0])
#                 x1, y1, x2, y2 = map(int, box.xyxy[0])

#                 detections.append({
#                     "box": (x1, y1, x2, y2),
#                     "conf": conf
#                 })

#         return detections

















# Final
import os
from ultralytics import YOLO

class SignboardDetector:
    def __init__(self):
        # Project root directory
        ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

        MODEL_PATH = os.path.join(
            ROOT_DIR,
            "runs",
            "detect",
            "train",
            "weights",
            "best.pt"
        )

        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

        self.model = YOLO(MODEL_PATH)

        # thresholds
        self.low_conf = 0.01
        self.medium_conf = 0.15
        self.strong_conf = 0.35

        self.poi_class_id = 0


    def detect(self, img):
        results = self.model(img, conf=self.low_conf, iou=0.45)

        detections = []

        for r in results:
            if r.boxes is None:
                continue

            for box in r.boxes:
                cls_id = int(box.cls[0])
                if cls_id != self.poi_class_id:
                    continue

                conf = float(box.conf[0])
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                detections.append({
                    "box": (x1, y1, x2, y2),
                    "conf": conf
                })

        return detections