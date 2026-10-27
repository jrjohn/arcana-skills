# 踩過的坑（省你幾小時）

## 滑鼠 / session

| 坑 | 症狀 | 解法 |
|---|---|---|
| **system 身分滑鼠被擋** | `PsExec -i 1 -s`(system)跑,`type_keys` 可以但 `mouse.click` 沒反應 | 必須 `-u <桌面使用者>`(非 system),滑鼠才作用 |
| **使用者沒登入桌面** | `PsExec -i 1` 沒 GUI 可操作 | 目標使用者要先登入 Windows 桌面(鎖定畫面 OK) |
| **App Store 版虛擬機鎖 exec** | Parallels App Store 版 `prlctl exec` 不能用 | 只走 SSH + PsExec |

## 控件 / 座標

| 坑 | 症狀 | 解法 |
|---|---|---|
| **control_id 每次變** | 寫死 id 下次跑找不到 | 動態定位(class+相對座標+label),見 techniques.md |
| **座標左右上下漂移** | 多欄位/多列 grid 點歪、改錯格 | **先 `win.maximize()`** 讓全部一次顯示、座標固定 |
| **自繪 cell editor 隱藏** | `type_keys` 報 `ElementNotVisible` | 不走控件,用螢幕座標單擊進格子 + `send_keys` |
| **`Desktop().windows()` 枚舉當掉** | `InvalidWindowHandle: Handle N is not a valid window handle`(枚舉時某視窗正在關閉,如啟動 splash 閃現) | 枚舉包 try: `try: wins=Desktop(...).windows() except: wins=[]`,找不到就重試 |
| **Tab 亂跳** | 在舊系統用 `{TAB}` 跳欄,跳過欄位或亂序 | 改用 `{ENTER}`;grid 換列用 `{DOWN}` |

## 啟動 / 時機

| 坑 | 症狀 | 解法 |
|---|---|---|
| **冷啟動/重開機後很慢** | 等視窗的 timeout 太短 → 其實晚幾秒就開了卻判失敗 | timeout 加長(登入視窗 70s、主選單 35s、作業視窗 50s);VM 尤其慢 |
| **啟動捷徑對中文路徑不可靠** | `cmd start "" "中文.lnk"` 沒反應 | 用 `os.startfile(r'...中文.lnk')` |

## SSH / PsExec 連線

| 坑 | 症狀 | 解法 |
|---|---|---|
| **ssh exec 間歇失敗** | `exec request failed on channel 0` / `banner timeout`(VM 負載高或重開機後 sshd 不穩) | 傳檔用 `scp`;指令用 `cmd /c` 比 PowerShell 輕;長任務 `PsExec -d` 背景跑;用 `run_in_background` + `until ssh echo; do sleep 6; done` 等穩 |
| **長任務卡住 SSH channel** | `ssh "PsExec python 跑3分鐘"` 中途斷線 | `PsExec -d`(背景啟動立即返回)+ 另外 `run_in_background` 輪詢 log 檔等「完成」標記 |
| **PsExec 第一次 RPC 失敗** | 重開機後首次 `Couldn't install PSEXESVC service` | 通常重試即成(服務裝好後 OK) |
| **孤兒進程卡死整台 VM** | python/ffmpeg 殘留吃滿 CPU,連 SSH 都連不進 | 每次重跑前 `taskkill /F /IM python.exe /IM ffmpeg.exe`;ffmpeg 一定要 `-t` 上限 |

## 編碼 / 讀取

| 坑 | 症狀 | 解法 |
|---|---|---|
| **Mac 解 base64 遇中文爆** | `tr: illegal byte sequence` / `awk: multibyte` | Mac 端一律用 `python3 base64.b64decode`,別用 `base64 -d`+`tr`/`awk`/`sed` 處理含中文的輸出 |
| **PowerShell 中文指令亂碼** | 直接送中文指令變亂碼 | `powershell -NoProfile -EncodedCommand <UTF-16LE base64>` |
| **log+圖混傳切壞** | 兩者黏一起無法分離 | 用 ASCII 分隔符 `===SPLIT===`,log 與圖各自 base64 |

## 安全 / 權限（見 setup.md 第 4 節）

- SmartScreen / Smart App Control 擋無簽章程式 → **使用者本人**去 Windows 安全性關(Claude classifier 會擋「用程式關防護」)。
- comtypes gen 無寫入權限 → `icacls ... /grant Users:(OI)(CI)M`。
- **憑證/密碼**: 放在使用者自己的機器環境變數或設定檔,**不要寫進腳本或 skill**;Claude classifier 也會擋「代替使用者拿憑證呼叫外部 API」。
