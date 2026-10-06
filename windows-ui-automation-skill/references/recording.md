# 螢幕錄影（錄 demo 給人看）

目的: 把 Claude 自動操作的全程錄成影片。**首選 ffmpeg**(高效、CPU 低、錄全桌面跨視窗沒問題)。

## 工具比較（實測）

| 方式 | CPU | 跨視窗 | 結論 |
|---|---|---|---|
| **ffmpeg gdigrab** | 低(C 優化) | ✅ 錄整個桌面 | **首選** |
| Xbox Game Bar(Win+Alt+R) | 低(GPU) | ❌ 只錄單一 app,切視窗會跟丟 | 不適合多視窗流程 |
| python mss + opencv 逐幀 | 高(軟體編碼) | ✅ | 吃 CPU、慢,已棄 |

## ffmpeg 安裝

下載 gyan.dev essentials build,解壓取 `ffmpeg.exe` 放 `<TOOLS>`。

## 錄影命令（⚠️ 兩個必加的參數）

```
ffmpeg -y -t 180 -f gdigrab -framerate 8 -i desktop \
       -vf scale=trunc(iw/2)*2:trunc(ih/2)*2 \
       -c:v libx264 -preset ultrafast -pix_fmt yuv420p demo.mp4
```

| 參數 | 為什麼**非加不可** |
|---|---|
| `-vf scale=trunc(iw/2)*2:trunc(ih/2)*2` | **桌面寬或高是奇數時**(例 1920x**937**),libx264 + yuv420p 要求偶數,否則 `Error while opening encoder` + **輸出 0 bytes**。這行自動把寬高補成偶數。 |
| `-t 180` | ffmpeg 若變**孤兒進程**(python 掛了沒收它)會**吃滿 CPU 一直錄,卡死整台**(連 SSH 都 banner timeout)。`-t` 設上限讓它最長錄 N 秒自停。 |

## python 包裝（邊操作邊錄）

```python
import subprocess
FF=None
def start_record(video):
    global FF
    FF=subprocess.Popen([r'<TOOLS>\ffmpeg.exe','-y','-t','180','-f','gdigrab',
        '-framerate','8','-i','desktop','-vf','scale=trunc(iw/2)*2:trunc(ih/2)*2',
        '-c:v','libx264','-preset','ultrafast','-pix_fmt','yuv420p',video],
        stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
def stop_record():
    if FF:
        try: FF.communicate(input=b'q', timeout=15)   # 送 'q' 讓 ffmpeg 正常收尾(寫完 moov)
        except: FF.terminate()

# 主流程
start_record(r'<TOOLS>\demo.mp4')
time.sleep(2)
do_automation()        # 你的操作
stop_record()
```

## 收尾（避免孤兒卡機）

- 操作結束**務必** `stop_record()`;即使中途失敗也要在 `finally` 裡呼叫。
- 保險: 每次重跑前先 `taskkill /F /IM ffmpeg.exe`(+ python)清殘留。
- 診斷 0 bytes: 把 stderr 導到檔案看(`... 2> err.txt`),常見就是上面的奇數尺寸。

## 傳影片回來

用 `scp` 取回(影片大,scp 比 base64 穩):
`scp <USER>@<HOST>:C:/path/demo.mp4 ./demo.mp4`
