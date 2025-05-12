# filepath: c:\Users\Roberto\Desktop\GUI\mask.py

import cv2
import numpy as np
import os
import matplotlib.pyplot as plt

def create_binary_mask():
    # Path to the Pre_mask.jpg file
    input_path = os.path.join('PIC', 'Right', 'Pre_mask.jpg')
    
    # Check if the file exists
    if not os.path.exists(input_path):
        print(f"Error: File {input_path} not found!")
        return
    
    # Read the image
    img = cv2.imread(input_path)
    
    if img is None:
        print(f"Error: Cannot read image {input_path}!")
        return
    
    # Convert to grayscale
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Create binary mask: Convert dark pixels to black (0) and everything else to white (255)
    # Using a threshold - you might need to adjust this value
    threshold_value = 50
    _, binary_mask = cv2.threshold(gray_img, threshold_value, 255, cv2.THRESH_BINARY)
    
    # Plot the binary mask
    plt.figure(figsize=(10, 8))
    plt.imshow(binary_mask, cmap='gray')
    plt.title('Binary Mask')
    plt.axis('on')
    plt.show()
      # Save the binary mask
    output_path = os.path.join('PIC', 'Right', 'binary_mask.jpg')
    cv2.imwrite(output_path, binary_mask)
    print(f"Binary mask created and saved as {output_path}")

# Execute the function when the script is run
if __name__ == "__main__":
    create_binary_mask()