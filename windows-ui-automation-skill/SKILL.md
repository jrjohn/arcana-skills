---
name: windows-ui-automation-skill
description: >-
  讓 Claude 自動控制 Windows 桌面程式的 UI（點擊、輸入、讀畫面、錄影）——適用任何「沒有 API」的程式:
  ERP、Delphi/VB/PowerBuilder 舊系統、安裝精靈、會計/MES/進銷存軟體、任何視窗 app。
  從 Mac/Linux 透過 SSH + PsExec + pywinauto 操作目標 Windows（實體機或 Parallels/VMware VM），
  用「截圖」當眼睛、「pywinauto + 座標」當手。2026-10 在某 Delphi 架構 ERP 的應付憑單全自動建單實戰淬煉。
  關鍵字: Windows automation, UI 自動化, pywinauto, PsExec, 無 API, 遠端桌面控制, RPA, 螢幕錄影 ffmpeg。
---

# Windows UI 自動化 — 讓 Claude 像人一樣操作任何 Windows 程式

**核心理念**: 很多企業軟體（ERP、舊系統）沒有 API，只能用滑鼠鍵盤操作。這個 skill 讓 Claude
**看畫面 → 判斷 → 點/打字 → 再看**，就像真人坐在電腦前，自動完成重複的 UI 工作。

## 什麼時候用

- 目標程式**沒有 API / 資料庫寫入會破壞邏輯**（例: ERP 過帳檢核），只能走 UI。
- Delphi / VB / PowerBuilder / 老舊 Win32 程式，控件樹讀不完整（自繪 grid、自訂控件）。
- 重複性 UI 工作: 每月建單、批次輸入、安裝精靈、設定頁點選。
- 要**錄影 demo**（給同事/主管看自動化流程）。

## 架構（一張圖看懂）

```
Mac/Linux (Claude Code)
   │  1. SSH 下指令
   ▼
Windows (實體機 or Parallels/VMware VM)   ← sshd (OpenSSH)
   │  2. PsExec -i 1 -u <桌面使用者>  跳進「互動桌面 session」
   ▼
python + pywinauto  (在使用者桌面跑，滑鼠/鍵盤才有效)
   │  3. 操作目標 app（click / type / 讀控件）
   ▼
目標 Windows 程式
   │  4. 截圖 → base64 → SSH 傳回 Mac → Claude「看」
   └──────────────────────────────────────────►
```

## 為什麼非得這樣架（血淚重點）

| 設計 | 原因 |
|---|---|
| **PsExec `-i 1 -u <user>`** 跑 python | SSH session 是**非互動**的,看不到 GUI 視窗;而且**用 system 身分的滑鼠點擊會被 Windows 擋**(跨 session 隔離)。必須以**登入桌面那個使用者的身分**、進 session 1,滑鼠/鍵盤才作用。前提: 那個使用者要**已登入桌面**。 |
| **截圖當眼睛** | 控件樹(pywinauto win32 / UIA)對**自繪控件**(Delphi 自繪 grid、遊戲、Canvas)讀不到內容。截圖+視覺判斷最通用,任何畫面都能看。 |
| **鍵盤用控件層 `type_keys`,滑鼠用 `mouse.click` 座標** | 一般欄位用 `control.type_keys()`(綁控件,穩);自繪 grid 的格子沒有獨立控件,只能算**螢幕座標**點。 |

## 核心操作循環（最小範本）

```python
# 在 Windows 上跑: PsExec64 -accepteula -i 1 -u <user> -p <pwd> python this.py
from pywinauto import Desktop, mouse
from pywinauto.keyboard import send_keys
import io, base64

# 找目標視窗(用 class name 開頭比對,比 title 穩)
win = next(w for w in Desktop(backend='win32').windows()
           if w.class_name().startswith('TfrmMain'))
win.set_focus()

# 讀控件 / 點按鈕 / 輸入
field = next(c for c in win.descendants() if c.control_id()==12345)
field.type_keys("{END}+{HOME}{DEL}要輸入的值{ENTER}", set_foreground=True)
mouse.click(coords=(x, y))          # 自繪控件用座標
send_keys("^s")                     # 快捷鍵

# 截圖回傳(給 Claude 看)
img = win.capture_as_image()        # 需裝 Pillow
img.save(r'C:\tmp\shot.png')
```

截圖傳回 Mac: PowerShell `[Convert]::ToBase64String([IO.File]::ReadAllBytes('shot.png'))`
→ SSH 取回 → Mac `python3 -c "import base64; open('shot.png','wb').write(base64.b64decode(...))"`
→ Claude 用 Read 工具看圖判斷下一步。

## 細節在 references/

| 檔案 | 內容 |
|---|---|
| `references/setup.md` | 一次性環境設置: OpenSSH、python、pywinauto、Pillow、PsExec、權限(SmartScreen/comtypes) |
| `references/techniques.md` | 操作技巧: 控件動態定位、自繪 grid、中文輸入、對話框處理、最大化固定座標、Enter vs Tab |
| `references/recording.md` | 螢幕錄影(ffmpeg gdigrab): 補偶數、孤兒防護 |
| `references/pitfalls.md` | 踩過的坑: SSH 不穩、PsExec RPC、冷啟動 timeout、InvalidWindowHandle、座標漂移 |

## 黃金守則（先讀這幾條省幾小時）

1. **控件 id 每次重開會變** → 絕不寫死 id,用「class + 旁邊 label + 相對座標 + tab 順序」動態定位。
2. **自繪 grid/多欄位** → 先 `win.maximize()`,讓所有欄位一次顯示、座標固定,再用絕對座標點(解決左右上下捲動)。
3. **跳欄用 `{ENTER}` 不要 `{TAB}`** → 很多舊系統 Tab 會亂跳/跳過唯讀欄。
4. **中文輸入 `type_keys` 打不了** → 用 `pyperclip.copy(中文)` + `send_keys("^v")` 貼上。
5. **每步可能彈對話框** → 操作後都要偵測+清掉 modal(OK/Cancel),否則卡住後續。
6. **每個關鍵動作後截圖驗證**,不要盲目連續操作(座標可能偏、值可能沒進)。
7. **破壞性動作(存檔/送出/刪除)要人工把關** → 腳本填完「停住不存」,讓使用者檢查後自己按。
8. **SSH 不穩時**: 傳檔用 `scp`(比 ssh exec 穩)、指令用 `cmd` 比 powershell 輕、長任務用 `PsExec -d` 背景跑 + `run_in_background` 輪詢等完成。
