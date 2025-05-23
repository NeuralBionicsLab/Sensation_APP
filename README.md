# SensoryNBLab

## Overview

SensoryNBLab is a specialized research tool designed for quantitative and qualitative assessment of sensory responses from peripheral nerve stimulation, developed at the **Neural Bionics Lab**. The application provides an intuitive graphical interface for mapping and documenting sensations experienced during electrical nerve stimulation experiments.

### Key Features

- **Dual-hand support**: Select either right or left hand for stimulation mapping
- **Multiple modulation types**: Configure amplitude, frequency, or pulse width modulation
- **Precision parameter control**: Fine-tune stimulation parameters with appropriate decimal precision
- **Nerve selection**: Target median nerve, ulnar nerve, or both
- **Visual mapping interface**: Interactive hand visualization for precise sensation localization
- **Comprehensive sensation catalog**: Select from multiple predefined sensation types or add custom descriptions
- **Quantitative assessment**: Rate sensation naturalness, painfulness, and other qualities
- **Data collection**: Store multiple reports in a structured format

## Data Storage Format

All experiment data is saved in MATLAB (.mat) format with the following structure:

```
data
├── Date: "yyyy/mm/dd h:min"
├── PatientID: "patient ID"
├── Hand: "Left" or "Right"
├── ModulationType: "amplitude", "pulse_width", or "frequency"
├── Nerve: "Median", "Ulnar", or "Both"
├── InterphaseDistance_us: interphase distance value in μs
├── Current: value in mA (or [] if it is the modulating parameter)
├── Frequency: value in Hz (or [] if it is the modulating parameter)
├── PulseWidth: value in μs (or [] if it is the modulating parameter)
├── MotorThreshold: motor threshold value
├── SensoryThreshold: sensory threshold value
└── Report: struct
    ├── 1: struct (first saved sensation)
    │   ├── Map: 2D matrix (dimensions of the Hand.jpg image) with 1 in selected pixels, 0 elsewhere
    │   ├── ModulatedParameter
    │   ├── Sensation: cell containing the selected sensation types
    │   ├── AdditionalDescription: string with additional description
    │   ├── Naturalness: value from 0 to 10
    │   ├── Painfulness: value from 0 to 10
    │   └── UnderElectrodeSensation: value from 0 to 10
    ├── 2: struct (second saved sensation)
    │   └── ...
    └── n: struct (nth saved sensation)
        └── ...
```

Each report contains a binary map of the selected hand area and detailed sensation information, allowing for comprehensive analysis in MATLAB.

## Executable Version

The application is also available as a standalone executable file, which does not require Python to be installed, at the following link: https://drive.google.com/file/d/1YbZ5gNUnAoFdnu2plVS0AD05VOJQgd9p/view?usp=drive_link . You can find the executable in the SensoryAPP.zip file included in this project. Simply extract the contents of the ZIP file and run the executable to start using the application.

## Requirements for Development

If you want to run or develop SensoryNBLab from source code, you will need the following dependencies:

```
PyQt5>=5.15.0     # For the graphical user interface
numpy>=1.19.0     # For numerical computations
opencv-python>=4.5.0  # For image processing
scipy>=1.6.0      # For MATLAB file operations
```

You can install all required dependencies using pip:

```
pip install -r requirements.txt
```

## Important Note

Please do not modify or delete any files in the `PIC` folder or other directories included in the project. These files are essential for the proper functioning of the application. 

To use the application, simply run the standalone executable file (`.exe`) provided in the `SensoryAPP.zip` archive. Extract the contents of the ZIP file and double-click the executable to start the application. No additional setup or modification of files is required.
