"""
Utility to debug the mask loading and interpretation.
This script loads and displays the binary mask from the Right and Left folders
to help understand how they should be interpreted.
"""
import cv2
import numpy as np
import os
import matplotlib.pyplot as plt

def examine_mask(side="Right"):
    # Path to the binary mask
    mask_path = os.path.join('PIC', side, 'binary_mask.jpg')
    
    try:
        # Read the mask using OpenCV
        mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
        if mask is None:
            print(f"Error: Could not load hand mask from {mask_path}")
            return
            
        print(f"{side} hand mask loaded from {mask_path}")
        mask_mean = np.mean(mask)
        print(f"Mask mean value: {mask_mean}")
        
        # Count black vs white pixels
        black_pixels = np.sum(mask < 50)  # Count very dark pixels
        white_pixels = np.sum(mask > 200)  # Count very light pixels
        print(f"Black pixels: {black_pixels}, White pixels: {white_pixels}")
        
        # Display original mask
        plt.figure(figsize=(12, 6))
        plt.subplot(1, 2, 1)
        plt.title(f"Original {side} Mask")
        plt.imshow(mask, cmap='gray')
        
        # Display inverted mask
        inverted_mask = cv2.bitwise_not(mask)
        plt.subplot(1, 2, 2)
        plt.title(f"Inverted {side} Mask")
        plt.imshow(inverted_mask, cmap='gray')
        
        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"Exception examining mask: {e}")

if __name__ == "__main__":
    print("Examining Right hand mask:")
    examine_mask("Right")
    
    print("\nExamining Left hand mask:")
    examine_mask("Left")
