# Design Psychology Principles

This document defines the design psychology principles that UI/UX design must follow to ensure a good user experience.

## Core Principles

### 1. Cognitive Load Theory

**Definition:** Avoid presenting too much information at once, reducing users' cognitive burden.

**Application Scenarios:**
- Dashboard design
- Feature layering
- Form design

**Design Guidelines:**
| Principle | Description | Example |
|-----------|-------------|---------|
| Chunking | Present information in small chunks | Multi-step form filling |
| Progressive Loading | Show important info first, details later | Dashboard shows summary first |
| Visual Hierarchy | Use size, color to differentiate importance | Primary buttons use primary color |

---

### 2. Progressive Disclosure

**Definition:** Gradually guide users deeper, not showing all features at once.

**Application Scenarios:**
- Onboarding flow
- Feature navigation
- Settings page

**Design Guidelines:**
```
Standard flow:
Login → Dashboard Overview → Select Feature → Detailed Operation

Prohibited flow:
Login → Directly enter complex feature (skip overview)
```

---

### 3. Spatial Orientation

**Definition:** Let users know "where am I" and "where can I go".

**Application Scenarios:**
- Navigation design
- Dashboard mental map
- Breadcrumb

**Design Guidelines:**
| Element | Function | Implementation |
|---------|----------|----------------|
| Bottom Navigation Bar | Show current location | Highlight current Tab |
| Top Title | Show page name | Fixed display |
| Back Button | Provide exit path | Arrow in top left |

---

### 4. Fitts' Law

**Definition:** Larger and closer targets are easier to click.

**Application Scenarios:**
- Button size design
- Touch targets
- Primary action positioning

**Design Guidelines:**
| Element | Minimum Size | Recommended Size |
|---------|--------------|------------------|
| Button | 44×44 pt | 48×48 pt |
| Touch Area | 44×44 pt | Including padding |
| Primary Action Button | - | Bottom of screen or thumb-reachable zone |

---

### 5. Hick's Law

**Definition:** More options lead to longer decision time.

**Application Scenarios:**
- Option categorization
- Menu design
- Settings page

**Design Guidelines:**
```
❌ Wrong: Display 20 options at once
✅ Correct: Categorize into 4-5 groups, 3-4 options each

❌ Wrong: Settings page lists all settings
✅ Correct: Divided into "Account" "Notifications" "Privacy" "Other" subcategories
```

---

### 6. Achievement Psychology

**Definition:** Visible progress enhances motivation.

**Application Scenarios:**
- Gamification elements
- Progress bars
- Badge systems

**Design Guidelines:**
| Element | Function | Psychological Effect |
|---------|----------|---------------------|
| Progress Bar | Show completion percentage | Motivates completion |
| Streak Days | Consecutive usage record | Forms habit |
| Badges/Achievements | Milestone rewards | Positive feedback |
| Stars/Points | Instant rewards | Short-term motivation |

---

## Flow Design Checklist

When reviewing App flow design, must confirm the following:

### Post-Login Phase

| Check Item | Correct Design | Wrong Design |
|------------|----------------|--------------|
| Is there a Dashboard? | Login → Dashboard | Login → Directly enter feature |
| Is status displayed? | Show connection status, progress | No status indication |
| Is there navigation? | Bottom Tab or hamburger menu | No clear navigation |

### Feature Entry Phase

| Check Item | Correct Design | Wrong Design |
|------------|----------------|--------------|
| Prerequisite check? | Check device connection before entry | Only discover unusable after entry |
| Friendly guidance? | Prompt "Please connect first" + button | Only show error message |
| Offline features? | Features not requiring device work offline | All features need connection |

### Completion Phase

| Check Item | Correct Design | Wrong Design |
|------------|----------------|--------------|
| Positive feedback? | Success animation, encouragement message | Only shows "Complete" |
| Reward mechanism? | Earn stars, badges | No rewards |
| Next step guidance? | Suggest next task | Return to home with no prompt |

---

## Prerequisite Design Pattern

### Standard Prerequisite Check Flow

```
User clicks feature entry
        │
        ▼
    Check prerequisites
        │
    ┌───┴───┐
    │       │
    ▼       ▼
   Met    Not Met
    │       │
    ▼       ▼
Enter    Show
feature  guidance
          │
          ▼
    ┌─────────────┐
    │ Friendly    │
    │ prompt      │
    │ [Go to      │
    │  Settings]  │
    └─────────────┘
          │
          ▼
    Return after
    completing setup
```

### Example: Training Module Prerequisites

```swift
func checkTrainingPrerequisites() -> PrerequisiteResult {
    // 1. Check device connection
    if !deviceManager.isConnected {
        return .notMet(
            message: "Please connect device first",
            action: .navigateTo(.devicePairing)
        )
    }

    // 2. Check device battery
    if deviceManager.batteryLevel < 20 {
        return .warning(
            message: "Device battery below 20%, recommend charging before training"
        )
    }

    // 3. Prerequisites met
    return .met
}
```

---

## Dashboard Design Specifications

Dashboard is the App's "psychological buffer zone", must contain the following elements:

### Required Elements

| Element | Function | Psychology Basis |
|---------|----------|------------------|
| **Device Status** | Show connected/disconnected | Spatial Orientation - Prerequisite prompt |
| **Progress Overview** | Show completion percentage | Achievement Psychology |
| **Today's Tasks** | Show pending items | Progressive Disclosure - Guide next step |
| **Quick Entry** | Common feature buttons | Fitts' Law - Improve efficiency |
| **Navigation Bar** | Bottom Tab | Spatial Orientation - Know where to go |

### Dashboard Layout Example

```
┌────────────────────────────────────┐
│  Avatar │  Stars: 150 ⭐  │  Day 7  │  ← Status bar
├────────────────────────────────────┤
│  🔵 Device Connected    85% Battery │  ← Device status
├────────────────────────────────────┤
│  ┌────────────┐  ┌────────────┐   │
│  │ Today's    │  │ Coach Says │   │  ← Dual cards
│  │ Training   │  │ Great job  │   │
│  │ • Practice │  │ yesterday! │   │
│  │ • Exercise │  │            │   │
│  └────────────┘  └────────────┘   │
├────────────────────────────────────┤
│  Sleep Log                         │  ← Data summary
│  Last night 7h 32m  ⭐⭐⭐⭐       │
├────────────────────────────────────┤
│  🏠   📊   🎮   ⚙️   👤          │  ← Bottom navigation
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
- Miller's Law (1956) - 7±2 item memory limit
- Jakob's Law - Users expect consistency

### Medical Software Special Considerations
- IEC 62366-1:2015 - Usability Engineering for Medical Devices
- FDA Human Factors Guidance
- Clinical environment special needs (glove operation, emergency situations)
