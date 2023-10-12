import tkinter as tk
import uuid
from functools import partial
from pathlib import Path
from tkinter import ttk, filedialog, messagebox
import configparser
from tkinter import Canvas
import threading
import queue
from datetime import datetime
import webbrowser
# from utils import SharedState
import os
from calibrate_correct import CalibrateCorrect
from pattern_generator import PatternGenerator, DICTIONARY


def open_web_page(event):
    webbrowser.open('http://github.com/exponentialR')


class CalibrationApp:
    def __init__(self, root_):

        self.copyright_label = None
        self.footer_frame = None
        self.animated_text_index = None
        self.status_queue = queue.Queue()
        self.root = root_
        self.root.geometry("1080x920")
        self.root.title('Camera Calibration and Video Correction')
        self.root.configure(bg='black')
        self.create_footer(root_)

        self.calib_instance = None
        self.current_thread = None

        self.animated_text = ""
        self.animation_stop = False
        self.LOG_LEVELS = ['INFO', 'DEBUG', 'ERROR', 'WARNING', 'CORRECTED', 'CC-done']

        self.frame_interval_entry = None
        self.save_every_n_frames_entry = None

        # Initialize variables
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
        self.pattern_type_var = tk.StringVar()
        self.rows_var = tk.StringVar()
        self.columns_var = tk.StringVar()
        self.checker_width_var = tk.StringVar()
        self.marker_et_percentage_var = tk.StringVar()
        self.margin_var = tk.StringVar()
        self.dpi_var = tk.StringVar()
        self.display_video_var = tk.StringVar()
        self.display_video_options = ['Yes', 'No']
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
            ('Dictionary:', self.dictionary_var, self.create_dictionary_dropdown, None),
            ('Display Video During Calibration?:', self.display_video_var, self.create_video_display_dropdown, None)
        ]

        self.pattern_params = [('Calibration Pattern Type:', self.pattern_type_var, None, None),
                               ('Pattern Location (Where to save):', self.proj_repo_var, self.browse_proj_repo, None),
                               ('Number of Rows:', self.rows_var, None, None),
                               ('Number of Columns:', self.columns_var, None, None),
                               ('Checker Width (mm):', self.checker_width_var, None, None),
                               ('Percentage of Marker Length:', self.marker_et_percentage_var, None, None),
                               ('Length of Side Margin (mm):', self.margin_var, None, None),
                               ('Dots per Inch (dpi for printing):', self.dpi_var, None, None),
                               ('Dictionary:', self.dictionary_var, self.create_dictionary_dropdown, None)

                               ]

        # Initialize frames
        self.container = tk.Frame(self.root)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.start_frame = ttk.Frame(self.container, style='My.TFrame')
        self.input_frame = ttk.Frame(self.container, style='My.TFrame')
        self.status_frame = ttk.Frame(self.container, style='My.TFrame')
        self.dictionary_menu = ttk.OptionMenu(self.input_frame, self.dictionary_var, self.dictionary_options[0],
                                              *self.dictionary_options)
        self.display_video_menu = ttk.OptionMenu(self.input_frame, self.display_video_var,
                                                 self.display_video_options[0], *self.display_video_options)

        for frame in [self.start_frame, self.input_frame, self.status_frame]:
            frame.grid(row=0, column=0, sticky="nsew")

        self.made_with_love_label = tk.Label(self.start_frame, text="Made with ❤️ @ Queen's University Belfast.",
                                             bg='#ADD8E6',
                                             fg='black')
        self.made_with_love_label.grid(row=1000, column=0, pady=100, padx=20, sticky='ew', columnspan=50)

        self.start_frame.grid_columnconfigure(0, weight=1)

        self.video_display_frame = Canvas(self.status_frame, bg='#ADD8E6', height=360, width=440)
        self.video_display_frame.pack(side="top", fill="none", expand=True, anchor='n', padx=40, pady=10)

        self.animated_text_label = tk.Label(self.status_frame, bg='#ADD8E6', fg='#000000')
        self.animated_text_label.pack()

        # Styling the frames
        self.style = ttk.Style()
        self.label_style = {'bg': '#ADD8E6', 'fg': '#000000', 'font': ('Courier New', 12)}
        self.style.configure('My.TFrame', background='#ADD8E6')  # Light blue background
        self.welcome_frame = tk.Frame(self.start_frame, bg='#ADD8E6')
        self.welcome_frame.grid(row=0, column=0, columnspan=3, pady=20, sticky='ew')
        # Create the Label first
        self.welcome_label = tk.Label(self.welcome_frame, text="Camera Calibration Toolbox", **self.label_style)
        self.welcome_label.config(font=('Courier New', 25, 'bold'))
        self.welcome_label.grid(row=0, column=0)
        self.welcome_frame.grid_columnconfigure(0, weight=2)

        self.single_video_label = tk.Label(self.input_frame, text="Single Video File:", **self.label_style)
        self.single_video_entry = ttk.Entry(self.input_frame, textvariable=self.single_video_file_var, width=40)
        self.single_video_button = ttk.Button(self.input_frame, text="Browse", command=self.browse_single_video_file)

        # Create buttons
        ttk.Button(self.start_frame, text='CALIBRATE AND CORRECT', command=lambda: self.show_frame(self.input_frame,
                                                                                                   'Single Calib and Multiple Video Correction')).grid(
            row=1, column=0, pady=10, sticky='ew', padx=20)
        ttk.Button(self.start_frame, text="CALIBRATION ONLY",
                   command=lambda: self.show_frame(self.input_frame, "Calibrate Only")).grid(
            row=2, column=0, pady=10, sticky='ew', padx=20)
        ttk.Button(self.start_frame, text="CORRECTION ONLY", command=self.on_correct_only_click).grid(
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

        # Start Task button
        self.start_task_button = ttk.Button(self.input_frame, text="Start Task", command=self.start_task)
        self.start_task_button.grid(row=len(self.params) + 3, column=1, padx=5, pady=5)
        ttk.Button(self.input_frame, text="Back", command=lambda: self.show_frame(self.start_frame)).grid(
            row=len(self.params) + 4,
            column=1,
            padx=5, pady=5)
        self.task_label = tk.Label(self.input_frame, text="", font=("Verdana", 18, 'bold'), bg='#ADD8E6', fg='#000000')
        self.task_label.grid(row=0, column=0, columnspan=3, pady=20, sticky="ew")

        self.animation_active = False
        self.animated_text_label = tk.Label(self.status_frame, bg='#ADD8E6', fg='#000000')
        self.animated_text_label.pack()
        self.current_animation_id = None
        self.tree = ttk.Treeview(self.status_frame, columns=("Old Video", "Calibration File", "New Video"))
        self.tree.heading("#1", text="Old Video")
        self.tree.heading("#2", text="Calibration File")
        self.tree.heading("#3", text="New Video")
        self.tree.pack(side="bottom", fill="both", expand=True)

        self.back_button = tk.Button(self.status_frame, text="Back", command=self.go_back)
        self.back_button.pack()

        self.status_text_frame = tk.Frame(self.status_frame)
        self.status_text_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.scrollbar = tk.Scrollbar(self.status_text_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.status_text = tk.Text(self.status_text_frame, wrap="word", width=150, height=40,
                                   yscrollcommand=self.scrollbar.set)
        self.status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.status_text.yview)

        self.status_text.tag_configure("INFO", foreground="black", font=('Cambria', 9,))
        self.status_text.tag_configure("DEBUG", foreground="blue", font=('Verdana', 9))
        self.status_text.tag_configure("", foreground="blue", font=('Verdana', 9))
        self.status_text.tag_configure("-", foreground="black", font=('Verdana', 9))
        self.status_text.tag_configure("WARNING", foreground="orange")
        self.status_text.tag_configure("ERROR", foreground="red")
        self.status_text.tag_configure("CORRECTED", foreground="red")

        self.show_frame(self.start_frame)
        self.tree.pack(side="bottom", fill="both", expand=True)

        self.load_entries_from_config()
        self.root.after(10, self.update_gui)
        self.root.mainloop()

    def show_frame(self, frame, text=None):
        self.task_label.config(text=text)
        self.populate_form_based_on_task(text)
        frame.tkraise()

    def populate_form_with_params(self, params):
        print("Populating form with:", params)  # Debugging line

        for widget in self.input_frame.winfo_children():
            widget.grid_forget()

        # Then repopulate
        self.task_label.grid(row=0, column=0, columnspan=3, pady=20, sticky="ew")
        n_rows = len(params)

        for i, (text, var, cmd, _) in enumerate(params):
            print(text)

            label = tk.Label(self.input_frame, text=text, **self.label_style)
            label.grid(row=i + 1, column=0, sticky="w")

            if text == 'Dictionary:':
                cmd(i + 1, 1)
            elif text == "Display Video During Calibration?:":
                cmd(i + 1, 1)

            else:

                entry = ttk.Entry(self.input_frame, textvariable=var, width=40)
                entry.grid(row=i + 1, column=1)

                if cmd:
                    ttk.Button(self.input_frame, text="Browse", command=cmd).grid(row=i + 1, column=2)

        # Add the Start Task button
        self.start_task_button.grid(row=n_rows + 1, column=1, padx=5, pady=5)
        # Add a new Back button just for this frame
        ttk.Button(self.input_frame, text="Back", command=lambda: self.show_frame(self.start_frame)).grid(
            row=n_rows + 2, column=1, padx=5, pady=5)

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
            self.populate_form_with_params(self.pattern_params)

    def on_self_calibrate_correct_click(self):
        self.show_frame(self.status_frame, "Self-Calibrate & Correct")
        self.calib_instance = CalibrateCorrect(
            self.proj_repo_var.get(),
            self.project_name_var.get(),
            self.video_files_var.get().split(';'),  # Assuming files are separated by semicolons
            int(self.squaresX_var.get()),
            int(self.squaresY_var.get()),
            int(self.squareLength_var.get()),
            int(self.markerLength_var.get()),
            self.dictionary_var.get(),
            int(self.frame_interval_calib_var.get()),
            video_frame=self.video_display_frame,
            save_every_n_frames=int(self.save_every_n_frames_var.get()),
            display=str(self.display_video_var.get()),
            status_queue=self.status_queue
        )
        self.current_thread = threading.Thread(target=self.calib_instance.self_calibrate_correct)  # .start()
        self.current_thread.start()

    def on_calibrate_correct_click(self):
        self.show_frame(self.status_frame, 'Single Calib and Multiple Video Correction')
        self.calib_instance = CalibrateCorrect(
            self.proj_repo_var.get(),
            self.project_name_var.get(),
            self.video_files_var.get().split(';'),  # Assuming files are separated by semicolons
            int(self.squaresX_var.get()),
            int(self.squaresY_var.get()),
            int(self.squareLength_var.get()),
            int(self.markerLength_var.get()),
            self.dictionary_var.get(),
            int(self.frame_interval_calib_var.get()),
            video_frame=self.video_display_frame,
            save_every_n_frames=int(self.save_every_n_frames_var.get()),
            display=str(self.display_video_var.get()),
            status_queue=self.status_queue
        )
        self.current_thread = threading.Thread(target=self.calib_instance.singleCalibMultiCorrect,
                                               args=(self.single_video_file_var.get(),))
        self.current_thread.start()

    def on_calibrate_click(self):
        self.show_frame(self.status_frame, "Calibrate Only")

        self.calib_instance = CalibrateCorrect(
            self.proj_repo_var.get(),
            self.project_name_var.get(),
            self.video_files_var.get().split(';'),  # Assuming files are separated by semicolons
            int(self.squaresX_var.get()),
            int(self.squaresY_var.get()),
            int(self.squareLength_var.get()),
            int(self.markerLength_var.get()),
            self.dictionary_var.get(),
            int(self.frame_interval_calib_var.get()),
            video_frame=self.video_display_frame,
            save_every_n_frames=int(self.save_every_n_frames_var.get()),
            display=str(self.display_video_var.get()),
            status_queue=self.status_queue
        )
        self.current_thread = threading.Thread(target=self.calib_instance.calibrate_only)  # .start()
        self.current_thread.start()

    def on_generate_pattern_click(self):
        self.show_frame(self.status_frame, 'Generate Calibration Pattern')
        self.calib_instance = PatternGenerator(pattern_type=self.pattern_type_var.get(),
                                               rows=int(self.rows_var.get()),
                                               columns=int(self.columns_var.get()),
                                               checker_width=int(self.checker_width_var.get()),
                                               dictionary=self.dictionary_var.get(),
                                               marker_et_percentage=float(self.marker_et_percentage_var.get()),
                                               margin=int(self.margin_var.get()),
                                               dpi=int(self.dpi_var.get()),
                                               status_queue=self.status_queue,
                                               pattern_location=Path(self.proj_repo_var.get()), )
        self.current_thread = threading.Thread(target=self.calib_instance.generate)
        self.current_thread.start()

    def on_correct_only_click(self):
        self.show_frame(self.status_frame, "Correct Only")
        answer = messagebox.askyesno("Use own Calibration", "Would you like to use your own calibration files?")
        if answer:
            self.correct_only_popup_window()

        else:
            messagebox.showinfo('Notice',
                                'Saved settings and previously calculated calibration paramaters will be used ')
            self.show_frame(self.input_frame, "Correct Only")
            self.start_task_button.config(command=lambda: self.start_correct_only_task())

    def correct_only_popup_window(self):
        popup = tk.Toplevel()
        popup.title("Correct Only Settings")

        calib_files_var = tk.StringVar()
        video_files_var_ = tk.StringVar()

        ttk.Label(popup, text="View Video:").grid(row=0, column=0)
        ttk.OptionMenu(popup, 'Yes').grid(row=0, column=1)

        def browse_calib_files():
            files_selected = filedialog.askopenfilenames()
            calib_files_var.set(';'.join(files_selected))

        def browse_video_files_():
            files_selected = filedialog.askopenfilenames()
            video_files_var_.set(';'.join(files_selected))

        ttk.Label(popup, text="Select Calibration Files:").grid(row=1, column=0)
        ttk.Button(popup, text="Browse", command=browse_calib_files).grid(row=1, column=1)

        ttk.Label(popup, text="Select Video Files:").grid(row=2, column=0)
        ttk.Button(popup, text="Browse", command=browse_video_files_).grid(row=2, column=1)

        def on_done_click():
            calib_files = calib_files_var.get().split(';')
            video_files = video_files_var_.get().split(';')

            if len(calib_files) != len(video_files):
                messagebox.showerror("Error", "The number of calibration files must match the number of video files.")
                return

            merged_dict = dict(zip(video_files, calib_files))
            self.calib_instance_correct_only = CalibrateCorrect(
                self.proj_repo_var.get(),
                self.project_name_var.get(),
                self.video_files_var.get().split(';'),
                int(self.squaresX_var.get()),
                int(self.squaresY_var.get()),
                int(self.squareLength_var.get()),
                int(self.markerLength_var.get()),
                self.dictionary_var.get(),
                int(self.frame_interval_calib_var.get()),
                video_frame=self.video_display_frame,
                save_every_n_frames=int(self.save_every_n_frames_var.get()),
                display=str(self.display_video_var.get()),
                status_queue=self.status_queue
            )
            self.current_thread = threading.Thread(target=self.calib_instance_correct_only.correct_only,
                                                   args=merged_dict)  # .start()
            self.current_thread.start()

            popup.destroy()

        ttk.Button(popup, text="Done", command=on_done_click).grid(row=3, column=0, columnspan=2)

    def start_correct_only_task(self):
        self.save_entries_to_config()
        self.calib_instance = CalibrateCorrect(
            self.proj_repo_var.get(),
            self.project_name_var.get(),
            self.video_files_var.get().split(';'),  # Assuming files are separated by semicolons
            int(self.squaresX_var.get()),
            int(self.squaresY_var.get()),
            int(self.squareLength_var.get()),
            int(self.markerLength_var.get()),
            self.dictionary_var.get(),
            int(self.frame_interval_calib_var.get()),
            status_queue=self.status_queue,
            video_frame=self.video_display_frame,

        )
        self.show_frame(self.status_frame, "Correct Only")
        self.current_thread = threading.Thread(target=self.calib_instance.correct_only, args=(None,))  # .start()
        self.current_thread.start()

    def create_dictionary_dropdown(self, row, column):
        if hasattr(self, 'dictionary_menu'):
            self.dictionary_menu.grid_forget()
        self.dictionary_menu.grid(row=row, column=column)

    def create_video_display_dropdown(self, row, column):
        if hasattr(self, 'display_video_menu'):
            self.display_video_menu.grid_forget()
        self.display_video_menu.grid(row=row, column=column)

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

    def create_footer(self, root_):
        self.footer_frame = tk.Frame(root_, bg='green')
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
        self.copyright_label.bind("<Button-1>", open_web_page)

    def go_back(self):

        self.calib_instance.stop()
        self.status_queue.queue.clear()

        # Wait for the thread to stop (optional and should be used cautiously)
        if self.current_thread and self.current_thread.is_alive():
            self.current_thread.join(timeout=1)

        # Nullify the instances
        self.calib_instance = None
        self.current_thread = None

        # Stop any running animations
        self.stop_animation()

        # Clear the status queue to remove any lingering updates
        while not self.status_queue.empty():
            try:
                self.status_queue.get_nowait()
            except queue.Empty:
                break

        # Show the starting frame again
        self.show_frame(self.start_frame)

        # Optionally, display a user feedback message that the task has been stopped
        messagebox.showinfo("Task Stopped", "The running task has been stopped.")

    def browse_proj_repo(self):
        folder_selected = filedialog.askdirectory()
        self.proj_repo_var.set(folder_selected)

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

    def play_video(self):
        if self.calib_instance is not None:
            self.calib_instance.play_video()

    def pause_video(self):
        if self.calib_instance is not None:
            self.calib_instance.pause_video()

    def insert_status_text(self, text, log_level='INFO'):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        current_scroll_position = self.status_text.yview()[1]

        if log_level in self.LOG_LEVELS:  # For non-empty log levels
            full_text = f'\n[{timestamp}] [{log_level}] - {text}\n'
            self.status_text.insert(tk.END, full_text, log_level)
        elif log_level == "-" or log_level in self.LOG_LEVELS:
            full_text = f'{text}\n'
            self.stop_animation()
            self.animation_stop = True
            self.status_text.insert(tk.END, full_text, log_level)
        elif log_level == 'anime':
            if self.animated_text_index is not None:
                self.status_text.delete(self.animated_text_index, f"{self.animated_text_index} lineend")
            full_text = f'{text}\n'
            self.status_text.insert(tk.END, full_text)

            self.animated_text_index = self.status_text.index(tk.END)  # Store the index of the animated text
            self.animated_text_index = f"{float(self.animated_text_index) - 1.0} linestart"  # Go to the beginning of the line
            self.animation_stop = False  # Reset the stop flag
            self.start_animation(text)  # Start the animation
        elif log_level == 'stop-anime':
            self.animation_stop = True
        else:  # For empty log level
            pass

        new_scroll_position = self.status_text.yview()[1]

        # Only automatically scroll to the end if the user was already at the bottom
        if current_scroll_position == 1.0 or new_scroll_position == 1.0:
            self.status_text.see(tk.END)

    def start_animation(self, initial_text):
        if not self.animation_stop and self.animated_text_index and not self.animation_active:
            new_animation_id = uuid.uuid4()
            self.current_animation_id = new_animation_id
            self._start_animation_helper(initial_text, new_animation_id)

    def _start_animation_helper(self, initial_text, animation_id):
        if self.current_animation_id == animation_id:
            num_dots = int(datetime.now().timestamp()) % 5
            animated_text = f"{initial_text} {'|||' * num_dots}"
            self.status_text.delete(self.animated_text_index, f"{self.animated_text_index} lineend")
            self.status_text.insert(self.animated_text_index, animated_text)

            self.root.after(500, lambda: self._start_animation_helper(initial_text, animation_id))

    def stop_animation(self):
        self.animation_stop = True
        self.current_animation_id = None

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
                    print(f'CURRENT STATUS: {current_status}')
                    for old_video, corrected_vid_details in current_status.items():
                        old_video_name = os.path.basename(old_video).split('.')[0]
                        calib_file, new_video = corrected_vid_details[0], corrected_vid_details[1]
                        self.tree.insert("", tk.END, values=(old_video_name, calib_file, new_video))

                self.insert_status_text(current_status, log_level)

        except queue.Empty:
            pass
        self.root.after(10, self.update_gui)


if __name__ == '__main__':
    root = tk.Tk()
    app = CalibrationApp(root)
