# App Icon Export Guide

## From AI Generation to Complete Assets

### Step 1: AI Generate 1024x1024 Original Image

Use the following prompt to generate the base image:

```
Professional mobile app icon for medical healthcare application,
featuring a minimalist heart with pulse line inside a shield shape,
modern flat design style,
primary color: #2196F3 (blue),
secondary color: #FFFFFF (white),
clean and trustworthy appearance,
no text, no letters, no words,
centered composition,
1024x1024 resolution,
suitable for both iOS and Android app stores
```

**Prompt Adjustment Tips:**
- Replace `heart with pulse line` with your main element
- Replace color codes with your brand colors
- Keep "no text" and "1024x1024" unchanged

### Step 2: Post-Processing

**Recommended Software:**
- Figma (free)
- Photoshop
- Affinity Designer

**Processing Tasks:**
1. Confirm size is 1024x1024 px
2. Confirm RGB color mode
3. iOS: Remove transparent background (App Store doesn't accept)
4. Android: Can keep transparent background

### Step 3: Export All Sizes

---

## Python Export Script

### Complete Script

```python
#!/usr/bin/env python3
"""
App Icon Export Script
Generates all Android and iOS sizes from 1024x1024 source
"""

from PIL import Image
import os
import json

# Android size configuration
ANDROID_SIZES = {
    'mipmap-mdpi': 48,
    'mipmap-hdpi': 72,
    'mipmap-xhdpi': 96,
    'mipmap-xxhdpi': 144,
    'mipmap-xxxhdpi': 192,
}

# Android Adaptive Icon sizes
ANDROID_ADAPTIVE_SIZES = {
    'mipmap-mdpi': 108,
    'mipmap-hdpi': 162,
    'mipmap-xhdpi': 216,
    'mipmap-xxhdpi': 324,
    'mipmap-xxxhdpi': 432,
}

# iOS size configuration
IOS_SIZES = {
    'Icon-20@2x': 40,
    'Icon-20@3x': 60,
    'Icon-29@2x': 58,
    'Icon-29@3x': 87,
    'Icon-40@2x': 80,
    'Icon-40@3x': 120,
    'Icon-60@2x': 120,
    'Icon-60@3x': 180,
    'Icon-76': 76,
    'Icon-76@2x': 152,
    'Icon-83.5@2x': 167,
    'Icon-1024': 1024,
}

def resize_image(img, size):
    """Resize image using high-quality scaling"""
    return img.resize((size, size), Image.LANCZOS)

def export_android(source_img, output_dir):
    """Export Android resources"""
    android_dir = os.path.join(output_dir, 'android')

    for folder, size in ANDROID_SIZES.items():
        folder_path = os.path.join(android_dir, folder)
        os.makedirs(folder_path, exist_ok=True)

        resized = resize_image(source_img, size)
        resized.save(
            os.path.join(folder_path, 'ic_launcher.png'),
            'PNG',
            optimize=True
        )
        print(f"  ✓ {folder}/ic_launcher.png ({size}x{size})")

    # Play Store icon
    playstore_dir = os.path.join(android_dir, 'playstore')
    os.makedirs(playstore_dir, exist_ok=True)
    resized = resize_image(source_img, 512)
    resized.save(
        os.path.join(playstore_dir, 'ic_launcher-512.png'),
        'PNG',
        optimize=True
    )
    print(f"  ✓ playstore/ic_launcher-512.png (512x512)")

def export_android_adaptive(foreground_img, background_color, output_dir):
    """Export Android Adaptive Icon resources"""
    android_dir = os.path.join(output_dir, 'android')

    for folder, size in ANDROID_ADAPTIVE_SIZES.items():
        folder_path = os.path.join(android_dir, folder)
        os.makedirs(folder_path, exist_ok=True)

        # Foreground
        resized = resize_image(foreground_img, size)
        resized.save(
            os.path.join(folder_path, 'ic_launcher_foreground.png'),
            'PNG',
            optimize=True
        )

        # Background (solid color)
        bg = Image.new('RGB', (size, size), background_color)
        bg.save(
            os.path.join(folder_path, 'ic_launcher_background.png'),
            'PNG',
            optimize=True
        )

        print(f"  ✓ {folder}/ic_launcher_foreground.png ({size}x{size})")

def export_ios(source_img, output_dir):
    """Export iOS resources"""
    ios_dir = os.path.join(output_dir, 'ios', 'AppIcon.appiconset')
    os.makedirs(ios_dir, exist_ok=True)

    # Remove transparent background (iOS requirement)
    if source_img.mode == 'RGBA':
        background = Image.new('RGB', source_img.size, (255, 255, 255))
        background.paste(source_img, mask=source_img.split()[3])
        source_img = background

    images_info = []

    for name, size in IOS_SIZES.items():
        resized = resize_image(source_img, size)
        filename = f"{name}.png"
        resized.save(
            os.path.join(ios_dir, filename),
            'PNG',
            optimize=True
        )
        print(f"  ✓ {filename} ({size}x{size})")

        # Prepare Contents.json info
        if '@' in name:
            base_name = name.split('@')[0].replace('Icon-', '')
            scale = name.split('@')[1]
        else:
            base_name = name.replace('Icon-', '')
            scale = '1x'

        images_info.append({
            "size": f"{base_name}x{base_name}" if base_name != '1024' else "1024x1024",
            "idiom": "iphone" if float(base_name.replace('.', '')) <= 83.5 else "ios-marketing",
            "filename": filename,
            "scale": scale
        })

    # Generate Contents.json
    contents = {
        "images": [
            {"size": "20x20", "idiom": "iphone", "scale": "2x", "filename": "Icon-20@2x.png"},
            {"size": "20x20", "idiom": "iphone", "scale": "3x", "filename": "Icon-20@3x.png"},
            {"size": "29x29", "idiom": "iphone", "scale": "2x", "filename": "Icon-29@2x.png"},
            {"size": "29x29", "idiom": "iphone", "scale": "3x", "filename": "Icon-29@3x.png"},
            {"size": "40x40", "idiom": "iphone", "scale": "2x", "filename": "Icon-40@2x.png"},
            {"size": "40x40", "idiom": "iphone", "scale": "3x", "filename": "Icon-40@3x.png"},
            {"size": "60x60", "idiom": "iphone", "scale": "2x", "filename": "Icon-60@2x.png"},
            {"size": "60x60", "idiom": "iphone", "scale": "3x", "filename": "Icon-60@3x.png"},
            {"size": "76x76", "idiom": "ipad", "scale": "1x", "filename": "Icon-76.png"},
            {"size": "76x76", "idiom": "ipad", "scale": "2x", "filename": "Icon-76@2x.png"},
            {"size": "83.5x83.5", "idiom": "ipad", "scale": "2x", "filename": "Icon-83.5@2x.png"},
            {"size": "1024x1024", "idiom": "ios-marketing", "scale": "1x", "filename": "Icon-1024.png"}
        ],
        "info": {"version": 1, "author": "app-icon-generator"}
    }

    with open(os.path.join(ios_dir, 'Contents.json'), 'w') as f:
        json.dump(contents, f, indent=2)
    print(f"  ✓ Contents.json")

def main(source_path, output_dir):
    """Main function"""
    print(f"\n📱 App Icon Export Tool")
    print(f"Source: {source_path}")
    print(f"Output: {output_dir}\n")

    # Read source image
    img = Image.open(source_path)
    if img.size != (1024, 1024):
        print(f"⚠️  Source image size is {img.size}, resizing to 1024x1024")
        img = resize_image(img, 1024)

    # Export Android
    print("🤖 Android:")
    export_android(img, output_dir)

    # Export iOS
    print("\n🍎 iOS:")
    export_ios(img, output_dir)

    print(f"\n✅ Complete! Assets exported to: {output_dir}")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("Usage: python app_icon_export.py <source_image> [output_dir]")
        print("Example: python app_icon_export.py app-icon-1024.png ./app-icons")
        sys.exit(1)

    source = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else './app-icons'
    main(source, output)
```

### Usage

```bash
# Install dependencies
pip install Pillow

# Run export
python app_icon_export.py app-icon-1024.png ./03-assets/app-icons
```

---

## Online Tool Alternatives

If you don't want to use scripts, use these online tools:

| Tool | URL | Features |
|------|-----|----------|
| App Icon Generator | appicon.co | Free, simple |
| MakeAppIcon | makeappicon.com | Professional, multi-format |
| Icon Kitchen | icon.kitchen | Google official |
| Figma Plugin | Search in Figma | Direct in design software |

---

## Checklist

### Pre-Generation Check

- [ ] Source image is 1024x1024 px
- [ ] RGB color mode
- [ ] Main elements centered
- [ ] No text or letters
- [ ] Icon recognizable at small sizes

### Post-Export Check

**Android:**
- [ ] mipmap-mdpi (48x48) generated
- [ ] mipmap-hdpi (72x72) generated
- [ ] mipmap-xhdpi (96x96) generated
- [ ] mipmap-xxhdpi (144x144) generated
- [ ] mipmap-xxxhdpi (192x192) generated
- [ ] Play Store 512x512 generated

**iOS:**
- [ ] All @2x, @3x generated
- [ ] Icon-1024.png generated (no transparency)
- [ ] Contents.json created

### Device Testing

- [ ] Android emulator displays correctly
- [ ] iOS simulator displays correctly
- [ ] Visible in dark mode
- [ ] Visible in light mode
