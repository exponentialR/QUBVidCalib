import os

import cv2
import numpy as np
from tkinter import NW

from PIL import Image, ImageTk
from tkinter import Button, Label, Scale, HORIZONTAL
from tkinter import Button, Scale, HORIZONTAL


def create_dir(direc):
    return os.makedirs(direc, exist_ok=True) if not os.path.exists(direc) else None


class CalibrateCorrect:
    def __init__(self, proj_repo, projectname, video_files, squaresX, squaresY, squareLength, markerLength,
                 dictionary, frame_interval_calib=None, display=None, video_frame=None, save_every_n_frames=None,
                 status_queue=None):

        self.pause_button = None
        self.play_button = None
        self.projectname = os.path.join(proj_repo, projectname)
        create_dir(self.projectname)
        self.param_folder = f'{self.projectname}/CalibrationFiles'
        create_dir(self.param_folder)
        self.corrected_video_folder = f'{self.projectname}/CorrectedVideos'
        create_dir(self.corrected_video_folder)
        self.save_calib_frames = save_every_n_frames
        self.video_files = video_files  # List of video file paths
        if self.save_calib_frames is not None:
            self.calib_frames = f'{self.projectname}/CalibrationFrames'
            for idx, video_path in enumerate(self.video_files):
                video_name = os.path.basename(video_path).split('.')[0]
                output_folder_ = os.path.join(self.calib_frames, video_name)
                create_dir(output_folder_)

        self.display = display
        self.save_path_prefix = 'calib_param'
        self.frame_interval_calib = frame_interval_calib
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, dictionary))
        self.board = cv2.aruco.CharucoBoard((squaresX, squaresY), squareLength / 1000, markerLength / 1000,
                                            self.aruco_dict)
        self.min_corners = 10
        self.calibration_params = None  # To store calibration parameters
        self.current_progress = 0  # To store the current progress percentage
        self.video_frame = video_frame
        self.status_queue = status_queue
        self.video_name = None
        self.correct_et_orig_dict = {}
        self.paused = None
        self.cap_orig = None
        self.cap_corrected = None
        self.play_video = True

    def add_controls(self, control_frame):
        # Add Play Button
        self.play_button = Button(control_frame, text="Play", command=self.play)
        self.play_button.pack(side="left")

        # Add Pause Button
        self.pause_button = Button(control_frame, text="Pause", command=self.pause)
        self.pause_button.pack(side="left")

        # Add Slider
        self.slider = Scale(control_frame, from_=0, to=100, orient=HORIZONTAL)
        self.slider.pack(side="left")

    def play(self):
        self.play_video = True

    def pause(self):
        self.play_video = False

    def display_corrected_video(self):

        if not self.play_video:
            self.video_frame.after(100, self.display_corrected_video)
            return

        if self.cap_orig is None or self.cap_corrected is None:
            old_video, corrected_vid = list(self.correct_et_orig_dict.items())[0]
            self.cap_orig = cv2.VideoCapture(old_video)
            self.cap_corrected = cv2.VideoCapture(corrected_vid)

        ret_orig, frame_orig = self.cap_orig.read()
        ret_corrected, frame_corrected = self.cap_corrected.read()

        if not ret_orig or not ret_corrected:
            self.cap_orig.release()
            self.cap_corrected.release()
            return

        # Resize for display if necessary
        frame_orig_resized = cv2.resize(frame_orig, (220, 180))
        frame_corrected_resized = cv2.resize(frame_corrected, (220, 180))
        cv2.putText(frame_orig_resized, 'Uncorrected Video', (0, 165), cv2.FONT_HERSHEY_SIMPLEX, .3, (0, 0, 255), 1)
        cv2.putText(frame_corrected_resized, 'Corrected Video', (0, 165), cv2.FONT_HERSHEY_SIMPLEX, .3, (0, 0, 255), 1)

        # Concatenate horizontally
        concat_frame = np.hstack((frame_orig_resized, frame_corrected_resized))

        # Convert to Tkinter compatible format and display
        self.video_frame.img = ImageTk.PhotoImage(
            image=Image.fromarray(cv2.cvtColor(concat_frame, cv2.COLOR_BGR2RGB)))

        self.video_frame.create_image(0, 0, image=self.video_frame.img, anchor=NW)
        current_frame_number = int(self.cap_orig.get(cv2.CAP_PROP_POS_FRAMES))
        self.slider.set(current_frame_number)

        # Schedule the next frame
        self.video_frame.after(10, self.display_corrected_video)

    def process_video(self, video_file_path, calib_file_path):
        if not os.path.exists(calib_file_path):
            self.status_queue.put((f'CALIBRATION DATA FILE {calib_file_path} NOT FOUND!', 'ERROR'))
            return

        with np.load(calib_file_path) as data:
            mtx, dist = data['mtx'], data['dist']

        video_name = os.path.basename(video_file_path)
        video_name_ = os.path.basename(video_file_path).split('.')[0]

        cap = cv2.VideoCapture(video_file_path)
        frame_width = int(cap.get(3))
        frame_height = int(cap.get(4))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        output_video_path = f'{self.corrected_video_folder}/{video_name_}.MP4'
        out = cv2.VideoWriter(output_video_path, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), fps,
                              (frame_width, frame_height))
        self.status_queue.put((f"Correcting {video_name}", ""))
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            corrected = cv2.undistort(frame, mtx, dist, None, mtx)

            out.write(corrected)

        cap.release()
        out.release()
        return output_video_path

    def correct_only(self, merged_calib_vid_dict):
        total_videos = len(self.video_files)

        if merged_calib_vid_dict is not None:
            for idx, (video_file_path, calib_file_path) in enumerate(merged_calib_vid_dict.items()):
                output_vid_path = self.process_video(video_file_path, calib_file_path)
                self.correct_et_orig_dict[video_file_path] = output_vid_path
        else:
            for idx, video_path in enumerate(self.video_files):
                video_name = os.path.basename(video_path).split('.')[0]
                calib_file_path = f'{self.param_folder}/{self.save_path_prefix}_{video_name}.npz'
                output_vid_path = self.process_video(video_path, calib_file_path)
                self.correct_et_orig_dict[video_path] = output_vid_path
        # Initialize table header for status_queue
        table_header = "\n______________________________________________________________________________________________________________________\n"
        table_header += " Old Video Path                                 |    New Video Path                                                                     "
        table_header += "-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------"

        self.status_queue.put((table_header, "-"))
        for old_video, corrected_vid in self.correct_et_orig_dict.items():
            old_video_name = os.path.basename(old_video).split('.')[0]
            table_row = f"{old_video_name[:20]:<39} | {corrected_vid:<45}"
            self.status_queue.put((table_row, "-"))
            self.status_queue.put(
                (
                    "-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------",
                    "-"))
        self.status_queue.put(('', "CORRECTED"))

    def calibrate_only(self):

        all_charuco_corners = []
        all_charuco_ids = []
        for idx, video_path in enumerate(self.video_files):
            cap = None
            if cap is not None:
                cap.release()

            video_name = os.path.basename(video_path).split('.')[0]
            if self.video_name is None:
                self.video_name = video_name
            save_path = f'{self.param_folder}/{self.save_path_prefix}_{video_name}.npz'
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                self.status_queue.put((f'COULD NOT OPEN VIDEO FILE {video_path}. SKIPPING', 'WARNING'))
                print(f"Warning: Couldn't open video file {video_path}. Skipping...")
                continue

            frame_count = 0
            gray = None
            while True:
                ret, frame = cap.read()
                if not ret:
                    self.video_frame.delete("all")
                    if self.status_queue:
                        self.status_queue.put((f"Done processing video: {video_name}", 'DEBUG'))

                    break

                if frame_count % self.frame_interval_calib == 0:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    corners, ids, _ = cv2.aruco.detectMarkers(gray, self.aruco_dict)

                    if len(corners) > 0:
                        debug_frame = cv2.aruco.drawDetectedMarkers(frame.copy(), corners, ids)
                        ret, charuco_corners, charuco_ids = cv2.aruco.interpolateCornersCharuco(corners, ids, gray,
                                                                                                self.board,
                                                                                                charucoIds=ids)

                        if self.status_queue:
                            self.status_queue.put(("Collecting Corners and IDs for Calibration", "INFO"))
                        if self.display == 'Yes':
                            debug_frame_ = cv2.resize(debug_frame, (440, 360))
                            self.video_frame.img = ImageTk.PhotoImage(
                                image=Image.fromarray(cv2.cvtColor(debug_frame_, cv2.COLOR_BGR2RGB)))
                            self.video_frame.create_image(0, 0, image=self.video_frame.img, anchor=NW)
                        if not ret or len(charuco_corners) <= self.min_corners:
                            if self.status_queue:
                                self.status_queue.put(('Not enough corners for interpolation', 'INFO'))
                            print(f'Not enough corners for interpolation')
                        else:
                            all_charuco_corners.append(charuco_corners)
                            all_charuco_ids.append(charuco_ids)

                            # Save the frame used for calibration
                            if self.save_calib_frames is not None and frame_count % self.save_calib_frames == 0:
                                frame_filename = os.path.join(self.calib_frames, video_name,
                                                              f'{video_name}_{frame_count}.png')
                                cv2.imwrite(frame_filename, debug_frame)

                frame_count += 1

            # Perform camera calibration
            if self.status_queue:
                self.status_queue.put(("Computing Calibration", "INFO"))
            if len(all_charuco_corners) > 0 and len(all_charuco_ids) > 0:
                ret, mtx, dist, rvecs, tvecs = cv2.aruco.calibrateCameraCharuco(all_charuco_corners,
                                                                                all_charuco_ids,
                                                                                self.board,
                                                                                gray.shape[::-1], None, None)

                np.savez(save_path, mtx=mtx, dist=dist)
                if self.status_queue:
                    self.status_queue.put((f"Calibration done. File saved at {save_path}", "DEBUG"))
