# Cognitive Psychology Principles

This document defines the cognitive psychology principles that UI/UX design must follow to ensure design aligns with human cognitive processes.

## Overview

Cognitive psychology studies how humans:
- **Perception** - Receive and interpret sensory information
- **Attention** - Selectively process information
- **Memory** - Store and retrieve information
- **Thinking** - Problem-solving and decision-making
- **Learning** - Acquire new knowledge and skills

Good UI design must align with these cognitive process principles.

---

## 1. Mental Model

### Definition
User's internal expectation and understanding of how the system operates.

### Importance
- Users predict system behavior based on mental models
- Design not aligned with mental model causes confusion and errors
- Medical software errors can cause serious consequences

### Design Principles

| Principle | Description | Example |
|------|------|------|
| **Align Expectations** | Design aligns with user's existing cognition | Trash can icon = Delete |
| **Use Metaphors** | Use familiar entities to create boundary concepts | Folder, bookmarks, shopping cart |
| **Consistency** | Same operation generates same result | Swipe always means navigation |
| **Progressive Reveal** | Gradually create correct mental model | Newbie tutorial guide |

### Common Mental Model Conflicts

| Situation | User Expectation | Wrong Design |
|------|-----------|---------|
| Back Button | Return to previous page | Close entire app |
| Downward Swipe | Content moves upward | Content moves downward |
| Red Button | Danger/Stop operation | Confirm/Resume operation |
| Checkmark Icon | Complete/Confirm | Select items |

---

## 2. Attention

### Definition
Selective information processing cognitive ability. Attention is a limited resource.

### Attention Types

| Type | Description | UI Application |
|------|------|---------|
| **Selective Attention** | Focus on specific stimuli | Dialog focuses on important message |
| **Divided Attention** | Process multiple items simultaneously | Avoid requiring multitasking |
| **Sustained Attention** | Maintain focus for extended period | Segmented tasks, rest hints |
| **Attention Shift** | Transition between different focus points | Clear visual guidance |

### Methods to Attract Attention

| Method | Principle | UI Implementation |
|------|------|---------|
| **Contrast** | Differences attract attention | Important buttons use contrasting colors |
| **Motion** | Movement attracts attention | Loading animation, hint flashing |
| **Position** | Specific positions get priority attention | Important information placed in upper left |
| **Size** | Larger elements more noticeable | Primary button larger than secondary button |
| **Spacing** | Independent elements more prominent | Highlight critical content with whitespace |

### Avoid Attention Interference

| Interference Type | Problem | Solution |
|---------|------|---------|
| Visual Noise | Too many elements competing for attention | Simplify interface, add whitespace |
| Unexpected Animation | Distracts user focus | Animations have purpose and are controllable |
| Pop-up Messages | Interrupt workflow | Non-urgent messages delay display |
| Auto-play | Forces attention shift | User controls media playback |

### Change Blindness

**Definition:** Users may miss changes on screen.

**Medical Software Impact:** Status changes may be ignored, causing errors.

**Solutions:**
- Important changes use animation transitions
- Change position uses visual emphasis
- Provide sound/vibration feedback
- Explicit text description of change content

---

## 3. Memory

### Memory Types

```
Sensory Memory (millisecond level)
    │
    ▼ Attention Filter
Working Memory (seconds~minutes, limited capacity)
    │
    ▼ Encoding Process
Long-term Memory (permanent, unlimited capacity)
    │
    ├── Explicit Memory (conscious retrieval)
    │   ├── Episodic Memory (event experience)
    │   └── Semantic Memory (factual knowledge)
    │
    └── Implicit Memory (unconscious retrieval)
        └── Procedural Memory (skills and habits)
```

### Working Memory

**Capacity Limitation:** 4±1 Items (modern research updates Miller's Law 7±2)

**Design Impact:**

| Design Item | Recommended Quantity | Reason |
|---------|---------|------|
| Navigation Items | 4-5 items | Exceeding makes it difficult to remember options |
| Step Flow | ≤5 steps | Avoid forgetting progress |
| Form Group | 3-4 fields/group | Reduce memory burden |
| Verification Code | 4-6 digits | Short-term memory limitation |
| Password Display | Provide show option | Forget content during input |

**Strategies to Reduce Memory Burden:**

| Strategy | Description | Example |
|------|------|------|
| **Recognition over Recall** | Provide options rather than require input | Dropdown instead of empty fields |
| **Persistent Display** | Keep important information visible | Fixed status bar |
| **Progress Indication** | Show current position | Step 2/5 |
| **Auto-fill** | Reduce duplicate input | Remember previous input |

### Long-term Memory

**Reinforce Long-term Memory Design:**

| Strategy | Cognitive Principle | UI Implementation |
|------|---------|---------|
| **Chunking** | Organize information into meaningful groups | Phone number segmented 0912-345-678 |
| **Association** | Link new with old knowledge | Use familiar metaphor icons |
| **Repetition** | Enhance memory trace | Frequently used function multiple entry points |
| **Context** | Context-related memory more solid | Consistent operating environment |
| **Emotion** | Emotion enhances memory | Positive feedback success animation |

### Memory-Related Design Principles

**Consistency Law**

| Level | Description | Example |
|------|------|------|
| Internal Consistency | Same function same appearance within app | All save buttons are blue |
| External Consistency | Align with platform conventions | iOS back button in upper left |
| Sequential Consistency | Same operation order | Always select then confirm |

---

## 4. Perception

### Visual Perception Principles

#### Gestalt Principles

| Principle | Description | UI Application | Example |
|------|------|---------|------|
| **Proximity** | Close elements viewed as group | Related controls placed together | Form label next to input box |
| **Similarity** | Similar appearance viewed as same category | Same category buttons same style | Primary buttons all blue |
| **Continuity** | Eye movement follows lines | Guide reading order | Arrow indicates flow |
| **Closure** | Brain completes incomplete shapes | Simplify icons | Missing circle still viewed as circle |
| **Figure-Ground** | Distinguish foreground and background | Dialog design | Mask layer + floating card |
| **Common Fate** | Same direction movement viewed as group | Animation design | Related elements move together |

#### Visual Hierarchy

```
High Importance ──────────────────────────► Low Importance

Large Font        Medium Font         Small Font
Bold             Normal              Fine
High Contrast     Medium Contrast     Low Contrast
Top/Left         Center              Bottom/Right
Spacing/Whitespace  Grouped           Dense
```

**Create Visual Hierarchy Methods:**

| Method | Description |
|------|------|
| Size | Important elements larger |
| Color | Critical information uses brand color |
| Contrast | Important content high contrast |
| Position | Main information at visual focus |
| Whitespace | Independent elements more prominent |
| Depth | Shadow indicates hierarchy |

### Color Perception

**Color Psychology and UI Application:**

| Color | Psychological Association | UI Purpose |
|------|---------|---------|
| Blue | Trust, professional, calm | Primary color, links |
| Green | Success, safety, natural | Confirm, positive status |
| Red | Danger, emergency, error | Warning, error, delete |
| Yellow | Attention, alert | Warning message |
| Orange | Energy, action | CTA button |
| Gray | Neutral, secondary | Disabled status, helper text |

**Accessibility Considerations:**
- 8% males have color blindness
- Don't rely solely on color to convey information
- Combine with icons or text
- Contrast ratio at least 4.5:1 (WCAG AA)

---

## 5. Affordance and Signifier

### Don Norman's Design Principles

| Principle | Definition | Good Design | Bad Design |
|------|------|---------|---------|
| **Affordance** | Object suggests possible operations | Raised button suggests pressable | Flat element cannot be identified |
| **Signifier** | Explicit instruction on how to operate | Icon+Text label | Mysterious icon with no description |
| **Mapping** | Control and result correspondence | Upward swipe=upward scroll | Counter-intuitive operation |
| **Feedback** | Immediate response after operation | Click has visual response | Click has no response |
| **Conceptual Model** | System operation explanation | Progress bar explains waiting | No status indication |
| **Constraint** | Prevent error operation | Disabled invalid button | Allow invalid operation |

### Button Affordance Design

```
High Affordance Button Characteristics:
┌─────────────────────┐
│  ✓ 3D Sense (shadow)     │
│  ✓ Explicit Border          │
│  ✓ Contrasting Fill        │
│  ✓ Appropriate Size (≥44pt)  │
│  ✓ Icon+Text         │
│  ✓ Hover/Click State     │
└─────────────────────┘

Low Affordance Elements (Avoid):
┌─────────────────────┐
│  ✗ Pure Text Link No Underline   │
│  ✗ Flat Design No Border     │
│  ✗ Low Contrast with Background     │
│  ✗ Too Small Size          │
│  ✗ Only Icon No Text     │
└─────────────────────┘
```

### Feedback Design

| Feedback Type | Timing | Example |
|---------|------|------|
| **Immediate Feedback** | During operation | Button color change on press |
| **Status Feedback** | Processing | Loading animation |
| **Result Feedback** | Operation complete | Success/Failed hint |
| **System Feedback** | Background status | Connection status icon |

**Feedback Methods:**

| Method | Appropriate Use Situation |
|------|---------|
| Visual | All operations (mandatory) |
| Audio | Important events, errors |
| Vibration | Mobile device tactile confirmation |
| Text | Complex results needing description |

---

## 6. Error Prevention and Handling

### Error Types (Norman's Error Classification)

| Type | Description | Example | Prevention Method |
|------|------|------|---------|
| **Slip** | Know correct but execute wrong | Press wrong button | Space dangerous buttons |
| **Mistake** | Wrong intention or plan | Misunderstand function | Clear description |

### Error Prevention Design

| Strategy | Description | Implementation |
|------|------|---------|
| **Constraint** | Limit possible operations | Disabled invalid options |
| **Confirmation** | Confirm before important operations | Dialog before delete |
| **Undo** | Provide undo function | Undo button |
| **Warning** | Remind before dangerous operations | Red warning text |
| **Default** | Safe default values | Default not delete |
| **Format** | Force correct format | Date picker |

### Error Message Design

**Bad Error Messages:**
```
❌ Error 500
❌ Format Error
❌ Operation Failed
```

**Good Error Messages:**
```
✓ Password needs at least 8 characters, including numbers and letters
✓ Cannot connect to server, please check network connection and try again
✓ Email format incorrect, please enter as name@example.com
```

**Error Message Elements:**

| Element | Description |
|------|------|
| Describe Problem | What happened |
| Describe Reason | Why it happened |
| Provide Solution | How to correct |
| Friendly Tone | Don't blame user |

---

## 7. Reading Psychology

### Reading Patterns

**F-Pattern Scan Pattern**

```
████████████████████████
████████████
██████████
██████████████████
██████████
████████
```

Users tend to:
1. Horizontal read top
2. Move downward, then horizontal read
3. Vertical scan leftmost

**Design Impact:**
- Important information placed in upper left
- Critical words placed at section beginning
- Use titles and bullet points

### Readability Principles

| Principle | Recommended Value | Reason |
|------|--------|------|
| Line Length | 45-75 characters | Too long difficult to track next line |
| Line Height | 1.4-1.6 times | Too narrow crowded, too loose dispersed |
| Paragraph | 3-5 sentences | Long paragraphs difficult to read |
| Contrast | ≥4.5:1 | WCAG AA standard |

### Font Selection

| Type | Appropriate Use | Example |
|------|------|------|
| Sans-serif | Screen reading, UI elements | SF Pro, Roboto, Arial |
| Serif | Long article reading, print | Times, Georgia |
| Monospace | Code, number alignment | Menlo, Courier |

### Medical Information Display

**Number Formatting:**

| Type | Format | Example |
|------|------|------|
| Large Numbers | Thousand separators | 1,234,567 |
| Small Numbers | Max 2 decimals | 98.65 |
| Percentage | With symbol | 85% |
| Time | With unit | 7h 32m |
| Temperature | With unit | 37.5°C |
| Blood Pressure | Fractional format | 120/80 mmHg |

**Critical Medical Information Emphasis:**

```
Abnormal Value Display:
┌─────────────────────────────┐
│  Heart Rate: ❗ 125 bpm (Too High)     │  ← Red + Icon + Text Description
│  SpO2: ✓ 98%                │  ← Green + Checkmark
│  Temperature: ⚠️ 38.2°C (Elevated)     │  ← Yellow + Warning
└─────────────────────────────┘
```

---

## 8. Learnability

### Learning Curve Types

```
Efficiency
  │
  │      ╭──────── Ideal Curve (gradual learning)
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
|------|------|---------|
| **Progressive Reveal** | Gradually introduce functions | Newbie mode, tutorial hints |
| **Consistency** | Similar situations similar operations | Unified design language |
| **Immediate Feedback** | Operation results immediately visible | Form immediate validation |
| **Explorability** | Safe to try without fear of errors | Undo, preview function |
| **Context Description** | Provide help when needed | Tooltip, question mark icon |

### Onboarding Guide Design

**Onboarding Types:**

| Type | Appropriate Use Situation | Advantage | Disadvantage |
|------|---------|------|------|
| Tour Style | Complex functions | Complete introduction | May skip |
| Progressive Style | Gradual learning | Doesn't interrupt flow | Learning slower |
| Interactive Style | Learning by doing | Memory deeper | Development cost higher |
| Contextual Style | Just-in-time help | Appears when needed | May interfere |

---

## Cognitive Psychology Review List

### Complete Checklist

| Category | Check Item | Pass Criteria | Weight |
|------|---------|---------|------|
| **Mental Model** | Operations align expectations? | No description needed to understand | High |
| **Mental Model** | Use familiar metaphors? | Icons have explicit meaning | Medium |
| **Attention** | Critical information highlighted? | Find key points within 3 seconds | High |
| **Attention** | Avoid unnecessary interference? | No auto-play/popups | Medium |
| **Working Memory** | Step quantity reasonable? | Simple flow ≤5 steps | High |
| **Working Memory** | Reduce memory burden? | Important information continuously visible | High |
| **Long-term Memory** | Design consistent? | Same function same appearance | High |
| **Perception** | Visual grouping clear? | Related elements grouped | Medium |
| **Perception** | Visual hierarchy explicit? | Importance distinguished | Medium |
| **Affordance** | Interactive elements obvious? | Button looks clickable | High |
| **Feedback** | All operations have feedback? | Click has response | High |
| **Error Prevention** | Has foolproof design? | Invalid operations disabled | High |
| **Error Handling** | Error messages friendly? | Describe problem + solution | Medium |
| **Readability** | Text easy to read? | Contrast ≥4.5:1 | High |
| **Learnability** | Newbies can get started? | Has guide or description | Medium |

### Medical Software Special Check

| Check Item | Standard | Severity |
|---------|------|--------|
| Critical values clear? | Large font, with unit | Serious |
| Abnormal values highlighted? | Color+Icon+Text | Serious |
| Operation confirm mechanism? | Important operations need confirmation | Serious |
| Errors can undo? | Provide undo | High |
| Accessibility support? | VoiceOver/TalkBack | Medium |

---

## Reference Resources

### Classic Works
- Don Norman - "The Design of Everyday Things"
- Susan Weinschenk - "100 Things Every Designer Needs to Know About People"
- Steve Krug - "Don't Make Me Think"
- Jeff Johnson - "Designing with the Mind in Mind"

### Cognitive Psychology Principles
- Miller's Law (1956) - 7±2 / 4±1 Memory capacity
- Gestalt Principles (1920s) - Gestalt perception principles
- Fitts' Law (1954) - Target acquisition time
- Hick's Law (1952) - Decision time

### Medical Software Special Reference
- IEC 62366-1:2015 - Medical device usability engineering
- FDA Human Factors Guidance
- AAMI HE75 - Human Factors Engineering Guidelines
