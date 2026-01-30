import os

VALID_EXT = (".jpg", ".jpeg", ".png", ".bmp")

def load_images(folder):
    images = []
    for root, _, files in os.walk(folder):
        for f in files:
            if f.lower().endswith(VALID_EXT):
                images.append(os.path.join(root, f))
    return images
