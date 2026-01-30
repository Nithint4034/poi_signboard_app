import os
import sys
import threading
import cv2
import shutil          # ✅ ADD THIS
import tkinter as tk
from tkinter import filedialog, ttk, messagebox


# Fix imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from utils.image_loader import load_images
from pipeline.signboard_detector import SignboardDetector

detector = SignboardDetector()

OUTPUT_POI = "output/poi"
OUTPUT_NON_POI = "output/non_poi"

os.makedirs(OUTPUT_POI, exist_ok=True)
os.makedirs(OUTPUT_NON_POI, exist_ok=True)


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("POI Signboard Detector")
        self.geometry("500x300")
        self.resizable(False, False)

        self.input_folder = tk.StringVar()

        self.create_widgets()

    def create_widgets(self):
        tk.Label(self, text="Input Image Folder").pack(pady=10)

        frame = tk.Frame(self)
        frame.pack()

        tk.Entry(frame, textvariable=self.input_folder, width=40).pack(side=tk.LEFT, padx=5)
        tk.Button(frame, text="Browse", command=self.browse).pack(side=tk.LEFT)

        self.start_btn = tk.Button(self, text="Start Detection", command=self.start)
        self.start_btn.pack(pady=15)

        self.progress = ttk.Progressbar(self, length=400, mode="determinate")
        self.progress.pack(pady=10)

        self.status = tk.Label(self, text="")
        self.status.pack()

    def browse(self):
        folder = filedialog.askdirectory()
        if folder:
            self.input_folder.set(folder)

    def start(self):
        if not self.input_folder.get():
            messagebox.showerror("Error", "Select input folder")
            return

        self.start_btn.config(state=tk.DISABLED)
        threading.Thread(target=self.process_images, daemon=True).start()

    def process_images(self):
        input_dir = self.input_folder.get()

        POI_DIR = os.path.join(input_dir, "poi")
        NON_POI_DIR = os.path.join(input_dir, "non_poi")

        os.makedirs(POI_DIR, exist_ok=True)
        os.makedirs(NON_POI_DIR, exist_ok=True)

        images = load_images(input_dir)
        total = len(images)

        if total == 0:
            messagebox.showerror("Error", "No images found")
            return

        self.progress["maximum"] = total

        for idx, img_path in enumerate(images, 1):
            img = cv2.imread(img_path)
            if img is None:
                continue

            filename = os.path.basename(img_path)

            detections = detector.detect(img)

            strong = [d for d in detections if d["conf"] >= detector.strong_conf]
            medium = [d for d in detections if detector.medium_conf <= d["conf"] < detector.strong_conf]

            if len(strong) >= 1 or len(medium) >= 2:
                dest_dir = POI_DIR
            else:
                dest_dir = NON_POI_DIR

            dest_path = os.path.join(dest_dir, filename)

            if not os.path.exists(dest_path):
                shutil.move(img_path, dest_path)

            self.progress["value"] = idx
            self.status.config(text=f"Processing {idx}/{total}")
            self.update_idletasks()

        self.status.config(text="Completed ✅")
        self.start_btn.config(state=tk.NORMAL)
        messagebox.showinfo("Done", "Processing completed")


if __name__ == "__main__":
    app = App()
    app.mainloop()
