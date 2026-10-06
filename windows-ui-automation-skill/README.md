# Windows UI Automation Skill

Let Claude drive the UI of **any Windows desktop app that has no API** — ERP systems, Delphi/VB/PowerBuilder legacy software, install wizards, accounting/MES/inventory apps, any window program.

Claude **"sees" via screenshots** and **"acts" via pywinauto + screen coordinates**, driven from Mac/Linux over **SSH + PsExec** against a target Windows machine (physical or Parallels/VMware VM).

Forged in production (2026-10) while fully automating monthly accounts-payable voucher entry in a Delphi-based ERP — including the hardest part: a self-drawn data grid with no accessible control tree.

## When to use

- Target program has **no API**, or writing to its DB would break internal logic (e.g. ERP posting/validation) — UI is the only safe path.
- Legacy Delphi / VB / PowerBuilder / old Win32 apps whose control tree is incomplete (self-drawn grids, custom controls).
- Repetitive UI chores: monthly voucher entry, batch data entry, install wizards, settings pages.
- Recording an automation **demo video** for colleagues/management.

## How it works

```
Mac/Linux (Claude) --SSH--> Windows --PsExec -i 1 -u <user>--> python + pywinauto --> target app
                   <--screenshot (base64)--
```

Core loop: **screenshot → Claude decides → click/type → screenshot again.** Just like a person at the keyboard.

## Files

| File | Contents |
|------|----------|
| `SKILL.md` | Architecture, core loop, quick template, 8 golden rules |
| `references/setup.md` | One-time setup: OpenSSH, python, pywinauto, Pillow, PsExec, permissions |
| `references/techniques.md` | Dynamic control location, self-drawn grids, Chinese input, dialogs, maximize-for-fixed-coords |
| `references/recording.md` | Screen recording with ffmpeg (even-dimension fix, orphan-process guard) |
| `references/pitfalls.md` | 20+ battle-tested pitfalls and fixes |

## Quick start

1. Follow `references/setup.md` on the target Windows (OpenSSH + python + pywinauto + Pillow + PsExec).
2. Make sure the target user is **logged into the Windows desktop** (PsExec `-i 1` needs an interactive session).
3. Write a python script using the templates in `SKILL.md` / `references/techniques.md`.
4. Run it: `PsExec64.exe -accepteula -i 1 -u <user> -p <pwd> python your_script.py`.

## Golden rules (read these first — saves hours)

- Control IDs change every launch → **locate dynamically** (class + nearby label + relative coords), never hard-code.
- Self-drawn grids → **`window.maximize()` first** so all fields show at once and coordinates stay fixed.
- Jump fields with **`{ENTER}`, not `{TAB}`** (legacy apps mis-route Tab).
- Chinese/CJK input → **`pyperclip.copy` + `send_keys("^v")`** (type_keys can't type CJK).
- **Clear modal dialogs after every step**, or they stack and block you.
- **Screenshot-verify after each key action**; never fire blind sequences.
- **Destructive actions (save/submit/delete) stay human-gated** — script fills, person reviews & commits.

## Credentials & security

This skill contains **no real credentials, IPs, hostnames, or company data** — all placeholders (`<HOST>`, `<USER>`, `<TOOLS>`). Keep your secrets in your own machine's env/config, never in scripts. Claude's safety classifier also blocks "use the user's credentials to call an external API on their behalf."

## License

MIT
