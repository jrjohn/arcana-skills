# Cognitive Psychology Principles

This document defines the cognitive psychology principles that UI/UX design must follow to ensure designs align with human cognitive processes.

## Overview

Cognitive psychology studies how humans:
- **Perception** - Receiving and interpreting sensory information
- **Attention** - Selective processing of information
- **Memory** - Storing and retrieving information
- **Thinking** - Problem solving and decision making
- **Learning** - Acquiring new knowledge and skills

Good UI design must align with these cognitive principles.

---

## 1. Mental Model

### Definition
Users' internal expectations and understanding of how a system works.

### Importance
- Users predict system behavior based on their mental model
- Designs that don't match mental models cause confusion and errors
- Medical software errors can lead to serious consequences

### Design Principles

| Principle | Description | Example |
|-----------|-------------|---------|
| **Meet Expectations** | Design matches existing cognition | Trash icon = Delete |
| **Use Metaphors** | Use familiar real-world concepts | Folders, bookmarks, shopping cart |
| **Consistency** | Same operations produce same results | Swipe always navigates |
| **Progressive Disclosure** | Gradually build correct mental model | Onboarding tutorials |

### Common Mental Model Conflicts

| Scenario | User Expectation | Poor Design |
|----------|------------------|-------------|
| Back button | Return to previous page | Close entire app |
| Scroll down | Content scrolls up | Content moves down |
| Red button | Danger/Stop action | Confirm/Continue |
| Checkmark icon | Complete/Confirm | Select item |

---

## 2. Attention

### Definition
Cognitive ability to selectively process information; attention is a limited resource.

### Attention Types

| Type | Description | UI Application |
|------|-------------|----------------|
| **Selective Attention** | Focus on specific stimuli | Dialog focuses on important message |
| **Divided Attention** | Process multiple info simultaneously | Avoid requiring multitasking |
| **Sustained Attention** | Maintain focus over time | Segmented tasks, break reminders |
| **Attention Switching** | Switch between focal points | Clear visual guidance |

### Methods to Attract Attention

| Method | Principle | UI Implementation |
|--------|-----------|-------------------|
| **Contrast** | Differences attract attention | Important buttons use contrasting colors |
| **Motion** | Movement attracts attention | Loading animations, blinking prompts |
| **Position** | Certain positions get priority | Important info in top-left |
| **Size** | Larger elements are more noticeable | Primary buttons larger than secondary |
| **Isolation** | Standalone elements stand out | White space highlights key content |

### Avoiding Attention Interference

| Interference Type | Problem | Solution |
|-------------------|---------|----------|
| Visual noise | Too many elements competing | Simplify interface, add white space |
| Unexpected animation | Distracts user focus | Purposeful, controllable animations |
| Pop-up messages | Interrupts workflow | Delay non-urgent messages |
| Auto-play | Forces attention shift | User controls media playback |

### Change Blindness

**Definition:** Users may miss changes on the screen.

**Medical Software Impact:** Status changes may be overlooked, leading to errors.

**Solutions:**
- Use animated transitions for important changes
- Visual emphasis at change locations
- Provide sound/vibration feedback
- Clear text explanation of changes

---

## 3. Memory

### Memory Types

```
Sensory Memory (milliseconds)
    │
    ▼ Attention filtering
Working Memory (seconds~minutes, limited capacity)
    │
    ▼ Encoding process
Long-term Memory (permanent, unlimited capacity)
    │
    ├── Explicit Memory (consciously retrieved)
    │   ├── Episodic Memory (events, experiences)
    │   └── Semantic Memory (facts, knowledge)
    │
    └── Implicit Memory (unconsciously retrieved)
        └── Procedural Memory (skills, habits)
```

### Working Memory

**Capacity Limit:** 4±1 items (modern research revision of Miller's Law 7±2)

**Design Implications:**

| Design Item | Recommended Quantity | Reason |
|-------------|---------------------|--------|
| Navigation items | 4-5 | Too many hard to remember |
| Process steps | ≤5 steps | Avoid forgetting progress |
| Form groups | 3-4 fields/group | Reduce memory burden |
| Verification codes | 4-6 digits | Short-term memory limit |
| Password display | Provide show option | Forget content while typing |

**Strategies to Reduce Memory Load:**

| Strategy | Description | Example |
|----------|-------------|---------|
| **Recognition over Recall** | Provide options instead of requiring input | Dropdown vs blank field |
| **Persistent Display** | Keep important info visible | Fixed status bar |
| **Progress Indicator** | Show current position | Step 2/5 |
| **Auto-fill** | Reduce repeated input | Remember last input |

### Long-term Memory

**Designs to Strengthen Long-term Memory:**

| Strategy | Cognitive Principle | UI Implementation |
|----------|---------------------|-------------------|
| **Chunking** | Organize info into meaningful groups | Phone number segments 0912-345-678 |
| **Association** | Connect new and old knowledge | Use familiar metaphor icons |
| **Repetition** | Strengthen memory traces | Multiple entry points for common features |
| **Context** | Context-related memory is stronger | Consistent operating environment |
| **Emotion** | Emotion enhances memory | Positive feedback success animations |

### Memory-Related Design Principles

**Consistency Rule**

| Level | Description | Example |
|-------|-------------|---------|
| Internal Consistency | Same function, same appearance within app | All save buttons are blue |
| External Consistency | Follow platform conventions | iOS back button in top-left |
| Temporal Consistency | Same operation sequence | Always select then confirm |

---

## 4. Perception

### Visual Perception Principles

#### Gestalt Principles

| Principle | Description | UI Application | Example |
|-----------|-------------|----------------|---------|
| **Proximity** | Nearby elements seen as a group | Related controls together | Form labels near input fields |
| **Similarity** | Similar appearance seen as same type | Same style for same button type | Primary buttons all blue |
| **Continuity** | Eyes follow lines | Guide reading order | Arrows indicate flow |
| **Closure** | Brain completes incomplete shapes | Simplified icons | Gap circle still seen as circle |
| **Figure-Ground** | Distinguish foreground from background | Dialog design | Overlay + floating card |
| **Common Fate** | Same direction movement seen as group | Animation design | Related elements move together |

#### Visual Hierarchy

```
High Importance ──────────────────────────► Low Importance

Large Font        Medium Font         Small Font
Bold              Regular             Light
High Contrast     Medium Contrast     Low Contrast
Top/Left          Center              Bottom/Right
Isolated/Space    Grouped             Dense
```

**Methods to Establish Visual Hierarchy:**

| Method | Description |
|--------|-------------|
| Size | Important elements are larger |
| Color | Key info uses brand color |
| Contrast | Important content has high contrast |
| Position | Primary info at visual focal point |
| White Space | Isolated elements stand out |
| Depth | Shadows indicate hierarchy |

### Color Perception

**Color Psychology and UI Application:**

| Color | Psychological Association | UI Usage |
|-------|--------------------------|----------|
| Blue | Trust, professional, calm | Primary color, links |
| Green | Success, safe, natural | Confirmation, positive status |
| Red | Danger, urgent, error | Warnings, errors, delete |
| Yellow | Attention, alert | Warning messages |
| Orange | Energy, action | CTA buttons |
| Gray | Neutral, secondary | Disabled state, helper text |

**Accessibility Considerations:**
- 8% of males are colorblind
- Don't rely solely on color to convey information
- Pair with icons or text
- Contrast ratio at least 4.5:1 (WCAG AA)

---

## 5. Affordance & Signifier

### Don Norman's Design Principles

| Principle | Definition | Good Design | Poor Design |
|-----------|------------|-------------|-------------|
| **Affordance** | Implied possible actions | Raised button implies pressable | Flat elements unidentifiable |
| **Signifier** | Clear indication of how to operate | Icon + text label | Mystery icon without explanation |
| **Mapping** | Correspondence between control and result | Swipe up = scroll up | Counter-intuitive operations |
| **Feedback** | Immediate response after action | Click has visual reaction | Click has no response |
| **Conceptual Model** | Explanation of system operation | Progress bar explains waiting | No status indication |
| **Constraints** | Prevent incorrect operations | Disable invalid buttons | Allow invalid operations |

### Button Affordance Design

```
High Affordance Button Features:
┌─────────────────────┐
│  ✓ 3D feel (shadow)  │
│  ✓ Clear boundaries  │
│  ✓ Contrasting fill  │
│  ✓ Adequate size (≥44pt) │
│  ✓ Icon + text       │
│  ✓ Hover/press state │
└─────────────────────┘

Low Affordance Elements (Avoid):
┌─────────────────────┐
│  ✗ Plain text link without underline │
│  ✗ Flat design without borders │
│  ✗ Low contrast with background │
│  ✗ Size too small    │
│  ✗ Icon only without text │
└─────────────────────┘
```

### Feedback Design

| Feedback Type | Timing | Example |
|---------------|--------|---------|
| **Immediate Feedback** | At action moment | Button color changes on press |
| **Status Feedback** | During processing | Loading animation |
| **Result Feedback** | Action complete | Success/failure prompt |
| **System Feedback** | Background status | Connection status icon |

**Feedback Methods:**

| Method | Applicable Scenario |
|--------|---------------------|
| Visual | All operations (required) |
| Sound | Important events, errors |
| Vibration | Mobile device tactile confirmation |
| Text | Complex results needing explanation |

---

## 6. Error Prevention and Handling

### Error Types (Norman's Error Classification)

| Type | Description | Example | Prevention |
|------|-------------|---------|------------|
| **Slip** | Know correct but execute wrong | Press wrong button | Space dangerous buttons apart |
| **Mistake** | Wrong intent or plan | Misunderstand function | Clear explanations |

### Error Prevention Design

| Strategy | Description | Implementation |
|----------|-------------|----------------|
| **Constraints** | Limit possible operations | Disable invalid options |
| **Confirmation** | Confirm before important actions | Delete confirmation dialog |
| **Undo** | Provide undo functionality | Undo button |
| **Warning** | Remind before dangerous actions | Red warning text |
| **Defaults** | Safe default values | Default to not delete |
| **Formatting** | Force correct format | Date picker |

### Error Message Design

**Poor Error Messages:**
```
❌ Error 500
❌ Format error
❌ Operation failed
```

**Good Error Messages:**
```
✓ Password must be at least 8 characters with numbers and letters
✓ Cannot connect to server, please check your network and try again
✓ Invalid email format, please enter like name@example.com
```

**Error Message Elements:**

| Element | Description |
|---------|-------------|
| Explain problem | What happened |
| Explain cause | Why it happened |
| Provide solution | How to fix |
| Friendly tone | Don't blame user |

---

## 7. Reading Psychology

### Reading Patterns

**F-Pattern Scanning**

```
████████████████████████
████████████████
████████████
██████████████████
██████████
████████
```

Users tend to:
1. Read horizontally across the top
2. Move down, then read horizontally again
3. Scan vertically down the left side

**Design Implications:**
- Important info in top-left
- Key words at paragraph beginnings
- Use headings and bullet points

### Readability Principles

| Principle | Recommended Value | Reason |
|-----------|-------------------|--------|
| Line length | 45-75 characters | Too long hard to track next line |
| Line height | 1.4-1.6x | Too tight crowded, too wide scattered |
| Paragraphs | 3-5 sentences | Long paragraphs hard to read |
| Contrast | ≥4.5:1 | WCAG AA standard |

### Font Selection

| Type | Suitable For | Examples |
|------|--------------|----------|
| Sans-serif | Screen reading, UI elements | SF Pro, Roboto, Arial |
| Serif | Long-form reading, print | Times, Georgia |
| Monospace | Code, number alignment | Menlo, Courier |

### Medical Information Display

**Number Formatting:**

| Type | Format | Example |
|------|--------|---------|
| Large numbers | Thousands separator | 1,234,567 |
| Decimals | Max 2 places | 98.65 |
| Percentage | With symbol | 85% |
| Time | With units | 7h 32m |
| Temperature | With units | 37.5°C |
| Blood pressure | Fraction format | 120/80 mmHg |

**Highlighting Critical Medical Info:**

```
Abnormal Value Display:
┌─────────────────────────────┐
│  Heart Rate: ❗ 125 bpm (high)  │  ← Red + icon + text explanation
│  Blood Oxygen: ✓ 98%           │  ← Green + checkmark
│  Temperature: ⚠️ 38.2°C (elevated) │  ← Yellow + warning
└─────────────────────────────┘
```

---

## 8. Learnability

### Learning Curve Types

```
Efficiency
  │
  │      ╭──────── Ideal Curve (progressive learning)
  │     ╱
  │    ╱
  │   ╱
  │  ╱ ╭──────── Steep Curve (expert system)
  │ ╱ ╱
  │╱ ╱
  └──────────────────► Time
```

### Strategies to Improve Learnability

| Strategy | Description | Implementation |
|----------|-------------|----------------|
| **Progressive Disclosure** | Gradually introduce features | Beginner mode, tutorial tips |
| **Consistency** | Similar situations, similar operations | Unified design language |
| **Immediate Feedback** | Action results immediately visible | Real-time form validation |
| **Explorable** | Safe to try without fear of errors | Undo, preview features |
| **Contextual Help** | Provide help when needed | Tooltips, question mark icons |

### Onboarding Design

**Onboarding Types:**

| Type | Suitable Scenario | Pros | Cons |
|------|-------------------|------|------|
| Guided | Complex features | Complete introduction | May be skipped |
| Progressive | Gradual learning | Doesn't interrupt flow | Slower learning |
| Interactive | Hands-on learning | Deep memory retention | High development cost |
| Contextual | Just-in-time help | Appears when needed | May distract |

---

## Cognitive Psychology Review Checklist

### Complete Checklist

| Category | Check Item | Pass Criteria | Weight |
|----------|------------|---------------|--------|
| **Mental Model** | Operations meet expectations? | Understandable without explanation | High |
| **Mental Model** | Uses familiar metaphors? | Icons have clear meaning | Medium |
| **Attention** | Key info highlighted? | Find focus within 3 seconds | High |
| **Attention** | Avoids unnecessary distractions? | No auto-play/pop-ups | Medium |
| **Working Memory** | Reasonable number of steps? | Single flow ≤5 steps | High |
| **Working Memory** | Reduces memory burden? | Important info stays visible | High |
| **Long-term Memory** | Consistent design? | Same function, same appearance | High |
| **Perception** | Clear visual grouping? | Related elements grouped | Medium |
| **Perception** | Clear visual hierarchy? | Importance differentiated | Medium |
| **Affordance** | Interactive elements obvious? | Buttons look clickable | High |
| **Feedback** | All operations have feedback? | Clicks have response | High |
| **Error Prevention** | Has fail-safe design? | Invalid operations disabled | High |
| **Error Handling** | Friendly error messages? | Explain problem + solution | Medium |
| **Readability** | Text readable? | Contrast ≥4.5:1 | High |
| **Learnability** | Beginners can get started? | Has guidance or instructions | Medium |

### Medical Software Special Checks

| Check Item | Standard | Severity |
|------------|----------|----------|
| Critical values clear? | Large font, with units | Critical |
| Abnormal values highlighted? | Color + icon + text | Critical |
| Operation confirmation? | Important operations require confirmation | Critical |
| Errors recoverable? | Provide Undo | High |
| Accessibility support? | VoiceOver/TalkBack | Medium |

---

## Reference Resources

### Classic Works
- Don Norman - "The Design of Everyday Things"
- Susan Weinschenk - "100 Things Every Designer Needs to Know About People"
- Steve Krug - "Don't Make Me Think"
- Jeff Johnson - "Designing with the Mind in Mind"

### Cognitive Psychology Principles
- Miller's Law (1956) - 7±2 / 4±1 memory capacity
- Gestalt Principles (1920s) - Gestalt perception principles
- Fitts' Law (1954) - Target acquisition time
- Hick's Law (1952) - Decision time

### Medical Software Special References
- IEC 62366-1:2015 - Usability Engineering for Medical Devices
- FDA Human Factors Guidance
- AAMI HE75 - Human Factors Engineering Guidelines
