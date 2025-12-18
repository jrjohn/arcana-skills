# App Icon 匯出指南

## 從 AI 產生到完整資產

### 步驟 1：AI 產生 1024x1024 原圖

使用以下 Prompt 產生基礎圖：

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

**Prompt 調整建議：**
- 更換 `heart with pulse line` 為您的主要元素
- 更換顏色代碼為品牌色
- 保持 "no text" 和 "1024x1024" 不變

### 步驟 2：後製處理

**建議軟體：**
- Figma (免費)
- Photoshop
- Affinity Designer

**處理項目：**
1. 確認尺寸為 1024x1024 px
2. 確認 RGB 色彩模式
3. iOS: 移除透明背景 (App Store 不接受)
4. Android: 可保留透明背景

### 步驟 3：匯出各尺寸

---

## Python 匯出腳本

### 完整腳本

```python
#!/usr/bin/env python3
"""
App Icon 匯出腳本
從 1024x1024 原圖產生 Android 和 iOS 所有尺寸
"""

from PIL import Image
import os
import json

# Android 尺寸配置
ANDROID_SIZES = {
    'mipmap-mdpi': 48,
    'mipmap-hdpi': 72,
    'mipmap-xhdpi': 96,
    'mipmap-xxhdpi': 144,
    'mipmap-xxxhdpi': 192,
}

# Android Adaptive Icon 尺寸
ANDROID_ADAPTIVE_SIZES = {
    'mipmap-mdpi': 108,
    'mipmap-hdpi': 162,
    'mipmap-xhdpi': 216,
    'mipmap-xxhdpi': 324,
    'mipmap-xxxhdpi': 432,
}

# iOS 尺寸配置
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
    """調整圖片尺寸，使用高品質縮放"""
    return img.resize((size, size), Image.LANCZOS)

def export_android(source_img, output_dir):
    """匯出 Android 資源"""
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

    # Play Store 圖標
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
    """匯出 Android Adaptive Icon 資源"""
    android_dir = os.path.join(output_dir, 'android')

    for folder, size in ANDROID_ADAPTIVE_SIZES.items():
        folder_path = os.path.join(android_dir, folder)
        os.makedirs(folder_path, exist_ok=True)

        # 前景
        resized = resize_image(foreground_img, size)
        resized.save(
            os.path.join(folder_path, 'ic_launcher_foreground.png'),
            'PNG',
            optimize=True
        )

        # 背景 (純色)
        bg = Image.new('RGB', (size, size), background_color)
        bg.save(
            os.path.join(folder_path, 'ic_launcher_background.png'),
            'PNG',
            optimize=True
        )

        print(f"  ✓ {folder}/ic_launcher_foreground.png ({size}x{size})")

def export_ios(source_img, output_dir):
    """匯出 iOS 資源"""
    ios_dir = os.path.join(output_dir, 'ios', 'AppIcon.appiconset')
    os.makedirs(ios_dir, exist_ok=True)

    # 移除透明背景 (iOS 要求)
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

        # 準備 Contents.json 資訊
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

    # 產生 Contents.json
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
    """主程式"""
    print(f"\n📱 App Icon 匯出工具")
    print(f"來源: {source_path}")
    print(f"輸出: {output_dir}\n")

    # 讀取原圖
    img = Image.open(source_path)
    if img.size != (1024, 1024):
        print(f"⚠️  來源圖片尺寸為 {img.size}，將調整為 1024x1024")
        img = resize_image(img, 1024)

    # 匯出 Android
    print("🤖 Android:")
    export_android(img, output_dir)

    # 匯出 iOS
    print("\n🍎 iOS:")
    export_ios(img, output_dir)

    print(f"\n✅ 完成！資源已匯出到: {output_dir}")

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print("用法: python app_icon_export.py <source_image> [output_dir]")
        print("範例: python app_icon_export.py app-icon-1024.png ./app-icons")
        sys.exit(1)

    source = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else './app-icons'
    main(source, output)
```

### 使用方式

```bash
# 安裝依賴
pip install Pillow

# 執行匯出
python app_icon_export.py app-icon-1024.png ./03-assets/app-icons
```

---

## 線上工具替代方案

如果不想使用腳本，可使用以下線上工具：

| 工具 | 網址 | 特點 |
|------|------|------|
| App Icon Generator | appicon.co | 免費、簡單 |
| MakeAppIcon | makeappicon.com | 專業、多格式 |
| Icon Kitchen | icon.kitchen | Google 官方 |
| Figma Plugin | Figma 內搜尋 | 直接在設計軟體內 |

---

## 檢核清單

### 產生前檢查

- [ ] 原圖為 1024x1024 px
- [ ] RGB 色彩模式
- [ ] 主要元素置中
- [ ] 無文字或字母
- [ ] 圖示在小尺寸仍可辨識

### 匯出後檢查

**Android:**
- [ ] mipmap-mdpi (48x48) 已產生
- [ ] mipmap-hdpi (72x72) 已產生
- [ ] mipmap-xhdpi (96x96) 已產生
- [ ] mipmap-xxhdpi (144x144) 已產生
- [ ] mipmap-xxxhdpi (192x192) 已產生
- [ ] Play Store 512x512 已產生

**iOS:**
- [ ] 所有 @2x, @3x 已產生
- [ ] Icon-1024.png 已產生 (無透明)
- [ ] Contents.json 已建立

### 實機測試

- [ ] Android 模擬器顯示正常
- [ ] iOS 模擬器顯示正常
- [ ] 深色模式下可見
- [ ] 淺色模式下可見
