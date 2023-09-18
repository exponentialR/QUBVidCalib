import os

import cv2
import numpy as np
from tkinter import NW

from PIL import Image, ImageTk

def create_dir(direc):
    return os.makedirs(direc, exist_ok=True) if not os.path.exists(direc) else None


class CalibrateCorrect:
    def __init__(self, proj_repo, projectname, video_files, squaresX, squaresY, squareLength, markerLength,
                 dictionary, frame_interval_calib, display='Yes', video_frame=None, save_every_n_frames=None, status_queue=None):
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

    def calibrate_only(self):

        all_charuco_corners = []
        all_charuco_ids = []
        for idx, video_path in enumerate(self.video_files):
            cap = None
            if cap is not None:
                cap.release()
            # try:
            video_name = os.path.basename(video_path).split('.')[0]
            if self.video_name is None:
                self.video_name = video_name
            save_path = f'{self.param_folder}/{self.save_path_prefix}_{video_name}.npz'
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
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
                            self.video_frame.img = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(debug_frame_, cv2.COLOR_BGR2RGB)))
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




