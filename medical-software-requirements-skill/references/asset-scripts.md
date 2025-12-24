# 資產處理腳本

本文件包含用於處理設計資產的 Python 腳本。

## 環境準備

```bash
# 安裝依賴
pip install Pillow cairosvg

# 或使用 requirements.txt
pip install -r requirements.txt
```

### requirements.txt

```
Pillow>=10.0.0
cairosvg>=2.7.0
```

---

## App Icon 匯出腳本

### app_icon_export.py

```python
#!/usr/bin/env python3
"""
App Icon 多尺寸匯出腳本
用法: python app_icon_export.py <source_1024.png> <output_dir>
"""

from PIL import Image
import os
import json
import sys

# 尺寸配置
ANDROID_SIZES = {
    'mipmap-mdpi': 48,
    'mipmap-hdpi': 72,
    'mipmap-xhdpi': 96,
    'mipmap-xxhdpi': 144,
    'mipmap-xxxhdpi': 192,
}

IOS_SIZES = [
    ('Icon-20@2x.png', 40),
    ('Icon-20@3x.png', 60),
    ('Icon-29@2x.png', 58),
    ('Icon-29@3x.png', 87),
    ('Icon-40@2x.png', 80),
    ('Icon-40@3x.png', 120),
    ('Icon-60@2x.png', 120),
    ('Icon-60@3x.png', 180),
    ('Icon-76.png', 76),
    ('Icon-76@2x.png', 152),
    ('Icon-83.5@2x.png', 167),
    ('Icon-1024.png', 1024),
]

IOS_CONTENTS = {
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
    "info": {"version": 1, "author": "asset-generator"}
}


def resize_image(img, size):
    """高品質縮放圖片"""
    return img.resize((size, size), Image.LANCZOS)


def export_android(source_img, output_dir):
    """匯出 Android 資源"""
    print("\n🤖 Android:")
    android_dir = os.path.join(output_dir, 'android')

    for folder, size in ANDROID_SIZES.items():
        folder_path = os.path.join(android_dir, folder)
        os.makedirs(folder_path, exist_ok=True)

        resized = resize_image(source_img, size)
        output_path = os.path.join(folder_path, 'ic_launcher.png')
        resized.save(output_path, 'PNG', optimize=True)
        print(f"  ✓ {folder}/ic_launcher.png ({size}x{size})")

    # Play Store
    playstore_dir = os.path.join(android_dir, 'playstore')
    os.makedirs(playstore_dir, exist_ok=True)
    resized = resize_image(source_img, 512)
    resized.save(os.path.join(playstore_dir, 'ic_launcher-512.png'), 'PNG', optimize=True)
    print(f"  ✓ playstore/ic_launcher-512.png (512x512)")


def export_ios(source_img, output_dir):
    """匯出 iOS 資源"""
    print("\n🍎 iOS:")
    ios_dir = os.path.join(output_dir, 'ios', 'AppIcon.appiconset')
    os.makedirs(ios_dir, exist_ok=True)

    # iOS 不支援透明背景
    if source_img.mode == 'RGBA':
        bg = Image.new('RGB', source_img.size, (255, 255, 255))
        bg.paste(source_img, mask=source_img.split()[3])
        source_img = bg

    for filename, size in IOS_SIZES:
        resized = resize_image(source_img, size)
        resized.save(os.path.join(ios_dir, filename), 'PNG', optimize=True)
        print(f"  ✓ {filename} ({size}x{size})")

    # Contents.json
    with open(os.path.join(ios_dir, 'Contents.json'), 'w') as f:
        json.dump(IOS_CONTENTS, f, indent=2)
    print(f"  ✓ Contents.json")


def main():
    if len(sys.argv) < 2:
        print("用法: python app_icon_export.py <source_image> [output_dir]")
        sys.exit(1)

    source_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else './app-icons'

    print(f"\n📱 App Icon 匯出工具")
    print(f"來源: {source_path}")
    print(f"輸出: {output_dir}")

    img = Image.open(source_path)
    if img.size != (1024, 1024):
        print(f"\n⚠️  調整來源圖片從 {img.size} 到 1024x1024")
        img = resize_image(img, 1024)

    export_android(img, output_dir)
    export_ios(img, output_dir)

    print(f"\n✅ 完成！")


if __name__ == '__main__':
    main()
```

---

## 圖片多解析度匯出腳本

### image_export.py

```python
#!/usr/bin/env python3
"""
圖片多解析度匯出腳本
用法: python image_export.py <source_image> <output_dir> [base_size]
"""

from PIL import Image
import os
import sys

# Android 密度配置
ANDROID_DENSITIES = {
    'drawable-mdpi': 1.0,
    'drawable-hdpi': 1.5,
    'drawable-xhdpi': 2.0,
    'drawable-xxhdpi': 3.0,
    'drawable-xxxhdpi': 4.0,
}

# iOS scale 配置
IOS_SCALES = [1, 2, 3]


def export_android(source_img, output_dir, base_name, base_size):
    """匯出 Android 多密度圖片"""
    print("\n🤖 Android:")
    android_dir = os.path.join(output_dir, 'android')

    base_width, base_height = base_size

    for folder, scale in ANDROID_DENSITIES.items():
        folder_path = os.path.join(android_dir, folder)
        os.makedirs(folder_path, exist_ok=True)

        new_width = int(base_width * scale)
        new_height = int(base_height * scale)
        resized = source_img.resize((new_width, new_height), Image.LANCZOS)

        output_path = os.path.join(folder_path, f'{base_name}.png')
        resized.save(output_path, 'PNG', optimize=True)
        print(f"  ✓ {folder}/{base_name}.png ({new_width}x{new_height})")


def export_ios(source_img, output_dir, base_name, base_size):
    """匯出 iOS 多 scale 圖片"""
    print("\n🍎 iOS:")
    ios_dir = os.path.join(output_dir, 'ios', 'Images.xcassets', f'{base_name}.imageset')
    os.makedirs(ios_dir, exist_ok=True)

    base_width, base_height = base_size
    images = []

    for scale in IOS_SCALES:
        new_width = int(base_width * scale)
        new_height = int(base_height * scale)
        resized = source_img.resize((new_width, new_height), Image.LANCZOS)

        if scale == 1:
            filename = f'{base_name}.png'
        else:
            filename = f'{base_name}@{scale}x.png'

        output_path = os.path.join(ios_dir, filename)
        resized.save(output_path, 'PNG', optimize=True)
        print(f"  ✓ {filename} ({new_width}x{new_height})")

        images.append({
            "idiom": "universal",
            "scale": f"{scale}x",
            "filename": filename
        })

    # Contents.json
    contents = {
        "images": images,
        "info": {"version": 1, "author": "asset-generator"}
    }
    with open(os.path.join(ios_dir, 'Contents.json'), 'w') as f:
        import json
        json.dump(contents, f, indent=2)
    print(f"  ✓ Contents.json")


def main():
    if len(sys.argv) < 2:
        print("用法: python image_export.py <source_image> [output_dir] [base_width] [base_height]")
        print("範例: python image_export.py bg_login.png ./images 360 640")
        sys.exit(1)

    source_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else './images'

    img = Image.open(source_path)
    base_name = os.path.splitext(os.path.basename(source_path))[0]

    # 使用提供的 base_size 或從圖片計算
    if len(sys.argv) >= 5:
        base_size = (int(sys.argv[3]), int(sys.argv[4]))
    else:
        # 假設來源是 3x 尺寸
        base_size = (img.width // 3, img.height // 3)

    print(f"\n🖼️  圖片匯出工具")
    print(f"來源: {source_path} ({img.width}x{img.height})")
    print(f"基準尺寸: {base_size[0]}x{base_size[1]}")
    print(f"輸出: {output_dir}")

    export_android(img, output_dir, base_name, base_size)
    export_ios(img, output_dir, base_name, base_size)

    print(f"\n✅ 完成！")


if __name__ == '__main__':
    main()
```

---

## SVG 轉 PNG 腳本

### svg_to_png.py

```python
#!/usr/bin/env python3
"""
SVG 轉 PNG 多尺寸腳本
用法: python svg_to_png.py <source.svg> <output_dir> [sizes]
"""

import cairosvg
import os
import sys


def svg_to_png(svg_path, output_dir, sizes):
    """將 SVG 轉換為多尺寸 PNG"""
    base_name = os.path.splitext(os.path.basename(svg_path))[0]
    os.makedirs(output_dir, exist_ok=True)

    for size in sizes:
        output_path = os.path.join(output_dir, f'{base_name}_{size}.png')
        cairosvg.svg2png(
            url=svg_path,
            write_to=output_path,
            output_width=size,
            output_height=size
        )
        print(f"  ✓ {base_name}_{size}.png ({size}x{size})")


def main():
    if len(sys.argv) < 2:
        print("用法: python svg_to_png.py <source.svg> [output_dir] [size1,size2,...]")
        print("範例: python svg_to_png.py ic_home.svg ./icons 24,48,72,96")
        sys.exit(1)

    svg_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else './icons'
    sizes = [int(s) for s in sys.argv[3].split(',')] if len(sys.argv) > 3 else [24, 48, 72, 96]

    print(f"\n🔄 SVG to PNG 轉換")
    print(f"來源: {svg_path}")
    print(f"尺寸: {sizes}")
    print(f"輸出: {output_dir}\n")

    svg_to_png(svg_path, output_dir, sizes)

    print(f"\n✅ 完成！")


if __name__ == '__main__':
    main()
```

---

## 批次處理腳本

### batch_export.py

```python
#!/usr/bin/env python3
"""
批次匯出資源腳本
用法: python batch_export.py <source_dir> <output_dir>
"""

import os
import sys
from PIL import Image
import json

# 從上面的腳本引入函數
# 這裡簡化為獨立實作


def process_app_icon(source_path, output_dir):
    """處理 App Icon"""
    # ... (使用 app_icon_export.py 的邏輯)
    pass


def process_image(source_path, output_dir):
    """處理一般圖片"""
    # ... (使用 image_export.py 的邏輯)
    pass


def main():
    if len(sys.argv) < 3:
        print("用法: python batch_export.py <source_dir> <output_dir>")
        sys.exit(1)

    source_dir = sys.argv[1]
    output_dir = sys.argv[2]

    print(f"\n📦 批次匯出工具")
    print(f"來源目錄: {source_dir}")
    print(f"輸出目錄: {output_dir}\n")

    # 處理所有圖片
    for filename in os.listdir(source_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            source_path = os.path.join(source_dir, filename)
            print(f"處理: {filename}")

            if 'app-icon' in filename.lower() or 'appicon' in filename.lower():
                process_app_icon(source_path, output_dir)
            else:
                process_image(source_path, output_dir)

    print(f"\n✅ 批次處理完成！")


if __name__ == '__main__':
    main()
```

---

## 使用範例

### 1. App Icon 匯出

```bash
# 從 1024x1024 原圖產生所有尺寸
python app_icon_export.py ./source/app-icon-1024.png ./03-assets/app-icons/
```

### 2. 圖片匯出

```bash
# 從 @3x 圖片產生所有解析度
python image_export.py ./source/bg_login@3x.png ./03-assets/images/ 360 640
```

### 3. SVG 轉 PNG

```bash
# 將 SVG 轉換為多尺寸 PNG
python svg_to_png.py ./source/ic_home.svg ./03-assets/icons/ 24,48,72,96
```

### 4. 批次處理

```bash
# 批次處理整個資料夾
python batch_export.py ./source/ ./03-assets/
```

---

## 整合到專案

### Makefile

```makefile
.PHONY: assets icons app-icon images

PYTHON = python3
SOURCE_DIR = ./source
OUTPUT_DIR = ./03-assets

assets: app-icon icons images

app-icon:
	$(PYTHON) scripts/app_icon_export.py $(SOURCE_DIR)/app-icon-1024.png $(OUTPUT_DIR)/app-icons

icons:
	for f in $(SOURCE_DIR)/icons/*.svg; do \
		$(PYTHON) scripts/svg_to_png.py $$f $(OUTPUT_DIR)/icons/png 24,48,72,96; \
	done

images:
	for f in $(SOURCE_DIR)/images/*@3x.png; do \
		$(PYTHON) scripts/image_export.py $$f $(OUTPUT_DIR)/images; \
	done
```

### npm scripts (package.json)

```json
{
  "scripts": {
    "assets:app-icon": "python3 scripts/app_icon_export.py ./source/app-icon-1024.png ./03-assets/app-icons",
    "assets:icons": "python3 scripts/batch_icons.py ./source/icons ./03-assets/icons",
    "assets:images": "python3 scripts/batch_images.py ./source/images ./03-assets/images",
    "assets": "npm run assets:app-icon && npm run assets:icons && npm run assets:images"
  }
}
```
