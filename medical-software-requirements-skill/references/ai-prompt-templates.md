# AI Prompt Template Library

Complete AI image generation prompt templates, suitable for use in Midjourney, DALL-E, Stable Diffusion, etc.

## Directory
1. [App Icon Prompts](#app-icon-prompts)
2. [UI Screen Prompts](#ui-screen-prompts)
3. [Illustration Prompts](#illustration-prompts)
4. [Background Image Prompts](#background-image-prompts)
5. [Prompt Structure Guide](#prompt-structure-guide)

---

## App Icon Prompts

### Medical Healthcare Category

```
Professional medical healthcare app icon,
minimalist heart with pulse line design,
inside a rounded shield shape,
primary color #2196F3 (blue),
secondary color #FFFFFF (white),
clean flat design style,
no text no letters,
1024x1024 resolution,
centered composition,
suitable for iOS and Android app stores
```

```
Modern healthcare app icon,
stethoscope forming a circular shape,
gradient from #1976D2 to #42A5F5,
white highlights,
subtle 3D effect,
medical professional aesthetic,
no text,
1024x1024
```

```
Telemedicine app icon design,
abstract person with medical cross,
teal #009688 and white color scheme,
minimalist geometric style,
rounded corners,
friendly and trustworthy,
no text,
1024x1024
```

### Fitness Activity Category

```
Fitness tracking app icon,
dynamic running figure silhouette,
gradient orange #FF5722 to yellow #FFC107,
motion blur effect,
energetic and active,
no text,
1024x1024
```

### Finance Business Category

```
Finance banking app icon,
abstract coin or currency symbol,
gradient from #1E88E5 to #42A5F5,
secure and professional appearance,
minimal geometric design,
no text,
1024x1024
```

### Education Learning Category

```
Educational learning app icon,
open book with lightbulb above,
friendly blue #2196F3 color,
flat illustration style,
knowledge and wisdom concept,
no text,
1024x1024
```

---

## UI Screen Prompts

### Login Screen

```
Mobile app login screen UI/UX design,
modern minimal style,
top: company logo placeholder,
center: email and password input fields,
primary action button "Sign In",
social login options (Google, Apple),
bottom: forgot password and sign up links,
blue #2196F3 accent color,
white background,
iPhone 14 Pro frame,
high fidelity mockup
```

### Dashboard

```
Mobile dashboard home screen design,
healthcare patient management app,
top: greeting "Good morning, Dr. Smith" with avatar,
stats cards row: patients, appointments, alerts,
upcoming appointments list section,
quick action buttons grid,
bottom navigation bar,
clean white and blue color scheme,
Material Design style,
realistic UI mockup
```

### Data List

```
Mobile list view screen design,
patient records list,
search bar at top,
filter chips below search,
list items with: avatar, name, ID, status badge,
pull to refresh indicator,
floating action button (FAB) bottom right,
white background with subtle dividers,
iOS style
```

### Detail Data Page

```
Mobile detail screen UI design,
patient profile page,
top: large profile photo with name,
info section: age, gender, blood type, allergies,
tabs: Overview, History, Documents,
vital signs chart,
action buttons: Call, Message, Schedule,
modern healthcare app aesthetic
```

---

## Illustration Prompts

### Empty State Illustration

```
Flat illustration for empty state,
character looking at empty clipboard or folder,
blue and gray muted colors,
friendly cartoon style,
subtle shadow,
"no data" or "no results" concept,
transparent or white background,
400x400 size
```

```
Minimal line illustration,
magnifying glass finding nothing,
light blue #64B5F6 single color,
simple stroke design,
empty search results concept,
vector style,
transparent background
```

### Success State Illustration

```
Celebration illustration,
checkmark inside circle with confetti,
green #4CAF50 primary color,
happy successful completion concept,
flat design with subtle gradients,
transparent background,
300x300 size
```

### Error State Illustration

```
Error state illustration,
confused character with warning sign,
red #F44336 accent color,
friendly not scary,
problem or issue concept,
flat illustration style,
transparent background,
400x400
```

### Onboarding Illustration

```
Mobile app onboarding illustration,
doctor using tablet device,
patient health monitoring concept,
blue and teal color scheme,
modern flat illustration style,
medical healthcare theme,
friendly and approachable,
600x400 size
```

```
Onboarding illustration slide 2,
connected devices concept,
smartphone, smartwatch, health sensors,
data flowing between devices,
gradient blue background,
tech-forward illustration style,
600x400
```

---

## Background Image Prompts

### Login Background

```
Abstract gradient background for mobile app,
soft blue #E3F2FD to white gradient,
subtle geometric patterns,
medical healthcare theme,
professional and calming,
1080x1920 mobile resolution,
can have UI elements overlaid
```

### Dashboard Background

```
Subtle pattern background,
light gray #F5F5F5 base,
very subtle hexagon or grid pattern,
minimal and clean,
dashboard background texture,
tileable seamless pattern,
professional aesthetic
```

### Professional Medical Background

```
Healthcare medical background image,
blurred hospital corridor or clinic,
soft blue tint,
very subtle and muted,
bokeh light effects,
can overlay text and UI,
1920x1080 or larger
```

---

## Prompt Structure Guide

### Basic Structure

```
[Subject Description], [Style Description], [Color Description], [Technical Specifications]
```

### Detailed Structure

```
[What] What is it
[Style] What style
[Color] What color
[Mood] What atmosphere
[Technical] Technical specifications
[Negative] What to exclude
```

### Example Breakdown

```
Professional medical healthcare app icon,     ← What
minimalist flat design style,                  ← Style
blue #2196F3 and white color scheme,          ← Color
clean and trustworthy appearance,              ← Mood
1024x1024 resolution,                          ← Technical
no text no letters no words                    ← Negative
```

---

## Tool-Specific Syntax

### Midjourney

```
/imagine prompt: [your prompt] --ar 1:1 --v 6 --style raw

Parameter Description:
--ar 1:1    Aspect ratio (1:1 square, 16:9 landscape)
--v 6       Version 6
--style raw Less AI style transformation
--no text   Exclude text
--q 2       High quality
```

### DALL-E 3

```
Direct description is fine, DALL-E 3 understands natural language
Recommended additions:
- Clear size: "1024x1024"
- Exclude items: "no text, no watermarks"
- Style specification: "flat design", "vector style"
```

### Stable Diffusion

```
Prompt: [positive description]
Negative Prompt: text, letters, words, watermark, signature, blurry, low quality

Recommended Parameters:
- Steps: 30-50
- CFG Scale: 7-12
- Sampler: DPM++ 2M Karras
```

---

## Medical-Specific Prompt Library

### Clinical Icons

```
Medical vital signs icon set,
heart rate, blood pressure, temperature, SpO2,
line icon style,
2px stroke weight,
single color [#2196F3 or #424242],
24x24 size each,
medical dashboard icons,
transparent background
```

### Medical Specialty Icons

```
Medical specialty icons set,
cardiology (heart), neurology (brain),
orthopedics (bone), pediatrics (child),
dermatology (skin), ophthalmology (eye),
filled icon style,
consistent rounded design,
medical blue color,
32x32 each
```

### Medical Devices

```
Medical device illustration,
[blood pressure monitor/glucose meter/thermometer/pulse oximeter],
isometric 3D style,
soft shadows,
white background,
product illustration style,
300x300 size
```

---

## Prompt Best Practices

### DO ✓

1. **Specific Description** - "heart with pulse line" instead of "heart"
2. **Specify Color** - Use hex code "#2196F3"
3. **Specify Size** - "1024x1024 resolution"
4. **Specify Style** - "flat design", "Material Design"
5. **Exclude Text** - "no text, no letters"
6. **Specify Purpose** - "for iOS and Android app stores"

### DON'T ✗

1. Vague description - "a nice icon"
2. Too many elements - describing too many things at once
3. Contradictory commands - "minimal but detailed"
4. Ignore size - let AI decide by itself
5. Require text - App icons should not have text

### Iterative Optimization

1. First generate foundation version
2. Observe results, adjust prompt
3. Add/reduce details
4. Adjust style keywords
5. Try different tools to compare results
