import datetime
import os.path

import cv2
import numpy as np
from PIL import Image as PILImage
from matplotlib import pyplot as plt

from reportlab.lib.pagesizes import landscape, portrait
from reportlab.platypus import SimpleDocTemplate, Image
from calibrate_correct import DICTIONARY
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


class PatternGenerator:
    def __init__(self, pattern_type, rows, columns, checker_width, dictionary=None, marker_length=None, margin=20,
                 pattern_name=datetime.datetime.now(), dpi: int = 300):
        """
        Parameters
        ----------
        pattern_type : str
            Type of the pattern ('checkerboard' or 'charuco').
        rows : int
            Number of rows in the pattern.
        columns : int
            Number of columns in the pattern.
        checker_width : float
            Size of each square in the checkerboard.
        dictionary : object, optional
            ArUco dictionary used for Charuco pattern.
        marker_length : float, optional
            Marker length for Charuco pattern.
        margin : int, optional
            Margin around the board (default is 20).
        pattern_name : datetime, optional
            Name of the pattern (default is current datetime).
        """
        self.pattern_type = pattern_type
        self.pattern_size = (rows, columns)
        self.square_size = checker_width  # This is indeed the width of each square in the checkerboard
        self.board_width = columns * checker_width  # Updated
        self.board_height = rows * checker_width  # Updated
        self.dictionary = dictionary
        self.marker_length = marker_length
        self.margin = margin
        self.paper_sizes = PAPER_SIZES
        self.pattern_name = pattern_name
        self.dpi = dpi
        os.makedirs('Generated') if not os.path.exists('Generated') else None

    def generate_checkerboard(self):
        # Calculate image dimensions
        width_px = int((self.board_width / 25.4 + 2 * self.margin / 25.4) * self.dpi)
        height_px = int((self.board_height / 25.4 + 2 * self.margin / 25.4) * self.dpi)

        # Create a white image
        pattern_image = np.ones((height_px, width_px), dtype=np.uint8) * 255

        # Draw the checkerboard
        square_size_px = int((self.square_size / 25.4) * self.dpi)
        for i in range(self.pattern_size[0]):
            for j in range(self.pattern_size[1]):
                if (i + j) % 2 == 0:
                    continue
                x1 = j * square_size_px + self.margin
                y1 = i * square_size_px + self.margin
                x2 = (j + 1) * square_size_px + self.margin
                y2 = (i + 1) * square_size_px + self.margin
                pattern_image[y1:y2, x1:x2] = 0

        return pattern_image

    def export_to_pdf(self, image):
        fig, ax = plt.subplots(figsize=(self.board_width / 25.4 + 2 * self.margin / 25.4,
                                        self.board_height / 25.4 + 2 * self.margin / 25.4), dpi=self.dpi)
        ax.axis('off')
        extent = [self.margin, image.shape[1] - self.margin, self.margin, image.shape[0] - self.margin]
        ax.imshow(image, cmap='gray', extent=extent)

        recommended_paper_size = self.recommend_paper_size()
        paper_width_mm, paper_height_mm = [dim / 72 * 25.4 for dim in self.get_paper_size(recommended_paper_size)]
        font_scale = paper_width_mm / 500  # Adjust text size based on paper width
        fontsize = int(12 * font_scale)

        annotations = [
            f"Recommended Paper Size: {recommended_paper_size}",
            f"Pattern Type: {self.pattern_type}",
            f"Number of Rows: {self.pattern_size[0]}",
            f"Number of Columns: {self.pattern_size[1]}",
            f"Square Size: {self.square_size} mm"
        ]

        for idx, annotation in enumerate(annotations):
            ax.annotate(annotation,
                        xy=(0.5, 1.02 - idx * 0.02),
                        xycoords='axes fraction',
                        fontsize=fontsize,
                        ha='center',
                        family='serif')  # Using 'serif' as the font family

        pdf_path = f"Generated/CalibrationPattern_Matplotlib_{self.pattern_name.strftime('%Y%m%d_%H%M%S')}.pdf"
        plt.savefig(pdf_path, bbox_inches='tight', pad_inches=0, dpi=self.dpi)
        print(f"PDF saved to {pdf_path}")

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

    def get_image_dimensions(self) -> tuple:
        width_px = int((self.board_width / 25.4 + 2 * self.margin / 25.4) * self.dpi)
        height_px = int((self.board_height / 25.4 + 2 * self.margin / 25.4) * self.dpi)
        return width_px, height_px

    def generate(self):
        if self.pattern_type == 'checkerboard':
            return self.generate_checkerboard()
        elif self.pattern_type == 'charuco':
            return self.generate_charuco()
        else:
            raise ValueError("Unsupported pattern type")

    def generate_charuco(self) -> np.ndarray:
        width_px, height_px = self.get_image_dimensions()

        if self.dictionary is None:
            # Use predefined dictionary:
            aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_6X6_250)
        else:
            aruco_dict = cv2.aruco.getPredefinedDictionary(getattr(cv2.aruco, self.dictionary))
        charuco_board = cv2.aruco.CharucoBoard(
            (self.pattern_size[1], self.pattern_size[0]),
            self.square_size / 1000, self.marker_length / 1000,
            aruco_dict
        )
        pattern_image = charuco_board.generateImage((width_px - 2 * int((self.margin / 25.4) * self.dpi),
                                                     height_px - 2 * int((self.margin / 25.4) * self.dpi)))
        return pattern_image

    def recommend_paper_size(self):
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
                return size_name  # Return the first suitable size found

        return 'Custom Size'  # Return 'Custom Size' if no suitable size was found

    def add_annotations(self, pattern_image, paper_size_name):
        paper_width_mm, paper_height_mm = [dim / 72 * 25.4 for dim in self.get_paper_size(paper_size_name)]
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = paper_width_mm / 500  # Adjust text size based on paper width
        font_color = (0, 0, 0)  # Black
        font_thickness = 2
        y0 = int(self.margin / 2)  # Starting y-coordinate for text, in the middle of the top margin

        annotations = []
        if self.pattern_type == 'checkerboard':
            annotations.append(f"Checker width: {self.square_size} mm")
        elif self.pattern_type == 'charuco':
            annotations.append(f"Square size: {self.square_size} mm")
            annotations.append(f"Marker length: {self.marker_length if self.marker_length else 'N/A'} mm")

        annotations.append(f"Recommended Paper Size: {paper_width_mm} mm x {paper_height_mm} mm")

        y = y0
        for annotation in annotations:
            cv2.putText(pattern_image, annotation, (int(self.margin / 2), y), font, font_scale, font_color,
                        font_thickness, cv2.LINE_AA)
            y += int(40 * font_scale)  #


# Define margins (in mm)
margin_mm = 20

# Maximum dimensions (in mm)
max_width_mm = 210 - 2 * margin_mm  # A4 width - 2 * margin
max_height_mm = 297 - 2 * margin_mm  # A4 height - 2 * margin

# Define the square size (in mm), let's say 30mm
square_size_mm = 30

# Calculate the number of rows and columns based on the square size
num_rows = int(max_height_mm // square_size_mm)
num_columns = int(max_width_mm // square_size_mm)

# Create a PatternGenerator object
pattern_generator = PatternGenerator(
    pattern_type='checkerboard',
    rows=num_rows,
    columns=num_columns,
    checker_width=square_size_mm,
    margin=margin_mm,
    dpi=300
)

# Generate the checkerboard pattern
checkerboard_pattern = pattern_generator.generate()

# Now you can use the export_to_pdf method to save the pattern, or display it using OpenCV, etc.
pattern_generator.export_to_pdf(checkerboard_pattern)
