# Create a file named 'watermark.py'
import cv2
import numpy as np
from scipy.fftpack import dct, idct

# --- Helper function to convert text to binary ---
def text_to_binary(text):
    binary_message = ''.join(format(ord(char), '08b') for char in text)
    # Add a simple delimiter to know when the message ends
    binary_message += "1111111100000000" 
    return binary_message

def embed_watermark(image_path, watermark_text, output_path, strength=20):
    # 1. Load Image and Convert to YCrCb
    image = cv2.imread(image_path)
    image_ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
    # Get the Y (Luma/Brightness) channel. We only watermark this.
    y_channel = image_ycrcb[:, :, 0].astype(np.float32)
    
    # 2. Prepare Watermark
    binary_watermark = text_to_binary(watermark_text)
    watermark_len = len(binary_watermark)
    bit_index = 0

    # 3. Process image in 8x8 blocks
    for i in range(0, y_channel.shape[0] - 8, 8):
        for j in range(0, y_channel.shape[1] - 8, 8):
            if bit_index >= watermark_len:
                break # Stop if message is fully embedded
            
            # Get current 8x8 block
            block = y_channel[i:i+8, j:j+8]
            
            # Apply 2D DCT
            dct_block = dct(dct(block.T, norm='ortho').T, norm='ortho')
            
            # Get watermark bit
            bit = int(binary_watermark[bit_index])
            
            # --- This is the core logic (Quantization) ---
            Q = strength
            q_val_1 = (3/4) * Q
            q_val_0 = (1/4) * Q
            
            # Pick a mid-frequency coefficient to modify
            coeff_x, coeff_y = 4, 5 
            c = dct_block[coeff_x, coeff_y]
            
            # Quantize: Modify the coefficient
            remainder = c % Q
            if bit == 1:
                new_c = c - remainder + q_val_1
            else: # bit == 0
                new_c = c - remainder + q_val_0
            
            dct_block[coeff_x, coeff_y] = new_c
            # --- End of core logic ---
            
            # Apply Inverse 2D DCT
            idct_block = idct(idct(dct_block.T, norm='ortho').T, norm='ortho')
            
            # Place modified block back
            y_channel[i:i+8, j:j+8] = idct_block
            bit_index += 1
            
        if bit_index >= watermark_len:
            break

    # 4. Reconstruct and Save Image
    image_ycrcb[:, :, 0] = y_channel.astype(np.uint8)
    watermarked_image = cv2.cvtColor(image_ycrcb, cv2.COLOR_YCrCb2BGR)
    cv2.imwrite(output_path, watermarked_image)
    print(f"Watermark embedded. Saved to {output_path}")


# --- Helper function to convert binary to text ---
def binary_to_text(binary_string):
    byte_strings = [binary_string[i:i+8] for i in range(0, len(binary_string), 8)]
    text = ""
    for byte in byte_strings:
        if len(byte) == 8:
            text += chr(int(byte, 2))
    return text

def extract_watermark(image_path, strength=20):
    # 1. Load Image and Convert to YCrCb
    image = cv2.imread(image_path)
    image_ycrcb = cv2.cvtColor(image, cv2.COLOR_BGR2YCrCb)
    y_channel = image_ycrcb[:, :, 0].astype(np.float32)
    
    extracted_bits = ""
    delimiter = "1111111100000000"
    
    # 2. Process image in 8x8 blocks (in the exact same order)
    for i in range(0, y_channel.shape[0] - 8, 8):
        for j in range(0, y_channel.shape[1] - 8, 8):
            
            # Get current 8x8 block and apply DCT
            block = y_channel[i:i+8, j:j+8]
            dct_block = dct(dct(block.T, norm='ortho').T, norm='ortho')
            
            # --- This is the core logic (Extraction) ---
            Q = strength
            q_val_1 = (3/4) * Q
            q_val_0 = (1/4) * Q
            
            # Read the same mid-frequency coefficient
            coeff_x, coeff_y = 4, 5
            c = dct_block[coeff_x, coeff_y]
            
            # Check which value it's closer to
            remainder = c % Q
            if abs(remainder - q_val_1) < abs(remainder - q_val_0):
                extracted_bits += "1"
            else:
                extracted_bits += "0"
            # --- End of core logic ---
            
            # 3. Check for delimiter
            if extracted_bits.endswith(delimiter):
                # We found the end of the message
                message = binary_to_text(extracted_bits[:-len(delimiter)])
                return message
                
    return "Could not find watermark."

# --- Add this to the bottom to test it ---
if __name__ == "__main__":
    # 1. Embed
    print("Embedding...")
    embed_watermark(
        image_path="host_image.png", # Get a test image
        watermark_text="This is Rakshit's work",
        output_path="watermarked_image.png",
        strength=20
    )
    
    # 2. Extract
    print("\nExtracting...")
    message = extract_watermark(
        image_path="watermarked_image.png",
        strength=20
    )
    print(f"Extracted message: {message}")