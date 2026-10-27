# 操作技巧

## 1. 找視窗 / 控件（動態定位，別寫死 id）

```python
from pywinauto import Desktop
# 用 class name 開頭比對(比 title 穩,title 常帶變動內容)
win = next(w for w in Desktop(backend='win32').windows()
           if w.class_name().startswith('TfrmMain'))
```

**⚠️ 控件 control_id 每次重開程式/重開單會變** → 不要寫死。改用「相對螢幕座標 + 旁邊 label」動態找:

```python
def find_edit(win, relx, rely, tol=40):
    """找最接近(視窗內相對座標 relx,rely)的可見輸入框"""
    r0 = win.rectangle(); best=None; bd=9999
    for c in win.descendants():
        if 'Edit' not in c.class_name() or not c.is_visible(): continue
        try: r = c.rectangle()
        except: continue
        dx=abs((r.left-r0.left)-relx); dy=abs((r.top-r0.top)-rely)
        if dx+dy<bd and dx<tol and dy<18: bd=dx+dy; best=c
    return best
```

## 2. 一般欄位輸入（控件層，最穩）

```python
field.set_focus()
field.type_keys("{END}+{HOME}{DEL}新值{ENTER}", set_foreground=True, pause=0.08)
# {END}+{HOME}{DEL} = 全選清空再打(比 ^a 穩)
```

## 3. 自繪表格/grid（沒有獨立控件的格子）

**關鍵: 先把視窗最大化**,讓所有欄位+多列一次顯示 → 座標固定不漂移:
```python
win.maximize(); time.sleep(1.3)
r0 = win.rectangle()
def clk(x,y): mouse.click(coords=(r0.left+x, r0.top+y)); time.sleep(0.5)
```
- **進格子: 單擊**(`mouse.click`)。**雙擊常會誤觸該欄的查詢/F2 彈窗**。
- **填值: 單擊後直接 `send_keys`**(全域鍵盤)。空格直接打;**要改既有值先 `{END}{BACKSPACE n}` 清空**(單擊進格子不會自動全選)。
- **下拉欄: 打代號即可**(例 grid 的下拉,打 `9` 會跳到代號 9 的項)。
- **跳下一欄/列**: 看系統脾氣 — 多數舊系統 **`{ENTER}` 可靠**(跳到下一個要填欄),`{TAB}` 會亂跳/跳過唯讀欄。換列常用 `{DOWN}`(在最後一列會自動新增)或工具列「新增列」。
- 每填一欄後 `clk` 下一格,別連續盲打。

## 4. 中文輸入（type_keys 打不了中文）

```python
import pyperclip
pyperclip.copy("要貼的中文")
field.set_focus()
send_keys("{END}+{HOME}{DEL}", pause=0.05)   # 清空
send_keys("^v", pause=0.1)                    # 貼上
```

## 5. 自繪工具列按鈕（沒 HWND，UIA 也讀不到名字）

截圖認位置 → 用「視窗尺寸比例」算座標點 + **驗證是否生效,沒生效重點**:
```python
for attempt in range(4):
    win.set_focus()
    r0=win.rectangle(); ww=r0.right-r0.left; wh=r0.bottom-r0.top
    # 例: 新增鈕在截圖(1127x694)的(22,67) → 按比例換算
    mouse.click(coords=(r0.left+int(22*ww/1127), r0.top+int(67*wh/694))); time.sleep(2.5)
    # 驗證: 進新增模式?(例如某日期欄被自動帶出今天)
    if <某欄位出現預期值>: break
```

## 6. 對話框處理（每步都要清）

舊系統操作常彈確認/錯誤框,卡住不處理 → 後續全失敗,甚至**堆疊**:
```python
def clear_modal(prefer='Cancel'):
    for _ in range(6):
        hit=None
        for w in Desktop(backend='win32').windows():
            try:
                if not w.is_visible(): continue
                yes=[c for c in w.descendants() if c.window_text() in ('OK','&OK','Yes','&Yes','是(&Y)','確定')]
                no =[c for c in w.descendants() if c.window_text() in ('Cancel','&Cancel','No','&No','否(&N)')]
                if yes and no:
                    names = yes if prefer=='OK' else no
                    hit=names[0]; break
            except: pass
        if not hit: break
        hit.click_input(); time.sleep(0.8)
```
- 破壞性詢問(如「是否過帳/送出」)可針對框內文字判斷 → 按「否」避免誤執行。

## 7. 截圖回傳（給 Claude 看）

Windows: `win.capture_as_image().save(r'<TOOLS>\shot.png')`(需 Pillow)。
傳回 Mac: PowerShell `[Convert]::ToBase64String([IO.File]::ReadAllBytes('shot.png'))` → SSH 取 →
**Mac 端一律用 python 解 base64**(`import base64; open('x.png','wb').write(base64.b64decode(data))`)。
⚠️ **別用 `base64 -d` + `tr`/`awk` 處理混中文的輸出** — macOS 會 `illegal byte sequence`。
log 與圖一起傳時用純 ASCII 分隔符(如 `===SPLIT===`),兩邊各自 base64。

## 8. 破壞性動作把關

填完資料**停在畫面不要自動存檔/送出**,讓使用者檢查後自己按。真要自動存,也把「送出/過帳」留給人。
