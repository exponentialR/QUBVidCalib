import tkinter as tk
from tkinter import ttk, filedialog
from calibrate_correct import CalibrateCorrect  # Import your existing class
import configparser
from tkinter import Canvas, StringVar
import threading
import queue
from datetime import datetime
from queue import Queue
calib_instance = None
status_queue = queue.Queue()

LOG_LEVELS = {
    'INFO': {'color': 'green', 'font_size':12},
    'WARNING': {'color': 'orange', 'font_size': 12},
    'DEBUG': {'color': 'blue', 'font_size': 12},
    'ERROR': {'color': 'red', 'font_size': 14}
}
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


# Function to switch to the parameter input frame and set the task_label
def show_frame(frame, text=None):
    if text:
        task_label.config(text=text)  # Set the task_label
    frame.tkraise()

def start_task():
    save_entries_to_config()

    if task_label.cget("text") == "Calibrate Only":
        on_calibrate_click()
    elif task_label.cget("text") == "Correct Only":
        pass
    else:
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



def update_gui():
    global status_queue
    try:
        while True:
            current_status, log_level = status_queue.get_nowait()
            insert_status_text(current_status, log_level)
    except queue.Empty:
        pass
    root.after(10, update_gui)


def insert_status_text(text, log_level='INFO'):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    full_text = f'[{timestamp}] [{log_level}] - {text}\n'

    current_scroll_position = status_text.yview()[1]


    status_text.insert(tk.END, full_text, log_level)
    if current_scroll_position == 1.0:
        status_text.see(tk.END)
        status_text.see(tk.END)


# Initialize the main window
if __name__ == '__main__':
    root = tk.Tk()
    root.geometry("720x720")
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
        ("Project Repository:", proj_repo_var, browse_proj_repo),
        ("Project Name:", project_name_var, None),
        ("Video Files:", video_files_var, browse_video_files),
        ("SquaresX:", squaresX_var, None),
        ("SquaresY:", squaresY_var, None),
        ("SquareLength:", squareLength_var, None),
        ("MarkerLength:", markerLength_var, None),
        ("Frame Interval:", frame_interval_calib_var, None),
        ("Save Every N Frames:", save_every_n_frames_var, None)
    ]

    container = tk.Frame(root)
    container.pack(side="top", fill="both", expand=True)
    container.grid_rowconfigure(0, weight=1)
    container.grid_columnconfigure(0, weight=1)

    # Initialize frames
    start_frame = ttk.Frame(container, style='My.TFrame')
    input_frame = ttk.Frame(container, style='My.TFrame')
    status_frame = ttk.Frame(container, style='My.TFrame')

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
    ttk.Button(start_frame, text=" START CORRECTION", command=lambda: show_frame(input_frame, "Correct Only")).grid(row=2,
                                                                                                                    column=0,
                                                                                                                    pady=10,
                                                                                                                    sticky='w',
                                                                                                                    padx=20)

    ttk.Button(start_frame, text="START CALIBRATION & CORRECTION",
               command=lambda: show_frame(input_frame, "Calibrate & Correct")).grid(row=3, column=0, pady=10, sticky='w',
                                                                                    padx=20)



    # Start Task button
    start_task_button = ttk.Button(input_frame, text="Start Task", command=start_task)
    start_task_button.grid(row=len(params) + 3, column=1, padx=5, pady=5)
    ttk.Button(input_frame, text="Back", command=lambda: show_frame(start_frame)).grid(row=len(params) + 4, column=1,
                                                                                       padx=5, pady=5)
    task_label = tk.Label(input_frame, text="", font=("Helvetica", 18), bg='#ADD8E6', fg='#000000')
    task_label.grid(row=0, column=0, columnspan=3, pady=20, sticky="ew")

    for i, (text, var, cmd) in enumerate(params):
        tk.Label(input_frame, text=text, **label_style).grid(row=i + 1, column=0, sticky="w")
        ttk.Entry(input_frame, textvariable=var, width=40).grid(row=i + 1, column=1)
        if cmd:
            ttk.Button(input_frame, text="Browse", command=cmd).grid(row=i + 1, column=2)

    dictionary_options = [
        'DICT_4X4_50', 'DICT_4X4_100', 'DICT_4X4_250', 'DICT_4X4_1000','DICT_5X5_50',
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
    ttk.Label(input_frame, text="Display video?:", **display_video_label_style).grid(row=len(params) + 2, column=0,
                                                                                     sticky="w")
    display_video_menu = ttk.OptionMenu(input_frame, display_video_var, display_video_frame_options[0],
                                        *display_video_frame_options)
    display_video_menu.grid(row=len(params) + 2, column=1)

    status_text_frame = tk.Frame(status_frame)
    status_text_frame.pack(fill=tk.BOTH, expand=True, pady=5)

    scrollbar = tk.Scrollbar(status_text_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    status_text = tk.Text(status_text_frame, wrap="word", width=100, height=20, yscrollcommand=scrollbar.set)
    status_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar.config(command=status_text.yview)

    status_text.tag_configure("INFO", foreground="black", font=('Cambria', 9, 'bold'))
    status_text.tag_configure("DEBUG", foreground="blue", font=('Verdana', 10, 'bold'))
    status_text.tag_configure("WARNING", foreground="orange")
    status_text.tag_configure("ERROR", foreground="red")



    show_frame(start_frame)
    load_entries_from_config()
    root.after(10, update_gui)  # Start running update_gui after 500 ms

    root.mainloop()

