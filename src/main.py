import tkinter as tk
from tkinter import ttk, filedialog, simpledialog, messagebox
from calibrate_correct import CalibrateCorrect  # Import your existing class
import configparser
from tkinter import Canvas, StringVar
import threading
import queue
from datetime import datetime

display_video_label = None
display_video_menu = None
frame_interval_entry = None
save_every_n_frames_entry = None

calib_instance = None
status_queue = queue.Queue()
animated_text = ""
animation_stop = False
LOG_LEVELS = ['INFO', 'DEBUG', 'ERROR', 'WARNING', 'CORRECTED', 'CC-done']


def save_entries_to_config():
    config = configparser.ConfigParser()
    config['Parameters'] = {
        'Project Repository': proj_repo_var.get(),
        'Project Name': project_name_var.get(),
        'Video Files': video_files_var.get(),
        'SquareX': squaresX_var.get(),
        'SquareY': squaresY_var.get(),
        'SquareLength': squareLength_var.get(),
        'MarkerLength': markerLength_var.get(),
        'Frame Interval': frame_interval_calib_var.get(),
        'Save Every N Frames': save_every_n_frames_var.get(),
        'Dictionary': dictionary_var.get(),
        'Display Video': display_video_var.get()
    }
    with open('settings.ini', 'w') as configfile:
        config.write(configfile)


def load_entries_from_config():
    config = configparser.ConfigParser()
    config.read('settings.ini')
    if 'Parameters' in config:
        proj_repo_var.set(config['Parameters'].get('Project Repository', ''))
        project_name_var.set(config['Parameters'].get('Project Name', ''))
        video_files_var.set(config['Parameters'].get('Video Files', ''))
        squaresX_var.set(config['Parameters'].get('SquareX', ''))
        squaresY_var.set(config['Parameters'].get('SquareY', ''))
        squareLength_var.set(config['Parameters'].get('SquareLength', ''))
        markerLength_var.set(config['Parameters'].get('MarkerLength', ''))
        frame_interval_calib_var.set(config['Parameters'].get('Frame Interval', ''))
        save_every_n_frames_var.set(config['Parameters'].get('Save Every N Frames', ''))
        dictionary_var.set(config['Parameters'].get('Dictionary', ''))
        display_video_var.set(config['Parameters'].get('Display Video', ''))


def show_frame(frame, text=None):
    if text:
        task_label.config(text=text)  # Set the task_label
    if text == "Correct Only":
        for _, _, _, label in params:
            if label and label.cget("text") in ["Frame Interval:", "Save Every N Frames:", ""]:
                label.grid_remove()
        frame_interval_entry.grid_remove()
        save_every_n_frames_entry.grid_remove()
        display_video_label.grid_remove()
        display_video_menu.grid_remove()
    else:
        for _, _, _, label in params:
            if label and label.cget("text") in ["Frame Interval:", "Save Every N Frames:"]:
                label.grid()
        frame_interval_entry.grid()
        save_every_n_frames_entry.grid()
        display_video_label.grid()
        display_video_menu.grid()
    frame.tkraise()


def start_task():
    save_entries_to_config()

    if task_label.cget("text") == "Calibrate Only":
        on_calibrate_click()
    elif task_label.cget("text") == "Correct Only":
        on_correct_only_click()
    elif task_label.cget('text') == 'Calibrate and Correct':
        on_calibrate_correct_click()
        pass


def go_back():
    show_frame(start_frame)


def browse_proj_repo():
    folder_selected = filedialog.askdirectory()
    proj_repo_var.set(folder_selected)


def browse_video_files():
    files_selected = filedialog.askopenfilenames(
        filetypes=[
            ("Video files", "*.mp4 *.MP4 *.avi *.AVI *.mov *.MOV *.flv *.FLV *.mkv *.MKV *.wmv *.WMV *.webm *.WEBM"),
            ("All files", "*.*")
        ]
    )
    video_files_var.set(';'.join(files_selected))


def on_calibrate_correct_click():
    show_frame(status_frame, "Calibrate and Correct")
    global calib_instance
    calib_instance = CalibrateCorrect(
        proj_repo_var.get(),
        project_name_var.get(),
        video_files_var.get().split(';'),  # Assuming files are separated by semicolons
        int(squaresX_var.get()),
        int(squaresY_var.get()),
        int(squareLength_var.get()),
        int(markerLength_var.get()),
        dictionary_var.get(),
        int(frame_interval_calib_var.get()),
        video_frame=video_display_frame,
        save_every_n_frames=int(save_every_n_frames_var.get()),
        display=str(display_video_var.get()),
        status_queue=status_queue
    )
    threading.Thread(target=calib_instance.calibrate_correct).start()


def on_calibrate_click():
    show_frame(status_frame, "Calibrate Only")
    global calib_instance
    calib_instance = CalibrateCorrect(
        proj_repo_var.get(),
        project_name_var.get(),
        video_files_var.get().split(';'),  # Assuming files are separated by semicolons
        int(squaresX_var.get()),
        int(squaresY_var.get()),
        int(squareLength_var.get()),
        int(markerLength_var.get()),
        dictionary_var.get(),
        int(frame_interval_calib_var.get()),
        video_frame=video_display_frame,
        save_every_n_frames=int(save_every_n_frames_var.get()),
        display=str(display_video_var.get()),
        status_queue=status_queue
    )
    threading.Thread(target=calib_instance.calibrate_only).start()


def on_correct_only_click():
    global calib_instance
    show_frame(status_frame, "Correct Only")
    answer = messagebox.askyesno("Use own Calibration", "Would you like to use your own calibration files?")
    if answer:
        correct_only_popup_window()

    else:
        messagebox.showinfo('Notice', 'Saved settings and previously calculated calibration paramaters will be used ')
        show_frame(input_frame, "Correct Only")
        start_task_button.config(command=lambda: start_correct_only_task())


def correct_only_popup_window():
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
        calib_instance_correct_only = CalibrateCorrect(
            proj_repo_var.get(),
            project_name_var.get(),
            video_files_var.get().split(';'),
            int(squaresX_var.get()),
            int(squaresY_var.get()),
            int(squareLength_var.get()),
            int(markerLength_var.get()),
            dictionary_var.get(),
            int(frame_interval_calib_var.get()),
            video_frame=video_display_frame,
            save_every_n_frames=int(save_every_n_frames_var.get()),
            display=str(display_video_var.get()),
            status_queue=status_queue
        )
        threading.Thread(target=calib_instance_correct_only.correct_only,
                         args=(merged_dict)).start()
        popup.destroy()

    ttk.Button(popup, text="Done", command=on_done_click).grid(row=3, column=0, columnspan=2)


def start_correct_only_task():
    save_entries_to_config()
    global calib_instance
    calib_instance = CalibrateCorrect(
        proj_repo_var.get(),
        project_name_var.get(),
        video_files_var.get().split(';'),  # Assuming files are separated by semicolons
        int(squaresX_var.get()),
        int(squaresY_var.get()),
        int(squareLength_var.get()),
        int(markerLength_var.get()),
        dictionary_var.get(),
        int(frame_interval_calib_var.get()),
        status_queue=status_queue,
        video_frame=video_display_frame,

    )
    show_frame(status_frame, "Correct Only")
    threading.Thread(target=calib_instance.correct_only, args=(None,)).start()


def play_video():
    global calib_instance
    if calib_instance:
        calib_instance.play_video()


def pause_video():
    global calib_instance
    if calib_instance:
        calib_instance.pause_video()


def update_gui():
    global status_queue
    try:
        while True:
            current_status, log_level = status_queue.get_nowait()
            if log_level == "CORRECTED" or log_level == 'CC-done':
                display_video_side_side = messagebox.askyesno("Display Corrected Video(s)",
                                                              "Would you like to display the corrected videos?")
                if display_video_side_side:
                    play_button = tk.Button(control_frame, text="Play", command=calib_instance.play_video)
                    pause_button = tk.Button(control_frame, text="Pause", command=calib_instance.pause)
                    # video_slider = tk.Scale(control_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=calib_instance.seek_video)

                    play_button.pack(side=tk.LEFT)
                    pause_button.pack(side=tk.LEFT)
                    calib_instance.add_controls(control_frame)
                    calib_instance.display_corrected_video()
            elif log_level == "-" or log_level in LOG_LEVELS:
                stop_animation()
            insert_status_text(current_status, log_level)
    except queue.Empty:
        pass
    root.after(10, update_gui)


def insert_status_text(text, log_level='INFO'):
    global animated_text_index, animation_stop
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    current_scroll_position = status_text.yview()[1]

    if log_level in LOG_LEVELS:  # For non-empty log levels
        full_text = f'\n[{timestamp}] [{log_level}] - {text}\n'
        status_text.insert(tk.END, full_text, log_level)
    elif log_level == "-":
        full_text = f'{text}\n'
        animation_stop = True
        status_text.insert(tk.END, full_text, log_level)
    else:  # For empty log level
        full_text = f'{text}\n'
        status_text.insert(tk.END, full_text)
        animated_text_index = status_text.index(tk.END)  # Store the index of the animated text
        animated_text_index = f"{float(animated_text_index) - 1.0} linestart"  # Go to the beginning of the line
        animation_stop = False  # Reset the stop flag
        start_animation(text)  # Start the animation

    new_scroll_position = status_text.yview()[1]

    # Only automatically scroll to the end if the user was already at the bottom
    if current_scroll_position == 1.0 or new_scroll_position == 1.0:
        status_text.see(tk.END)


def start_animation(initial_text):
    global animated_text_index, animation_stop
    if not animation_stop and animated_text_index:
        num_dots = int(datetime.now().timestamp()) % 5
        animated_text = f"{initial_text} {'|||' * num_dots}"

        # Update the text at the animated_text_index
        status_text.delete(animated_text_index, f"{animated_text_index} lineend")
        status_text.insert(animated_text_index, animated_text)

        root.after(500, lambda: start_animation(initial_text))


def stop_animation():
    global animation_stop
    animation_stop = True


# Initialize the main window
if __name__ == '__main__':
    root = tk.Tk()
    root.geometry("1080x920")
    root.title('Camera Calibration and Correction')
    root.configure(bg='blue')

    proj_repo_var = tk.StringVar()
    project_name_var = tk.StringVar()
    video_files_var = tk.StringVar()
    squaresX_var = tk.StringVar()
    squaresY_var = tk.StringVar()
    squareLength_var = tk.StringVar()
    markerLength_var = tk.StringVar()
    dictionary_var = tk.StringVar()
    frame_interval_calib_var = tk.StringVar()
    save_every_n_frames_var = tk.StringVar()

    display_video_var = tk.StringVar()

    params = [
        ("Project Repository:", proj_repo_var, browse_proj_repo, None),
        ("Project Name:", project_name_var, None, None),
        ("Video Files:", video_files_var, browse_video_files, None),
        ("SquaresX:", squaresX_var, None, None),
        ("SquaresY:", squaresY_var, None, None),
        ("SquareLength:", squareLength_var, None, None),
        ("MarkerLength:", markerLength_var, None, None),
        ("Frame Interval:", frame_interval_calib_var, None, None),
        ("Save Every N Frames:", save_every_n_frames_var, None, None)
    ]

    container = tk.Frame(root)
    container.pack(side="top", fill="both", expand=True)
    container.grid_rowconfigure(0, weight=1)
    container.grid_columnconfigure(0, weight=1)

    # Initialize frames
    start_frame = ttk.Frame(container, style='My.TFrame')
    input_frame = ttk.Frame(container, style='My.TFrame')
    status_frame = ttk.Frame(container, style='My.TFrame')
    control_frame = ttk.Frame(root)
    control_frame.pack(side="bottom")

    for frame in [start_frame, input_frame, status_frame]:
        frame.grid(row=0, column=0, sticky="nsew")

    video_display_frame = Canvas(status_frame, bg='#ADD8E6', height=360, width=440)
    video_display_frame.pack(side="top", fill="none", expand=True, anchor='n', padx=40, pady=10)

    animated_text_label = tk.Label(status_frame, bg='#ADD8E6', fg='#000000')
    animated_text_label.pack()

    back_button = tk.Button(status_frame, text="Back", command=go_back)
    back_button.pack()

    # Styling the frames
    style = ttk.Style()
    label_style = {'bg': '#ADD8E6', 'fg': '#000000', 'font': ('Helvetica', 12)}
    style.configure('My.TFrame', background='#ADD8E6')  # Light blue background
    welcome_frame = tk.Frame(start_frame, bg='#ADD8E6')

    welcome_frame.grid(row=0, column=0, columnspan=3, pady=20, sticky='ew')
    # Create the Label first
    welcome_label = tk.Label(welcome_frame, text="Welcome to Camera Calibration and Correction", **label_style)
    welcome_label.config(font=('Helvetica', 24))
    welcome_label.grid(row=0, column=0)

    welcome_frame.grid_columnconfigure(0, weight=1)
    # Create buttons
    ttk.Button(start_frame, text=" START CALIBRATION", command=lambda: show_frame(input_frame, "Calibrate Only")).grid(
        row=1, column=0, pady=10, sticky='w', padx=20)
    ttk.Button(start_frame, text=" START CORRECTION", command=on_correct_only_click).grid(
        row=2,
        column=0,
        pady=10,
        sticky='w',
        padx=20
    )

    ttk.Button(start_frame, text="START CALIBRATION & CORRECTION",
               command=lambda: show_frame(input_frame, "Calibrate and Correct")).grid(row=3, column=0, pady=10,
                                                                                      sticky='w',
                                                                                      padx=20)

    # Start Task button
    start_task_button = ttk.Button(input_frame, text="Start Task", command=start_task)
    start_task_button.grid(row=len(params) + 3, column=1, padx=5, pady=5)
    ttk.Button(input_frame, text="Back", command=lambda: show_frame(start_frame)).grid(row=len(params) + 4, column=1,
                                                                                       padx=5, pady=5)
    task_label = tk.Label(input_frame, text="", font=("Helvetica", 18), bg='#ADD8E6', fg='#000000')
    task_label.grid(row=0, column=0, columnspan=3, pady=20, sticky="ew")

    for i, (text, var, cmd, _) in enumerate(params):
        label = tk.Label(input_frame, text=text, **label_style)
        label.grid(row=i + 1, column=0, sticky="w")
        entry = ttk.Entry(input_frame, textvariable=var, width=40)
        entry.grid(row=i + 1, column=1)

        if text == "Frame Interval:":
            frame_interval_entry = entry
        elif text == "Save Every N Frames:":
            save_every_n_frames_entry = entry

        if cmd:
            ttk.Button(input_frame, text="Browse", command=cmd).grid(row=i + 1, column=2)

        # Store the reference back into params
        params[i] = (text, var, cmd, label)

    dictionary_options = [
        'DICT_4X4_50', 'DICT_4X4_100', 'DICT_4X4_250', 'DICT_4X4_1000', 'DICT_5X5_50',
        'DICT_5X5_100', 'DICT_5X5_250', 'DICT_5X5_1000',
        'DICT_6X6_50', 'DICT_6X6_100', 'DICT_6X6_250', 'DICT_6X6_1000',
        'DICT_7X7_50', 'DICT_7X7_100', 'DICT_7X7_250', 'DICT_7X7_1000',
        'DICT_ARUCO_ORIGINAL', 'DICT_APRILTAG_16h5', 'DICT_APRILTAG_16H5',
        'DICT_APRILTAG_25h9', 'DICT_APRILTAG_25H9', 'DICT_APRILTAG_36h10',
        'DICT_APRILTAG_36H10', 'DICT_APRILTAG_36h11', 'DICT_APRILTAG_36H11',
        'DICT_ARUCO_MIP_36h12', 'DICT_ARUCO_MIP_36H12'
    ]
    dictionary_label_style = {'foreground': '#000000', 'font': ('Helvetica', 12)}
    ttk.Label(input_frame, text="Dictionary:", **dictionary_label_style).grid(row=len(params) + 1, column=0, sticky="w")
    dictionary_menu = ttk.OptionMenu(input_frame, dictionary_var, dictionary_options[0], *dictionary_options)
    dictionary_menu.grid(row=len(params) + 1, column=1)

    display_video_frame_options = ['Yes', 'No']
    display_video_label_style = {'foreground': '#000000', 'font': ('Helvetica', 10)}
    display_video_label = ttk.Label(input_frame, text="Display Video during Calibration?:", **display_video_label_style)
    display_video_label.grid(row=len(params) + 2, column=0, sticky="w")

    display_video_menu = ttk.OptionMenu(input_frame, display_video_var, display_video_frame_options[0],
                                        *display_video_frame_options)
    display_video_menu.grid(row=len(params) + 2, column=1)

    status_text_frame = tk.Frame(status_frame)
    status_text_frame.pack(fill=tk.BOTH, expand=True, pady=5)

    scrollbar = tk.Scrollbar(status_text_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    status_text = tk.Text(status_text_frame, wrap="word", width=150, height=40, yscrollcommand=scrollbar.set)
    status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar.config(command=status_text.yview)

    status_text.tag_configure("INFO", foreground="black", font=('Cambria', 9,))
    status_text.tag_configure("DEBUG", foreground="blue", font=('Verdana', 9))
    status_text.tag_configure("", foreground="blue", font=('Verdana', 9))
    status_text.tag_configure("-", foreground="black", font=('Verdana', 9))
    status_text.tag_configure("WARNING", foreground="orange")
    status_text.tag_configure("ERROR", foreground="red")
    status_text.tag_configure("CORRECTED", foreground="red")

    show_frame(start_frame)
    load_entries_from_config()
    root.after(10, update_gui)  # Start running update_gui after 500 ms

    root.mainloop()
