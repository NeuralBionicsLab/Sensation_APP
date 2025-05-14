import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QRadioButton, QCheckBox, QLabel,
                           QVBoxLayout, QHBoxLayout, QPushButton, QGroupBox, QFormLayout,
                           QDoubleSpinBox, QFrame, QGridLayout, QButtonGroup, QMessageBox, QLineEdit)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon


class SelectionScreen(QWidget):
    # Signal to pass data to the main window
    selectionComplete = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sensory NBLab")
    
        # Set the application icon
        app_icon = QIcon("Icon/Icon.png")
        self.setWindowIcon(app_icon)
        
        self.setWindowState(Qt.WindowMaximized)  # Make window maximized
        
        # Set stylesheet for a nice UI
        self.setStyleSheet("""
            QWidget {
                font-size: 11pt;
                background-color: #f5f5f5;
            }
            QLabel {
                font-weight: bold;
                color: #333333;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QGroupBox {
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
            }
            QRadioButton, QCheckBox {
                font-weight: normal;
                margin: 5px;
            }
            QDoubleSpinBox {
                border: 1px solid #cccccc;
                border-radius: 3px;
                padding: 5px;
                min-height: 25px;
            }
        """)
          # Create the layout
        main_layout = QVBoxLayout()
          # Patient ID input section
        patient_group = QGroupBox("Patient Information")
        patient_layout = QFormLayout()
        
        # Add patient ID field
        self.patient_id = QLineEdit()
        self.patient_id.setPlaceholderText("Enter Patient ID")
        patient_layout.addRow("Patient ID:", self.patient_id)
        patient_group.setLayout(patient_layout)

        # Device input section
        device_group = QGroupBox("Device Information")
        device_layout = QFormLayout()

        # Add device name field  
        self.device_name = QLineEdit()
        self.device_name.setPlaceholderText("Enter Device Name")
        device_layout.addRow("Device name:", self.device_name)
        device_group.setLayout(device_layout)
        
        # Hand selection group
        hand_group = QGroupBox("Hand Selection")
        hand_layout = QHBoxLayout()
        
        self.right_hand = QRadioButton("Right Hand")
        self.right_hand.setChecked(True)  # Default selection
        self.left_hand = QRadioButton("Left Hand")
        
        # Group the radio buttons
        hand_button_group = QButtonGroup(self)
        hand_button_group.addButton(self.right_hand)
        hand_button_group.addButton(self.left_hand)
        
        hand_layout.addWidget(self.right_hand)
        hand_layout.addWidget(self.left_hand)
        hand_group.setLayout(hand_layout)
        
        # Modulation type group
        modulation_group = QGroupBox("Modulation Type")
        modulation_layout = QVBoxLayout()
        
        self.amplitude_radio = QRadioButton("Amplitude")
        self.amplitude_radio.setChecked(True)  # Default selection
        self.pulse_width_radio = QRadioButton("Pulse-width")
        self.frequency_radio = QRadioButton("Frequency")
        
        # Group the radio buttons
        modulation_button_group = QButtonGroup(self)
        modulation_button_group.addButton(self.amplitude_radio)
        modulation_button_group.addButton(self.pulse_width_radio)
        modulation_button_group.addButton(self.frequency_radio)
        
        # Connect modulation type selection to parameter visibility update
        self.amplitude_radio.toggled.connect(self.updateParameterVisibility)
        self.pulse_width_radio.toggled.connect(self.updateParameterVisibility)
        self.frequency_radio.toggled.connect(self.updateParameterVisibility)
        
        modulation_layout.addWidget(self.amplitude_radio)
        modulation_layout.addWidget(self.pulse_width_radio)
        modulation_layout.addWidget(self.frequency_radio)
        modulation_group.setLayout(modulation_layout)
        
        # Parameter settings group
        param_group = QGroupBox("Fixed Parameters")
        self.param_layout = QFormLayout()
        
        # For the current input - set 2 decimal places
        self.current_input = QDoubleSpinBox()
        self.current_input.setRange(0.1, 20.0)
        self.current_input.setSingleStep(0.1)
        self.current_input.setValue(1.0)
        self.current_input.setSuffix(" mA")
        self.current_input.setDecimals(2)  # Show 2 decimal places

        # For frequency, pulse width and interphase - set 0 decimal places
        self.frequency_input = QDoubleSpinBox()
        self.frequency_input.setRange(1, 1000)
        self.frequency_input.setSingleStep(1)
        self.frequency_input.setValue(50)
        self.frequency_input.setSuffix(" Hz")
        self.frequency_input.setDecimals(0)  # Show 0 decimal places

        self.pulse_width_input = QDoubleSpinBox()
        self.pulse_width_input.setRange(1, 1000)
        self.pulse_width_input.setSingleStep(1)
        self.pulse_width_input.setValue(200)
        self.pulse_width_input.setSuffix(" μs")
        self.pulse_width_input.setDecimals(0)  # Show 0 decimal places

        self.interphase_input = QDoubleSpinBox()
        self.interphase_input.setRange(0, 500)
        self.interphase_input.setSingleStep(1)
        self.interphase_input.setValue(100)
        self.interphase_input.setSuffix(" μs")
        self.interphase_input.setDecimals(0)  # Show 0 decimal places

        # For threshold inputs - these need to change based on modulation type
        self.sensory_threshold_input = QDoubleSpinBox()
        self.sensory_threshold_input.setRange(0.1, 20.0)
        self.sensory_threshold_input.setSingleStep(0.1)
        self.sensory_threshold_input.setValue(1.0)
        self.sensory_threshold_input.setSuffix(" mA")
        self.sensory_threshold_input.setDecimals(2)  # Default for mA

        self.motor_threshold_input = QDoubleSpinBox()
        self.motor_threshold_input.setRange(0.1, 20.0)
        self.motor_threshold_input.setSingleStep(0.1)
        self.motor_threshold_input.setValue(1.5)
        self.motor_threshold_input.setSuffix(" mA")
        self.motor_threshold_input.setDecimals(2)  # Default for mA
        
        # Add parameters to layout
        self.param_layout.addRow("Current:", self.current_input)
        self.param_layout.addRow("Frequency:", self.frequency_input)
        self.param_layout.addRow("Pulse width:", self.pulse_width_input)
        self.param_layout.addRow("Interphase distance:", self.interphase_input)
        self.param_layout.addRow("Sensory threshold:", self.sensory_threshold_input)
        self.param_layout.addRow("Motor threshold:", self.motor_threshold_input)
        param_group.setLayout(self.param_layout)
        
        # Nerve stimulation type group
        nerve_group = QGroupBox("Stimulation Nerve")
        nerve_layout = QVBoxLayout()
        
        self.median_nerve = QCheckBox("Median nerve")
        self.ulnar_nerve = QCheckBox("Ulnar nerve")
        
        nerve_layout.addWidget(self.median_nerve)
        nerve_layout.addWidget(self.ulnar_nerve)
        nerve_group.setLayout(nerve_layout)
        
        # Continue button
        button_layout = QHBoxLayout()
        self.continue_button = QPushButton("Continue to Sensation Interface")
        self.continue_button.clicked.connect(self.onContinueClicked)
        button_layout.addStretch()
        button_layout.addWidget(self.continue_button)
        
        # Create a grid layout for the top section
        top_grid = QGridLayout()
        top_grid.addWidget(hand_group, 0, 0)
        top_grid.addWidget(modulation_group, 0, 1)
        top_grid.addWidget(param_group, 1, 0)
        top_grid.addWidget(nerve_group, 1, 1)          # Add sections to main layout
        main_layout.addWidget(patient_group)
        main_layout.addWidget(device_group)
        main_layout.addLayout(top_grid)
        main_layout.addStretch()
        main_layout.addLayout(button_layout)
        
        self.setLayout(main_layout)
        
        # Update parameter visibility based on default selection
        self.updateParameterVisibility()
    
    def updateParameterVisibility(self):
        """Update which parameters are enabled based on modulation type selected"""
        # Current is disabled if Amplitude modulation is selected
        self.current_input.setEnabled(not self.amplitude_radio.isChecked())
        
        # Frequency is disabled if Frequency modulation is selected
        self.frequency_input.setEnabled(not self.frequency_radio.isChecked())
        
        # Pulse width is disabled if Pulse-width modulation is selected
        self.pulse_width_input.setEnabled(not self.pulse_width_radio.isChecked())
        
        # Update threshold suffixes based on modulation type
        if self.amplitude_radio.isChecked():
            self.sensory_threshold_input.setSuffix(" mA")
            self.motor_threshold_input.setSuffix(" mA")
            self.sensory_threshold_input.setRange(0.1, 20.0)
            self.motor_threshold_input.setRange(0.1, 20.0)
            self.motor_threshold_input.setSingleStep(0.10)
            self.sensory_threshold_input.setSingleStep(0.10)
            self.sensory_threshold_input.setDecimals(2)  # 2 decimals for current
            self.motor_threshold_input.setDecimals(2)
        elif self.pulse_width_radio.isChecked():
            self.sensory_threshold_input.setSuffix(" μs")
            self.motor_threshold_input.setSuffix(" μs")
            self.sensory_threshold_input.setRange(1, 1000)
            self.motor_threshold_input.setRange(1, 1000)
            self.motor_threshold_input.setSingleStep(1)
            self.sensory_threshold_input.setSingleStep(1)
            self.sensory_threshold_input.setDecimals(0)  # 0 decimals for pulse width
            self.motor_threshold_input.setDecimals(0)
        else:  # frequency
            self.sensory_threshold_input.setSuffix(" Hz")
            self.motor_threshold_input.setSuffix(" Hz")
            self.sensory_threshold_input.setRange(1, 1000)
            self.motor_threshold_input.setRange(1, 1000)
            self.motor_threshold_input.setSingleStep(1)
            self.sensory_threshold_input.setSingleStep(1)
            self.sensory_threshold_input.setDecimals(0)  # 0 decimals for frequency
            self.motor_threshold_input.setDecimals(0)
    
    def onContinueClicked(self):
        """Collect all selected parameters and emit signal to main app"""
        # Determine which hand was selected
        hand = "right" if self.right_hand.isChecked() else "left"
        # Collect Patient ID and Device Name
        patient_id = self.patient_id.text().strip()
        device_name = self.device_name.text().strip()
        
        # Determine modulation type
        modulation = ""
        modulation_param_value = 0
        
        if self.amplitude_radio.isChecked():
            modulation = "amplitude"
            modulation_param_name = "Current (mA)"
            # This will be entered in the main window
        elif self.pulse_width_radio.isChecked():
            modulation = "pulse_width"
            modulation_param_name = "Pulse width (μs)"
            # This will be entered in the main window
        else:  # frequency
            modulation = "frequency"
            modulation_param_name = "Frequency (Hz)"
            # This will be entered in the main window
        
        # Get threshold values
        sensory_threshold = self.sensory_threshold_input.value()
        motor_threshold = self.motor_threshold_input.value()
        
        # Check if motor threshold is greater than sensory threshold
        if motor_threshold <= sensory_threshold:
            QMessageBox.warning(self, "Error", "Motor threshold must be greater than sensory threshold.")
            return
        
        # Get fixed parameter values
        parameters = {
            "current": self.current_input.value() if not self.amplitude_radio.isChecked() else None,
            "frequency": self.frequency_input.value() if not self.frequency_radio.isChecked() else None,
            "pulse_width": self.pulse_width_input.value() if not self.pulse_width_radio.isChecked() else None,
            "interphase": self.interphase_input.value(),
            "sensory_threshold": sensory_threshold,
            "motor_threshold": motor_threshold
        }
        
        # Get stimulation types
        stimulation = {
            "median_nerve": self.median_nerve.isChecked(),
            "ulnar_nerve": self.ulnar_nerve.isChecked()
        }
        # Check if at least one nerve is selected
        if not (stimulation["median_nerve"] or stimulation["ulnar_nerve"]):
            QMessageBox.warning(self, "Warning", "Please select at least one nerve stimulation type.")
            return
        
        if not patient_id:
            QMessageBox.warning(self, "Error", "Please enter a Patient ID before proceeding.")
            return
            
        if not device_name:
            QMessageBox.warning(self, "Error", "Please enter a Device Name before proceeding.")
            return
        
        # Create data to pass to main interface
        data = {
            "hand": hand,
            "modulation": {
                "type": modulation,
                "param_name": modulation_param_name
            },
            "parameters": parameters,
            "stimulation": stimulation,
            "patient_id": patient_id,
            "device_name": device_name,
            "sensory_threshold": sensory_threshold,
            "motor_threshold": motor_threshold
        }
        
        # Emit signal with data
        self.selectionComplete.emit(data)
        
        # Close this window
        self.hide()

if __name__ == "__main__":
    # For testing this module independently
    app = QApplication(sys.argv)
    window = SelectionScreen()
    window.show()
    sys.exit(app.exec_())
