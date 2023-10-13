import configparser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import queue
import os

from calibrate_correct import DICTIONARY
from utils import open_web_page


class CalibrationUI:
    def __init__(self, root, status_queue, calib_instance):
        self.root = root
        self.container = tk.Frame(self.root)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.start_frame = ttk.Frame(self.container)
        self.input_frame = ttk.Frame(self.container)
        self.status_frame = ttk.Frame(self.container)
        self.status_queue = status_queue
        self.copyright_label = None
        self.footer_frame = None

        # Initialize variables for Calibrations
        self.proj_repo_var = tk.StringVar()
        self.project_name_var = tk.StringVar()
        self.video_files_var = tk.StringVar()
        self.squaresX_var = tk.StringVar()
        self.squaresY_var = tk.StringVar()
        self.squareLength_var = tk.StringVar()
        self.markerLength_var = tk.StringVar()
        self.frame_interval_calib_var = tk.StringVar()
        self.save_every_n_frames_var = tk.StringVar()
        self.dictionary_var = tk.StringVar()
        self.single_video_file_var = tk.StringVar()
        self.dictionary_options = DICTIONARY

        # Variables for Pattern Generator
        self.pattern_type_var = tk.StringVar()
        self.pattern_type_var.trace('w', self.update_pattern_form)
        self.rows_var = tk.StringVar()
        self.columns_var = tk.StringVar()
        self.checker_width_var = tk.StringVar()
        self.marker_et_percentage_var = tk.StringVar()
        self.margin_var = tk.StringVar()
        self.dpi_var = tk.StringVar()
        self.display_video_var = tk.StringVar()
        self.display_video_options = ['Yes', 'No']
        self.pattern_type_options = ['Charuco', 'Checker']

        self.dictionary_options = DICTIONARY

        self.params = [
            ("Project Repository:", self.proj_repo_var, self.browse_proj_repo, None),
            ("Project Name:", self.project_name_var, None, None),
            ("Video Files (for correction):", self.video_files_var, self.browse_video_files, None),
            ("SquaresX:", self.squaresX_var, None, None),
            ("SquaresY:", self.squaresY_var, None, None),
            ("SquareLength:", self.squareLength_var, None, None),
            ("MarkerLength:", self.markerLength_var, None, None),
            ("Frame Interval:", self.frame_interval_calib_var, None, None),
            ("Save Every N Frames:", self.save_every_n_frames_var, None, None),
            ('Dictionary:', self.dictionary_var, self.create_dropdown, None),
            ('Display Video During Calibration?:', self.display_video_var, self.create_dropdown, None)
        ]

        self.common_pattern_params = [('Calibration Pattern Type:', self.pattern_type_var, self.create_dropdown, None),
                                      ('Pattern Location (Where to save):', self.proj_repo_var, self.browse_proj_repo,
                                       None),
                                      ('Number of Rows:', self.rows_var, None, None),
                                      ('Number of Columns:', self.columns_var, None, None),
                                      ('Square Size/Checker Width (mm):', self.checker_width_var, None, None),
                                      ('Length of Side Margin (mm):', self.margin_var, None, None),
                                      ('Dots per Inch (dpi for printing):', self.dpi_var, None, None), ]

        self.charuco_exclusive_params = [('Dictionary:', self.dictionary_var, self.create_dropdown, None),
                                         ('Marker/Square Ratio:', self.marker_et_percentage_var, None, None),
                                         ]
        self.checker_exclusive_params = []
        self.start_task_button = ttk.Button(self.input_frame, text="Start Task", command=self.start_task)
        self.task_label = tk.Label(self.input_frame, text="", font=("Verdana", 18, 'bold'), bg='#ADD8E6', fg='#000000')

        self.setup_main_window()
        self.create_footer()
        # Initialize frames
        self.initialize_frames()
        # Initialize variables for Calibrations
        self.create_buttons()
        self.LOG_LEVELS = ['INFO', 'DEBUG', 'ERROR', 'WARNING', 'CORRECTED', 'CC-done']

        self.calib_instance = calib_instance

    def setup_main_window(self):
        self.root.geometry("1080x920")
        self.root.title('CalibraVision')
        self.root.configure(bg='black')

    def create_footer(self):
        self.footer_frame = tk.Frame(self.root, bg='green')
        self.footer_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.copyright_label = tk.Label(
            self.footer_frame,
            text=f"(c) {datetime.now().year} Samuel Adebayo",
            bg='green',
            fg='white',
            padx=20,
            pady=10,
            cursor="hand2",
            relief="raised",
            bd=4
        )
        self.copyright_label.pack(side=tk.BOTTOM, anchor='s')
        # You can bind this to a function that opens a web page
        self.copyright_label.bind("<Button-1>", open_web_page)

    def create_dropdown(self, row, column, menu_attribute):
        if hasattr(self, menu_attribute):
            getattr(self, menu_attribute).grid_forget()
            getattr(self, menu_attribute).grid(row=row, column=column)
        else:
            pass

    def browse_video_files(self):
        files_selected = filedialog.askopenfilenames(
            filetypes=[
                (
                    "Video files",
                    "*.mp4 *.MP4 *.avi *.AVI *.mov *.MOV *.flv *.FLV *.mkv *.MKV *.wmv *.WMV *.webm *.WEBM"),
                ("All files", "*.*")
            ]
        )
        self.video_files_var.set(';'.join(files_selected))

    def initialize_frames(self):
        for frame in [self.start_frame, self.input_frame, self.status_frame]:
            frame.grid(row=0, column=0, sticky="nsew")

    def create_buttons(self, text=None, on_correct_only_click=None):
        if text is not None:
            ttk.Button(self.start_frame, text='CALIBRATE AND CORRECT', command=lambda: self.show_frame(self.input_frame,
                                                                                                       'Single Calib and Multiple Video Correction')).grid(
                row=1, column=0, pady=10, sticky='ew', padx=20)
            ttk.Button(self.start_frame, text="CALIBRATION ONLY",
                       command=lambda: self.show_frame(self.input_frame, "Calibrate Only")).grid(
                row=2, column=0, pady=10, sticky='ew', padx=20)
            if on_correct_only_click is not None:
                ttk.Button(self.start_frame, text="CORRECTION ONLY", command=on_correct_only_click).grid(
                    row=3,
                    column=0,
                    pady=10,
                    sticky='ew',
                    padx=20
                )
            ttk.Separator(self.start_frame, orient='horizontal').grid(row=4, column=0, sticky='ew', padx=20)
            tk.Label(self.start_frame, text="Others", bg='#ADD8E6').grid(row=5, column=0, sticky='w', padx=20)
            ttk.Button(self.start_frame, text="START SELF-CALIBRATION & CORRECTION",
                       command=lambda: self.show_frame(self.input_frame, "Self-Calibrate & Correct")).grid(row=8, column=0,
                                                                                                           pady=10,
                                                                                                           sticky='ew',
                                                                                                           padx=20)

            ttk.Button(self.start_frame, text='GENERATE CALIBRATION PATTERN',
                       command=lambda: self.show_frame(self.input_frame, 'Generate Calibration Pattern')).grid(
                row=9, column=0, pady=10, sticky='ew', padx=20)

            self.task_label.grid(row=0, column=0, columnspan=3, pady=20, sticky="ew")

            # Start Task button
            self.start_task_button.grid(row=len(self.params) + 3, column=1, padx=5, pady=5)
            ttk.Button(self.input_frame, text="Back", command=lambda: self.show_frame(self.start_frame)).grid(
                row=len(self.params) + 4,
                column=1,
                padx=5, pady=5)

    def show_frame(self, frame, text=None):
        self.task_label.config(text=text)
        self.populate_form_based_on_task(text)
        frame.tkraise()

    def browse_proj_repo(self):
        folder_selected = filedialog.askdirectory()
        self.proj_repo_var.set(folder_selected)

    def populate_form_based_on_task(self, task):
        params_copy = [list(p) for p in self.params]

        if task == "Calibrate Only":
            for i, param in enumerate(params_copy):
                if param[0] == "Video Files (for correction):":
                    param[0] = "Video Files (for calibration):"
            self.populate_form_with_params(params_copy)

        elif task == "Correct Only":
            self.populate_form_with_params(params_copy[:7])  # Assuming first 7 are necessary

        elif task == "Self-Calibrate & Correct":
            self.populate_form_with_params(params_copy)

        elif task == "Single Calib and Multiple Video Correction":
            params_copy.append(["Single Video File:", self.single_video_file_var, self.browse_single_video_file, None])
            self.populate_form_with_params(params_copy)
            self.shift_down_widgets(start_row=4, shift_amount=1)

        elif task == "Generate Calibration Pattern":
            pattern_type = self.pattern_type_var.get()
            if pattern_type == 'Charuco':
                self.populate_pattern_form(self.charuco_exclusive_params)
            else:
                self.populate_pattern_form(self.checker_exclusive_params)

    def update_gui(self):
        try:
            while True:
                current_status, log_level = self.status_queue.get_nowait()
                if log_level == "CORRECTED" or log_level == 'CC-done':
                    display_video_side_side = messagebox.askyesno("Display Corrected Video(s)",
                                                                  "Would you like to display the corrected videos?")
                    if display_video_side_side and self.calib_instance:
                        self.calib_instance.display_corrected_video()
                elif log_level == "-" or log_level in self.LOG_LEVELS:
                    self.animation_active = False
                    self.stop_animation()
                elif log_level == "update-treeview":
                    for item in self.tree.get_children():
                        self.tree.delete(item)
                    for old_video, corrected_vid_details in current_status.items():
                        old_video_name = os.path.basename(old_video).split('.')[0]
                        calib_file, new_video = corrected_vid_details[0], corrected_vid_details[1]
                        self.tree.insert("", tk.END, values=(old_video_name, calib_file, new_video))

                elif log_level == 'display-pattern':
                    """"""

                self.insert_status_text(current_status, log_level)

        except queue.Empty:
            pass
        self.root.after(10, self.update_gui)

    def populate_form_with_params(self, params):
        # Your code to populate form with parameters
        pass

    def update_pattern_form(self, *args):
        pattern_type = self.pattern_type_var.get()
        if pattern_type == 'Charuco':
            self.populate_pattern_form(self.charuco_exclusive_params)
        else:
            self.populate_pattern_form(self.checker_exclusive_params)

    def populate_pattern_form(self, exclusive_params):
        all_params = self.common_pattern_params + exclusive_params
        self.populate_form_with_params(all_params)

    def browse_single_video_file(self):
        single_video_file = filedialog.askopenfilename(
            filetypes=[
                (
                    "Video files",
                    "*.mp4 *.MP4 *.avi *.AVI *.mov *.MOV *.flv *.FLV *.mkv *.MKV *.wmv *.WMV *.webm *.WEBM"),
                ("All files", "*.*")
            ]
        )
        self.single_video_file_var.set(single_video_file)

    def shift_down_widgets(self, start_row, shift_amount):
        for child in self.input_frame.winfo_children():
            info = child.grid_info()
            if info:
                current_row = int(info['row'])
                if current_row >= start_row:
                    child.grid(row=current_row + shift_amount)

    def start_task(self):
        self.save_entries_to_config()

        if self.task_label.cget("text") == "Calibrate Only":
            self.on_calibrate_click()
        elif self.task_label.cget("text") == "Correct Only":
            self.on_correct_only_click()
        elif self.task_label.cget('text') == 'Self-Calibrate & Correct':
            self.on_self_calibrate_correct_click()
        elif self.task_label.cget("text") == 'Single Calib and Multiple Video Correction':
            self.on_calibrate_correct_click()
        elif self.task_label.cget("text") == 'Generate Calibration Pattern':
            self.on_generate_pattern_click()
            pass

    def save_entries_to_config(self):
        config = configparser.ConfigParser()
        config['Parameters'] = {
            'Project Repository': self.proj_repo_var.get(),
            'Project Name': self.project_name_var.get(),
            'Single Video Calib': self.single_video_file_var.get(),
            'Video Files': self.video_files_var.get(),
            'SquareX': self.squaresX_var.get(),
            'SquareY': self.squaresY_var.get(),
            'SquareLength': self.squareLength_var.get(),
            'MarkerLength': self.markerLength_var.get(),
            'Frame Interval': self.frame_interval_calib_var.get(),
            'Save Every N Frames': self.save_every_n_frames_var.get(),
            'Dictionary': self.dictionary_var.get(),
            'Display Video': self.display_video_var.get()
        }
        with open('settings.ini', 'w') as configfile:
            config.write(configfile)

    def load_entries_from_config(self):
        config = configparser.ConfigParser()
        config.read('settings.ini')
        if 'Parameters' in config:
            self.proj_repo_var.set(config['Parameters'].get('Project Repository', ''))
            self.project_name_var.set(config['Parameters'].get('Project Name', ''))
            self.single_video_file_var.set(config['Parameters'].get('Single Video Calib', ''))
            self.video_files_var.set(config['Parameters'].get('Video Files', ''))
            self.squaresX_var.set(config['Parameters'].get('SquareX', ''))
            self.squaresY_var.set(config['Parameters'].get('SquareY', ''))
            self.squareLength_var.set(config['Parameters'].get('SquareLength', ''))
            self.markerLength_var.set(config['Parameters'].get('MarkerLength', ''))
            self.frame_interval_calib_var.set(config['Parameters'].get('Frame Interval', ''))
            self.save_every_n_frames_var.set(config['Parameters'].get('Save Every N Frames', ''))
            self.dictionary_var.set(config['Parameters'].get('Dictionary', ''))
            self.display_video_var.set(config['Parameters'].get('Display Video', ''))

