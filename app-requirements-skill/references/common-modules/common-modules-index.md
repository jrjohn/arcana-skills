# Common Modules Index

**Required modules** definition for all App projects. These modules are loaded first during smart prediction to ensure basic functionality is complete.

---

## Required Modules List

| Module | Code | Necessity | Minimum Screens | Description |
|--------|------|-----------|-----------------|-------------|
| Authentication Module | AUTH | **Required** | 3 | Login, Register, Forgot Password |
| Profile Module | PROFILE | **Required** | 2 | View, Edit Profile |
| Settings Module | SETTING | **Required** | 4 | Main, Account, Privacy, About |
| Common States Module | COMMON | **Required** | 4 | loading, empty, error, no-network |

---

## Template File Index

| Template File | Description | Content |
|---------------|-------------|---------|
| `auth-module-template.md` | AUTH Module | 8 standard screen definitions |
| `profile-module-template.md` | PROFILE Module | 3 standard screen definitions |
| `setting-module-template.md` | SETTING Module | 18 standard screen definitions |
| `common-states-template.md` | COMMON Module | 5 state screen definitions |

---

## Smart Prediction Priority Order

```
1️⃣ Required Modules (common-modules/)
   └── AUTH, PROFILE, SETTING, COMMON

2️⃣ App Type Requirements (auto-loaded by keywords)
   ├── education-requirements.md
   ├── ecommerce-requirements.md
   ├── social-requirements.md
   ├── healthcare-requirements.md
   └── productivity-requirements.md

3️⃣ Button Navigation Analysis
   └── Navigation gap auto-detection

4️⃣ Naming Convention Inference
   └── Detail pages, Edit pages, Confirmation pages
```

---

## Required Module Validation Script

```bash
#!/bin/bash
# === Required Module Validation (BLOCKING) ===
# Execution timing: After Step 4 Smart Prediction completion

REQUIRED_MODULES=("AUTH" "PROFILE" "SETTING" "COMMON")
SDD_FILE="02-design/SDD-*.md"

echo "🔍 Validating required modules..."

ERRORS=0
for MODULE in "${REQUIRED_MODULES[@]}"; do
  COUNT=$(grep -c "^#### SCR-${MODULE}-" $SDD_FILE 2>/dev/null || echo "0")
  if [ "$COUNT" -eq 0 ]; then
    echo "❌ Missing required module: $MODULE"
    ERRORS=$((ERRORS+1))
  else
    echo "✅ $MODULE: $COUNT screens"
  fi
done

# COMMON state screens special validation
echo ""
echo "🔍 Validating COMMON state screens..."
COMMON_STATES=("loading" "empty" "error" "no-network")
for STATE in "${COMMON_STATES[@]}"; do
  if grep -q "SCR-COMMON-.*-${STATE}" $SDD_FILE 2>/dev/null; then
    echo "✅ COMMON state: $STATE"
  else
    echo "❌ Missing COMMON state: $STATE"
    ERRORS=$((ERRORS+1))
  fi
done

echo ""
if [ $ERRORS -eq 0 ]; then
  echo "✅ Required module validation passed"
else
  echo "❌ Required module validation failed ($ERRORS errors)"
  echo "⚠️ Please refer to common-modules/ templates to add missing modules"
  exit 1
fi
```

---

## Required Module Minimum Requirements

### AUTH Module Minimum Requirements (3 screens)

| Required | Screen ID | Name |
|----------|-----------|------|
| ✅ | SCR-AUTH-*-login | Login |
| ✅ | SCR-AUTH-*-register | Register |
| ✅ | SCR-AUTH-*-forgot | Forgot Password |

### PROFILE Module Minimum Requirements (2 screens)

| Required | Screen ID | Name |
|----------|-----------|------|
| ✅ | SCR-PROFILE-*-view | Profile View |
| ✅ | SCR-PROFILE-*-edit | Profile Edit |

### SETTING Module Minimum Requirements (4 screens)

| Required | Screen ID | Name |
|----------|-----------|------|
| ✅ | SCR-SETTING-*-main | Settings Main |
| ✅ | SCR-SETTING-*-account | Account Settings |
| ✅ | SCR-SETTING-*-privacy | Privacy Settings |
| ✅ | SCR-SETTING-*-about | About |

### COMMON Module Minimum Requirements (4 screens)

| Required | Screen ID | Name |
|----------|-----------|------|
| ✅ | SCR-COMMON-*-loading | Loading State |
| ✅ | SCR-COMMON-*-empty | Empty State |
| ✅ | SCR-COMMON-*-error | Error State |
| ✅ | SCR-COMMON-*-no-network | No Network State |

---

## Usage Instructions

### During SDD Writing

1. Load `common-modules-index.md` first to confirm required modules
2. Copy corresponding module template to SDD
3. Adjust screen details based on project requirements
4. Execute validation script to confirm completeness

### During UI Flow Generation

1. `app-uiux-designer.skill` automatically copies HTML from `templates/common-modules/`
2. Adjust navigation based on SDD Button Navigation
3. Execute Template Compliance Gate validation
