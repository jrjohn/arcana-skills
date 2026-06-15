# SonataFlow setup（Phase 0 recon 沉澱，2026-05-29）

## 版本（鎖版，避免 SWF DSL churn）
- **目標 = Apache KIE 10.1.0-incubating**（2025-07 最新 stable；備選 10.0.0）。
- 映像在 Docker Hub `apache/incubator-kie-*`：
  - `apache/incubator-kie-sonataflow-devmode:10.0.0`（dev，hot-reload，in-memory）
  - `apache/incubator-kie-sonataflow-builder:10.0.0`（build 出 production Quarkus app image）
  - `apache/incubator-kie-sonataflow-operator`（**K8s only — 不用**，bluesea 無 K8s）
- SWF DSL 版本跟著該 release 鎖；workflow 定義檔放 `src/main/resources/`。

## 部署形式（全 Docker，無 K8s）
- **Phase 1 MVP**：`sonataflow-devmode` 映像 + docker-compose，bind-mount workflow resources：
  ```
  docker run -p 8080:8080 \
    -v <resources>:/home/kogito/serverless-workflow-project/src/main/resources \
    apache/incubator-kie-sonataflow-devmode:10.0.0
  ```
  devmode = in-memory process store，hot-reload workflow，HTTP CloudEvent 入口內建 → 快速證明 event→workflow→agent→report。
- **Phase 2+**：跨時間 wait-for-event correlation 需持久化 → 用 `builder` 出 Quarkus app image，配 **PostgreSQL** process store。

## 事件入口
- 單機先用 **HTTP CloudEvent**（Jenkins RunListener → `POST` CloudEvent 到 SonataFlow）。免 Kafka。
- 量大 / 要 durable replay 再升 Kafka 或橋既有 Mosquitto MQTT。

## bluesea 主機 recon（headroom 足）
- Mem：23Gi total，**~15Gi available**（大戶 sonarqube 1.6G / jenkins 1.1G / ollama 982M / nexus 841M）。Swap 已用 2.1G → 略有壓力 → SonataFlow 傾向 **Quarkus native build** 壓低 RSS。
- PG：`pg-archive-test`（既有 archive PG，**mem limit 1GiB**）可開新 db `sonataflow` 當 process store；留意 1G 上限，Phase 2 上 PG 時視情況 bump limit 或另起一個 PG 容器。
- Disk：`/data` 47G free → `/data/sonataflow/`。
- 網路：jenkins 與 daily-ci-agent 同在 `devops_default`（已驗證互通）→ SonataFlow + agent-task-node 也掛 `devops_default`。

## ✅ arm64-native build recipe（已驗證可行，2026-05-29）

官方 KIE 映像全 amd64、qemu 在 arm64 不可行（devmode 卡 code-gen 6min+ CPU 狂飆）。**正解 = 從 kogito-examples 基底自建 Quarkus app，用 arm64 maven 容器 build**：

1. `git clone --depth 1 --branch 10.0.x https://github.com/apache/incubator-kie-kogito-examples.git`（10.x 用 **branch** 不是 tag；tag 只到 1.44.x）。基底用 `serverless-workflow-examples/serverless-workflow-greeting-quarkus`（known-good pom：`quarkus-bom:3.8.4` + `kogito-bom:10.0.0` + extension `org.apache.kie.sonataflow:sonataflow-quarkus`）。
2. 換 `src/main/resources/`：放我們的 `*.sw.yaml` + `specs/*.yaml` + `application.properties`。
3. build（**在 examples tree 內**跑，parent relativePath 才解析得到）：
   ```
   docker run --rm --platform linux/arm64 -v <clone>:/work \
     -w /work/serverless-workflow-examples/serverless-workflow-greeting-quarkus \
     -v <m2-cache>:/root/.m2 maven:3.9-eclipse-temurin-17 mvn -B -DskipTests package
   ```
   冷 build ~10-20min（下載 kogito+quarkus 全樹），warm 後快。產出 `target/quarkus-app/quarkus-run.jar`。
4. run：`docker run --platform linux/arm64 --network devops_default -e AGENT_TASK_URL=... -v <target/quarkus-app>:/deployments/quarkus-app eclipse-temurin:17 java -jar /deployments/quarkus-app/quarkus-run.jar`。
   **實測 arm64 boot 3.3s、137MB RSS**（vs qemu 卡死）。Installed features 含 `kogito-serverless-workflow`+`smallrye-openapi`+`resteasy-client`（OpenAPI function 依賴內建）。

> 自建專案要可攜（脫離 examples tree）→ Phase 5 把 pom 攤平成 self-contained（移除 parent relativePath，內聯 quarkus-maven-plugin build 設定 + 兩個 BOM import）。

## ⚠️ SWF DSL 雷（對真引擎 codegen 撞出來的，2026-05-29）

- **沒有 `type: openapi`**：OpenAPI-described REST 服務用 **`type: rest`**，`operation: <spec>.yaml#<operationId>`。寫 openapi 會 `IllegalArgumentException: openapi` on FunctionDefinition["type"]。
- **每個 state 必須可達**：孤兒 state（沒 incoming connection / 連不到 start）→ codegen `Process could not be validated! Node 'X' has no connection to the start node`。MVP 不要留「之後才用」的 state，要用再加。
- **event-start workflow 不能用 plain REST 啟動**：`POST /<workflowId>` 回 `no start node that matches the trigger none`。必須送 **CloudEvent**。
- ✅ **HTTP CloudEvent 入口（已驗證可行）**：`application.properties` 加 `mp.messaging.incoming.<CH>.connector=quarkus-http` + `.path=/jenkins/build`，其中 **`<CH>` = 該 event 的 `type`（不是 name！）**。type 要無點號的 token（如 `ci_build_completed`），否則 property 解析破。啟動 log 看到 `Consumer for <type> started` = wired；POST 結構化 CloudEvent(`Content-Type: application/cloudevents+json`, body 含 `type/source/data`)到 path → HTTP 202 → workflow instance 起、triage(switch)、sysout report **全 e2e 跑通(green path 已實證)**。

## ✅ 已解：OpenAPI rest-function codegen — 缺 `generate-code` goal（2026-06-01 CRACKED）

症狀：工作流呼叫 OpenAPI-described 服務(`operation: <spec>#<opId>`)→ runtime `KogitoWorkItemHandlerNotFoundException for <spec>_<opId>`;build log 只 `Generator discovery [processes]`、open-api-stream 空、沒生 client。

**真因（transplant 測試證明）**：把同一份 spec+function 移植進 working 範例 `service-calls` → 正常生成 → 證明 **spec/workflow 沒問題,是 build skeleton**。Diff `quarkus-maven-plugin` execution goals：
- service-calls(works)：`generate-code` + `generate-code-tests` + `build`
- 我基底的 greeting：**只有 `build`** ← 缺 `generate-code` goal = OpenAPI Generator codegen 根本沒跑。

**排除的 red herring**（都不是）：spec 檔名 hyphen、yaml-vs-json workflow、spec 放 resources/specs/、`servers:` 區塊、function `type` 欄位、function-name==operationId。

**修法（必做）**：自建 Quarkus 專案的 pom，`quarkus-maven-plugin` execution 必須含三個 goal：
```xml
<goals><goal>generate-code</goal><goal>generate-code-tests</goal><goal>build</goal></goals>
```
（greeting 範例只有 `build`，所以**不可拿 greeting 當基底**;用 service-calls 的 pom，或確保自建 pom 有這三 goal。）spec 放 `src/main/resources/`(根)、加 `servers: [{url: http://agent-task-node:8090}]`、function `operation: <spec>.json#<opId>` 無 type 即可。

**rest-client timeout**：生成的 client `@RegisterRestClient(configKey="<specfile_底線>")`（`agentnode.json`→`agentnode_json`）。claude task 分鐘級 → `application.properties` 設 `quarkus.rest-client.agentnode_json.read-timeout=900000`（否則 default ~30s → `SocketTimeoutException`）。

**✅ FULL E2E 證明（2026-06-01）**：CloudEvent → event consumer → triage → Diagnose state → 生成的 openapi rest-client(`Agentnode_diagnose` handler 已註冊) → **agent-task-node 收到 `POST /task/diagnose`**。整條 SonataFlow 編排 + Claude agent-as-node 鏈路打通。(測試時 agent 回 500 是 claude 在假 buildUrl 上跑失敗,非 wiring 問題。)

## ✅ Phase 2 已證明：event correlation + bounded retry（2026-06-01 e2e）

Phase 2 把 Phase 1（diagnose→report）擴成完整維護迴路：`WaitForBuildEvent → Triage → Diagnose → Fix → Verify → Decide →（Report | retry 回 Fix | Escalate）`。三個機制全 e2e 跑通（workflow = `templates/workflows/ci-maintenance.sw.json` v2.0）：

**① Event correlation（等「該 job」的 re-build 事件，不是任何事件）**
- 在 event 定義加 `"correlation": [{"contextAttributeName": "jobref"}]`。`jobref` = CloudEvent 的**頂層 extension attribute**（structured CloudEvent JSON 裡跟 `type`/`source` 同層的 key，不是 `data` 內欄位）。
- 第一個事件（start，走 `WaitForBuildEvent`）綁定該 instance 的 correlation 值；之後 `Verify` event-state（同 event ref）只會被**同 `jobref`** 的事件喚醒。
- **判別實證**：POST event1`{result:FAILURE, jobref:rust-42}` → instance 跑到 Verify 停住；POST event2`{result:SUCCESS, jobref:rust-42}` → log 出 `[ci-maintenance] job=arcana-cloud-rust result=FAILURE verify=SUCCESS retries=1` ── `result=FAILURE` 是 event1 的資料、`verify=SUCCESS` 是 event2，**證明 event2 喚醒了原 instance 而非起新的**（全程只一條 `Starting new process instance`）。correlation 失敗的話會是第二條 `Starting new process instance` + `verify=n/a`。

**② Bounded retry（用 jq 計數，免外部 function 遞增）**
- SWF `inject` state 的 `data` 是**靜態 literal、不 eval jq** → 無法用它遞增 counter。**正解**：在 `Verify` event-state 加 `"stateDataFilter": {"output": "${ . + {retries: ((.retries // 0) + 1)} }"}` —— 每次該 state 收到事件完成時 jq merge 自增 `retries`，保留其餘 state data。
- `Decide` switch：先判 `${ .verify.result == "SUCCESS" }`→Report；再判 `${ .retries < 2 }`→回 `Fix`（retry 回邊）；`defaultCondition`→`Escalate`。回邊 `Decide→Fix` 是合法（reachable），SWF validate 通過、無 orphan。
- **實證**：三連 FAILURE 同 jobref → `Escalate: still RED after 2 verify attempts`（start→retries=1 回 Fix→retries=2 不<2→Escalate）。retry 上限確實生效、不無限迴圈。

**③ Verify 有 SLA 上限**：`Verify` 加 `"timeouts": {"eventTimeout": "PT30M"}` → 等不到 re-build 事件 30 分就逾時往下（Phase 3 把逾時導到真 Escalate/notify）。

**測試隔離技巧 — agent STUB 模式**：Diagnose/Fix 呼叫真 agent（`claude -p` 數分鐘且假 buildUrl 會失敗）會在到 Verify 前拖垮/失敗 instance → 無法乾淨測 correlation。`agent-task-node/server.py` 加 `AGENT_STUB=1` env：`run_claude` 短路回 schema-valid canned JSON（秒回），instance 快速抵達 Verify。correlation/retry 是純編排機制，與 agent 智能正交 → STUB 隔離測最乾淨。production 容器**不帶** `AGENT_STUB`（real claude），STUB 能力保留供 `verify.sh` 自檢。

**部署注意**：sf-ci 容器 bind-mount `target/quarkus-app` → 改 workflow 要**重 build + 重啟 sf-ci**才生效（devmode 才 hot-reload，production jar 不會）。build tree 放**持久路徑 `/data/projects/claude-agents-workflow/build/`**，**別放 `/tmp`**（host /tmp 雖實際存活，但 daily-ci-agent 容器 namespace 的 /tmp 與 host /tmp 是兩個目錄，`docker exec` 進去看會誤判「檔案不見了」—— 全部直接在 host 上操作避免混淆）。

## ✅ Ingestion 改 Kafka（2026-06-01 切換 + e2e durability 證明）

Phase 1-3 用 `quarkus-http` connector(Jenkins HTTP POST 直打 sf-ci)。**問題 = durability gap**:HTTP fire-and-forget,sf-ci 一重啟(每次改 workflow 都要重啟)那段空窗的 build 事件直接遺失,也無事件流可回溯。John 拍板換 Kafka(看重事件可追蹤/replay/審計)。

**架構**:`Jenkins RunListener --HTTP--> ce-kafka-bridge --produce(acks=all)--> Kafka topic ci.build.completed --> smallrye-kafka --> sf-ci`。事件先落進 Kafka(retained log)才被消費 → sf-ci 不在也不丟。

**broker**:`apache/kafka-native:3.9.1`(KRaft,免 Zookeeper,multi-arch arm64,映像 ~50MB,native AOT 低 RSS),單節點 RF=1,持久化 `/data/kafka`,retention 30 天。CLI 腳本 native 映像沒帶 → 用一次性 `apache/kafka:3.9.1`(JVM)容器連 broker 建 topic/管理。

**SonataFlow 端**(pom + properties,**workflow DSL 不動**):
- pom 加 `io.quarkus:quarkus-smallrye-reactive-messaging-kafka`(**Quarkus 3.8.4 BOM 是這個舊 artifactId;`quarkus-messaging-kafka` 是後來改名、3.8 BOM 沒 manage → version missing 報錯**)。
- `application.properties`：
  ```
  mp.messaging.incoming.ci_build_completed.connector=smallrye-kafka
  mp.messaging.incoming.ci_build_completed.topic=ci.build.completed
  mp.messaging.incoming.ci_build_completed.group.id=sf-ci-maintenance
  mp.messaging.incoming.ci_build_completed.auto.offset.reset=earliest
  mp.messaging.incoming.ci_build_completed.value.deserializer=org.apache.kafka.common.serialization.StringDeserializer
  mp.messaging.incoming.ci_build_completed.cloud-events=true
  kafka.bootstrap.servers=kafka:9092
  ```
- **structured CloudEvent over Kafka 免 header**:把 CE JSON 整包當 Kafka message value 即可,kogito 自動解析(不需設 `content-type: application/cloudevents+json` header)。topic 名可含點(`ci.build.completed`),但 **CE `type` 仍必須無點號(`ci_build_completed`)** 才被 consumer 路由。

**✅ DURABILITY 實證**:stop sf-ci → produce 事件(此時 consumer 離線)→ start sf-ci → 該事件被消費(consumer group `sf-ci-maintenance` 從 committed offset / earliest 續讀)。這正是 HTTP 補不了的洞。

**producer = ce-kafka-bridge（Rust + rdkafka）**:
- 為何不直接 Jenkins→Kafka:groovy RunListener 加 kafka-clients 到 classpath 脆弱、侵入。**thin HTTP→Kafka bridge** 讓 groovy 只改 URL,bridge 是 restart-stable 小 infra(不隨 workflow 改動重啟)。
- 為何 Rust 不 Python:常駐永久 sidecar 該選最穩+最小足跡。`kafka-python 2.0.2` 在 **Python 3.12 vendored-six(`kafka.vendor.six.moves`)炸**且本體半棄維護 = 技術債。Rust `rdkafka`(librdkafka,業界黃金標準 client)→ **實測 RSS 1.45MiB**(vs python ~30-50MB / node kafkajs ~50-80MB)。同步 `BaseProducer` + 每請求 `flush(acks=all)` → Jenkins 拿到 202 = broker 已 ack(比舊的 fire-and-forget 強)。免 tokio,deps 最少。multi-stage Dockerfile(`rust:1-bookworm` 裝 cmake+build-essential 給 `cmake-build` feature vendored librdkafka → `debian:bookworm-slim` runtime,需 `libsasl2-2`)。
- 模板:`templates/ce-kafka-bridge/{Cargo.toml,src/main.rs,Dockerfile}`。

**Jenkins groovy(`jenkins-cloudevent.groovy`)修正(部署 = Phase 4 cutover,現未進 production init.groovy.d)**:
- POST 目標 → `http://ce-kafka-bridge:8088/jenkins/build`。
- **CE `type` 從 `ci.build.completed` 改 `ci_build_completed`**(原點號版根本不被 workflow consumer 路由 = 隱性 bug)。
- **加 `jobref` = job fullName**(correlation context attribute;跨原 build 與 re-build 穩定,讓 Verify event-state 等到同一 job 的 re-build)。

## ✅ Phase 4：timer-sweep 取代 cron（2026-06-01，bridge-heartbeat 方案）

目標 = 把舊 OS cron `0 * * * *` 的 monolithic daily-run 換成 observable workflow。

**⚠️ 雷：kogito SWF `start.schedule.cron` 在純 in-memory build 不觸發**。試過 `start: {stateName, schedule:{cron:{expression:"0 * * * * ?"}}}` → build 接受、但**0 instance 被建**。in-flight timer(eventTimeout，Phase 2/3 用的)能動是走 in-VM timer manager;但「**定時 CREATE 新 instance**」需要 **Kogito Job Service**。
- 加 `org.kie:kogito-addons-quarkus-jobs-service-embedded`(注意 groupId 是 **`org.kie`** 不是 org.kie.kogito)→ **boot 直接掛**:`initdb: error: cannot be run as root` + `Failed to start application`。embedded jobs service 預設要起 embedded PostgreSQL(initdb),容器內以 root 跑失敗。要它動得配**外部 PG datasource**(plan 的「Phase 2+ PG process store」那塊)。
- 結論:in-app cron-start = 要 jobs-service + PG。對一條**安全網 sweep** 不值得拖進 PG(過度設計)。

**✅ 採用方案：bridge-heartbeat + event-started sweep workflow**(全用已知可動的機制):
- `ce-kafka-bridge`(Rust)加一個 heartbeat thread(自帶獨立 `BaseProducer`),每 `SWEEP_INTERVAL_SECS` 產一個 `ci_sweep_requested` CloudEvent 到 topic `ci.sweep.requested`。`SWEEP_INTERVAL_SECS=0` = 停用(休眠)。
- `ci-sweep.sw.json` = **event-started**(`WaitForSweepTick` 收 `ci_sweep_requested` → `Sweep`(agent `#sweep`)→ `Report`)。event-start 已證實穩定。
- sf-ci `application.properties` 加第二個 incoming channel `ci_sweep_requested`(綁 topic `ci.sweep.requested`,`auto.offset.reset=latest` —— sweep tick 不需補歷史)。**一個 Quarkus app 跑兩條 workflow**(ci-maintenance + ci-sweep),各自一個 Kafka channel,by CE type 路由。
- agent 加 `/task/sweep`(列出 red main repos + 重觸發其 Jenkins build,讓 build event 流回 ci-maintenance)。
- **這樣「cron 的 tick」變成既有 bridge 裡幾行 heartbeat,sweep LOGIC 進 observable workflow**;無 OS cron、無 PG。
- **✅ e2e 證實**(SWEEP_INTERVAL_SECS=60 測):bridge `sweep tick -> ci.sweep.requested` → sf-ci `Starting new process instance 'ci_sweep_requested'` → agent `POST /task/sweep 200` → `[ci-sweep] checked=14 red=0 retriggered=0`。

**⚠️ Cutover 尚未執行(pre-cutover 安全狀態)**:bridge `SWEEP_INTERVAL_SECS=0`(heartbeat 休眠)+ Jenkins RunListener 未部署 → SonataFlow 平台**不取代現役 OS cron daily-ci-agent**,平行待命。Cutover = 同時做(a)部署 RunListener groovy 進 Jenkins `init.groovy.d/`(真 build 開始流入)+(b)bridge 設 `SWEEP_INTERVAL_SECS=21600`(6h 安全網)+(c)停 OS cron daily-run。三者必須一起(只做 a→雙重維護 race;只做 c→平台無事件源)。這是「真 PR 開始被 auto-merge」的 go-live,需明確決策。

## ⚠️ Cutover 嘗試（2026-06-01）：機制全證實,但卡在 agent 執行層 → 已拉回

John 下令執行 cutover。執行後**證實了編排機制、也暴露兩個只有真資料才會現形的問題**,最後**拉回安全狀態(OS cron 仍現役)**。

**修好的兩個雷(已沉澱進 template)**:
1. **RunListener 動態註冊不觸發**:script console 跑 groovy 註冊後 listener 進了 `RunListener.all()`,但真 build 完成時 `onFinalized` 不被呼叫。根因:`RunListener<Run>` 的 no-arg super 構造子靠泛型反射推 `targetType`,**GroovyShell 定義的 class 反射失敗 → targetType=null → Jenkins `targetType.isInstance(run)` 過濾跳過**。修:構造子顯式 `super(Run.class)`。修後 build #18 完成 **auto-fire 成功**(bridge POST 自動發生)。
2. **Kafka ack 超時 vs 長 workflow**:真 agent `claude -p` diagnose 要數分鐘,但 smallrye 預設 `throttled` commit 要求 60s 內 ack → `TooManyMessagesWithoutAckException` → **Kafka channel 失敗**。STUB 測試秒回所以沒暴露。修:兩個 incoming channel 都加 `commit-strategy=latest`(週期 commit、無 per-record age 檢查)。修後不再爆。

**未解的真正阻斷 → 拉回原因**:真 build 失敗打進平台 → Diagnose 呼叫 agent `/task/diagnose` → **agent 回 500 / claude hang**(容器內手動 `claude -p` 8s 無輸出、多個 claude proc 卡住)。**agent-as-node 的執行層在真 task 上跑不通**(STUB 一直遮著這問題)。平台的編排層(correlation/retry/sweep/SLA/Kafka durability/auto-fire)全證實,但「Claude 真的去診斷+修+merge 真失敗」這條從沒在真資料上 work。

**判斷**:讓平台 live = 一個執行層壞掉的 auto-maintainer 跟正常運作的 OS cron 互搶 → 比不 cutover 更糟。故**拉回**:移除 RunListener(init.groovy.d + live 都清)、heartbeat `SWEEP_INTERVAL_SECS=0`、OS cron daily-ci-agent 維持現役(它 work)。平台容器續跑供繼續迭代。

**真 cutover 的前置條件(下一步該做的)**:把 agent-task-node 的 claude 執行在真 build 上跑通 —— 為何 `claude -p` 在該容器 hang/500(auth? log 抓取? `--json-schema` + 真 prompt 行為?),逐一在真失敗上驗 diagnose→fix→merge 真的產出正確 PR。這層 work 了,cutover 才安全(機制側已就緒)。

## agent 執行節點（關鍵能力已驗證）
- 容器內 claude CLI **2.1.152 支援 `-p/--print` + `--json-schema <schema>`** → `claude -p '<task prompt>' --json-schema '{...}'` 回 **validated structured JSON**。這是 agent-as-node 的乾淨實作基礎（SonataFlow 拿到 typed 結果做 switch/retry）。
- agent-task-node 容器 = **FROM 既有 daily-ci-agent image**（已含 claude+gh+git+auth、bind-mount claude-home）+ 一支 HTTP server 對應 `/task/diagnose|fix|merge`，內部 exec `claude -p --json-schema`。
