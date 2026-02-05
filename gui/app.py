import os
import sys
import threading
import time
from pathlib import Path
from datetime import timedelta
import cv2
import shutil
import tkinter as tk
from tkinter import filedialog, ttk, messagebox

# Fix imports
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from utils.image_loader import load_images
from pipeline.signboard_detector import SignboardDetector


class POIDetectorApp(tk.Tk):
    """Main application for POI Signboard Detection with frame validation."""
    
    # Constants
    VALID_FOLDER = "Valid_Frames"
    INVALID_FOLDER = "Invalid_Frames"
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp'}
    
    # UI Colors
    COLOR_PRIMARY = '#2c3e50'
    COLOR_SUCCESS = '#27ae60'
    COLOR_WARNING = '#e74c3c'
    COLOR_INFO = '#3498db'
    COLOR_ACCENT = '#e67e22'
    COLOR_SECONDARY = '#95a5a6'
    COLOR_BG = '#f5f5f5'
    COLOR_LIGHT_BG = '#ecf0f1'
    COLOR_TEXT_MUTED = '#7f8c8d'
    COLOR_TIME = '#16a085'
    
    def __init__(self):
        super().__init__()
        
        self.title("POI Signboard Detector")
        self.geometry("550x520")  # Increased height for checkbox
        self.resizable(False, False)
        self.configure(bg=self.COLOR_BG)
        
        # Initialize detector
        self.detector = SignboardDetector()
        
        # State variables
        self.input_folder = tk.StringVar()
        self.selected_folder = tk.StringVar()
        self.delete_original = tk.BooleanVar(value=True)  # Default to True for space saving
        self.processing = False
        self.stop_flag = False
        self.total_images = 0
        self.processed_images = 0
        self.start_time = None
        self.elapsed_time = 0
        self.time_update_job = None
        
        # Output directories
        self.valid_root = None
        self.invalid_root = None
        self.processed_folder_path = None  # Track the folder being processed for deletion
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the complete user interface."""
        self._create_header()
        self._create_main_container()
        self._create_footer()
    
    def _create_header(self):
        """Create header section."""
        header = tk.Frame(self, bg=self.COLOR_PRIMARY, height=60)
        header.pack(fill=tk.X, pady=(0, 10))
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="POI Signboard Detector",
            font=('Arial', 16, 'bold'),
            bg=self.COLOR_PRIMARY,
            fg='white'
        ).pack(expand=True)
    
    def _create_main_container(self):
        """Create main content area."""
        container = tk.Frame(self, bg=self.COLOR_BG)
        container.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        self._create_folder_selection(container)
        self._create_control_buttons(container)
        self._create_progress_section(container)
    
    def _create_folder_selection(self, parent):
        """Create folder selection section."""
        section = tk.LabelFrame(
            parent,
            text=" Folder Selection ",
            font=('Arial', 10, 'bold'),
            bg=self.COLOR_BG,
            fg=self.COLOR_PRIMARY,
            padx=15,
            pady=10
        )
        section.pack(fill=tk.X, pady=(0, 10))
        
        # Directory path input
        tk.Label(
            section,
            text="Main Directory Path:",
            font=('Arial', 9),
            bg=self.COLOR_BG
        ).pack(anchor=tk.W, pady=(0, 5))
        
        path_frame = tk.Frame(section, bg=self.COLOR_BG)
        path_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.path_entry = tk.Entry(
            path_frame,
            textvariable=self.input_folder,
            font=('Arial', 9),
            bd=2,
            relief=tk.GROOVE
        )
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Action buttons
        action_frame = tk.Frame(path_frame, bg=self.COLOR_BG)
        action_frame.pack(side=tk.RIGHT)
        
        self._create_button(
            action_frame,
            "Refresh",
            self._refresh_folders,
            self.COLOR_INFO,
            '#2980b9',
            6
        ).pack(side=tk.LEFT, padx=2)
        
        self._create_button(
            action_frame,
            "Clear",
            self._clear_selection,
            self.COLOR_SECONDARY,
            '#7f8c8d',
            4
        ).pack(side=tk.LEFT, padx=2)
        
        # Folder dropdown
        tk.Label(
            section,
            text="Select Folder to Process:",
            font=('Arial', 9),
            bg=self.COLOR_BG
        ).pack(anchor=tk.W, pady=(0, 5))
        
        self.folder_combobox = ttk.Combobox(
            section,
            textvariable=self.selected_folder,
            font=('Arial', 9),
            state="readonly"
        )
        self.folder_combobox.pack(fill=tk.X, pady=(0, 5))
        self.folder_combobox.bind('<<ComboboxSelected>>', self._on_folder_selected)
        
        # Selected folder display
        self.selected_folder_display = tk.Label(
            section,
            text="No folder selected",
            font=('Arial', 9, 'italic'),
            bg=self.COLOR_BG,
            fg=self.COLOR_TEXT_MUTED,
            anchor=tk.W
        )
        self.selected_folder_display.pack(fill=tk.X)
        
        # Delete original folder checkbox
        delete_frame = tk.Frame(section, bg=self.COLOR_BG)
        delete_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.delete_checkbox = tk.Checkbutton(
            delete_frame,
            text="Delete original subfolders after processing (saves disk space)",
            variable=self.delete_original,
            font=('Arial', 9, 'bold'),
            bg=self.COLOR_BG,
            fg=self.COLOR_WARNING,
            activebackground=self.COLOR_BG,
            selectcolor=self.COLOR_BG,
            cursor='hand2'
        )
        self.delete_checkbox.pack(anchor=tk.W)
    
    def _create_control_buttons(self, parent):
        """Create control buttons section."""
        control_frame = tk.Frame(parent, bg=self.COLOR_BG)
        control_frame.pack(fill=tk.X, pady=(10, 10))
        
        self.start_btn = self._create_button(
            control_frame,
            "▶ START DETECTION",
            self._start_processing,
            self.COLOR_SUCCESS,
            '#229954',
            18,
            height=1
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_btn = self._create_button(
            control_frame,
            "⏹ STOP",
            self._stop_processing,
            self.COLOR_WARNING,
            '#c0392b',
            18,
            height=1,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT)
    
    def _create_progress_section(self, parent):
        """Create progress tracking section."""
        progress_frame = tk.Frame(parent, bg=self.COLOR_BG)
        progress_frame.pack(fill=tk.X, pady=(5, 5))
        
        # Progress bar
        self.progress = ttk.Progressbar(progress_frame, mode="determinate")
        self.progress.pack(fill=tk.X, pady=(5, 0))
        
        # Progress label
        self.progress_label = tk.Label(
            progress_frame,
            text="0%",
            font=('Arial', 9),
            bg=self.COLOR_BG,
            fg=self.COLOR_INFO
        )
        self.progress_label.pack(pady=(5, 0))
        
        # Status label
        self.status_label = tk.Label(
            progress_frame,
            text="Ready",
            font=('Arial', 9, 'bold'),
            bg=self.COLOR_BG,
            fg=self.COLOR_PRIMARY
        )
        self.status_label.pack(pady=(5, 0))
        
        # Time tracking
        time_frame = tk.Frame(progress_frame, bg=self.COLOR_BG)
        time_frame.pack(fill=tk.X, pady=(5, 0))
        
        tk.Label(
            time_frame,
            text="Execution Time:",
            font=('Arial', 9, 'bold'),
            bg=self.COLOR_BG,
            fg=self.COLOR_PRIMARY
        ).pack(side=tk.LEFT)
        
        self.time_display = tk.Label(
            time_frame,
            text="00:00:00",
            font=('Arial', 10, 'bold'),
            bg=self.COLOR_BG,
            fg=self.COLOR_TIME
        )
        self.time_display.pack(side=tk.LEFT, padx=(5, 0))
        
        # Current folder info
        folder_info_frame = tk.Frame(progress_frame, bg=self.COLOR_BG)
        folder_info_frame.pack(fill=tk.X, pady=(5, 0))
        
        tk.Label(
            folder_info_frame,
            text="Processing:",
            font=('Arial', 9, 'bold'),
            bg=self.COLOR_BG,
            fg=self.COLOR_PRIMARY
        ).pack(side=tk.LEFT)
        
        self.current_folder_display = tk.Label(
            folder_info_frame,
            text="None",
            font=('Arial', 9, 'bold'),
            bg=self.COLOR_BG,
            fg=self.COLOR_ACCENT,
            anchor=tk.W,
            width=45,
            wraplength=400
        )
        self.current_folder_display.pack(side=tk.LEFT, padx=(5, 0))
    
    def _create_footer(self):
        """Create footer section."""
        footer = tk.Frame(self, bg=self.COLOR_LIGHT_BG, height=30)
        footer.pack(side=tk.BOTTOM, fill=tk.X)
        footer.pack_propagate(False)
        
        tk.Label(
            footer,
            text="POI Detection System v2.0 - Frame Validation",
            font=('Arial', 8),
            bg=self.COLOR_LIGHT_BG,
            fg=self.COLOR_TEXT_MUTED
        ).pack(pady=5)
    
    def _create_button(self, parent, text, command, bg, active_bg, width, height=None, state=tk.NORMAL):
        """Helper method to create styled buttons."""
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            font=('Arial', 10 if width < 10 else 11, 'bold'),
            bg=bg,
            fg='white',
            activebackground=active_bg,
            activeforeground='white',
            relief=tk.RAISED,
            cursor='hand2',
            width=width,
            state=state
        )
        if height:
            btn.config(height=height)
        return btn
    
    def _format_time(self, seconds):
        """Format seconds into HH:MM:SS."""
        return str(timedelta(seconds=int(seconds)))
    
    def _update_time_display(self):
        """Update the time display every second."""
        if self.processing and self.start_time:
            self.elapsed_time = time.time() - self.start_time
            self.time_display.config(text=self._format_time(self.elapsed_time))
            self.time_update_job = self.after(1000, self._update_time_display)
    
    def _update_progress(self, current, total):
        """Update progress bar and labels."""
        if total > 0:
            progress_percent = (current / total) * 100
            self.progress["value"] = progress_percent
            self.progress_label.config(text=f"{current}/{total} ({progress_percent:.1f}%)")
        else:
            self.progress["value"] = 0
            self.progress_label.config(text="0%")
        self.update_idletasks()
    
    def _clear_selection(self):
        """Clear all selections and reset UI."""
        self.input_folder.set("")
        self.selected_folder.set("")
        self.folder_combobox.set('')
        self.folder_combobox['values'] = []
        self.selected_folder_display.config(text="No folder selected", fg=self.COLOR_TEXT_MUTED)
        self.status_label.config(text="Ready", fg=self.COLOR_PRIMARY)
        self.progress["value"] = 0
        self.progress_label.config(text="0%")
        self.current_folder_display.config(text="None", fg=self.COLOR_TEXT_MUTED)
        self.time_display.config(text="00:00:00")
        self.total_images = 0
        self.processed_images = 0
        self.elapsed_time = 0
    
    def _refresh_folders(self):
        """Refresh and populate the folder dropdown."""
        main_dir = self.input_folder.get()
        
        if not main_dir or not os.path.exists(main_dir):
            messagebox.showwarning("Input Required", "Please enter a valid directory path first")
            return
        
        try:
            main_path = Path(main_dir)
            subfolders = []
            
            for item in main_path.iterdir():
                if item.is_dir() and item.name not in {self.VALID_FOLDER, self.INVALID_FOLDER}:
                    # Check if folder contains images or subdirectories
                    has_content = any(
                        item.glob(f'*{ext}') for ext in self.IMAGE_EXTENSIONS
                    ) or any(subitem.is_dir() for subitem in item.iterdir())
                    
                    if has_content:
                        subfolders.append(item.name)
            
            if not subfolders:
                self.status_label.config(text="No subfolders found", fg=self.COLOR_WARNING)
                self.folder_combobox.set('')
                self.folder_combobox['values'] = []
                self.selected_folder_display.config(
                    text="No folders found in directory",
                    fg=self.COLOR_WARNING
                )
                return
            
            # Update combobox
            subfolders.sort()
            self.folder_combobox['values'] = subfolders
            self.folder_combobox.set('')
            self.selected_folder_display.config(
                text=f"Found {len(subfolders)} folder(s). Select one to process.",
                fg=self.COLOR_SUCCESS
            )
            self.status_label.config(text="Folders loaded. Select one to process.", fg=self.COLOR_PRIMARY)
            
        except Exception as e:
            messagebox.showerror("Directory Error", f"Error reading folder: {str(e)}")
    
    def _on_folder_selected(self, event=None):
        """Handle folder selection from dropdown."""
        selected = self.selected_folder.get()
        if selected:
            self.selected_folder_display.config(text=f"Selected: {selected}", fg=self.COLOR_SUCCESS)
            self.status_label.config(text=f"Ready to process: {selected}", fg=self.COLOR_PRIMARY)
    
    def _start_processing(self):
        """Start the detection process."""
        if not self.input_folder.get():
            messagebox.showerror("Input Error", "Please enter a directory path")
            return
        
        selected_folder = self.selected_folder.get()
        if not selected_folder:
            messagebox.showwarning("Selection Required", "Please select a folder from the dropdown")
            return
        
        # Update state
        self.processing = True
        self.stop_flag = False
        self.start_btn.config(state=tk.DISABLED, bg=self.COLOR_SECONDARY)
        self.stop_btn.config(state=tk.NORMAL)
        
        # Reset progress and time
        self.progress["value"] = 0
        self.progress_label.config(text="0%")
        self.total_images = 0
        self.processed_images = 0
        self.status_label.config(text="Starting...", fg=self.COLOR_INFO)
        self.current_folder_display.config(text=f"{selected_folder}/...", fg=self.COLOR_ACCENT)
        
        # Start timer
        self.start_time = time.time()
        self.elapsed_time = 0
        self.time_display.config(text="00:00:00", fg=self.COLOR_TIME)
        self._update_time_display()
        
        # Setup output directories INSIDE the selected folder
        folder_to_process = os.path.join(self.input_folder.get(), selected_folder)
        selected_folder_path = Path(folder_to_process)
        self.valid_root = selected_folder_path / self.VALID_FOLDER
        self.invalid_root = selected_folder_path / self.INVALID_FOLDER
        self.valid_root.mkdir(exist_ok=True)
        self.invalid_root.mkdir(exist_ok=True)
        
        # Start processing thread
        self.processed_folder_path = folder_to_process  # Store for deletion (if needed)
        threading.Thread(
            target=self._process_nested_folders,
            args=(folder_to_process,),
            daemon=True
        ).start()
    
    def _stop_processing(self):
        """Stop the detection process."""
        self.stop_flag = True
        self.status_label.config(text="Stopping...", fg=self.COLOR_WARNING)
        self.start_btn.config(state=tk.DISABLED)
        if self.time_update_job:
            self.after_cancel(self.time_update_job)
    
    def _get_all_processable_folders(self, root_folder):
        """Get all folders that need processing (excluding valid/invalid folders)."""
        root_path = Path(root_folder)
        folders = []
        
        for root, dirs, _ in os.walk(root_path):
            # Skip valid/invalid frame folders
            dirs[:] = [d for d in dirs if d not in {self.VALID_FOLDER, self.INVALID_FOLDER}]
            
            for dir_name in dirs:
                folder_path = Path(root) / dir_name
                # Only include folders with images
                if any(folder_path.glob(f'*{ext}') for ext in self.IMAGE_EXTENSIONS):
                    folders.append(folder_path)
        
        # Include root folder if it has images
        if any(root_path.glob(f'*{ext}') for ext in self.IMAGE_EXTENSIONS):
            folders.insert(0, root_path)
        
        return folders
    
    def _count_images_in_folder(self, folder_path):
        """Count images in a folder."""
        return sum(
            1 for f in Path(folder_path).iterdir()
            if f.is_file() and f.suffix.lower() in self.IMAGE_EXTENSIONS
        )
    
    def _process_nested_folders(self, start_folder):
        """Process all nested folders starting from the selected folder."""
        main_dir = Path(start_folder)
        base_folder_name = self.selected_folder.get()
        
        # Get all folders to process
        all_folders = self._get_all_processable_folders(main_dir)
        
        if not all_folders:
            self.after(0, lambda: self._finish_processing(
                success=False,
                message="No images found in the selected folder"
            ))
            return
        
        # Count total images
        self.total_images = sum(self._count_images_in_folder(f) for f in all_folders)
        
        # Update UI
        self.after(0, lambda: self._update_progress(0, self.total_images))
        self.after(0, lambda: self.status_label.config(
            text=f"Processing {self.total_images} images...",
            fg=self.COLOR_INFO
        ))
        
        processed_images = 0
        
        # Process each folder
        for folder in all_folders:
            if self.stop_flag:
                break
            
            # Update current folder display
            self._update_folder_display(folder, main_dir, base_folder_name)
            
            # Process folder
            images_processed = self._process_single_folder(folder, main_dir, processed_images)
            processed_images += images_processed
            
            # Update progress
            self.after(0, lambda c=processed_images, t=self.total_images: self._update_progress(c, t))
        
        # Finish processing
        self.after(0, lambda: self._finish_processing(
            success=not self.stop_flag,
            processed_count=processed_images
        ))
    
    def _update_folder_display(self, folder, main_dir, base_folder_name):
        """Update the current folder display."""
        try:
            rel_path = folder.relative_to(main_dir)
            folder_display = str(rel_path) if str(rel_path) != '.' else "(main folder)"
            
            display_text = (
                f"{base_folder_name}/{folder_display}"
                if folder_display != "(main folder)"
                else f"{base_folder_name}/"
            )
            
            self.after(0, lambda: self.current_folder_display.config(
                text=display_text,
                fg=self.COLOR_ACCENT
            ))
            self.after(0, lambda: self.status_label.config(
                text=f"Processing: {display_text}",
                fg=self.COLOR_INFO
            ))
        except Exception:
            # Fallback display
            self.after(0, lambda: self.current_folder_display.config(
                text=f"{base_folder_name}/.../{folder.name}",
                fg=self.COLOR_ACCENT
            ))
    
    def _process_single_folder(self, folder_path, selected_folder_root, processed_so_far):
        """Process a single folder and segregate frames into centralized Valid/Invalid folders."""
        folder_path = Path(folder_path)
        
        # Calculate relative path from selected folder root for subfolder structure
        try:
            rel_path = folder_path.relative_to(selected_folder_root)
            
            # Create subfolder structure: Valid_Frames/subfolder/... (no parent folder name needed)
            if str(rel_path) != '.':
                # For nested folders - preserve the subfolder structure
                valid_dest_dir = self.valid_root / rel_path
                invalid_dest_dir = self.invalid_root / rel_path
            else:
                # For the main selected folder itself - direct to root
                valid_dest_dir = self.valid_root
                invalid_dest_dir = self.invalid_root
        except Exception:
            # Fallback: use folder name directly
            valid_dest_dir = self.valid_root / folder_path.name
            invalid_dest_dir = self.invalid_root / folder_path.name
        
        # Create destination directories
        valid_dest_dir.mkdir(parents=True, exist_ok=True)
        invalid_dest_dir.mkdir(parents=True, exist_ok=True)
        
        # Get images
        images = [
            f for f in folder_path.iterdir()
            if f.is_file() and f.suffix.lower() in self.IMAGE_EXTENSIONS
        ]
        
        processed_count = 0
        
        for img_path in images:
            if self.stop_flag:
                break
            
            # Skip already processed images
            if self.VALID_FOLDER in str(img_path) or self.INVALID_FOLDER in str(img_path):
                continue
            
            # Read image
            img = cv2.imread(str(img_path))
            if img is None:
                continue
            
            # Perform detection
            detections = self.detector.detect(img)
            
            # Classify based on detection confidence
            strong = [d for d in detections if d["conf"] >= self.detector.strong_conf]
            medium = [
                d for d in detections
                if self.detector.medium_conf <= d["conf"] < self.detector.strong_conf
            ]
            
            # Determine destination (Valid or Invalid)
            dest_dir = valid_dest_dir if (len(strong) >= 1 or len(medium) >= 2) else invalid_dest_dir
            
            # Copy/Move image to centralized location
            dest_path = dest_dir / img_path.name
            
            # Handle duplicate filenames
            counter = 1
            original_stem = dest_path.stem
            while dest_path.exists():
                dest_path = dest_dir / f"{original_stem}_{counter}{img_path.suffix}"
                counter += 1
            
            # Move the image
            shutil.move(str(img_path), str(dest_path))
            
            processed_count += 1
            current_total = processed_so_far + processed_count
            
            # Update progress
            self.after(0, lambda c=current_total: self._update_progress(c, self.total_images))
        
        return processed_count
    
    def _finish_processing(self, success=True, processed_count=0, message=None):
        """Finish processing and update UI."""
        # Stop timer
        if self.time_update_job:
            self.after_cancel(self.time_update_job)
        
        final_time = self._format_time(self.elapsed_time)
        
        # Update UI state
        self.processing = False
        self.start_btn.config(state=tk.NORMAL, bg=self.COLOR_SUCCESS)
        self.stop_btn.config(state=tk.DISABLED)
        
        if success:
            self.status_label.config(text="Completed successfully! ✅", fg=self.COLOR_SUCCESS)
            self.current_folder_display.config(text="Completed", fg=self.COLOR_SUCCESS)
            
            # Get statistics
            valid_count = sum(1 for _ in self.valid_root.rglob('*') if _.is_file() and _.suffix.lower() in self.IMAGE_EXTENSIONS)
            invalid_count = sum(1 for _ in self.invalid_root.rglob('*') if _.is_file() and _.suffix.lower() in self.IMAGE_EXTENSIONS)
            
            # Delete original folder if option is enabled
            deleted_msg = ""
            if self.delete_original.get() and self.processed_folder_path:
                try:
                    self.status_label.config(text="Cleaning up - deleting processed subfolders...", fg=self.COLOR_INFO)
                    self.update_idletasks()
                    
                    # Delete all subfolders except Valid_Frames and Invalid_Frames
                    processed_path = Path(self.processed_folder_path)
                    for item in processed_path.iterdir():
                        if item.is_dir() and item.name not in {self.VALID_FOLDER, self.INVALID_FOLDER}:
                            shutil.rmtree(item)
                    
                    # Delete loose image files in the root of selected folder
                    for item in processed_path.iterdir():
                        if item.is_file() and item.suffix.lower() in self.IMAGE_EXTENSIONS:
                            item.unlink()
                    
                    deleted_msg = f"\n✓ Original subfolders deleted to save space"
                    
                    self.status_label.config(text="Completed and cleaned up! ✅", fg=self.COLOR_SUCCESS)
                except Exception as e:
                    deleted_msg = f"\n⚠ Warning: Could not delete all original content\n{str(e)}"
            
            messagebox.showinfo(
                "Processing Complete",
                f"Successfully processed '{self.selected_folder.get()}'\n\n"
                f"Total images: {processed_count}\n"
                f"Valid frames: {valid_count}\n"
                f"Invalid frames: {invalid_count}\n"
                f"Execution time: {final_time}\n\n"
                f"Output location:\n"
                f"{self.selected_folder.get()}/\n"
                f"  ├── {self.VALID_FOLDER}/\n"
                f"  └── {self.INVALID_FOLDER}/"
                f"{deleted_msg}"
            )
        else:
            if message:
                self.status_label.config(text=message, fg=self.COLOR_WARNING)
                messagebox.showinfo("No Images", message)
            else:
                self.status_label.config(text="Processing stopped", fg=self.COLOR_WARNING)
                
                # Ask if user wants to delete partial results
                if self.delete_original.get() and self.processed_folder_path:
                    response = messagebox.askyesno(
                        "Delete Original Content?",
                        "Processing was stopped. Do you still want to delete original subfolders?\n\n"
                        "(Valid_Frames and Invalid_Frames will be kept)\n\n"
                        "⚠ This action cannot be undone!"
                    )
                    
                    if response:
                        try:
                            processed_path = Path(self.processed_folder_path)
                            deleted_count = 0
                            
                            # Delete subfolders except Valid_Frames and Invalid_Frames
                            for item in processed_path.iterdir():
                                if item.is_dir() and item.name not in {self.VALID_FOLDER, self.INVALID_FOLDER}:
                                    shutil.rmtree(item)
                                    deleted_count += 1
                            
                            # Delete loose image files
                            for item in processed_path.iterdir():
                                if item.is_file() and item.suffix.lower() in self.IMAGE_EXTENSIONS:
                                    item.unlink()
                            
                            messagebox.showinfo(
                                "Processing Stopped",
                                f"Processing was stopped by user\n\n"
                                f"Images processed: {processed_count}\n"
                                f"Time elapsed: {final_time}\n\n"
                                f"✓ Original content deleted ({deleted_count} folders)"
                            )
                        except Exception as e:
                            messagebox.showwarning(
                                "Deletion Failed",
                                f"Could not delete original content:\n{str(e)}"
                            )
                    else:
                        messagebox.showinfo(
                            "Processing Stopped",
                            f"Processing was stopped by user\n\n"
                            f"Images processed: {processed_count}\n"
                            f"Time elapsed: {final_time}\n\n"
                            f"Original content preserved"
                        )
                else:
                    messagebox.showinfo(
                        "Processing Stopped",
                        f"Processing was stopped by user\n\n"
                        f"Images processed: {processed_count}\n"
                        f"Time elapsed: {final_time}"
                    )


def main():
    """Main entry point."""
    app = POIDetectorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
