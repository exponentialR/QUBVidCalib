import unittest
from pattern_generator import PatternGenerator, PAPER_SIZES  # Import PAPER_SIZES from your module


def expected_paper_size(board_width, board_height, margin):
    total_width_mm = board_width + 2 * margin
    total_height_mm = board_height + 2 * margin

    # Find the smallest paper size that can fit the pattern
    recommended_size = None
    for size_name, size_dim in PAPER_SIZES.items():
        size_width_mm, size_height_mm = [dim / 72 * 25.4 for dim in size_dim]  # Convert from points to millimeters
        if (total_width_mm <= size_width_mm and total_height_mm <= size_height_mm) or \
                (total_width_mm <= size_height_mm and total_height_mm <= size_width_mm):  # Check both orientations
            if recommended_size is None:
                recommended_size = size_name  # First suitable size found
            else:
                # Check if the current size is smaller than the previously found suitable size
                prev_size_dim = PAPER_SIZES[recommended_size]
                if size_width_mm * size_height_mm < prev_size_dim[0] / 72 * 25.4 * prev_size_dim[1] / 72 * 25.4:
                    recommended_size = size_name

    return recommended_size if recommended_size is not None else 'Custom Size'


class TestPaperSizeRecommendation(unittest.TestCase):

    def test_paper_size_recommendation(self):
        test_cases = [
            ((6, 9, 25, int(size_dim[0] / 72 * 25.4) - 40, int(size_dim[1] / 72 * 25.4) - 40), size_name)
            for size_name, size_dim in PAPER_SIZES.items()
        ]

        for pattern_size, expected_size in test_cases:
            rows, columns, checker_width, board_width, board_height = pattern_size
            pattern_gen = PatternGenerator('charuco', rows, columns, checker_width, board_width, board_height)
            recommended_size = pattern_gen.recommend_paper_size()
            self.assertEqual(recommended_size, expected_size, f"Failed for {pattern_size}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
