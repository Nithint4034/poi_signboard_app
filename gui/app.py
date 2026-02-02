import os
import sys
import threading
import cv2
import shutil
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from pathlib import Path

# Fix imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from utils.image_loader import load_images
from pipeline.signboard_detector import SignboardDetector

detector = SignboardDetector()


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("POI Signboard Detector")
        self.geometry("550x440")
        self.resizable(False, False)
        
        # Configure style
        self.configure(bg='#f5f5f5')
        self.columnconfigure(0, weight=1)
        
        # Initialize variables
        self.input_folder = tk.StringVar()
        self.selected_folder = tk.StringVar()
        self.processing = False
        self.stop_flag = False
        self.total_images = 0
        self.processed_images = 0

        self.create_widgets()

    def create_widgets(self):
        # Header Frame
        header_frame = tk.Frame(self, bg='#2c3e50', height=60)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="POI Signboard Detector", font=('Arial', 16, 'bold'), 
                bg='#2c3e50', fg='white').pack(expand=True)
        
        # Main container with padding
        main_container = tk.Frame(self, bg='#f5f5f5')
        main_container.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

        # Folder Input Section
        input_section = tk.LabelFrame(main_container, text=" Folder Selection ", 
                                     font=('Arial', 10, 'bold'), bg='#f5f5f5', 
                                     fg='#2c3e50', padx=15, pady=10)
        input_section.pack(fill=tk.X, pady=(0, 10))

        tk.Label(input_section, text="Main Directory Path:", font=('Arial', 9), 
                bg='#f5f5f5').pack(anchor=tk.W, pady=(0, 5))
        
        # Path input frame with icons
        path_frame = tk.Frame(input_section, bg='#f5f5f5')
        path_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Path entry with placeholder effect
        self.path_entry = tk.Entry(path_frame, textvariable=self.input_folder, 
                                  font=('Arial', 9), bd=2, relief=tk.GROOVE)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Action buttons frame
        action_frame = tk.Frame(path_frame, bg='#f5f5f5')
        action_frame.pack(side=tk.RIGHT)
        
        # Refresh button with icon
        refresh_btn = tk.Button(action_frame, text="Refresh", 
                               command=self.refresh_folders,
                               font=('Arial', 10, 'bold'),
                               bg='#3498db', fg='white',
                               activebackground='#2980b9',
                               activeforeground='white',
                               relief=tk.RAISED,
                               cursor='hand2',
                               width=6)
        refresh_btn.pack(side=tk.LEFT, padx=2)
        
        # Clear button
        clear_btn = tk.Button(action_frame, text="Clear", 
                             command=self.clear_selection,
                             font=('Arial', 10),
                             bg='#95a5a6', fg='white',
                             activebackground='#7f8c8d',
                             activeforeground='white',
                             relief=tk.RAISED,
                             cursor='hand2',
                             width=4)
        clear_btn.pack(side=tk.LEFT, padx=2)
        
        # Folder dropdown section
        tk.Label(input_section, text="Select Folder to Process:", font=('Arial', 9), 
                bg='#f5f5f5').pack(anchor=tk.W, pady=(0, 5))
        
        # Combobox with scrollbar
        combobox_frame = tk.Frame(input_section, bg='#f5f5f5')
        combobox_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.folder_combobox = ttk.Combobox(combobox_frame, textvariable=self.selected_folder, 
                                           font=('Arial', 9), state="readonly")
        self.folder_combobox.pack(fill=tk.X)
        self.folder_combobox.bind('<<ComboboxSelected>>', self.on_folder_selected)
        
        # Selected folder display
        self.selected_folder_display = tk.Label(input_section, text="No folder selected", 
                                               font=('Arial', 9, 'italic'),
                                               bg='#f5f5f5', fg='#7f8c8d',
                                               anchor=tk.W)
        self.selected_folder_display.pack(fill=tk.X)
        
        # Control Buttons Section
        control_frame = tk.Frame(main_container, bg='#f5f5f5')
        control_frame.pack(fill=tk.X, pady=(10, 10))
        
        # Start button with success color
        self.start_btn = tk.Button(control_frame, text="▶ START DETECTION", 
                                  command=self.start,
                                  font=('Arial', 11, 'bold'),
                                  bg='#27ae60', fg='white',
                                  activebackground='#229954',
                                  activeforeground='white',
                                  relief=tk.RAISED,
                                  cursor='hand2',
                                  width=18,
                                  height=1)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Stop button with warning color (initially disabled)
        self.stop_btn = tk.Button(control_frame, text="⏹ STOP", 
                                 command=self.stop,
                                 font=('Arial', 11, 'bold'),
                                 bg='#e74c3c', fg='white',
                                 activebackground='#c0392b',
                                 activeforeground='white',
                                 relief=tk.RAISED,
                                 cursor='hand2',
                                 state=tk.DISABLED,
                                 width=18,
                                 height=1)
        self.stop_btn.pack(side=tk.LEFT)
        
        # Progress Bar Section
        progress_frame = tk.Frame(main_container, bg='#f5f5f5')
        progress_frame.pack(fill=tk.X, pady=(5, 5))
        
        # Progress bar
        self.progress = ttk.Progressbar(progress_frame, mode="determinate")
        self.progress.pack(fill=tk.X, pady=(5, 0))
        
        # Progress label
        self.progress_label = tk.Label(progress_frame, text="0%", 
                                      font=('Arial', 9),
                                      bg='#f5f5f5', fg='#3498db')
        self.progress_label.pack(pady=(5, 0))
        
        # Status label
        self.status_label = tk.Label(progress_frame, text="Ready", 
                                    font=('Arial', 9, 'bold'),
                                    bg='#f5f5f5', fg='#2c3e50')
        self.status_label.pack(pady=(5, 0))
        
        # Current folder info section - UPDATED
        folder_info_frame = tk.Frame(progress_frame, bg='#f5f5f5')
        folder_info_frame.pack(fill=tk.X, pady=(5, 0))
        
        tk.Label(folder_info_frame, text="Processing:", 
                font=('Arial', 9, 'bold'), bg='#f5f5f5', fg='#2c3e50').pack(side=tk.LEFT)
        
        # CURRENT NESTED FOLDER DISPLAY - More prominent
        self.current_folder_display = tk.Label(folder_info_frame, text="None", 
                                             font=('Arial', 9, 'bold'),
                                             bg='#f5f5f5', fg='#e67e22',  # Orange color
                                             anchor=tk.W,
                                             width=45,
                                             wraplength=400)  # Allow text wrapping
        self.current_folder_display.pack(side=tk.LEFT, padx=(5, 0))
        
        # Footer
        footer_frame = tk.Frame(self, bg='#ecf0f1', height=30)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X)
        footer_frame.pack_propagate(False)
        
        tk.Label(footer_frame, text="POI Detection System v1.0", 
                font=('Arial', 8), bg='#ecf0f1', fg='#7f8c8d').pack(pady=5)

    def clear_selection(self):
        """Clear all selections"""
        self.input_folder.set("")
        self.selected_folder.set("")
        self.folder_combobox.set('')
        self.folder_combobox['values'] = []
        self.selected_folder_display.config(text="No folder selected", fg='#7f8c8d')
        self.status_label.config(text="Ready", fg='#2c3e50')
        self.progress["value"] = 0
        self.progress_label.config(text="0%")
        self.current_folder_display.config(text="None", fg='#7f8c8d')
        self.total_images = 0
        self.processed_images = 0

    def refresh_folders(self):
        """Refresh and populate the folder dropdown"""
        main_dir = self.input_folder.get()
        
        if not main_dir or not os.path.exists(main_dir):
            messagebox.showwarning("Input Required", 
                                  "Please enter a valid directory path first")
            return
        
        try:
            # Get all subdirectories (first level only)
            main_path = Path(main_dir)
            subfolders = []
            
            for item in main_path.iterdir():
                if item.is_dir():
                    # Check if folder contains any images
                    has_images = any(item.glob(pattern) for pattern in ['*.jpg', '*.jpeg', '*.png', '.bmp'])
                    if has_images or any(subitem.is_dir() for subitem in item.iterdir()):
                        subfolders.append(item.name)
            
            if not subfolders:
                self.status_label.config(text="No subfolders found", fg='#e74c3c')
                self.folder_combobox.set('')
                self.folder_combobox['values'] = []
                self.selected_folder_display.config(text="No folders found in directory", fg='#e74c3c')
                return
            
            # Update combobox with folders
            subfolders.sort()
            self.folder_combobox['values'] = subfolders
            self.folder_combobox.set('')
            self.selected_folder_display.config(text=f"Found {len(subfolders)} folder(s). Select one to process.", 
                                              fg='#27ae60')
            self.status_label.config(text="Folders loaded. Select one to process.", fg='#2c3e50')
            
        except Exception as e:
            messagebox.showerror("Directory Error", f"Error reading folder: {str(e)}")

    def on_folder_selected(self, event=None):
        """When a folder is selected from dropdown"""
        selected = self.selected_folder.get()
        if selected:
            full_path = os.path.join(self.input_folder.get(), selected)
            self.selected_folder_display.config(text=f"Selected: {selected}", fg='#27ae60')
            self.status_label.config(text=f"Ready to process: {selected}", fg='#2c3e50')

    def start(self):
        if not self.input_folder.get():
            messagebox.showerror("Input Error", "Please enter a directory path")
            return
        
        selected_folder = self.selected_folder.get()
        if not selected_folder:
            messagebox.showwarning("Selection Required", "Please select a folder from the dropdown")
            return

        self.processing = True
        self.stop_flag = False
        self.start_btn.config(state=tk.DISABLED, bg='#95a5a6')
        self.stop_btn.config(state=tk.NORMAL)
        
        # Reset progress
        self.progress["value"] = 0
        self.progress_label.config(text="0%")
        self.total_images = 0
        self.processed_images = 0
        self.status_label.config(text="Starting...", fg='#3498db')
        self.current_folder_display.config(text=f"{selected_folder}/...", fg='#e67e22')
        
        # Create full path to selected folder
        folder_to_process = os.path.join(self.input_folder.get(), selected_folder)
        threading.Thread(target=self.process_nested_folders, args=(folder_to_process,), daemon=True).start()

    def stop(self):
        self.stop_flag = True
        self.status_label.config(text="Stopping...", fg='#e74c3c')
        self.start_btn.config(state=tk.DISABLED)

    def update_progress(self, current, total):
        """Update progress bar and labels"""
        if total > 0:
            progress_percent = (current / total) * 100
            self.progress["value"] = progress_percent
            self.progress_label.config(text=f"{current}/{total} ({progress_percent:.1f}%)")
        else:
            self.progress["value"] = 0
            self.progress_label.config(text="0%")
        
        self.update_idletasks()

    def process_nested_folders(self, start_folder):
        """Process nested folders starting from the selected folder"""
        main_dir = Path(start_folder)
        
        # Find all subdirectories that are not named 'poi' or 'non_poi'
        all_folders = []
        for root, dirs, _ in os.walk(main_dir):
            # Skip folders named 'poi' or 'non_poi'
            dirs[:] = [d for d in dirs if d.lower() not in ['poi', 'non_poi']]
            
            for dir_name in dirs:
                folder_path = Path(root) / dir_name
                # Only process folders that contain images
                if any(folder_path.glob("*.*")):
                    all_folders.append(folder_path)
        
        # Also include the main selected folder if it contains images
        if any(main_dir.glob("*.*")):
            all_folders.insert(0, main_dir)
        
        if not all_folders:
            self.after(0, lambda: self.status_label.config(text="No images found", fg='#e74c3c'))
            self.processing = False
            self.after(0, lambda: self.start_btn.config(state=tk.NORMAL, bg='#27ae60'))
            self.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))
            messagebox.showinfo("No Images", "No images found in the selected folder")
            return
        
        # Count total images for progress bar
        total_images = 0
        for folder in all_folders:
            image_count = sum(1 for _ in folder.glob("*.*") if _.suffix.lower() in ['.jpg', '.jpeg', '.png', '.bmp'])
            total_images += image_count
        
        self.total_images = total_images
        
        # Update UI with initial state
        self.after(0, lambda: self.update_progress(0, total_images))
        self.after(0, lambda: self.status_label.config(text=f"Processing {total_images} images...", fg='#3498db'))
        
        processed_images = 0
        
        # Process each folder
        for folder in all_folders:
            if self.stop_flag:
                break
                
            # Get the relative path from the main selected folder
            try:
                rel_path = folder.relative_to(main_dir)
                # Convert to string and show the actual nested folder path
                folder_display = str(rel_path)
                if folder_display == '.':
                    folder_display = "(main folder)"
                else:
                    folder_display = f"{folder_display}"
                
                # Update current folder display with the nested folder path
                self.after(0, lambda f=folder_display: self.current_folder_display.config(
                    text=f"{self.selected_folder.get()}/{f}" if f != "(main folder)" 
                    else f"{self.selected_folder.get()}/",
                    fg='#e67e22'))
                
                # Also update status for more detail
                self.after(0, lambda f=folder_display: self.status_label.config(
                    text=f"Processing: {self.selected_folder.get()}/{f}" if f != "(main folder)"
                    else f"Processing: {self.selected_folder.get()}/",
                    fg='#3498db'))
                    
            except Exception as e:
                # Fallback if relative path fails
                folder_display = folder.name
                self.after(0, lambda f=folder_display: self.current_folder_display.config(
                    text=f"{self.selected_folder.get()}/.../{f}",
                    fg='#e67e22'))
            
            self.update_idletasks()
            
            images_processed = self.process_folder(folder, processed_images)
            processed_images += images_processed
            
            # Update progress
            self.after(0, lambda c=processed_images, t=total_images: self.update_progress(c, t))
            
            if self.stop_flag:
                break
        
        if not self.stop_flag:
            self.after(0, lambda: self.status_label.config(text="Completed successfully! ✅", fg='#27ae60'))
            self.after(0, lambda: self.current_folder_display.config(text="Completed", fg='#27ae60'))
            messagebox.showinfo("Processing Complete", 
                              f"Successfully processed '{self.selected_folder.get()}'\n\n"
                              f"Total images: {processed_images}")
        else:
            self.after(0, lambda: self.status_label.config(text="Processing stopped", fg='#e74c3c'))
            messagebox.showinfo("Processing Stopped", "Processing was stopped by user")
        
        self.processing = False
        self.after(0, lambda: self.start_btn.config(state=tk.NORMAL, bg='#27ae60'))
        self.after(0, lambda: self.stop_btn.config(state=tk.DISABLED))

    def process_folder(self, folder_path, processed_so_far):
        """Process a single folder, segregating images into poi/non_poi subfolders"""
        folder_path = Path(folder_path)
        
        # Create poi and non_poi subdirectories if they don't exist
        poi_dir = folder_path / "poi"
        non_poi_dir = folder_path / "non_poi"
        
        poi_dir.mkdir(exist_ok=True)
        non_poi_dir.mkdir(exist_ok=True)
        
        # Get all image files in the folder (excluding poi/non_poi folders)
        images = []
        for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp']:
            images.extend(folder_path.glob(ext))
        
        processed_in_folder = 0
        
        # Process each image
        for img_path in images:
            if self.stop_flag:
                break
                
            # Skip if image is already in poi/non_poi folder
            if "poi" in str(img_path).lower() or "non_poi" in str(img_path).lower():
                continue
                
            img = cv2.imread(str(img_path))
            if img is None:
                continue
            
            # Perform detection
            detections = detector.detect(img)
            
            # Apply classification logic
            strong = [d for d in detections if d["conf"] >= detector.strong_conf]
            medium = [d for d in detections if detector.medium_conf <= d["conf"] < detector.strong_conf]
            
            if len(strong) >= 1 or len(medium) >= 2:
                dest_dir = poi_dir
            else:
                dest_dir = non_poi_dir
            
            # Move the image
            dest_path = dest_dir / img_path.name
            if not dest_path.exists():
                shutil.move(str(img_path), str(dest_path))
            
            processed_in_folder += 1
            current_total = processed_so_far + processed_in_folder
            
            # Update progress every image for smooth progress
            self.after(0, lambda c=current_total, t=self.total_images: self.update_progress(c, t))
        
        return processed_in_folder


if __name__ == "__main__":
    app = App()
    app.mainloop()