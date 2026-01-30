# from utils.image_loader import load_images
# from pipeline.signboard_detector import SignboardDetector
# from utils.image_utils import resize_for_display
# import cv2

# detector = SignboardDetector()
# image_paths = load_images("data/raw_images")

# for path in image_paths[:3]:
#     img = cv2.imread(path)
#     boxes = detector.detect(img)

#     for (x1, y1, x2, y2) in boxes:
#         cv2.rectangle(img, (x1, y1), (x2, y2), (0,255,0), 2)

#     img_display = resize_for_display(img)

#     cv2.imshow("YOLO Test", img_display)
#     cv2.waitKey(0)

# cv2.destroyAllWindows()


# import os
# import cv2
# from utils.image_loader import load_images
# from pipeline.signboard_detector import SignboardDetector
# from utils.image_utils import resize_for_display

# detector = SignboardDetector()
# image_paths = load_images("data/raw_images")

# os.makedirs("output/crops", exist_ok=True)

# for path in image_paths[:100]:
#     img = cv2.imread(path)
#     image_name = os.path.splitext(os.path.basename(path))[0]

#     crop_paths = detector.detect_and_crop(img, image_name)

#     for crop_path in crop_paths:
#         crop_img = cv2.imread(crop_path)
#         crop_img = resize_for_display(crop_img, 500, 400)
#         cv2.imshow("Crop", crop_img)
#         cv2.waitKey(500)

# cv2.destroyAllWindows()


# ---------------------------------------------------------------------
# import os
# import cv2
# from utils.image_loader import load_images
# from pipeline.signboard_detector import SignboardDetector
# from utils.image_utils import resize_for_display

# detector = SignboardDetector()

# image_paths = load_images("data/raw_images")

# os.makedirs("output/poi", exist_ok=True)
# os.makedirs("output/non_poi", exist_ok=True)

# for path in image_paths[:10000]:
#     img = cv2.imread(path)
#     image_name = os.path.basename(path)

#     boxes = detector.detect(img)

#     if len(boxes) > 0:
#         # POI IMAGE
#         save_path = os.path.join("output/poi", image_name)

#         # Optional: draw bounding boxes
#         for box in boxes:
#             x1, y1, x2, y2 = map(int, box)
#             cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)

#     else:
#         # NON-POI IMAGE
#         save_path = os.path.join("output/non_poi", image_name)

#     cv2.imwrite(save_path, img)

#     # Display (optional)
#     display = resize_for_display(img, 800, 600)
#     cv2.imshow("Result", display)
#     cv2.waitKey(300)

# cv2.destroyAllWindows()



# # Final
# import os
# import cv2
# import shutil
# from utils.image_loader import load_images
# from pipeline.signboard_detector import SignboardDetector
# from utils.image_utils import resize_for_display

# detector = SignboardDetector()

# image_paths = load_images("data/raw_images")

# os.makedirs("output/poi", exist_ok=True)
# os.makedirs("output/non_poi", exist_ok=True)

# for idx, path in enumerate(image_paths[:10000]):
#     img = cv2.imread(path)
#     if img is None:
#         continue

#     image_name = os.path.basename(path)

#     detections = detector.detect(img)

#     # ---- IMAGE LEVEL DECISION ----
#     strong = [d for d in detections if d["conf"] >= detector.strong_conf]
#     medium = [d for d in detections if detector.medium_conf <= d["conf"] < detector.strong_conf]

#     if len(strong) >= 1 or len(medium) >= 2:
#         category = "poi"
#     else:
#         category = "non_poi"

#     # ---- DRAW BOXES (optional, only for debug) ----
#     debug_img = img.copy()
#     for d in detections:
#         x1, y1, x2, y2 = d["box"]
#         conf = d["conf"]

#         if conf >= detector.medium_conf:
#             cv2.rectangle(debug_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
#             cv2.putText(
#                 debug_img,
#                 f"{conf:.2f}",
#                 (x1, y1 - 5),
#                 cv2.FONT_HERSHEY_SIMPLEX,
#                 0.5,
#                 (0, 255, 0),
#                 1
#             )

#     # ---- SAVE ORIGINAL IMAGE ----
#     save_path = os.path.join("output", category, image_name)
#     shutil.copy(path, save_path)

#     # ---- DISPLAY (optional) ----
#     display = resize_for_display(debug_img, 800, 600)
#     cv2.imshow("POI Classification", display)
#     cv2.waitKey(100)

#     if idx % 100 == 0:
#         print(f"[{idx}] {image_name} → {category.upper()} | "
#               f"strong={len(strong)}, medium={len(medium)}")

# cv2.destroyAllWindows()














# server image dev
import os
import cv2
import shutil
from utils.image_loader import load_images
from pipeline.signboard_detector import SignboardDetector
from utils.image_utils import resize_for_display

SERVER_IMAGE_PATH = r"\\10.10.2.101\team_backup\Nithin\raw_images"

detector = SignboardDetector()

POI_DIR = os.path.join(SERVER_IMAGE_PATH, "poi")
NON_POI_DIR = os.path.join(SERVER_IMAGE_PATH, "non_poi")

os.makedirs(POI_DIR, exist_ok=True)
os.makedirs(NON_POI_DIR, exist_ok=True)

image_paths = load_images(SERVER_IMAGE_PATH)

for idx, path in enumerate(image_paths):
    img = cv2.imread(path)
    if img is None:
        continue

    image_name = os.path.basename(path)

    detections = detector.detect(img)

    # ---- IMAGE LEVEL DECISION ----
    strong = [d for d in detections if d["conf"] >= detector.strong_conf]
    medium = [d for d in detections if detector.medium_conf <= d["conf"] < detector.strong_conf]

    if len(strong) >= 1 or len(medium) >= 2:
        category = "poi"
        dest_dir = POI_DIR
    else:
        category = "non_poi"
        dest_dir = NON_POI_DIR

    # ---- MOVE ORIGINAL IMAGE ----
    dest_path = os.path.join(dest_dir, image_name)

    if not os.path.exists(dest_path):
        shutil.move(path, dest_path)

    # ---- OPTIONAL DISPLAY ----
    debug_img = img.copy()
    for d in detections:
        if d["conf"] >= detector.medium_conf:
            x1, y1, x2, y2 = d["box"]
            cv2.rectangle(debug_img, (x1, y1), (x2, y2), (0, 255, 0), 2)

    display = resize_for_display(debug_img, 800, 600)
    cv2.imshow("POI Classification", display)
    cv2.waitKey(1)

    if idx % 100 == 0:
        print(f"[{idx}] {image_name} → {category.upper()}")

cv2.destroyAllWindows()
