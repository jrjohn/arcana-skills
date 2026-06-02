# Build & deploy gotchas (every trap hit, with the fix)

Lessons from building arcana-ai-agent-flow Mac-first → deploying to bluesea.

## Kogito engines (Quarkus 3.8.4 / Kogito 10.0.0, arm64)

1. **Flatten the pom** — the kogito-examples parent isn't resolvable standalone.
   Self-contained pom: `quarkus-bom` 3.8.4 + `kogito-bom` 10.0.0 imports; repos
   `jboss-public` + `apache-releases`.
2. **Events addon needs the kafka connector.** Adding only
   `kie-addons-quarkus-events-process` → `SRMSG00019: Unable to connect an
   emitter with the channel kogito-processdefinitions-events` (the addon ships
   the messaging *provider*, not a connector). Add
   `io.quarkus:quarkus-smallrye-reactive-messaging-kafka` — **this exact
   artifact** (quarkus-bom 3.8.4 manages it; `quarkus-messaging-kafka` is NOT
   managed → "version missing").
3. **MetricDecorator NoClassDefFoundError.** smallrye-reactive-messaging ships a
   `MetricDecorator` whose `MetricRegistry` field trips ArC init (no MP-metrics
   API on classpath). Fix without adding a metrics extension:
   `quarkus.arc.exclude-types=io.smallrye.reactive.messaging.providers.metrics.MetricDecorator`.
4. **`mvn clean package`, not incremental** — stale incremental builds throw
   `ProtostreamObjectMarshaller not found` ServiceConfigurationError. Always
   clean-build after dependency/BPMN changes.
5. **Dockerfile**: `eclipse-temurin:21-jre`, COPY `target/quarkus-app/{lib,*.jar,app,quarkus}`, `CMD java -jar /deployments/quarkus-run.jar`. (The examples' amd64 Dockerfile.jvm + run-java.sh is broken on arm64.)
6. **BPMN process variables** must be declared as top-level `<bpmn2:property>`
   to be settable via the generated `POST /<processId>` body and readable via
   `GET /<processId>/<id>`. Added `job`/`buildUrl`/`result` so the Jenkins
   trigger can pass build context the worker then acts on.

## SonataFlow

- Extension: `org.apache.kie.sonataflow:sonataflow-quarkus` (in kogito-bom). Same
  events addon + kafka connector + MetricDecorator exclude as BPMN.
- SonataFlow uses JSON variables (no protobuf). Its instances/definitions land in
  the same Data Index; `ProcessDefinition.type = SW` (vs `BPMN`).
- **Flow-diagram edges**: the Data Index gives SWF *nodes* but no *edges* (so the
  diagram shows unconnected boxes). Edges live in the `.sw.yaml` as `start` +
  per-state `transition` + `end`. Parse them (`swf.rs`, serde_yaml) into edges
  **by state name**, then in `/definitions/:id/graph` map names → Data Index node
  ids (Kogito ids the SWF nodes `1`,`2`,… but the *names* — Start/End/<state> —
  match): `Start→<start state>`, `<state>→<transition>`, `<end state>→End`. Mount
  the `.sw.yaml` dir into the read-API (`SWF_DIR`), same pattern as `BPMN_DIR`.
  (BPMN edges come from sequence-flow sourceRef/targetRef, already node-ids.)

## Kogito Data Index

- Image (arm64-native, no emulation):
  `docker.io/apache/incubator-kie-kogito-data-index-postgresql:10.0.x-20260329-linux-arm64`.
- Mount each engine's protobuf descriptors
  (`target/classes/META-INF/resources/persistence/protobuf`) into
  `/home/kogito/data/protobufs`. Collect both engines' `.proto` into one dir.
- `ProcessInstance` has **no** `type` field (query errors); engine type is only
  on `ProcessDefinition.type`. The read-API builds a processId→engine map from
  ProcessDefinitions to annotate instances.
- A fresh Data Index DB after `down -v` does **not** replay old events — the
  kafka consumer-group offset persists in kafka, so the dashboard stays clean.

## read-API (arcana-cloud-rust, Axum + SQLx)

- The template repository is **MySQL**; bluesea is PostgreSQL → port
  `arcana-repository`: `MySqlPool`→`PgPool`, `?`→`$n` placeholders (bind order
  unchanged), migrations DDL (`DATETIME`→`TIMESTAMPTZ`, drop `ON UPDATE`, drop
  `ENGINE=InnoDB…`, `JSON`→`JSONB`). Migrations are compile-time embedded
  (`sqlx::migrate!`) → not needed at runtime.
- Production Dockerfile builder must `apt-get install protobuf-compiler`
  (arcana-grpc → prost-build needs `protoc`).
- `ARCANA_ENVIRONMENT=production` loads production.toml which sets
  `grpc_tls_enabled=true` → crash without certs. Override
  `ARCANA__SECURITY__GRPC_TLS_ENABLED=false` (internal network).
- Mount workflows router **after** the auth `.layer(...)` so it needs no token
  (dashboard polling). Config via `default.toml` + `ARCANA__*` env; never bake
  `local.toml` into the image.

## Dashboard (Angular 21 → nginx)

- Build image with `node:24-alpine` + `npm install` (not `npm ci`) — musl/arm64
  optional native deps (lightningcss/esbuild/@emnapi) aren't in the lockfile.
- nginx `/api` proxy must use a **resolver + variable**:
  `resolver 127.0.0.11 valid=10s ipv6=off; set $upstream http://<read-api>:8080; proxy_pass $upstream;`
  — `proxy_pass <fixed-name>` fails nginx boot if the upstream is briefly down;
  a variable `proxy_pass $upstream` **with no URI part** forwards the full
  original `/api/...` path (adding `/api/` to it double-prefixes → 404).

## bluesea / production

- Reuse the existing kafka (`KAFKA_BOOTSTRAP=kafka:9092`, advertised
  `kafka:9092`, on `devops_default`); don't run a second broker.
- One `kogito-pg` (postgres:17) hosting 3 DBs: `workflow` (engine), `dataindex`
  (Data Index), `arcana` (read-API) — `kogito-pg-init/*.sql` creates the latter
  two on first init. Don't reuse sonarqube-db / archive PG.
- Authelia subdomain exposure: cert is **per-host** (arcana.boo, not wildcard) →
  issue a separate cert for `workflow.arcana.boo` (`certbot certonly --nginx
  --cert-name workflow.arcana.boo`). Authelia needs **no change** if its session
  cookie `domain` is the parent (`arcana.boo`, covers subdomains) and
  `default_policy: two_factor`. The :80 vhost for ACME must NOT proxy the app
  unauthenticated (return 404; certbot --nginx injects the challenge).
- Classifier discipline: writing secrets to a prod host / pulling from Keychain /
  exposing a service without auth are gated — they need the user's explicit,
  *specific* authorization (a blanket "go ahead" is treated as insufficient).
  Image transfer, `compose up`, and non-secret nginx (incl. Authelia auth_request)
  pass.

## CI trigger (B2)

- Replace the inline-routine Jenkins RunListener with `ci-bpmn-trigger.groovy`:
  any non-SUCCESS build → POST `http://<engine>:8080/ci-flow {subject,job,buildUrl,result}`
  → BPMN instance → worker orchestrates. Idempotent re-register removes both the
  old `CiRoutineTrigger` and any prior `CiBpmnTrigger`. Activate live via
  `/jenkins/scriptText` (admin token); `docker cp` into `init.groovy.d` for
  restart persistence. The worker keeps the routine guardrail (auto-fix only red
  `*/main` + fixable code/deps/test) so replacing the inline routine doesn't
  regress remediation.

## Hourly scheduler (heartbeat)

- The `ci-scheduler` service starts a `ci-maintenance` SonataFlow instance every
  hour so the dashboard always shows recent automated runs (the event-driven B2
  trigger handles real red builds separately).
- **`curlimages/curl` ENTRYPOINT is `curl`** — `command: sh -c '...'` becomes
  `curl sh -c …` and breaks (`sh: -H: not found`). Override
  `entrypoint: ["/bin/sh","-c"]` and pass the loop as a **literal block scalar**
  (`|`), not a folded one (`>` mangles the embedded quotes).
