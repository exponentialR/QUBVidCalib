import datetime
import os.path

import cv2
import numpy as np
from matplotlib import pyplot as plt

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


class PatternGenerator:
    def __init__(self, pattern_type, rows, columns, checker_width, dictionary=None, marker_et_percentage=None,
                 margin=10,
                 pattern_name=datetime.datetime.now(), dpi: int = 300):

        self.pattern_type = pattern_type
        self.pattern_size = (rows, columns)
        self.square_size = checker_width  # This is indeed the width of each square in the checkerboard
        self.board_width = columns * checker_width  # Updated
        self.board_height = rows * checker_width  # Updated
        self.dictionary = dictionary
        self.marker_length = int(0.8 * self.square_size) if marker_et_percentage is None else int(
            marker_et_percentage * self.square_size)
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

        # Calculate the pixel value of the margin
        margin_px = int((self.margin / 25.4) * self.dpi)

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

        return pattern_image

    def export_to_pdf(self, image):
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
        annotations = [
            f"Recommended Paper Size: {recommended_paper_size} ({paper_width_mm:.2f} mm x {paper_height_mm:.2f} mm)",
            f"Pattern Type: {self.pattern_type}",
            f"Rows: {self.pattern_size[0]}",
            f"Columns: {self.pattern_size[1]}",
            f"Square Size: {self.square_size} mm"
        ]
        if self.pattern_type.lower() == 'charuco':
            annotations.append(f"ArUco Dictionary: {self.dictionary}")

        annotation_text = " | ".join(annotations)

        ax.annotate(annotation_text,
                    xy=(0.5, 1.02),
                    xycoords='axes fraction',
                    fontsize=fontsize,
                    ha='center')

        # Save as PDF
        pdf_path = f"Generated/{self.pattern_type.title()}-{self.pattern_name.strftime('%Y%m%d_%H%M%S')}.pdf"
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

    def generate(self):
        if self.pattern_type == 'checkerboard':
            return self.generate_checkerboard()
        elif self.pattern_type == 'charuco':
            return self.generate_charuco()
        else:
            raise ValueError("Unsupported pattern type")

    def generate_charuco(self) -> np.ndarray:
        if not self.marker_length or not self.dictionary:
            raise ValueError("Both Marker Length and Dictionary should be provided for Charuco pattern. ")
        # Calculate image dimensions
        width_px = int((self.board_width / 25.4 + 2 * self.margin / 25.4) * self.dpi)
        height_px = int((self.board_height / 25.4 + 2 * self.margin / 25.4) * self.dpi)
        print(f'Height of PX : {height_px}')
        print(f'Width of PX: {width_px}')
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
                print(f'SIZE WIDTH MM: {size_width_mm}')
                print(f'SIZE HEIGHT MM : {size_height_mm}')
                return size_name  # Return the first suitable size found

        return 'Custom Size'  # Return 'Custom Size' if no suitable size was found

