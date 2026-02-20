#!/usr/bin/env python3
"""
Diagnostic script to check if Tesseract OCR is properly installed and working.
Run this to verify your OCR setup before uploading images.
"""

import sys
import subprocess
from pathlib import Path

print("=" * 60)
print("TESSERACT OCR DIAGNOSTIC CHECK")
print("=" * 60)

# Check 1: Try importing pytesseract
print("\n1. Checking pytesseract Python package...")
try:
    import pytesseract
    print("   ✓ pytesseract is installed")
except ImportError:
    print("   ✗ pytesseract is NOT installed")
    print("   Run: pip install pytesseract")
    sys.exit(1)

# Check 2: Check if tesseract binary is available
print("\n2. Checking Tesseract binary installation...")
try:
    result = subprocess.run(
        ["tesseract", "--version"],
        capture_output=True,
        text=True,
        timeout=5
    )
    if result.returncode == 0:
        print("   ✓ Tesseract binary is installed")
        print(f"   Version info:\n{result.stdout.split(chr(10))[0]}")
    else:
        print("   ✗ Tesseract binary not found in PATH")
        raise FileNotFoundError()
except FileNotFoundError:
    print("   ✗ Tesseract is NOT installed on this system")
    print("\n   INSTALLATION INSTRUCTIONS:")
    print("   For Windows:")
    print("   1. Download installer from: https://github.com/UB-Mannheim/tesseract/wiki")
    print("   2. Run: tesseract-ocr-w64-setup-v5.x.exe")
    print("   3. Install to default location (usually C:\\Program Files\\Tesseract-OCR)")
    print("   4. Restart your terminal/IDE")
    sys.exit(1)
except Exception as e:
    print(f"   ✗ Error checking Tesseract: {e}")
    sys.exit(1)

# Check 3: Test OCR with a simple image
print("\n3. Testing OCR with PIL and pytesseract...")
try:
    from PIL import Image
    import io
    
    # Create a simple test image with text
    test_image = Image.new('RGB', (200, 100), color='white')
    from PIL import ImageDraw, ImageFont
    
    draw = ImageDraw.Draw(test_image)
    # Try to use a default font
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    draw.text((10, 40), "TEST", fill='black', font=font)
    
    # Convert to bytes
    img_bytes = io.BytesIO()
    test_image.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    # Test OCR
    test_image = Image.open(img_bytes)
    text = pytesseract.image_to_string(test_image)
    
    if text.strip():
        print(f"   ✓ OCR is working! Extracted: '{text.strip()}'")
    else:
        print("   ⚠ OCR ran but extracted no text (may need image quality improvements)")
        
except Exception as e:
    print(f"   ✗ OCR test failed: {e}")
    sys.exit(1)

# Check 4: Verify language data
print("\n4. Checking OCR language support...")
try:
    result = subprocess.run(
        ["tesseract", "--list-langs"],
        capture_output=True,
        text=True,
        timeout=5
    )
    langs = result.stdout.strip().split('\n')
    
    has_eng = 'eng' in langs
    has_hin = 'hin' in langs
    
    print(f"   {'✓' if has_eng else '✗'} English (eng) support: {has_eng}")
    print(f"   {'✓' if has_hin else '✗'} Hindi (hin) support: {has_hin}")
    
    if not has_eng:
        print("   ⚠ English language data missing! Download from:")
        print("     https://github.com/UB-Mannheim/tesseract/wiki/Downloads")
        
except Exception as e:
    print(f"   ⚠ Could not verify language data: {e}")

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
print("\nIf all checks pass, your OCR setup is working correctly.")
print("If there are failures, follow the instructions above to fix them.")
