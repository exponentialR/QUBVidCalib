import datetime
import os.path
from pathlib import Path
import cv2
import numpy as np
from matplotlib import pyplot as plt
import io
from PIL import Image, ImageTk
from tkinter import NW

from reportlab.lib.pagesizes import landscape, portrait
from reportlab.lib.pagesizes import JUNIOR_LEGAL, HALF_LETTER, A0, A1, A2, A3, A4, A5, A6, A7, A8, A9, \
    A10, B0, B1, B2, B3, B4, B5, B6, B7, B8, B9, B10, C0, C1, C2, C3, C4, C5, C6, C7, C8, C9, C10, LEGAL, LETTER, \
    ELEVENSEVENTEEN, GOV_LEGAL, GOV_LETTER

inch = 72.0
cm = inch / 2.54
mm = cm * 0.1
pica = 12.0
TABLOID = (11 * inch, 17 * inch)
LEDGER = (17 * inch, 11 * inch)

PAPER_SIZES = {
    "A0": A0, "A1": A1, "A2": A2, "A3": A3, "A4": A4, "A5": A5,
    "A6": A6, "A7": A7, "A8": A8, "A9": A9, "A10": A10,
    "B0": B0, "B1": B1, "B2": B2, "B3": B3, "B4": B4, "B5": B5,
    "B6": B6, "B7": B7, "B8": B8, "B9": B9, "B10": B10,
    "C0": C0, "C1": C1, "C2": C2, "C3": C3, "C4": C4, "C5": C5,
    "C6": C6, "C7": C7, "C8": C8, "C9": C9, "C10": C10,
    "Letter": LETTER, "Legal": LEGAL, "11x17": ELEVENSEVENTEEN,
    "Junior Legal": JUNIOR_LEGAL, "Half Letter": HALF_LETTER,
    "Gov Letter": GOV_LETTER, "Gov Legal": GOV_LEGAL,
    "Tabloid": TABLOID, "Ledger": LEDGER
}

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


def fig_to_np(fig, ax):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches='tight', pad_inches=0)
    buf.seek(0)
    img_arr = np.frombuffer(buf.getvalue(), dtype=np.uint8)
    buf.close()
    img = cv2.imdecode(img_arr, 1)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return img


class PatternGenerator:
    def __init__(self, pattern_location: Path, pattern_type: str, rows: int, columns: int, checker_width: int,
                 marker_et_percentage=None, dictionary: str = None,
                 margin: int = 10,
                 pattern_name=datetime.datetime.now(), dpi: int = 300, status_queue=None, video_frame=None):
        marker_et_percentage = float(marker_et_percentage) if marker_et_percentage is not None else None
        self.pattern_type = pattern_type
        self.pattern_size = (rows, columns)
        self.square_size = int(checker_width)
        print(f'SQUARE SIZE: {self.square_size}')
        self.board_width = columns * checker_width  # Updated
        self.board_height = rows * checker_width  # Updated
        self.dictionary = dictionary
        self.marker_length = int(0.8 * self.square_size) if marker_et_percentage is None else int(
            marker_et_percentage * self.square_size)
        self.margin = margin
        self.paper_sizes = PAPER_SIZES
        self.pattern_name = pattern_name
        self.dpi = dpi
        self.status_queue = status_queue
        self.project_dir = os.path.join(pattern_location, 'Generated-CalibPattern')
        os.makedirs(self.project_dir) if not os.path.exists(self.project_dir) else None
        self.stop_requested = False
        self.video_frame = video_frame

    def generate_charuco(self) -> np.ndarray:
        if self.stop_requested:
            return np.array([])
        if not self.marker_length or not self.dictionary:
            raise ValueError("Both Marker Length and Dictionary should be provided for Charuco pattern. ")
        # Calculate image dimensions
        width_px = int((self.board_width / 25.4 + 2 * self.margin / 25.4) * self.dpi)
        height_px = int((self.board_height / 25.4 + 2 * self.margin / 25.4) * self.dpi)

        # Calculate the pixel value of the margin
        margin_px = int((self.margin / 25.4) * self.dpi)

        # Create ArUco dictionaryy
        aruco_dict = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, self.dictionary))

        # Create Charuco board
        charuco_board = cv2.aruco.CharucoBoard((self.pattern_size[1], self.pattern_size[0]),
                                               self.square_size / 1000, self.marker_length / 1000,
                                               aruco_dict
                                               )
        # Generate Charuco pattern
        charuco_image = charuco_board.generateImage((width_px - 2 * margin_px, height_px - 2 * margin_px))

        # Create a white image with margins
        pattern_image = np.ones((height_px, width_px), dtype=np.uint8) * 255

        # Place the Charuco pattern on it
        pattern_image[margin_px:-margin_px, margin_px:-margin_px] = charuco_image

        return pattern_image

    def generate_checkerboard(self):
        if self.stop_requested:
            return np.array([])
        # Calculate image dimensions
        width_px = int((self.board_width / 25.4 + 2 * self.margin / 25.4) * self.dpi)
        height_px = int((self.board_height / 25.4 + 2 * self.margin / 25.4) * self.dpi)

        # Create a white image
        pattern_image = np.ones((height_px, width_px), dtype=np.uint8) * 255

        # Calculate the pixel value of the margin
        margin_px = int((self.margin / 25.4) * self.dpi)
        if self.status_queue is not None:
            self.status_queue.put(('DRAWING CHECKERBOARD PATTERN', "anime"))
        # Draw the checkerboard
        square_size_px = int((self.square_size / 25.4) * self.dpi)
        for i in range(self.pattern_size[0]):
            for j in range(self.pattern_size[1]):
                if (i + j) % 2 == 0:
                    continue
                x1 = j * square_size_px + margin_px
                y1 = i * square_size_px + margin_px
                x2 = (j + 1) * square_size_px + margin_px
                y2 = (i + 1) * square_size_px + margin_px
                pattern_image[y1:y2, x1:x2] = 0
        self.status_queue.put(('GENERATED CHECKERBOARD PATTERN', 'stop-anime'))
        return pattern_image

    def export_to_pdf(self, image):
        print('We are exporting PDF')
        self.status_queue.put(('SAVING TO PDF', 'anime'))
        # Create a Matplotlib figure and axis
        fig, ax = plt.subplots(figsize=(self.board_width / 25.4 + 2 * self.margin / 25.4,
                                        self.board_height / 25.4 + 2 * self.margin / 25.4), dpi=self.dpi)
        ax.axis('off')

        # Display the image
        ax.imshow(image, cmap='gray', extent=[0, image.shape[1], 0, image.shape[0]])

        # Manually set axes limits to ensure margin
        ax.set_xlim([0, image.shape[1]])
        ax.set_ylim([0, image.shape[0]])

        # Add annotations
        recommended_paper_size = self.recommend_paper_size()
        paper_width_mm, paper_height_mm = [dim / 72 * 25.4 for dim in self.get_paper_size(recommended_paper_size)]
        font_scale = paper_width_mm / 500  # Adjust text size based on paper width
        fontsize = int(12 * font_scale)

        # Add paper dimensions in mm to the annotation
        annotations_dict = {
            "Rec. Print Size": f"{recommended_paper_size} ({paper_width_mm:.2f} mm x {paper_height_mm:.2f} mm)",
            "Pattern Type": self.pattern_type,
            "Rows": str(self.pattern_size[0]),
            "Columns": str(self.pattern_size[1]),
            "Square Size": f"{self.square_size} mm"
        }

        if self.pattern_type.lower() == 'charuco':
            annotations_dict["ArUco Dictionary"] = self.dictionary
            annotations_dict["Marker Size"] = self.marker_length

        annotation_text = " | ".join(f"{key}: {value}" for key, value in annotations_dict.items())

        self.status_queue.put(('-------------', 'stop-anime'))
        # self.status_queue.put

        ax.annotate(annotation_text,
                    xy=(0.5, 1.02),
                    xycoords='axes fraction',
                    fontsize=fontsize,
                    ha='center')
        annotations_dict['Project Repository'], annotations_dict['Pattern Name']= self.project_dir, self.pattern_name
        self.status_queue.put((annotations_dict, 'display-pattern-text'))
        # Save as PDF
        pdf_path = f"{self.project_dir}/{self.pattern_type.title()}-{self.pattern_name.strftime('%Y%m%d_%H%M%S')}.pdf"
        plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0, dpi=self.dpi)
        self.status_queue.put((f'CALIBRATION PATTERN PDF SAVED TO {pdf_path}', 'stop-anime'))
        print(f"PDF saved to {pdf_path}")

        # Convert to NumPy array
        img = fig_to_np(fig, ax)

        # Resize and show on Tkinter (replace 'self.video_frame' and 'self.video_frame.img' with your actual canvas and image objects)
        img_resized = cv2.resize(img, (440, 360))
        tk_img = ImageTk.PhotoImage(image=Image.fromarray(img_resized))
        self.status_queue.put((f'Displaying Generated Pattern: {self.pattern_name}.pdf', 'anime'))
        self.video_frame.img = tk_img  # Update the PhotoImage object
        self.video_frame.create_image(0, 0, image=tk_img, anchor=NW)
        self.status_queue.put((f'Done', 'stop-anime'))
        self.status_queue.put((f'Please click on the link below to locate the calibration pattern: {pdf_path}', 'INFO'))

    def get_paper_orientation(self, name):
        paper_size = self.paper_sizes[name]
        if self.board_width > self.board_height:
            return landscape(paper_size)
        else:
            return portrait(paper_size)

    def get_paper_size(self, name):
        if name in self.paper_sizes:
            return self.get_paper_orientation(name)
        width_pt = (self.board_width + 2 * self.margin) / 25.4 * 72
        height_pt = (self.board_height + 2 * self.margin) / 25.4 * 72
        return width_pt, height_pt

    def generate(self):
        if self.stop_requested:
            return
        if self.pattern_type.lower() == 'checker':
            checker_board = self.generate_checkerboard()
            if self.stop_requested:
                return
            return self.export_to_pdf(checker_board)
        elif self.pattern_type.lower() == 'charuco':
            charuco_board = self.generate_charuco()
            if self.stop_requested:
                return
            return self.export_to_pdf(charuco_board)
        else:
            raise ValueError("Unsupported pattern type")
        # self.status_queue.put(())

    def recommend_paper_size(self):
        self.status_queue.put(('GETTING RECOMMENDED PAPER SIZE', 'anime'))
        total_width_mm = self.board_width + 2 * self.margin
        total_height_mm = self.board_height + 2 * self.margin

        # Sort paper sizes by area
        sorted_paper_sizes = sorted(
            self.paper_sizes.items(),
            key=lambda item: (item[1][0] / 72 * 25.4) * (item[1][1] / 72 * 25.4)
        )

        # Find the smallest paper size that can fit the pattern
        for size_name, size_dim in sorted_paper_sizes:
            size_width_mm, size_height_mm = [dim / 72 * 25.4 for dim in size_dim]  # Convert from points to millimeters

            if (total_width_mm <= size_width_mm and total_height_mm <= size_height_mm) or \
                    (total_width_mm <= size_height_mm and total_height_mm <= size_width_mm):  # Check both orientations
                self.status_queue.put((f'Recommended Print Size: {size_width_mm}x{size_height_mm} mm', 'stop-anime'))

                return size_name  # Return the first suitable size found

        return 'Custom Size'  # Return 'Custom Size' if no suitable size was found

    def stop(self):
        self.stop_requested = True
