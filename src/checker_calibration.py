import cv2
import numpy as np


def calibrate_camera_from_video(video_source=0, checkerboard=(15, 15)):
    # Initialize video capture
    cap = cv2.VideoCapture(video_source)

    # Initialize criteria and points storage
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    objpoints = []
    imgpoints = []

    # Initialize world coordinates for 3D points
    objp = np.zeros((1, checkerboard[0] * checkerboard[1], 3), np.float32)
    objp[0, :, :2] = np.mgrid[0:checkerboard[0], 0:checkerboard[1]].T.reshape(-1, 2)

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture image")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        ret, corners = cv2.findChessboardCorners(gray, checkerboard,
                                                 cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_FAST_CHECK + cv2.CALIB_CB_NORMALIZE_IMAGE)

        if ret:
            objpoints.append(objp)
            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            imgpoints.append(corners2)
            frame = cv2.drawChessboardCorners(frame, checkerboard, corners2, ret)

        cv2.imshow('Calibration', frame)

        # Press 'q' to exit the loop and proceed to calibration
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    # Perform calibration
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)

    print("Camera matrix : \n", mtx)
    print("Distortion coefficients : \n", dist)
    print("Rotation Vectors : \n", rvecs)
    print("Translation Vectors : \n", tvecs)


# Example usage
calibrate_camera_from_video(video_source=, checkerboard=(15, 15))
