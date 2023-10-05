import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox
from calibrate_correct import CalibrateCorrect
import configparser
from tkinter import Canvas, StringVar
import threading
import queue
from datetime import datetime
import webbrowser


class CalibrationApp:
    def __init__(self, root):
        self.status_queue = queue.Queue()
        self.root = root
        self.root.geometry("1080x920")
        self.root.title('Camera Calibration and Video Correction')
        self.root.configure(bg='blue')
        self.create_footer(root)
        # self.footer_frame = tk.Frame(root, bg='green')
        # self.footer_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.calib_instance = None
        self.current_thread = None

        self.animated_text = ""
        self.animation_stop = False
        self.LOG_LEVELS = ['INFO', 'DEBUG', 'ERROR', 'WARNING', 'CORRECTED', 'CC-done']

        self.display_video_label = None
        self.display_video_menu = None
        self.frame_interval_entry = None
        self.save_every_n_frames_entry = None
        # self.calib_instance = None

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
        self.display_video_var = tk.StringVar()

        self.params = [
            ("Project Repository:", self.proj_repo_var, self.browse_proj_repo, None),
            ("Project Name:", self.project_name_var, None, None),
            ("Video Files:", self.video_files_var, self.browse_video_files, None),
            ("SquaresX:", self.squaresX_var, None, None),
            ("SquaresY:", self.squaresY_var, None, None),
            ("SquareLength:", self.squareLength_var, None, None),
            ("MarkerLength:", self.markerLength_var, None, None),
            ("Frame Interval:", self.frame_interval_calib_var, None, None),
            ("Save Every N Frames:", self.save_every_n_frames_var, None, None)
        ]

        # Initialize frames
        self.container = tk.Frame(self.root)
        self.container.pack(side="top", fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.start_frame = ttk.Frame(self.container, style='My.TFrame')
        self.input_frame = ttk.Frame(self.container, style='My.TFrame')
        self.status_frame = ttk.Frame(self.container, style='My.TFrame')
        self.control_frame = ttk.Frame(self.root)
        self.control_frame.pack(side="bottom")
        for frame in [self.start_frame, self.input_frame, self.status_frame]:
            frame.grid(row=0, column=0, sticky="nsew")

        self.made_with_love_label = tk.Label(self.start_frame, text="Made with ❤️ @ Queen's University Belfast.",
                                             bg='#ADD8E6',
                                             fg='black')  # Adjust the background and foreground colors to match your theme
        self.made_with_love_label.grid(row=4, column=0, pady=100, sticky='ew', columnspan=3)

        self.start_frame.grid_columnconfigure(0, weight=1)

        self.video_display_frame = Canvas(self.status_frame, bg='#ADD8E6', height=360, width=440)
        self.video_display_frame.pack(side="top", fill="none", expand=True, anchor='n', padx=40, pady=10)

        self.animated_text_label = tk.Label(self.status_frame, bg='#ADD8E6', fg='#000000')
        self.animated_text_label.pack()

        self.back_button = tk.Button(self.status_frame, text="Back", command=self.go_back)
        self.back_button.pack()

        # Styling the frames
        self.style = ttk.Style()
        self.label_style = {'bg': '#ADD8E6', 'fg': '#000000', 'font': ('Helvetica', 12)}
        self.style.configure('My.TFrame', background='#ADD8E6')  # Light blue background
        self.welcome_frame = tk.Frame(self.start_frame, bg='#ADD8E6')

        self.welcome_frame.grid(row=0, column=0, columnspan=3, pady=20, sticky='ew')
        # Create the Label first
        self.welcome_label = tk.Label(self.welcome_frame, text="Welcome to Camera Calibration and Correction",
                                      **self.label_style)
        self.welcome_label.config(font=('Helvetica', 24))
        self.welcome_label.grid(row=0, column=0)

        self.welcome_frame.grid_columnconfigure(0, weight=1)
        # Create buttons
        ttk.Button(self.start_frame, text=" START CALIBRATION",
                   command=lambda: self.show_frame(self.input_frame, "Calibrate Only")).grid(
            row=1, column=0, pady=10, sticky='w', padx=20)
        ttk.Button(self.start_frame, text=" START CORRECTION", command=self.on_correct_only_click).grid(
            row=2,
            column=0,
            pady=10,
            sticky='w',
            padx=20
        )

        ttk.Button(self.start_frame, text="START CALIBRATION & CORRECTION",
                   command=lambda: self.show_frame(self.input_frame, "Calibrate and Correct")).grid(row=3, column=0,
                                                                                                    pady=10,
                                                                                                    sticky='w',
                                                                                                    padx=20)

        # Start Task button
        self.start_task_button = ttk.Button(self.input_frame, text="Start Task", command=self.start_task)
        self.start_task_button.grid(row=len(self.params) + 3, column=1, padx=5, pady=5)
        ttk.Button(self.input_frame, text="Back", command=lambda: self.show_frame(self.start_frame)).grid(
            row=len(self.params) + 4,
            column=1,
            padx=5, pady=5)
        self.task_label = tk.Label(self.input_frame, text="", font=("Helvetica", 18), bg='#ADD8E6', fg='#000000')
        self.task_label.grid(row=0, column=0, columnspan=3, pady=20, sticky="ew")

        for i, (text, var, cmd, _) in enumerate(self.params):
            label = tk.Label(self.input_frame, text=text, **self.label_style)
            label.grid(row=i + 1, column=0, sticky="w")
            entry = ttk.Entry(self.input_frame, textvariable=var, width=40)
            entry.grid(row=i + 1, column=1)

            if text == "Frame Interval:":
                self.frame_interval_entry = entry
            elif text == "Save Every N Frames:":
                self.save_every_n_frames_entry = entry

            if cmd:
                ttk.Button(self.input_frame, text="Browse", command=cmd).grid(row=i + 1, column=2)

            # Store the reference back into params
            self.params[i] = (text, var, cmd, label)
        self.dictionary_options = [
            'DICT_4X4_50', 'DICT_4X4_100', 'DICT_4X4_250', 'DICT_4X4_1000', 'DICT_5X5_50',
            'DICT_5X5_100', 'DICT_5X5_250', 'DICT_5X5_1000',
            'DICT_6X6_50', 'DICT_6X6_100', 'DICT_6X6_250', 'DICT_6X6_1000',
            'DICT_7X7_50', 'DICT_7X7_100', 'DICT_7X7_250', 'DICT_7X7_1000',
            'DICT_ARUCO_ORIGINAL', 'DICT_APRILTAG_16h5', 'DICT_APRILTAG_16H5',
            'DICT_APRILTAG_25h9', 'DICT_APRILTAG_25H9', 'DICT_APRILTAG_36h10',
            'DICT_APRILTAG_36H10', 'DICT_APRILTAG_36h11', 'DICT_APRILTAG_36H11',
            'DICT_ARUCO_MIP_36h12', 'DICT_ARUCO_MIP_36H12'
        ]
        self.dictionary_label_style = {'foreground': '#000000', 'font': ('Helvetica', 12)}
        ttk.Label(self.input_frame, text="Dictionary:", **self.dictionary_label_style).grid(row=len(self.params) + 1,
                                                                                            column=0,
                                                                                            sticky="w")
        self.dictionary_menu = ttk.OptionMenu(self.input_frame, self.dictionary_var, self.dictionary_options[0],
                                              *self.dictionary_options)
        self.dictionary_menu.grid(row=len(self.params) + 1, column=1)

        self.display_video_frame_options = ['Yes', 'No']
        self.display_video_label_style = {'foreground': '#000000', 'font': ('Helvetica', 10)}
        self.display_video_label = ttk.Label(self.input_frame, text="Display Video during Calibration?:",
                                             **self.display_video_label_style)
        self.display_video_label.grid(row=len(self.params) + 2, column=0, sticky="w")

        self.display_video_menu = ttk.OptionMenu(self.input_frame, self.display_video_var,
                                                 self.display_video_frame_options[0],
                                                 *self.display_video_frame_options)
        self.display_video_menu.grid(row=len(self.params) + 2, column=1)

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
        self.load_entries_from_config()
        self.root.after(10, self.update_gui)
        self.root.mainloop()


    def create_footer(self, root):
        self.footer_frame = tk.Frame(root, bg='green')
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
        self.copyright_label.bind("<Button-1>", self.open_web_page)

    def open_web_page(self, event):
        webbrowser.open('http://github.com/exponentialR')

    # def go_back(self):
    #     if self.calib_instance:
    #         self.calib_instance.stop_requested = True
    #
    #     if self.current_thread and self.current_thread.is_alive():
    #         pass
    #     self.calib_instance = None
    #     self.current_thread = None
    #     self.show_frame(self.start_frame)
    def go_back(self):
        # Flag to stop the running task in CalibrateCorrect
        # if self.calib_instance:
        self.calib_instance.stop()
        self.status_queue.queue.clear()


        # Wait for the thread to stop (optional and should be used cautiously)
        # if self.current_thread and self.current_thread.is_alive():
        #     self.current_thread.join(timeout=1)  # Uncomment this only if it makes sense for your use case

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
            self.video_files_var.set(config['Parameters'].get('Video Files', ''))
            self.squaresX_var.set(config['Parameters'].get('SquareX', ''))
            self.squaresY_var.set(config['Parameters'].get('SquareY', ''))
            self.squareLength_var.set(config['Parameters'].get('SquareLength', ''))
            self.markerLength_var.set(config['Parameters'].get('MarkerLength', ''))
            self.frame_interval_calib_var.set(config['Parameters'].get('Frame Interval', ''))
            self.save_every_n_frames_var.set(config['Parameters'].get('Save Every N Frames', ''))
            self.dictionary_var.set(config['Parameters'].get('Dictionary', ''))
            self.display_video_var.set(config['Parameters'].get('Display Video', ''))

    def show_frame(self, frame, text=None):
        if text:
            self.task_label.config(text=text)  # Set the task_label
        if text == "Correct Only":
            for _, _, _, label in self.params:
                if label and label.cget("text") in ["Frame Interval:", "Save Every N Frames:", ""]:
                    label.grid_remove()
            self.frame_interval_entry.grid_remove()
            self.save_every_n_frames_entry.grid_remove()
            self.display_video_label.grid_remove()
            self.display_video_menu.grid_remove()
        else:
            for _, _, _, label in self.params:
                if label and label.cget("text") in ["Frame Interval:", "Save Every N Frames:"]:
                    label.grid()
            self.frame_interval_entry.grid()
            self.save_every_n_frames_entry.grid()
            self.display_video_label.grid()
            self.display_video_menu.grid()
        frame.tkraise()

    def start_task(self):
        self.save_entries_to_config()

        if self.task_label.cget("text") == "Calibrate Only":
            self.on_calibrate_click()
        elif self.task_label.cget("text") == "Correct Only":
            self.on_correct_only_click()
        elif self.task_label.cget('text') == 'Calibrate and Correct':
            self.on_calibrate_correct_click()
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
        elif log_level == "-":
            full_text = f'{text}\n'
            self.animation_stop = True
            self.status_text.insert(tk.END, full_text, log_level)
        else:  # For empty log level
            full_text = f'{text}\n'
            self.status_text.insert(tk.END, full_text)
            self.animated_text_index = self.status_text.index(tk.END)  # Store the index of the animated text
            self.animated_text_index = f"{float(self.animated_text_index) - 1.0} linestart"  # Go to the beginning of the line
            self.animation_stop = False  # Reset the stop flag
            self.start_animation(text)  # Start the animation

        new_scroll_position = self.status_text.yview()[1]

        # Only automatically scroll to the end if the user was already at the bottom
        if current_scroll_position == 1.0 or new_scroll_position == 1.0:
            self.status_text.see(tk.END)

    def start_animation(self, initial_text):
        if not self.animation_stop and self.animated_text_index:
            num_dots = int(datetime.now().timestamp()) % 5
            animated_text = f"{initial_text} {'|||' * num_dots}"

            # Update the text at the animated_text_index
            self.status_text.delete(self.animated_text_index, f"{self.animated_text_index} lineend")
            self.status_text.insert(self.animated_text_index, animated_text)

            self.root.after(500, lambda: self.start_animation(initial_text))

    def stop_animation(self):
        self.animation_stop = True

    def update_gui(self):
        try:
            while True:
                current_status, log_level = self.status_queue.get_nowait()
                if log_level == "CORRECTED" or log_level == 'CC-done':
                    display_video_side_side = messagebox.askyesno("Display Corrected Video(s)",
                                                                  "Would you like to display the corrected videos?")
                    if display_video_side_side and self.calib_instance:
                        play_button = tk.Button(self.control_frame, text="Play", command=self.calib_instance.play_video)
                        pause_button = tk.Button(self.control_frame, text="Pause", command=self.calib_instance.pause)
                        # video_slider = tk.Scale(control_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=calib_instance.seek_video)

                        play_button.pack(side=tk.LEFT)
                        pause_button.pack(side=tk.LEFT)

                        self.calib_instance.add_controls(self.control_frame)
                        self.calib_instance.display_corrected_video()
                elif log_level == "-" or log_level in self.LOG_LEVELS:
                    self.stop_animation()
                self.insert_status_text(current_status, log_level)
        except queue.Empty:
            pass
        self.root.after(10, self.update_gui)

    def on_calibrate_correct_click(self):
        self.show_frame(self.status_frame, "Calibrate and Correct")
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
        self.current_thread = threading.Thread(target=self.calib_instance.calibrate_correct)#.start()
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
        self.current_thread=threading.Thread(target=self.calib_instance.calibrate_only)#.start()
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
                             args=(merged_dict))#.start()
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
        self.current_thread = threading.Thread(target=self.calib_instance.correct_only, args=(None,))#.start()
        self.current_thread.start()



