from PIL import Image, ImageEnhance
import os

def darken_image(path, factor=0.5):
    try:
        if not os.path.exists(path):
            print(f"File not found: {path}")
            return
            
        img = Image.open(path)
        
        # Check if it has an alpha channel (transparency)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
            
        # Enhance (Darken)
        enhancer = ImageEnhance.Brightness(img)
        darker_img = enhancer.enhance(factor)
        
        # Save back
        darker_img.save(path, "PNG")
        print(f"Successfully darkened {path} by factor {factor}")
        
    except Exception as e:
        print(f"Error processing image: {e}")

if __name__ == "__main__":
    icon_path = os.path.join("frontend", "src", "app", "icon.png")
    # Also process the original in public just in case
    public_path = os.path.join("frontend", "public", "anubislogo.png")
    
    darken_image(icon_path, 0.6) # Reduce brightness to 60%
    # darken_image(public_path, 0.6) # Optional: keep source original? User didn't specify, but safer to just update the active icon.
