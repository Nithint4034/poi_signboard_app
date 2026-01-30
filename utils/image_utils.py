import cv2

def resize_for_display(img, max_width=1000, max_height=700):
    h, w = img.shape[:2]

    scale = min(max_width / w, max_height / h)

    if scale < 1:
        img = cv2.resize(img, (int(w * scale), int(h * scale)))

    return img
