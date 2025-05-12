import sys
print("Script started")
from PyQt5.QtWidgets import (QApplication, QLabel, QWidget, QPushButton,
                             QVBoxLayout, QHBoxLayout, QSlider, QTextEdit, QFileDialog,
                             QGridLayout, QGroupBox, QFrame, QSizePolicy, QCheckBox,
                             QScrollArea, QDoubleSpinBox, QFormLayout, QWidgetItem)
print("PyQt5.QtWidgets modules imported")
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5.QtGui import QPixmap, QPainter, QColor, QFont, QPen, QPainterPath
print("Other PyQt5 modules imported")
import csv
import os
import cv2
import numpy as np

# Import the selection screen
from selection_screen import SelectionScreen

def resource_path(relative_path):
    """Get the absolute path to the resource, works for development and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class ImageLabelWithClick(QLabel):
    """Custom QLabel class that handles mouse clicks and maintains image proportions"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_app = None
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(100, 100)
        self.drawing = False
        self.lasso_points = []
        self.last_point = None
        self.realise_lasso = False

        
    def setParentApp(self, app):
        self.parent_app = app
        
    def mousePressEvent(self, event):
        """Start drawing the lasso when mouse is pressed"""
        if not self.pixmap() or not self.parent_app:
            return

        # Effective area of the image displayed within the label
        img_rect = self.getImageRect()
        
        if not img_rect.contains(event.pos()):
            # Click is outside the image
            return
            
        # Calculate normalized coordinates (0-1) within the image
        norm_x = (event.pos().x() - img_rect.x()) / img_rect.width()
        norm_y = (event.pos().y() - img_rect.y()) / img_rect.height()
        
        # Convert to original image coordinates
        original_pixmap = self.parent_app.original_pixmap
        img_x = norm_x * original_pixmap.width()
        img_y = norm_y * original_pixmap.height()
        
        # Start a new selection
        self.drawing = True
        self.lasso_points = [(img_x, img_y)]
        self.last_point = (img_x, img_y)
        
        # Redraw markers
        # self.parent_app.redrawAreaSelection()

    
    def mouseMoveEvent(self, event):
        """Add points to the lasso during mouse movement"""
        if not self.drawing or not self.pixmap() or not self.parent_app:
            return
            
        # Effective area of the image displayed within the label
        img_rect = self.getImageRect()
        
        if not img_rect.contains(event.pos()):
            # Movement is outside the image
            return
            
        # Calculate normalized coordinates (0-1) within the image
        norm_x = (event.pos().x() - img_rect.x()) / img_rect.width()
        norm_y = (event.pos().y() - img_rect.y()) / img_rect.height()
        
        # Convert to original image coordinates
        original_pixmap = self.parent_app.original_pixmap
        img_x = norm_x * original_pixmap.width()
        img_y = norm_y * original_pixmap.height()
        
        # Add point to the lasso
        self.lasso_points.append((img_x, img_y))
        self.last_point = (img_x, img_y)
        
        # Redraw markers
        self.parent_app.redrawAreaSelection()
    
    def mouseReleaseEvent(self, event):
        """Finish drawing the lasso and set the selected area"""
        self.parent_app.displayImage()
        self.realise_lasso = True
        if self.drawing and len(self.lasso_points) > 2:
            # Close the lasso
            self.lasso_points.append(self.lasso_points[0])  # Close the polygon
            
            # Process the lasso to check intersection with the hand mask
            # This will also set click_position and calculate center
            if self.parent_app.processLassoSelection(self.lasso_points):
                # Redraw the area
                self.parent_app.redrawAreaSelection()
            else:
                # Reset if the area doesn't intersect with the hand
                # self.parent_app.selected_area = []
                self.parent_app.redrawAreaSelection()
                self.parent_app.click_position = (None, None)
                print("Selected area does not intersect with the hand area")
        else:
            self.parent_app.redrawAreaSelection()
        
        self.drawing = False
        self.realise_lasso = False

    
    def getImageRect(self):
        """Return the exact rectangle occupied by the image within the label"""
        if not self.pixmap():
            return QRect()
            
        # Label and image dimensions
        label_size = self.size()
        pixmap_size = self.pixmap().size()
        
        # Calculate scale factor to maintain proportions
        scale_w = label_size.width() / pixmap_size.width()
        scale_h = label_size.height() / pixmap_size.height()
        scale = min(scale_w, scale_h)
        
        # Scaled image dimensions
        scaled_width = pixmap_size.width() * scale
        scaled_height = pixmap_size.height() * scale
        
        # Position of the centered image within the label
        x_offset = (label_size.width() - scaled_width) / 2
        y_offset = (label_size.height() - scaled_height) / 2
        
        return QRect(int(x_offset), int(y_offset), int(scaled_width), int(scaled_height))

class SensationApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sensation Cataloger")
        self.setGeometry(100, 100, 1000, 700)
        self.setMinimumSize(800, 600)
        
        # Initialize variables
        self.click_position = (None, None)
        self.device_name = ""  # Store device name
        self.patient_id = ""   # Store patient ID
        self.point_markers = []
        self.selected_area = []  # Stores the points of the selected area
        self.sensation_checkboxes = {}  # Store references to checkboxes
        self.hand_mask = None  # Will store the binary mask image
        
        # Parameters from selection screen (default values)
        self.hand_side = "right"  # Default to right hand
        self.modulation_type = "amplitude"
        self.modulation_param_name = "Current (mA)"
        self.fixed_parameters = {
            "current": None,
            "frequency": 50,
            "pulse_width": 200,
            "interphase": 100
        }
        self.stimulation_types = {
            "median_nerve": False,
            "ulnar_nerve": False
        }
        
        # Configure better style
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
            QTextEdit {
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 5px;
                background-color: white;
            }
            QSlider::groove:horizontal {
                height: 8px;
                background: #cccccc;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #4CAF50;
                border: 1px solid #4CAF50;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QGroupBox {
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
            }
            QCheckBox {
                font-weight: normal;
                margin: 3px;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        
        # Create frame for image with border
        image_frame = QFrame()
        image_frame.setFrameStyle(QFrame.Panel | QFrame.Sunken)
        image_frame.setLineWidth(2)
        
        # Use the custom class for the image label
        self.image_label = ImageLabelWithClick()
        self.image_label.setParentApp(self)
        
        # Load hand image based on selection (default to right)
        image_path = os.path.join('PIC', self.hand_side.capitalize(), 'Hand.jpg')
        self.original_pixmap = QPixmap(image_path)
        
        # Load hand mask
        self.loadHandMask()
        
        self.displayImage()
        
        # Add the image to the frame
        image_layout = QVBoxLayout(image_frame)
        image_layout.addWidget(self.image_label)
        
        # Right panel for controls
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        
        # Parameter information
        param_group = QGroupBox("Stimulation Parameters")
        self.param_layout = QFormLayout()
        
        # Create modulation parameter input
        self.modulation_input = QDoubleSpinBox()
        self.modulation_input.setMinimumHeight(30)
        
        if self.modulation_type == "amplitude":
            self.modulation_input.setRange(0.1, 50.0)
            self.modulation_input.setSingleStep(0.1)
            self.modulation_input.setValue(1.0)
            self.modulation_input.setSuffix(" mA")
        elif self.modulation_type == "pulse_width":
            self.modulation_input.setRange(1, 5000)
            self.modulation_input.setSingleStep(10)
            self.modulation_input.setValue(200)
            self.modulation_input.setSuffix(" μs")
        else:  # frequency
            self.modulation_input.setRange(1, 1000)
            self.modulation_input.setSingleStep(1)
            self.modulation_input.setValue(50)
            self.modulation_input.setSuffix(" Hz")
        
        # Call updateParameterDisplay to set up the parameter layout
        self.updateParameterDisplay()
        
        param_group.setLayout(self.param_layout)
        
        # Sensation type selection area
        sensation_group = QGroupBox("Sensation Type")
        sensation_layout = QGridLayout()
        
        # Create checkboxes for each sensation type
        sensation_types = [
            "Vibration", "Flutter", "Buzz", 
            "Movement through body/across skin",
            "Movement without motor activity",
            "Urge to move",
            "Touch",
            "Pressure",
            "Sharp",
            "Prick",
            "Tap",
            "Electric current",
            "Shock",
            "Pulsing",
            "Tickle",
            "Itch",
            "Tingle",
            "Numb",
            "Warm",
            "Cool"
        ]
        
        # Create a scrollable area for checkboxes
        scroll_widget = QWidget()
        checkbox_layout = QVBoxLayout(scroll_widget)
        
        for sensation in sensation_types:
            checkbox = QCheckBox(sensation)
            checkbox_layout.addWidget(checkbox)
            self.sensation_checkboxes[sensation] = checkbox
        
        # Add "Other" checkbox with text field
        other_layout = QHBoxLayout()
        self.other_checkbox = QCheckBox("Other:")
        self.other_textfield = QTextEdit()
        self.other_textfield.setMaximumHeight(50)
        self.other_textfield.setEnabled(False)
        self.other_checkbox.toggled.connect(lambda checked: self.other_textfield.setEnabled(checked))
        
        other_layout.addWidget(self.other_checkbox)
        other_layout.addWidget(self.other_textfield, 1)
        
        checkbox_layout.addLayout(other_layout)
        checkbox_layout.addStretch()
        
        # Add scrollable area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(scroll_widget)
        sensation_layout.addWidget(scroll)
        sensation_group.setLayout(sensation_layout)
        
        # Additional description area
        description_group = QGroupBox("Additional Description")
        description_layout = QVBoxLayout()
        self.description_box = QTextEdit()
        self.description_box.setPlaceholderText("Describe the sensation in more detail...")
        self.description_box.setMinimumHeight(100)
        description_layout.addWidget(self.description_box)
        description_group.setLayout(description_layout)
        
        # Sensation parameter sliders
        sliders_group = QGroupBox("Sensation Parameters")
        sliders_layout = QGridLayout()
        
        # Natural slider
        natural_label = QLabel("How natural was the sensation?")
        self.natural_slider = QSlider(Qt.Horizontal)
        self.natural_slider.setMinimum(0)
        self.natural_slider.setMaximum(10)
        self.natural_slider.setValue(5)
        self.natural_slider.setTickPosition(QSlider.TicksBelow)
        self.natural_slider.setTickInterval(1)
        self.natural_value = QLabel("5")
        self.natural_slider.valueChanged.connect(lambda v: self.natural_value.setText(str(v)))
        
        # Pain slider
        pain_label = QLabel("How painful was the sensation?")
        self.pain_slider = QSlider(Qt.Horizontal)
        self.pain_slider.setMinimum(0)
        self.pain_slider.setMaximum(10)
        self.pain_slider.setValue(0)
        self.pain_slider.setTickPosition(QSlider.TicksBelow)
        self.pain_slider.setTickInterval(1)
        self.pain_value = QLabel("0")
        self.pain_slider.valueChanged.connect(lambda v: self.pain_value.setText(str(v)))
        
        # Electrode sensation slider
        electrode_label = QLabel("Sensation under the electrode:")
        self.electrode_slider = QSlider(Qt.Horizontal)
        self.electrode_slider.setMinimum(0)
        self.electrode_slider.setMaximum(10)
        self.electrode_slider.setValue(5)
        self.electrode_slider.setTickPosition(QSlider.TicksBelow)
        self.electrode_slider.setTickInterval(1)
        self.electrode_value = QLabel("5")
        self.electrode_slider.valueChanged.connect(lambda v: self.electrode_value.setText(str(v)))
        
        # Add sliders to layout
        sliders_layout.addWidget(natural_label, 0, 0)
        sliders_layout.addWidget(self.natural_slider, 0, 1)
        sliders_layout.addWidget(self.natural_value, 0, 2)
        
        sliders_layout.addWidget(pain_label, 1, 0)
        sliders_layout.addWidget(self.pain_slider, 1, 1)
        sliders_layout.addWidget(self.pain_value, 1, 2)
        
        sliders_layout.addWidget(electrode_label, 2, 0)
        sliders_layout.addWidget(self.electrode_slider, 2, 1)
        sliders_layout.addWidget(self.electrode_value, 2, 2)
        
        sliders_group.setLayout(sliders_layout)
        
        # Save and Return buttons
        button_layout = QHBoxLayout()
        
        # Return to Selection Screen button
        self.return_button = QPushButton("Return to Selection")
        self.return_button.setMinimumHeight(40)
        self.return_button.clicked.connect(self.returnToSelection)
        self.return_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        
        # Clear selection button
        self.clear_button = QPushButton("Clear Selection")
        self.clear_button.setMinimumHeight(40)
        self.clear_button.clicked.connect(self.clearSelection)
        self.clear_button.setStyleSheet("""
            QPushButton {
                background-color: #FF5722;
                color: white;
            }
            QPushButton:hover {
                background-color: #E64A19;
            }
        """)
        
        # Save button
        self.save_button = QPushButton("Save Sensation")
        self.save_button.setMinimumHeight(40)
        self.save_button.clicked.connect(self.save_data)
        
        button_layout.addStretch()
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.return_button)
        button_layout.addWidget(self.save_button)
        button_layout.addStretch()
        
        # Right panel layout
        right_layout.addWidget(param_group, 0)
        right_layout.addWidget(sensation_group, 2)
        right_layout.addWidget(description_group, 1)
        right_layout.addWidget(sliders_group, 1)
        right_layout.addLayout(button_layout)
        right_layout.addStretch()
        
        # Main layout
        main_layout = QHBoxLayout()
        main_layout.addWidget(image_frame, 3)  # Ratio 3:2
        main_layout.addWidget(right_panel, 2)
        
        self.setLayout(main_layout)
        
        print("Interface initialized")
        
        # Schedule initial image resizing after rendering
        QApplication.instance().processEvents()
        self.adjustImage()

    def resizeEvent(self, event):
        # Resize the image when the window is resized
        self.displayImage()
        super().resizeEvent(event)

    def displayImage(self):
        # Resize image proportionally to container
        label_size = self.image_label.size()
        if label_size.width() > 0 and label_size.height() > 0:
            scaled_pixmap = self.original_pixmap.scaled(
                label_size, 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
            
            # Redraw markers if they exist
            if self.selected_area:
                self.redrawAreaSelection()

    def redrawPointMarkers(self):
        # Get pixmap for drawing
        pixmap = self.image_label.pixmap().copy()
        
        # Get rectangle of image in label
        img_rect = self.image_label.getImageRect()
        
        # Calculate scale factor
        scale_x = pixmap.width() / self.original_pixmap.width()
        scale_y = pixmap.height() / self.original_pixmap.height()
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        for x, y in self.point_markers:
            # Convert original image coordinates to displayed pixmap coordinates
            display_x = x * scale_x
            display_y = y * scale_y
            
            # Draw marker
            marker_size = 16
            painter.setPen(QColor(255, 0, 0))
            painter.setBrush(QColor(255, 0, 0, 128))
            painter.drawEllipse(int(display_x - marker_size/2), 
                               int(display_y - marker_size/2),
                               marker_size, marker_size)
        
        painter.end()
        self.image_label.setPixmap(pixmap)    
        
    def redrawAreaSelection(self):
        """Draw the selected area with the lasso on the map"""
        
        # Check if there is a valid image
        if not self.image_label.pixmap():
            return
            
        # Create a copy of the pixmap for drawing
        pixmap = self.image_label.pixmap().copy()
        
        # Calculate scale factor to convert original image coordinates to displayed coordinates
        scale_x = pixmap.width() / self.original_pixmap.width()
        scale_y = pixmap.height() / self.original_pixmap.height()
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw the selection area in progress (during lasso drawing)
        # Only show the lasso points while actively drawing
        if self.image_label.drawing and len(self.image_label.lasso_points) > 1:
            # Convert original image coordinates to displayed coordinates
            scaled_points = []
            for x, y in self.image_label.lasso_points:
                display_x = x * scale_x
                display_y = y * scale_y
                scaled_points.append((display_x, display_y))
            
            # Draw lasso outline with light blue color
            painter.setPen(QColor(0, 153, 255, 200))  # Light blue color
            for i in range(1, len(scaled_points)):
                painter.drawLine(
                    int(scaled_points[i-1][0]), 
                    int(scaled_points[i-1][1]),
                    int(scaled_points[i][0]), 
                    int(scaled_points[i][1])
                )
            
            
        
        # Draw the selected area (after completing the drawing)
        if self.selected_area and len(self.selected_area) > 2 and self.image_label.realise_lasso:
            # Since selected_area contains individual points rather than just the outline,
            # we'll directly draw each point as a small filled rectangle
            
            # Set the color for the filled area (light blue with transparency)
            painter.setBrush(QColor(0, 153, 255, 10))
            painter.setPen(Qt.NoPen)  # No outline
            
            # Get the original image dimensions to convert normalized coordinates if needed
            img_width = self.original_pixmap.width()
            img_height = self.original_pixmap.height()
            
            # Size of each point to draw (adjust as needed for density)
            point_size = 2
            
            # If points appear to be normalized (between 0-1), scale them to image dimensions
            first_point = self.selected_area[0]
            needs_scaling = (0 <= first_point[0] <= 1) and (0 <= first_point[1] <= 1)
            
            # Draw each point in the selected area
            for x, y in self.selected_area:
                # Convert coordinates if they are normalized
                if needs_scaling:
                    x = x * img_width
                    y = y * img_height
                    
                # Scale to display coordinates
                display_x = x * scale_x
                display_y = y * scale_y
                
                # Draw a small rectangle for each point
                painter.drawRect(int(display_x), int(display_y), point_size, point_size)
                
        
        painter.end()
        self.image_label.setPixmap(pixmap)

    def updateParameterDisplay(self):
        """Update the parameter display with current modulation values"""
        # Clear the existing form layout
        while self.param_layout.count() > 0:
            item = self.param_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Ricrea modulation_input since it's been deleted
        self.modulation_input = QDoubleSpinBox()
        self.modulation_input.setMinimumHeight(30)
        
        # Configure the input based on modulation type
        if self.modulation_type == "amplitude":
            self.modulation_input.setRange(0.1, 50.0)
            self.modulation_input.setSingleStep(0.1)
            self.modulation_input.setValue(1.0)
            self.modulation_input.setSuffix(" mA")
        elif self.modulation_type == "pulse_width":
            self.modulation_input.setRange(1, 5000)
            self.modulation_input.setSingleStep(10)
            self.modulation_input.setValue(200)
            self.modulation_input.setSuffix(" μs")
        else:  # frequency
            self.modulation_input.setRange(1, 1000)
            self.modulation_input.setSingleStep(1)
            self.modulation_input.setValue(50)
            self.modulation_input.setSuffix(" Hz")
        
        # Add modulation type label
        mod_type_text = "Current"
        if self.modulation_type == "pulse_width":
            mod_type_text = "Pulse-Width"
        elif self.modulation_type == "frequency":
            mod_type_text = "Frequency"
                
        mod_type_label = QLabel(f"Modulation type: {mod_type_text}")
        mod_type_label.setStyleSheet("font-weight: bold;")
        self.param_layout.addRow(mod_type_label)
        
        # Add modulated parameter with correct formatting
        if self.modulation_type == "amplitude":
            self.param_layout.addRow("Current (mA):", self.modulation_input)
        elif self.modulation_type == "pulse_width":
            self.param_layout.addRow("Pulse width (μs):", self.modulation_input)
        else:  # frequency
            self.param_layout.addRow("Frequency (Hz):", self.modulation_input)
        
        # Add fixed parameters as labels
        current_value = "-" if self.modulation_type == "amplitude" else f"{self.fixed_parameters['current']} mA"
        current_label = QLabel(f"Current: {current_value}")
        self.param_layout.addRow(current_label)
        
        freq_value = "-" if self.modulation_type == "frequency" else f"{self.fixed_parameters['frequency']} Hz"
        freq_label = QLabel(f"Frequency: {freq_value}")
        self.param_layout.addRow(freq_label)
        
        pw_value = "-" if self.modulation_type == "pulse_width" else f"{self.fixed_parameters['pulse_width']} μs"
        pw_label = QLabel(f"Pulse width: {pw_value}")
        self.param_layout.addRow(pw_label)
        
        # Always show interphase
        interphase_label = QLabel(f"Interphase: {self.fixed_parameters['interphase']} μs")
        self.param_layout.addRow(interphase_label)

    def save_data(self):
        # If no point or area has been selected
        if self.click_position == (None, None):
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Warning", "Select an area on the image before saving.")
            return
            
        # Dialog to select file
        default_dir = os.path.join(os.getcwd(), "Saving_folder")
        if not os.path.exists(default_dir):
            os.makedirs(default_dir)
            
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Sensation", 
            os.path.join(default_dir, "sensation.csv"),
            "CSV Files (*.csv)"
        )
        
        if filename:
            # Get selected sensation types
            selected_sensations = []
            for sensation, checkbox in self.sensation_checkboxes.items():
                if checkbox.isChecked():
                    selected_sensations.append(sensation)
            
            # Add custom sensation if selected
            if self.other_checkbox.isChecked() and self.other_textfield.toPlainText().strip():
                selected_sensations.append(f"Other: {self.other_textfield.toPlainText().strip()}")
            
            # Join selected sensations into a string
            sensations_str = ", ".join(selected_sensations)
            
            # Save data in CSV format
            with open(filename, mode='a', newline='') as file:
                writer = csv.writer(file)                # Check if file is empty to add headers                if os.path.getsize(filename) == 0:
                writer.writerow([
                    "Patient ID", "Device Name", "Sensation Types", "Additional Description", 
                    "Natural Rating", "Pain Rating", "Electrode Sensation",
                    "Center X", "Center Y", "Area",
                    "Hand", "Modulation Type", "Modulation Value",
                    "Current (mA)", "Frequency (Hz)", "Pulse Width (μs)", "Interphase (μs)",
                    "Median Nerve", "Ulnar Nerve"
                ])
                
                # Convert selected area to a string (format: x1,y1;x2,y2;...)
                area_str = ""
                if self.selected_area:
                    points_str = []
                    for x, y in self.selected_area:
                        points_str.append(f"{x:.1f},{y:.1f}")
                    area_str = ";".join(points_str)
                  # Save data, including the area and stimulation parameters                  
                writer.writerow([
                    self.patient_id,
                    self.device_name,
                    sensations_str,
                    self.description_box.toPlainText(),
                    self.natural_slider.value(),
                    self.pain_slider.value(),
                    self.electrode_slider.value(),
                    self.click_position[0],
                    self.click_position[1],
                    area_str,
                    self.hand_side,
                    self.modulation_type,
                    self.modulation_input.value(),
                    self.fixed_parameters.get("current"),
                    self.fixed_parameters.get("frequency"),
                    self.fixed_parameters.get("pulse_width"),
                    self.fixed_parameters.get("interphase"),
                    "Median" if self.stimulation_types["median_nerve"] else "",
                    "Ulnar" if self.stimulation_types["ulnar_nerve"] else ""
                ])
                
            # Clear fields for next recording
            self.description_box.clear()
            self.natural_slider.setValue(5)
            self.pain_slider.setValue(0)
            self.electrode_slider.setValue(5)
            
            # Reset all checkboxes
            for checkbox in self.sensation_checkboxes.values():
                checkbox.setChecked(False)
            self.other_checkbox.setChecked(False)
            self.other_textfield.clear()
            self.other_textfield.setEnabled(False)
            
            # Reset selected area
            self.selected_area = []
            self.click_position = (None, None)
            
            # Update display
            self.redrawAreaSelection()
            
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "Success", "Data saved successfully!")

    def adjustImage(self):
        """Ensure image is correctly sized at application startup"""
        # Force layout calculation
        self.layout().activate()
        QApplication.instance().processEvents()
        
        # Resize image based on current label size
        self.displayImage()
          
    def showEvent(self, event):
        """Handles initial window display event"""
        super().showEvent(event)
        # Schedule image adjustment after display
        QApplication.instance().processEvents()
        self.adjustImage()
        
    def clearSelection(self):
        """Clear the currently selected area"""
        if self.selected_area:
            self.selected_area = []
            self.click_position = (None, None)
            self.displayImage()
            print("Selection cleared")

    def returnToSelection(self):
        """Return to the selection screen"""
        # Hide the main window
        self.hide()
        # Show the selection screen again (this is done through the main script)
        if hasattr(self, 'selection_screen'):
            self.selection_screen.show()
    
    def updateFromSelectionScreen(self, data):
        """Update the interface based on parameters from the selection screen"""
        # Store the selected hand
        self.hand_side = data["hand"]  # "right" or "left"
        
        # Store modulation info
        self.modulation_type = data["modulation"]["type"]
        self.modulation_param_name = data["modulation"]["param_name"]

        # Store patient ID and device name
        self.patient_id = data.get("patient_id", "")
        self.device_name = data.get("device_name", "")
            
        # Store fixed parameters
        self.fixed_parameters = data["parameters"]
        
        # Store stimulation types
        self.stimulation_types = data["stimulation"]
        
        # Load the appropriate hand image
        image_path = os.path.join('PIC', self.hand_side.capitalize(), 'Hand.jpg')
        self.original_pixmap = QPixmap(image_path)
        
        # Load the matching hand mask
        self.loadHandMask()
        
        self.displayImage()
        
        # Update the modulation parameter input and set correct value based on modulation type
        if self.modulation_type == "amplitude":
            self.modulation_input.setRange(0.1, 20.0)
            self.modulation_input.setSingleStep(0.1)
            self.modulation_input.setSuffix(" mA")
            # Default value is 1.0 but only set if we don't have a current parameter
            if self.fixed_parameters["current"] is None:
                self.modulation_input.setValue(1.0)
            else:
                # Use the fixed current as the starting value
                self.modulation_input.setValue(float(self.fixed_parameters["current"]))
        elif self.modulation_type == "pulse_width":
            self.modulation_input.setRange(1, 1000)
            self.modulation_input.setSingleStep(10)
            self.modulation_input.setSuffix(" μs")
            # Default value is 200 but only set if we don't have a pulse width parameter
            if self.fixed_parameters["pulse_width"] is None:
                self.modulation_input.setValue(200)
            else:
                # Use the fixed pulse width as the starting value
                self.modulation_input.setValue(float(self.fixed_parameters["pulse_width"]))
        else:  # frequency
            self.modulation_input.setRange(1, 1000)
            self.modulation_input.setSingleStep(1)
            self.modulation_input.setSuffix(" Hz")
            # Default value is 50 but only set if we don't have a frequency parameter
            if self.fixed_parameters["frequency"] is None:
                self.modulation_input.setValue(50)
            else:
                # Use the fixed frequency as the starting value
                self.modulation_input.setValue(float(self.fixed_parameters["frequency"]))
        
        # Update the parameter display instead of updating individual labels
        self.updateParameterDisplay()

    def loadHandMask(self):
        """Load the binary mask for the selected hand (right or left)"""
        import cv2
        import numpy as np
        
        # Path to the binary mask
        mask_path = os.path.join('PIC', self.hand_side.capitalize(), 'binary_mask.jpg')
        
        try:
            # Read the mask using OpenCV
            self.hand_mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
            if self.hand_mask is None:
                print(f"Error: Could not load hand mask from {mask_path}")
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Warning", f"Non è possibile caricare la maschera della mano da {mask_path}")
            else:
                print(f"Hand mask loaded from {mask_path}")
                
                # We know for sure that black (0) represents the hand area
                # and white (255) represents the background
                black_pixels = np.sum(self.hand_mask < 50)  # Count very dark pixels (hand)
                white_pixels = np.sum(self.hand_mask > 200)  # Count very light pixels (background)
                print(f"Hand area pixels (black): {black_pixels}, Background pixels (white): {white_pixels}")
                
                # No need to invert the mask as we know the correct format
                
                # Save mask for debugging if needed
                # debug_path = os.path.join('PIC', self.hand_side.capitalize(), 'debug_mask.jpg')
                # cv2.imwrite(debug_path, self.hand_mask)
        except Exception as e:
            print(f"Exception loading hand mask: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Warning", f"Errore nel caricamento della maschera: {e}")
            self.hand_mask = None 
            
    def processLassoSelection(self, lasso_points):
        """Process the lasso points and check intersection with hand mask,
        uniting with any previously selected area
        
        Args:
            lasso_points: List of (x, y) tuples representing the lasso polygon points
            
        Returns:
            bool: True if the area intersects with the hand mask, False otherwise
        """
        import cv2
        import numpy as np
        
        if self.hand_mask is None:
            # If no mask is loaded, accept all selections
            print("Warning: No hand mask loaded, accepting all selections")
            
            # If we already have a selection, merge with it
            if self.selected_area:
                self.selected_area = self.selected_area + lasso_points
            else:
                self.selected_area = lasso_points
            
            # Calculate the center of the selected area
            total_x = sum(point[0] for point in self.selected_area)
            total_y = sum(point[1] for point in self.selected_area)
            center_x = total_x / len(self.selected_area)
            center_y = total_y / len(self.selected_area)
            
            self.click_position = (center_x, center_y)
            print(f"Area selected with center at coordinates: ({center_x:.1f}, {center_y:.1f})")
            
            return True
            
        try:
            # Create an empty mask with the same size as the hand mask
            mask_height, mask_width = self.hand_mask.shape
            lasso_mask = np.zeros((mask_height, mask_width), dtype=np.uint8)
            
            # Convert lasso points to numpy array in opencv format (integers)
            points = np.array([(int(x), int(y)) for x, y in lasso_points])
            
            # Draw the lasso polygon on the mask (255 = white/selected)
            cv2.fillPoly(lasso_mask, [points], 255)
            
            # Calculate the intersection between lasso selection and hand mask
            # The hand is black (0) in the mask, so we want areas where lasso_mask is 255
            # and hand_mask is close to 0
            intersection = cv2.bitwise_and(lasso_mask, cv2.threshold(self.hand_mask, 50, 255, cv2.THRESH_BINARY_INV)[1])
            
            # Check if the intersection is empty
            if cv2.countNonZero(intersection) == 0:
                # No intersection with the hand
                print("Selected area is completely outside the hand region")
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Warning", "La selezione deve intersecare l'area della mano (area nera nella maschera).")
                return False
                
            # Get the coordinates of the current intersection
            coords = np.argwhere(intersection == 255)
            # Normalizza le coordinate rispetto alle dimensioni dell'immagine
            mask_height, mask_width = intersection.shape
            new_intersection_area = [(float(coord[1]) / mask_width, float(coord[0]) / mask_height) for coord in coords]
            
            # If we already have a selected area, unite with the new one
            if self.selected_area:
                # We'll create a combined mask in image space
                combined_mask = np.zeros((mask_height, mask_width), dtype=np.uint8)
                
                # Add existing points to the mask
                for x, y in self.selected_area:
                    # Convert normalized coordinates back to image coordinates
                    img_x = int(x * mask_width)
                    img_y = int(y * mask_height)
                    if 0 <= img_x < mask_width and 0 <= img_y < mask_height:
                        combined_mask[img_y, img_x] = 255
                
                # Add new points to the mask
                for x, y in new_intersection_area:
                    # Convert normalized coordinates back to image coordinates
                    img_x = int(x * mask_width)
                    img_y = int(y * mask_height)
                    if 0 <= img_x < mask_width and 0 <= img_y < mask_height:
                        combined_mask[img_y, img_x] = 255
                
                # Get all points in the combined mask
                combined_coords = np.argwhere(combined_mask == 255)
                
                # Convert to normalized coordinates
                self.selected_area = [(float(coord[1]) / mask_width, float(coord[0]) / mask_height) for coord in combined_coords]
            else:
                # First selection
                self.selected_area = new_intersection_area
            
            # Calculate the center of the selected area
            total_x = sum(point[0] for point in self.selected_area)
            total_y = sum(point[1] for point in self.selected_area)
            center_x = total_x / len(self.selected_area)
            center_y = total_y / len(self.selected_area)
            
            self.click_position = (center_x, center_y)
            print(f"Area selected with center at coordinates: ({center_x:.1f}, {center_y:.1f})")
            
            return True
            
        except Exception as e:
            print(f"Error processing lasso selection: {e}")
            # On error, accept the original selection but don't merge
            self.selected_area = lasso_points
            
            # Calculate the center
            total_x = sum(point[0] for point in lasso_points)
            total_y = sum(point[1] for point in lasso_points)
            center_x = total_x / len(lasso_points)
            center_y = total_y / len(lasso_points)
            
            self.click_position = (center_x, center_y)
            print(f"Error in processing. Area selected with center at coordinates: ({center_x:.1f}, {center_y:.1f})")
            
            return True

if __name__ == '__main__':
    print("Starting application")
    app = QApplication(sys.argv)
    
    # Create the selection screen first
    selection = SelectionScreen()
    
    # Create the main sensation app (initially hidden)
    main_window = SensationApp()
    
    # Store reference to selection screen in main window
    main_window.selection_screen = selection
    
    # Connect the selection screen's signal to the main window
    selection.selectionComplete.connect(main_window.updateFromSelectionScreen)
    selection.selectionComplete.connect(lambda _: main_window.show())
    
    # Show the selection screen first
    selection.show()
    
    print("Application displayed")
    sys.exit(app.exec_())