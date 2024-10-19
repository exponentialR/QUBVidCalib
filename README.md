[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.13956034.svg)](https://doi.org/10.5281/zenodo.13956034)

# CalibraVision - Camera Calibration Toolbox
![CameraCalibration-tool.png](assets/CameraCalibration-tool.png)

Read about Calibration [here](https://samueladebayo.com/camera-calibration-part-1)


[Introduction](#introduction) &nbsp; | &nbsp; [Features](#features) &nbsp; | &nbsp; [Experimental Features](#experimental-features) &nbsp; | &nbsp; [Prerequisites](#prerequisites) &nbsp; | &nbsp; [Installation](#installation) &nbsp; | &nbsp; [Usage](#usage) &nbsp; | &nbsp; [Loading Configuration](#loading-configuration) &nbsp; | &nbsp; [Starting Calibration or Correction](#starting-calibration-or-correction) &nbsp; | &nbsp; [Screenshots](#screenshots) &nbsp; | &nbsp; [Video Guide](#video-guide) &nbsp; | &nbsp; [Development Status](#development-status) &nbsp; | &nbsp; [Contributing](#contributing) &nbsp; | &nbsp; [License](#license) &nbsp; | &nbsp; [Acknowledgements](#acknowledgements)


## Introduction

The CalibraVision offers a sophisticated yet user-friendly toolkit for camera calibration and video correction, integrating advanced pattern recognition and calibration techniques to enhance the accuracy and efficiency of the calibration process.
## Features

> **Dynamic Pattern Generation**: Support for Charuco and Checker patterns, customizable according to user needs.

> **Enhanced Calibration Options**: Including 'Calibrate Only', 'Self-Calibrate & Correct', 'Correct Only', and 'Single Calib and Multiple Video Correction'.

> **Real-time display** of corrected and uncorrected video streams

> Ability to **save calibration parameters** for future use

> Easy-to-use graphical interface with **intuitive controls**

> Option to load **custom calibration files**

> Extensive **logging** to monitor calibration and correction processes

## Prerequisites
To be installed using requirements.txt
- Python 3.x
- Tkinter
- OpenCV
- NumPy
- configparser

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/exponentialR/QUBVidCalib.git
2. Navigate to the project directory:
    ````bash
   cd QUBVidCalib
   
3. Create a Python environment and install dependencies:

- On Linux:

    ````bash 
   python3 -m venv calibra
   source calibra/bin/activate
   pip install -r requirements.txt
  
   
- On Windows:
    ````bash 
  python -m venv calibra
  .\calibra\Scripts\activate
  pip install -r requirements.txt

- On Mac:
    ````bash
  python3 -m venv calibra
  source calibra/bin/activate
  pip install -r requirements.txt


4. Starting the app
   ```bash 
   cd src 
   python3 main.py

## Usage
### Loading Configuration
Loading Configuration
On application start, the GUI loads existing configurations from settings.ini if available. Users have the option to manually set the following parameters:

* **Calibration Type**: Chaurco or Checkerboard
* **Project Repository**: Set the directory for saving project files.
* **Project Name**: Assign a unique name for the calibration session.
* **Video Files**: Specify the target videos for calibration or correction.
* **Calibration Board Dimensions**: Input the dimensions of the used calibration board.
* **Frame Interval**: Determine the frame capture rate for calibration.
* **Number of Frames to Save**: Set how many frames are saved during calibration.
* **Dictionary Type**: if using charuco, Choose the marker dictionary type for pattern detection.

### Starting Calibration or Correction
The main window offers three options:

1. **Calibrate Only**: Perform only the calibration step.
2. **Correct Only**: Perform only the correction step.
3. **Calibrate and Correct**: Perform both calibration and correction.
Once started, the application provides real-time logging and status updates. The corrected video and calibration parameters can be saved for future use.

### Calibration Pattern Generation
An additional feature, "Generate Calibration Pattern," is now available for creating custom calibration patterns. Users can define the pattern type, dimensions, and other parameters for printing, and recommended paper size will be atop the pattern.

### Experimental Features

- Play/Pause controls for video review (In Development)
- Slider for video navigation (In Development)

## Development Status
- Chessboard Pattern: Integration for Chessboard calibration patterns is now complete and available.
- Pattern Generation: Users can generate custom calibration patterns directly within the application.

## Contributing
Feel free to fork this repository and submit a pull request if you have some features or fixes to contribute. For more information, please read the CONTRIBUTING.md guide.

## License
This project is licensed under the MIT License - see the [LICENSE.md](./LICENSE.md) file for details.


## TODO 
> Enhancements to the embedded Video Player for a richer user experience.

## Citation
If you find this project useful, please consider citing it using the following BibTeX entry:
```bibtex

@misc{adebayo_exponentialrqubvidcalib_2024,
	title = {{exponentialR}/{QUBVidCalib}: {V1}.0},
	shorttitle = {{exponentialR}/{QUBVidCalib}},
	url = {https://zenodo.org/records/13956034},
	abstract = {publication release},
	urldate = {2024-10-19},
	publisher = {Zenodo},
	author = {Adebayo, Samuel},
	month = oct,
	year = {2024},
	doi = {10.5281/zenodo.13956034},
}
