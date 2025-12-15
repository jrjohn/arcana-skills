# Design Psychology Principles

This document defines the design psychology principles that UI/UX design must follow to ensure good user experience.

## Core Principles

### 1. Cognitive Load Theory

**Definition:** Avoid presenting too much information at once, reduce user cognitive burden.

**Application Scenarios:**
- Dashboard Design
- Function layering
- Form Design

**Design Guidelines:**
| Principle | Description | Example |
|------|------|------|
| Chunking | Present information in small chunks | Forms divided into multiple steps |
| Progressive Loading | Show important information first, delay details | Dashboard shows summary first |
| Visual Hierarchy | Use size and color to distinguish importance | Primary buttons use brand colors |

---

### 2. Progressive Disclosure

**Definition:** Gradually guide users deeper, don't show all functions at once.

**Application Scenarios:**
- Onboarding Flow
- Function navigation
- Settings Page

**Design Guidelines:**
```
Standard Flow:
Login → Dashboard Overview → Select Function → Detailed Operation

Prohibited Flow:
Login → Directly enter complex function (skip Overview)
```

---

### 3. Spatial Orientation

**Definition:** Let users know "where am I", "where can I go".

**Application Scenarios:**
- Navigation Design
- Dashboard mental map
- Breadcrumbs

**Design Guidelines:**
| Element | Function | Implementation |
|------|------|---------|
| Bottom Navigation Bar | Show current position | Highlight current Tab |
| Top Title | Show page name | Fixed display |
| Back Button | Provide return path | Upper left arrow |

---

### 4. Fitts' Law

**Definition:** Larger and closer targets are easier to click.

**Application Scenarios:**
- Button size design
- Touch area
- Primary operation position

**Design Guidelines:**
| Element | Minimum Size | Recommended Size |
|------|---------|---------|
| Button | 44×44 pt | 48×48 pt |
| Touch Area | 44×44 pt | Including spacing |
| Primary Operation Button | - | Bottom of screen or thumb-reachable area |

---

### 5. Hick's Law

**Definition:** More options, longer decision time.

**Application Scenarios:**
- Options classification
- Menu design
- Settings page

**Design Guidelines:**
```
❌ Wrong: Show 20 options at once
✅ Correct: Categorize into 4-5 groups, each group has 3-4 options

❌ Wrong: Settings page lists all setting items
✅ Correct: Divided into "Account", "Notifications", "Privacy", "Other" subcategories
```

---

### 6. Achievement Design Psychology

**Definition:** Progress visualization enhances motivation.

**Application Scenarios:**
- Gamification elements
- Progress bars
- Badge system

**Design Guidelines:**
| Element | Function | Psychological Effect |
|------|------|---------|
| Progress Bar | Show completion percentage | Motivate completion |
| Check-in count | Record continuous use | Build habits |
| Badges/Achievements | Milestone rewards | Positive feedback |
| Stars/Points | Immediate rewards | Short-term motivation |

---

## Flow Design Checklist

When reviewing App flow design, must confirm the following:

### Post-Login Phase

| Check Item | Correct Design | Wrong Design |
|---------|---------|---------|
| Has Dashboard? | Login → Dashboard | Login → Directly enter function |
| Shows Status? | Show connection status, progress | No status indication |
| Has Navigation? | Bottom Tab or hamburger menu | No explicit navigation |

### Function Entry Phase

| Check Item | Correct Design | Wrong Design |
|---------|---------|---------|
| Prerequisites Check? | Check device connection before entry | Only discover unusable after entry |
| Friendly Guide? | Hint "Please connect first" + Button | Only show error message |
| Standalone Function? | Functions not requiring device can work independently | All functions require connection |

### Post-Completion Phase

| Check Item | Correct Design | Wrong Design |
|---------|---------|---------|
| Positive Feedback? | Success animation, encouragement message | Only show "Complete" |
| Reward Mechanism? | Earn stars, badges | No rewards |
| Next Step Guide? | Recommend next task | Return to home with no hint |

---

## Prerequisites Design Pattern

### Standard Prerequisites Check Flow

```
User clicks function entry
        │
        ▼
    Check prerequisites
        │
    ┌───┴───┐
    │       │
    ▼       ▼
  Satisfied  Not satisfied
    │       │
    ▼       ▼
Enter function  Show guide
          │
          ▼
    ┌─────────────┐
    │ Friendly hint message │
    │ [Go to settings]   │
    └─────────────┘
          │
          ▼
    Return after completing settings
```

### Example: Training Module Prerequisites

```swift
func checkTrainingPrerequisites() -> PrerequisiteResult {
    // 1. Check device connection
    if !deviceManager.isConnected {
        return .notMet(
            message: "Please first connect iNAP Device",
            action: .navigateTo(.devicePairing)
        )
    }

    // 2. Check device battery
    if deviceManager.batteryLevel < 20 {
        return .warning(
            message: "Device battery below 20%, recommend charging before training"
        )
    }

    // 3. Prerequisites satisfied
    return .met
}
```

---

## Dashboard Design Specification

Dashboard is the App's "mental buffer zone", must include the following elements:

### Mandatory Elements

| Element | Function | Psychology Basis |
|------|------|-----------|
| **Device Status** | Show connected/disconnected | Spatial Orientation - Prerequisites hint |
| **Progress Overview** | Show completion percentage | Achievement design |
| **Today's Tasks** | Show pending items | Progressive Disclosure - guide next step |
| **Quick Entry** | Frequently used function buttons | Fitts' Law - improve efficiency |
| **Navigation Bar** | Bottom Tab | Spatial Orientation - know where to go |

### Dashboard Layout Example

```
┌────────────────────────────────────┐
│  Avatar  │  Stars: 150 ⭐  │  Day 7   │  ← Status Bar
├────────────────────────────────────┤
│  🔵 Device Connected     Battery 85%        │  ← Device Status
├────────────────────────────────────┤
│  ┌────────────┐  ┌────────────┐   │
│  │ Today's Training    │  │ Dream Coach   │   │  ← Dual Card
│  │ • Wearing practice  │  │ Last night's sleep   │   │
│  │ • Airtight practice  │  │ Very good!   │   │
│  └────────────┘  └────────────┘   │
├────────────────────────────────────┤
│  Sleep Log                          │  ← Data Summary
│  Last night 7h 32m  ⭐⭐⭐⭐          │
├────────────────────────────────────┤
│  🏠   📊   🎮   ⚙️   👤           │  ← Bottom Navigation
└────────────────────────────────────┘
```

---

## Reference Resources

### Design Psychology Books
- Don Norman - "The Design of Everyday Things"
- Steve Krug - "Don't Make Me Think"
- Susan Weinschenk - "100 Things Every Designer Needs to Know About People"

### Related Laws
- Fitts' Law (1954)
- Hick's Law (1952)
- Miller's Law (1956) - 7±2 Items memory limitation
- Jakob's Law - User expects consistency

### Medical Software Special Considerations
- IEC 62366-1:2015 - Medical device usability engineering
- FDA Human Factors Guidance
- Clinical environment special requirements (glove operation, emergency situations)
