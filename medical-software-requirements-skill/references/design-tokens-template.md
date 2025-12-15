# Design Tokens template

Design Tokens IsDesignSystem'sfoundationchangecount，CanExportsupplydevelopUse。

## Complete Design Tokens structure

```json
{
  "color": { ... },
  "typography": { ... },
  "spacing": { ... },
  "borderRadius": { ... },
  "shadow": { ... },
  "opacity": { ... }
}
```

---

## 色彩 (Colors)

### colors.json

```json
{
  "color": {
    "primary": {
      "50": { "value": "#E3F2FD", "type": "color" },
      "100": { "value": "#BBDEFB", "type": "color" },
      "200": { "value": "#90CAF9", "type": "color" },
      "300": { "value": "#64B5F6", "type": "color" },
      "400": { "value": "#42A5F5", "type": "color" },
      "500": { "value": "#2196F3", "type": "color", "description": "Primary brand color" },
      "600": { "value": "#1E88E5", "type": "color" },
      "700": { "value": "#1976D2", "type": "color" },
      "800": { "value": "#1565C0", "type": "color" },
      "900": { "value": "#0D47A1", "type": "color" }
    },
    "secondary": {
      "50": { "value": "#E0F2F1", "type": "color" },
      "100": { "value": "#B2DFDB", "type": "color" },
      "200": { "value": "#80CBC4", "type": "color" },
      "300": { "value": "#4DB6AC", "type": "color" },
      "400": { "value": "#26A69A", "type": "color" },
      "500": { "value": "#009688", "type": "color", "description": "Secondary brand color" },
      "600": { "value": "#00897B", "type": "color" },
      "700": { "value": "#00796B", "type": "color" },
      "800": { "value": "#00695C", "type": "color" },
      "900": { "value": "#004D40", "type": "color" }
    },
    "neutral": {
      "0": { "value": "#FFFFFF", "type": "color" },
      "50": { "value": "#FAFAFA", "type": "color" },
      "100": { "value": "#F5F5F5", "type": "color" },
      "200": { "value": "#EEEEEE", "type": "color" },
      "300": { "value": "#E0E0E0", "type": "color" },
      "400": { "value": "#BDBDBD", "type": "color" },
      "500": { "value": "#9E9E9E", "type": "color" },
      "600": { "value": "#757575", "type": "color" },
      "700": { "value": "#616161", "type": "color" },
      "800": { "value": "#424242", "type": "color" },
      "900": { "value": "#212121", "type": "color" },
      "1000": { "value": "#000000", "type": "color" }
    },
    "semantic": {
      "success": { "value": "#4CAF50", "type": "color" },
      "successLight": { "value": "#E8F5E9", "type": "color" },
      "warning": { "value": "#FF9800", "type": "color" },
      "warningLight": { "value": "#FFF3E0", "type": "color" },
      "error": { "value": "#F44336", "type": "color" },
      "errorLight": { "value": "#FFEBEE", "type": "color" },
      "info": { "value": "#2196F3", "type": "color" },
      "infoLight": { "value": "#E3F2FD", "type": "color" }
    },
    "clinical": {
      "critical": { "value": "#D32F2F", "type": "color", "description": "Critical/Emergency" },
      "abnormal": { "value": "#FF5722", "type": "color", "description": "Abnormal values" },
      "normal": { "value": "#4CAF50", "type": "color", "description": "Normal values" },
      "pending": { "value": "#9E9E9E", "type": "color", "description": "Pending/Unknown" }
    },
    "background": {
      "primary": { "value": "#FFFFFF", "type": "color" },
      "secondary": { "value": "#F5F5F5", "type": "color" },
      "tertiary": { "value": "#EEEEEE", "type": "color" }
    },
    "text": {
      "primary": { "value": "#212121", "type": "color" },
      "secondary": { "value": "#757575", "type": "color" },
      "disabled": { "value": "#BDBDBD", "type": "color" },
      "inverse": { "value": "#FFFFFF", "type": "color" }
    }
  }
}
```

---

## Font (Typography)

### typography.json

```json
{
  "typography": {
    "fontFamily": {
      "primary": { "value": "SF Pro Text, Roboto, sans-serif", "type": "fontFamily" },
      "secondary": { "value": "SF Pro Display, Roboto, sans-serif", "type": "fontFamily" },
      "monospace": { "value": "SF Mono, Roboto Mono, monospace", "type": "fontFamily" }
    },
    "fontSize": {
      "displayLarge": { "value": "57px", "type": "dimension" },
      "displayMedium": { "value": "45px", "type": "dimension" },
      "displaySmall": { "value": "36px", "type": "dimension" },
      "headlineLarge": { "value": "32px", "type": "dimension" },
      "headlineMedium": { "value": "28px", "type": "dimension" },
      "headlineSmall": { "value": "24px", "type": "dimension" },
      "titleLarge": { "value": "22px", "type": "dimension" },
      "titleMedium": { "value": "16px", "type": "dimension" },
      "titleSmall": { "value": "14px", "type": "dimension" },
      "bodyLarge": { "value": "16px", "type": "dimension" },
      "bodyMedium": { "value": "14px", "type": "dimension" },
      "bodySmall": { "value": "12px", "type": "dimension" },
      "labelLarge": { "value": "14px", "type": "dimension" },
      "labelMedium": { "value": "12px", "type": "dimension" },
      "labelSmall": { "value": "11px", "type": "dimension" }
    },
    "fontWeight": {
      "regular": { "value": "400", "type": "fontWeight" },
      "medium": { "value": "500", "type": "fontWeight" },
      "semibold": { "value": "600", "type": "fontWeight" },
      "bold": { "value": "700", "type": "fontWeight" }
    },
    "lineHeight": {
      "tight": { "value": "1.2", "type": "number" },
      "normal": { "value": "1.5", "type": "number" },
      "relaxed": { "value": "1.75", "type": "number" }
    },
    "letterSpacing": {
      "tight": { "value": "-0.5px", "type": "dimension" },
      "normal": { "value": "0px", "type": "dimension" },
      "wide": { "value": "0.5px", "type": "dimension" }
    }
  }
}
```

---

## Spacing (Spacing)

### spacing.json

```json
{
  "spacing": {
    "0": { "value": "0px", "type": "dimension" },
    "1": { "value": "4px", "type": "dimension" },
    "2": { "value": "8px", "type": "dimension" },
    "3": { "value": "12px", "type": "dimension" },
    "4": { "value": "16px", "type": "dimension" },
    "5": { "value": "20px", "type": "dimension" },
    "6": { "value": "24px", "type": "dimension" },
    "8": { "value": "32px", "type": "dimension" },
    "10": { "value": "40px", "type": "dimension" },
    "12": { "value": "48px", "type": "dimension" },
    "16": { "value": "64px", "type": "dimension" },
    "20": { "value": "80px", "type": "dimension" },
    "24": { "value": "96px", "type": "dimension" }
  },
  "padding": {
    "button": {
      "horizontal": { "value": "{spacing.4}", "type": "dimension" },
      "vertical": { "value": "{spacing.3}", "type": "dimension" }
    },
    "card": {
      "default": { "value": "{spacing.4}", "type": "dimension" },
      "compact": { "value": "{spacing.3}", "type": "dimension" }
    },
    "input": {
      "horizontal": { "value": "{spacing.4}", "type": "dimension" },
      "vertical": { "value": "{spacing.3}", "type": "dimension" }
    },
    "screen": {
      "horizontal": { "value": "{spacing.4}", "type": "dimension" },
      "top": { "value": "{spacing.6}", "type": "dimension" },
      "bottom": { "value": "{spacing.8}", "type": "dimension" }
    }
  }
}
```

---

## roundcorner (Border Radius)

### borderRadius.json

```json
{
  "borderRadius": {
    "none": { "value": "0px", "type": "dimension" },
    "sm": { "value": "4px", "type": "dimension" },
    "md": { "value": "8px", "type": "dimension" },
    "lg": { "value": "12px", "type": "dimension" },
    "xl": { "value": "16px", "type": "dimension" },
    "2xl": { "value": "24px", "type": "dimension" },
    "full": { "value": "9999px", "type": "dimension" }
  },
  "component": {
    "button": { "value": "{borderRadius.md}", "type": "dimension" },
    "card": { "value": "{borderRadius.lg}", "type": "dimension" },
    "input": { "value": "{borderRadius.sm}", "type": "dimension" },
    "chip": { "value": "{borderRadius.full}", "type": "dimension" },
    "avatar": { "value": "{borderRadius.full}", "type": "dimension" },
    "modal": { "value": "{borderRadius.xl}", "type": "dimension" }
  }
}
```

---

## 陰影 (Shadow)

### shadow.json

```json
{
  "shadow": {
    "none": { "value": "none", "type": "shadow" },
    "sm": {
      "value": {
        "x": "0px",
        "y": "1px",
        "blur": "2px",
        "spread": "0px",
        "color": "rgba(0, 0, 0, 0.05)"
      },
      "type": "shadow"
    },
    "md": {
      "value": {
        "x": "0px",
        "y": "2px",
        "blur": "4px",
        "spread": "0px",
        "color": "rgba(0, 0, 0, 0.1)"
      },
      "type": "shadow"
    },
    "lg": {
      "value": {
        "x": "0px",
        "y": "4px",
        "blur": "8px",
        "spread": "0px",
        "color": "rgba(0, 0, 0, 0.12)"
      },
      "type": "shadow"
    },
    "xl": {
      "value": {
        "x": "0px",
        "y": "8px",
        "blur": "16px",
        "spread": "0px",
        "color": "rgba(0, 0, 0, 0.15)"
      },
      "type": "shadow"
    }
  },
  "elevation": {
    "card": { "value": "{shadow.md}", "type": "shadow" },
    "modal": { "value": "{shadow.xl}", "type": "shadow" },
    "dropdown": { "value": "{shadow.lg}", "type": "shadow" },
    "button": { "value": "{shadow.sm}", "type": "shadow" }
  }
}
```

---

## PlatformConvert

### Android (XML)

```xml
<!-- colors.xml -->
<resources>
    <color name="primary_500">#2196F3</color>
    <color name="primary_700">#1976D2</color>
    <color name="semantic_success">#4CAF50</color>
    <color name="semantic_error">#F44336</color>
</resources>

<!-- dimens.xml -->
<resources>
    <dimen name="spacing_4">16dp</dimen>
    <dimen name="spacing_6">24dp</dimen>
    <dimen name="border_radius_md">8dp</dimen>
</resources>
```

### iOS (Swift)

```swift
// Colors.swift
extension UIColor {
    static let primary500 = UIColor(hex: "#2196F3")
    static let primary700 = UIColor(hex: "#1976D2")
    static let semanticSuccess = UIColor(hex: "#4CAF50")
    static let semanticError = UIColor(hex: "#F44336")
}

// Spacing.swift
enum Spacing {
    static let s4: CGFloat = 16
    static let s6: CGFloat = 24
}

// BorderRadius.swift
enum BorderRadius {
    static let md: CGFloat = 8
    static let lg: CGFloat = 12
}
```

### CSS Variables

```css
:root {
  /* Colors */
  --color-primary-500: #2196F3;
  --color-primary-700: #1976D2;
  --color-semantic-success: #4CAF50;
  --color-semantic-error: #F44336;

  /* Spacing */
  --spacing-4: 16px;
  --spacing-6: 24px;

  /* Border Radius */
  --radius-md: 8px;
  --radius-lg: 12px;

  /* Shadow */
  --shadow-md: 0px 2px 4px rgba(0, 0, 0, 0.1);
}
```

---

## Figma Token Studio Export

Use Figma Token Studio outsidehangCanstraightreceiveExportupper述Format：

1. exist Figma middle安裝 Token Studio
2. determine義placeHave Tokens
3. ExportIs JSON
4. Use Style Dictionary ConvertIseachPlatformFormat

### Style Dictionary Configuration

```json
{
  "source": ["tokens/**/*.json"],
  "platforms": {
    "android": {
      "transformGroup": "android",
      "buildPath": "build/android/",
      "files": [{
        "destination": "colors.xml",
        "format": "android/colors"
      }]
    },
    "ios-swift": {
      "transformGroup": "ios-swift",
      "buildPath": "build/ios/",
      "files": [{
        "destination": "Colors.swift",
        "format": "ios-swift/class.swift"
      }]
    },
    "css": {
      "transformGroup": "css",
      "buildPath": "build/css/",
      "files": [{
        "destination": "variables.css",
        "format": "css/variables"
      }]
    }
  }
}
```
