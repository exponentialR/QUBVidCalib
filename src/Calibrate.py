import os
import cv2
import numpy as np
from tkinter import Canvas, Tk, NW, Label
from PIL import Image, ImageTk, ImageSequence


def create_dir(direc):
    return os.makedirs(direc, exist_ok=True) if not os.path.exists(direc) else None


class Calibrate:
    def __init__(self, proj_repo, projectname, video_files, squaresX, squaresY, squareLength, markerLength,
                 dictionary, frame_interval_calib, display='Yes', video_frame=None, save_every_n_frames=None):
        self.projectname = os.path.join(proj_repo, projectname)
        create_dir(self.projectname)
        self.param_folder = f'{self.projectname}/CalibrationFiles'
        create_dir(self.param_folder)
        self.corrected_video_folder = f'{self.projectname}/CorrectedVideos'
        create_dir(self.corrected_video_folder)
        self.save_calib_frames = save_every_n_frames
        self.video_files = video_files  # List of video file paths
        if self.save_calib_frames is not None:
            output_folder = f'{self.projectname}/CalibrationFrames'
            for idx, video_path in enumerate(self.video_files):
                video_name = os.path.basename(video_path).split('.')[0]
                self.output_folder = os.path.join(output_folder, video_name)
                create_dir(self.output_folder)

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
        if video_frame is not None:
            print(f'Video Frame Passed!')
            self.canvas = Canvas(self.video_frame, width=640, height=480)
            self.canvas.pack()
            self.gif_image = Image.open("../assets/Blocks-1s-200px (1).gif")
            size = (50, 50)
            self.gif_frames = [ImageTk.PhotoImage(img.resize(size)) for img in ImageSequence.Iterator(self.gif_image)]

            self.text_canvas = Canvas(self.video_frame, width=640, height=100)
            self.text_canvas.pack(side='bottom')
            # self.gif_frames = [ImageTk.PhotoImage(img.resize(size, Image.ANTIALIAS)) for img in ImageSequence.Iterator(self.gif_image)]
            self.current_gif_frame = 0
            self.total_gif_frames = len(self.gif_frames)

            self.gif_label = Label(self.video_frame, image=self.gif_frames[0])
            self.gif_label.place(relx=0.5, rely=0.8)  # Position it according to your layout
        self.video_name = None

    def stop_displaying_video_and_show_text(self):
        self.canvas.delete("all")
        text_id = self.text_canvas.create_text(320, 50, anchor="center", font=("Helvetica", 20),
                                               text="Computing Calibration ||||")
        self.animate_text(text_id, 0)

    def animate_text(self, text_id, count):
        messages = ["Computing Calibration", "Computing Calibration |", "Computing Calibration ||",
                    "Computing Calibration |||", "Computing Calibration ||||"]
        self.text_canvas.itemconfig(text_id, text=messages[count % len(messages)])
        self.video_frame.after(500, self.animate_text, text_id, count + 1)

    def display_completion_text(self, video_name):
        self.text_canvas.delete("all")
        self.text_canvas.create_text(320, 50, anchor="center", font=("Helvetica", 20),
                                     text=f"Calibration completed for {video_name}")

    def calibrate_only(self):
        self.animate_gif(True)
        # total_videos = len(self.video_files)
        all_charuco_corners = []
        all_charuco_ids = []
        # print('Starting Calibration')

        for idx, video_path in enumerate(self.video_files):
            cap = None
            try:
                video_name = os.path.basename(video_path).split('.')[0]
                if self.video_name is None:
                    self.video_name = video_name
                save_path = f'{self.param_folder}/{self.save_path_prefix}_{video_name}.npz'
                self.report_progress(f"Processing {video_path}...", -1, "info")

                cap = cv2.VideoCapture(video_path)
                if not cap.isOpened():
                    print(f"Warning: Couldn't open video file {video_path}. Skipping...")
                    continue

                frame_count = 0
                gray = None
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break

                    if frame_count % self.frame_interval_calib == 0:
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        corners, ids, _ = cv2.aruco.detectMarkers(gray, self.aruco_dict)

                        if len(corners) > 0:
                            debug_frame = cv2.aruco.drawDetectedMarkers(frame.copy(), corners, ids)
                            if self.display.lower() == 'yes':
                                self.display_video(debug_frame)
                            ret, charuco_corners, charuco_ids = cv2.aruco.interpolateCornersCharuco(corners, ids, gray,
                                                                                                    self.board,
                                                                                                    charucoIds=ids)
                            if not ret or len(charuco_corners) <= self.min_corners:
                                print(f'Not enough corners for interpolation')
                            else:
                                all_charuco_corners.append(charuco_corners)
                                all_charuco_ids.append(charuco_ids)

                                # Save the frame used for calibration
                                if self.save_calib_frames is not None and frame_count % self.save_calib_frames == 0:
                                    frame_filename = os.path.join(self.output_folder,
                                                                  f'{video_name}_{frame_count}.png')
                                    cv2.imwrite(frame_filename, debug_frame)

                    frame_count += 1
                if self.display.lower() == 'yes':  # Close Tkinter window if display is enabled
                    self.canvas.delete('all')
                self.stop_displaying_video_and_show_text()
                # Perform camera calibration
                if len(all_charuco_corners) > 0 and len(all_charuco_ids) > 0:
                    ret, mtx, dist, rvecs, tvecs = cv2.aruco.calibrateCameraCharuco(all_charuco_corners,
                                                                                    all_charuco_ids,
                                                                                    self.board,
                                                                                    gray.shape[::-1], None, None)

                    np.savez(save_path, mtx=mtx, dist=dist)
                    self.update_status_text(f'Calibration Completed for {video_name}. File saved at {save_path}')
                    self.display_completion_text(video_name)

            except Exception as e:
                print(f"An error occurred while processing {video_path}. Error: {str(e)}")
            finally:
                if cap is not None:
                    cap.release()
