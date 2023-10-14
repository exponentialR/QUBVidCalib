import os

import cv2
import numpy as np
from tkinter import NW

from PIL import Image, ImageTk
from tkinter import Button, Scale, HORIZONTAL

# from utils import SharedState
"""
TODO: Calibrate and Correct code should be corrected
    1. Pick Calibration file, then use it correct multiple videos.
    2. 
# TODO: Correct Only 
    1. Pick a single calibration video, then use to correct multiple videos.
    2. 
  """
DICTIONARY = [
    'DICT_4X4_50', 'DICT_4X4_100', 'DICT_4X4_250', 'DICT_4X4_1000', 'DICT_5X5_50',
    'DICT_5X5_100', 'DICT_5X5_250', 'DICT_5X5_1000',
    'DICT_6X6_50', 'DICT_6X6_100', 'DICT_6X6_250', 'DICT_6X6_1000',
    'DICT_7X7_50', 'DICT_7X7_100', 'DICT_7X7_250', 'DICT_7X7_1000',
    'DICT_ARUCO_ORIGINAL', 'DICT_APRILTAG_16h5', 'DICT_APRILTAG_16H5',
    'DICT_APRILTAG_25h9', 'DICT_APRILTAG_25H9', 'DICT_APRILTAG_36h10',
    'DICT_APRILTAG_36H10', 'DICT_APRILTAG_36h11', 'DICT_APRILTAG_36H11',
    'DICT_ARUCO_MIP_36h12', 'DICT_ARUCO_MIP_36H12'
]


def create_dir(direc):
    return os.makedirs(direc, exist_ok=True) if not os.path.exists(direc) else None


def sep_direc_files(input_path):
    path_parts = input_path.split(os.sep)
    sep_dir_files_path = os.path.join(path_parts[-2], path_parts[-1])
    return sep_dir_files_path


class CalibrateCorrect:
    def __init__(self, proj_repo, projectname, video_files, squaresX, squaresY, squareLength, markerLength,
                 dictionary, frame_interval_calib=None, display=None, video_frame=None, save_every_n_frames=None,
                 status_queue=None):
        self.animation_active = False
        self.pause_button = None
        self.play_button = None
        self.projectname = os.path.join(proj_repo, projectname)
        create_dir(self.projectname)
        self.param_folder = f'{self.projectname}/CalibrationFiles'
        self.rejected_frames_dir = f'{self.projectname}/RejectedFrames'
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
        self.is_playing = True
        self.current_frame_number = 0
        self.display_video_dict = {}

        self.status_queue = status_queue
        self.video_name = None
        self.correct_et_orig_dict = {}
        self.paused = None
        self.cap_orig = None
        self.cap_corrected = None
        self.play_video = True
        self.calibrate_correct_dict = {}
        self.video_index = 0
        self.stop_requested = None

    def stop(self):
        self.stop_requested = True

    def add_controls(self, control_frame):
        # Add Play Button
        self.play_button = Button(control_frame, text="Play", command=self.play)
        self.play_button.pack(side="left")

        # Add Pause Button
        self.pause_button = Button(control_frame, text="Pause", command=self.pause)
        self.pause_button.pack(side="left")

    def play(self):
        self.play_video = True

    def pause(self):
        self.play_video = False

    def display_corrected_video(self):
        if self.stop_requested:
            return

        if not self.play_video:
            self.video_frame.after(100, self.display_corrected_video)
            return

        if self.cap_orig is None or self.cap_corrected is None:
            if self.video_index >= len(self.display_video_dict):
                return
            old_video, corrected_vid = list(self.display_video_dict.items())[self.video_index]
            self.cap_orig = cv2.VideoCapture(old_video)
            self.cap_corrected = cv2.VideoCapture(corrected_vid)

        ret_orig, frame_orig = self.cap_orig.read()
        ret_corrected, frame_corrected = self.cap_corrected.read()

        if not ret_orig or not ret_corrected:
            self.cap_orig.release()
            self.cap_corrected.release()
            self.cap_orig = None
            self.cap_corrected = None
            self.video_index += 1
            self.video_frame.delete('all')
            self.display_corrected_video()
            self.stop_requested = True
            self.stop()
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
        if self.stop_requested is not None:
            exit()
        frame_width = int(cap.get(3))
        frame_height = int(cap.get(4))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        output_video_path = f'{self.corrected_video_folder}/{video_name_}.MP4'
        out = cv2.VideoWriter(output_video_path, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), fps,
                              (frame_width, frame_height))
        self.status_queue.put((f"Correcting {video_name}", "anime"))
        while True:
            ret, frame = cap.read()
            if self.stop_requested is not None:
                break
            if not ret:
                break

            corrected = cv2.undistort(frame, mtx, dist, None, mtx)
            if self.stop_requested is not None:
                break

            out.write(corrected)

        cap.release()
        out.release()
        return output_video_path

    def correct_only(self, merged_calib_vid_dict=None, sing_calib_file=None):
        total_videos = len(self.video_files)
        if sing_calib_file is not None:
            calib_file_path = sing_calib_file
            for idx, video_path in enumerate(self.video_files):
                if self.stop_requested is not None:
                    break
                output_vid_path = self.process_video(video_path, calib_file_path)
                self.correct_et_orig_dict[video_path] = output_vid_path
        else:
            if merged_calib_vid_dict is not None:
                for idx, (video_file_path, calib_file_path) in enumerate(merged_calib_vid_dict.items()):
                    if self.stop_requested is not None:
                        break
                    output_vid_path = self.process_video(video_file_path, calib_file_path)
                    self.correct_et_orig_dict[video_file_path] = output_vid_path
            else:
                for idx, video_path in enumerate(self.video_files):
                    if self.stop_requested is not None:
                        break
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
            if self.stop_requested is not None:
                break
            old_video_name = os.path.basename(old_video).split('.')[0]
            table_row = f"{old_video_name[:20]:<39} | {corrected_vid:<45}"
            self.status_queue.put((table_row, "-"))
            self.status_queue.put(
                (
                    "-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------",
                    "-"))
        self.status_queue.put(('', "CORRECTED"))
        self.correct_et_orig_dict.clear()

    def calibrate_only(self):

        for idx, video_path in enumerate(self.video_files):
            if self.stop_requested is not None:
                return
            cap = None
            if cap is not None:
                cap.release()

            video_name = os.path.basename(video_path).split('.')[0]
            if self.video_name is None:
                self.video_name = video_name
            save_path = f'{self.param_folder}/{self.save_path_prefix}_{video_name}.npz'
            cap = cv2.VideoCapture(video_path)
            if self.stop_requested is not None:
                return

            if not cap.isOpened():
                self.status_queue.put((f'COULD NOT OPEN VIDEO FILE {video_path}. SKIPPING', 'WARNING'))
                print(f"Warning: Couldn't open video file {video_path}. Skipping...")
                continue

            frame_count = 0
            gray = None
            all_charuco_corners = []
            all_charuco_ids = []
            while True:
                ret, frame = cap.read()
                if self.stop_requested is not None:
                    break
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
                                self.status_queue.put(
                                    (f'Frame {frame_count} - Not enough corners for interpolation', 'INFO'))
                            # print(f'Not enough corners for interpolation')
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
                # self.status_queue.put(("Computing Calibration", ""))
                self.status_queue.put(("Computing Calibration", "anime"))

            if len(all_charuco_corners) > 0 and len(all_charuco_ids) > 0:
                ret, mtx, dist, rvecs, tvecs = cv2.aruco.calibrateCameraCharuco(all_charuco_corners,
                                                                                all_charuco_ids,
                                                                                self.board,
                                                                                gray.shape[::-1], None, None)

                np.savez(save_path, mtx=mtx, dist=dist)
                if self.status_queue:
                    self.status_queue.put((f"Calibration done. File saved at {save_path}", "DEBUG"))

    def self_calibrate_correct(self):
        total_vids_len = len(self.video_files)
        for idx, video_path in enumerate(self.video_files):
            if self.stop_requested:
                break
            if self.status_queue:
                self.status_queue.put((f'PROCESSING Videos {idx + 1} of {total_vids_len}', 'INFO'))
            save_path = self.calibrate_single_video(video_path)
            if save_path is None:
                self.status_queue.put((f'CALIBRATION FAILED FOR {video_path}', 'ERROR'))
                continue
            output_vid_path = self.process_video(video_path, save_path)
            self.correct_et_orig_dict[video_path] = output_vid_path
            save_path_ = sep_direc_files(save_path)
            output_vid_path_ = sep_direc_files(output_vid_path)
            self.calibrate_correct_dict[video_path] = [save_path_, output_vid_path_]

        self.status_queue.put(("", "-"))
        self.status_queue.put(('', 'CC-done'))
        self.display_video_dict = self.correct_et_orig_dict.copy()
        self.status_queue.put((self.calibrate_correct_dict, 'update-treeview'))
        self.correct_et_orig_dict.clear()

    def calibrate_single_video(self, single_video_calib):
        cap = cv2.VideoCapture(single_video_calib)
        if not cap.isOpened():
            self.status_queue.put((f'Could not open Video File {single_video_calib}. Exiting...', "INFO"))
            return
        frame_count = 0
        gray = None
        all_charuco_corners = []
        all_charuco_ids = []
        animation_started = False
        video_name = os.path.basename(single_video_calib).split('.')[0]
        rejected_folder = os.path.join(self.rejected_frames_dir, video_name)
        create_dir(rejected_folder)
        while True:
            ret, frame = cap.read()
            if self.stop_requested is not None:
                break
            if not ret:
                self.video_frame.delete("all")
                self.status_queue.put((f'Done Processing Video {single_video_calib}', 'INFO'))
                self.status_queue.put(('', 'stop-anime'))
                break
            if frame_count % self.frame_interval_calib == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                corners, ids, _ = cv2.aruco.detectMarkers(gray, self.aruco_dict)

                if len(corners) > 0:
                    debug_frame = cv2.aruco.drawDetectedMarkers(frame.copy(), corners, ids)
                    ret, charuco_corners, charuco_ids = cv2.aruco.interpolateCornersCharuco(corners, ids, gray,
                                                                                            self.board, charucoIds=ids)
                    if self.status_queue and not animation_started:
                        self.status_queue.put(("Collecting Corners and IDs for Calibration", "anime"))
                        animation_started = True

                    if self.display == 'Yes':
                        debug_frame_ = cv2.resize(debug_frame, (440, 360))
                        self.video_frame.img = ImageTk.PhotoImage(
                            image=Image.fromarray(cv2.cvtColor(debug_frame_, cv2.COLOR_BGR2RGB)))
                        self.video_frame.create_image(0, 0, image=self.video_frame.img, anchor=NW)

                    if not ret or len(charuco_corners) <= self.min_corners:
                        self.status_queue.put((f'Frame {frame_count}- Not enough corners for interpolation', 'DEBUG'))
                        rejected_frame_filename = os.path.join(rejected_folder, f'{video_name}_{frame_count}.png')
                        cv2.imwrite(rejected_frame_filename, debug_frame)
                        if animation_started:
                            self.status_queue.put(("Collecting Corners and IDs for Calibration", "anime"))
                    else:
                        all_charuco_corners.append(charuco_corners)
                        all_charuco_ids.append(charuco_ids)
                        if self.save_calib_frames is not None and frame_count % self.save_calib_frames == 0:
                            frame_filename = os.path.join(self.calib_frames, video_name,
                                                          f'{video_name}_{frame_count}.png')
                            cv2.imwrite(frame_filename, debug_frame)
                else:
                    self.status_queue.put((f"Frame {frame_count} - Not enough corners for interpolation", "DEBUG"))
                    if animation_started:
                        self.status_queue.put(("Collecting Corners and IDs for Calibration", "anime"))

            frame_count += 1

        if len(all_charuco_corners) > 0 and len(all_charuco_ids) > 0:
            # Status to show computing extrinsic and intrinsic parameters
            self.status_queue.put(('COMPUTING EXTRINSIC AND INTRINSIC PARAMETERS', "anime"))
            ret, mtx, dist, rvecs, tvecs = cv2.aruco.calibrateCameraCharuco(
                all_charuco_corners, all_charuco_ids, self.board, gray.shape[::-1], None, None)

            save_path = f'{self.param_folder}/calibration_{os.path.basename(single_video_calib)}.npz'

            np.savez(save_path, mtx=mtx, dist=dist)
            if self.status_queue:
                self.status_queue.put(('', "-"))

            cap.release()
            return save_path

    def singleCalibMultiCorrect(self, single_calib_video):
        self.animation_active = True
        self.status_queue.put((f'STARTING CALIBRATION FOR CALIBRATION VIDEO', 'INFO'))
        calib_file_path = self.calibrate_single_video(single_calib_video)
        if self.animation_active:
            self.status_queue.put(
                (f'Calibration done for video {os.path.basename(single_calib_video)}. File saved at {calib_file_path}',
                 '-'))
        if calib_file_path is None:
            print(f'Calibration file {calib_file_path} does not exist')
            self.status_queue.put(('Calibration Failed. Exiting...', 'DEBUG'))
            self.stop_requested = True
        self.status_queue.put(('STARTING VIDEO CORRECTION', 'DEBUG'))

        total_vids_len = len(self.video_files)
        for idx, video_path in enumerate(self.video_files):
            if self.status_queue:
                self.status_queue.put((f'Correcting Videos {idx + 1} of {total_vids_len}', 'INFO'))

            output_vid_path = self.process_video(video_path, calib_file_path)
            self.correct_et_orig_dict[video_path] = output_vid_path
            save_path_ = sep_direc_files(calib_file_path)
            output_vid_path_ = sep_direc_files(output_vid_path)
            self.calibrate_correct_dict[video_path] = [save_path_, output_vid_path_]

        self.status_queue.put(("", "-"))
        self.status_queue.put(('', 'CC-done'))
        self.display_video_dict = self.correct_et_orig_dict.copy()
        self.status_queue.put((self.calibrate_correct_dict, 'update-treeview'))
        self.correct_et_orig_dict.clear()
