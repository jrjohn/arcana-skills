# Jenkins Pipeline Patterns

> DevOps Skill Reference

## Declarative Pipeline Structure

```groovy
pipeline {
    agent any
    environment { ... }
    options { ... }
    stages {
        stage('Name') {
            steps { ... }
            post { ... }
        }
    }
    post { ... }
}
```

## Common Pipeline Stages

| Stage | Purpose | Failure Action |
|-------|---------|----------------|
| Checkout | Clone source code | Abort |
| Build | Compile/package | Abort + notify |
| Test | Run automated tests | Abort + notify |
| SonarQube | Code quality analysis | Abort if gate fails |
| Docker Build | Build container image | Abort + notify |
| Security Scan | Trivy vulnerability scan | Abort if CRITICAL found |
| Push | Push image to registry | Abort + notify |
| Deploy | Deploy to environment | Abort + rollback |
| Notify | Send status notification | Log only |

## Useful Pipeline Options

```groovy
options {
    timeout(time: 30, unit: 'MINUTES')
    disableConcurrentBuilds()
    buildDiscarder(logRotator(numToKeepStr: '10'))
    retry(2)
    timestamps()
}
```

## Conditional Execution

```groovy
stage('Deploy to Prod') {
    when {
        branch 'main'
        // OR: tag pattern: "v*"
        // OR: expression { return params.DEPLOY }
    }
    steps { ... }
}
```

## Credentials Management

```groovy
withCredentials([
    string(credentialsId: 'sonar-token', variable: 'SONAR_TOKEN'),
    usernamePassword(credentialsId: 'registry', usernameVariable: 'REG_USER', passwordVariable: 'REG_PASS'),
    file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')
]) {
    sh 'deploy with credentials'
}
```

## Parallel Execution

```groovy
stage('Tests') {
    parallel {
        stage('Unit Tests') { steps { sh 'npm test' } }
        stage('Integration') { steps { sh 'npm run test:integration' } }
        stage('Lint') { steps { sh 'npm run lint' } }
    }
}
```

## Post Actions

```groovy
post {
    always { cleanWs() }
    success { echo 'Build succeeded' }
    failure { echo 'Build failed' }
    unstable { echo 'Tests failed' }
}
```

## SonarQube Integration

```groovy
stage('SonarQube') {
    steps {
        withSonarQubeEnv('SonarQube') {
            sh './mvnw sonar:sonar'
        }
    }
}
stage('Quality Gate') {
    steps {
        timeout(time: 5, unit: 'MINUTES') {
            waitForQualityGate abortPipeline: true
        }
    }
}
```

## Shared Library Pattern

### Problem: Duplicated Pipeline Logic

With multiple Jenkinsfiles (springboot, node, mobile, cloud), common stages get duplicated:
- Docker build + tag + push
- Trivy security scan
- SSH remote deploy + health check + rollback
- Slack/Email notifications

### Solution: Jenkins Shared Library

A Shared Library is a Git repo loaded by Jenkins that provides reusable functions.

### Repository Structure

```
jenkins-shared-library/
├── vars/                          # Global functions (called from Jenkinsfile)
│   ├── dockerBuild.groovy         # Docker build + tag
│   ├── dockerPush.groovy          # Push to registry
│   ├── trivyScan.groovy           # Security scan
│   ├── deployRemote.groovy        # SSH remote deploy
│   ├── rollbackRemote.groovy      # SSH remote rollback
│   ├── healthCheck.groovy         # Post-deploy health check
│   └── notifySlack.groovy         # Slack notification
└── README.md
```

### Registering in Jenkins (JCasC)

```yaml
# jenkins-casc.yml
unclassified:
  globalLibraries:
    libraries:
      - name: "devops-shared"
        defaultVersion: "main"
        retriever:
          modernSCM:
            scm:
              git:
                remote: "{{SHARED_LIB_REPO_URL}}"
                credentialsId: "{{GIT_CREDENTIALS_ID}}"
```

### Usage in Jenkinsfile

```groovy
@Library('devops-shared') _

pipeline {
    agent any
    stages {
        stage('Build')   { steps { sh 'npm ci && npm run build' } }
        stage('Docker')  { steps { dockerBuild(tag: env.BUILD_NUMBER) } }
        stage('Scan')    { steps { trivyScan(image: "${PROJECT_NAME}:${BUILD_NUMBER}") } }
        stage('Push')    { steps { dockerPush(tag: env.BUILD_NUMBER, registry: env.REGISTRY) } }
        stage('Deploy')  { steps { deployRemote(tag: env.BUILD_NUMBER) } }
        stage('Verify')  { steps { healthCheck(url: env.HEALTH_CHECK_URL) } }
    }
    post {
        success { notifySlack(status: 'SUCCESS') }
        failure {
            rollbackRemote()
            notifySlack(status: 'FAILED')
        }
    }
}
```

### Key `vars/` Implementations

See template: `templates/jenkins/shared-library-vars/`

**Benefits:**
- Single source of truth for deploy/rollback logic
- Jenkinsfiles reduced from ~350 lines to ~30 lines
- Changes to deploy logic automatically apply to all pipelines
- Testable in isolation (unit test Groovy functions)

---

## Jenkins Configuration as Code (JCasC)

JCasC allows managing Jenkins configuration in YAML:
- System configuration
- Security settings
- Tool installations
- Job definitions
- Credentials (encrypted)

See `templates/jenkins/jenkins-casc.yml` for a complete example.

---

## Jenkins API — CSRF Crumb Handling

Jenkins requires a CSRF crumb for all POST API calls. The crumb must be obtained with a cookie session and sent back in the same session.

### Getting a Crumb

```bash
# Step 1: Get crumb + save session cookie
COOKIE_JAR=$(mktemp)
CRUMB=$(curl -s -c "$COOKIE_JAR" -u admin:PASSWORD \
  "http://localhost:8080/crumbIssuer/api/json" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['crumb'])")

# Step 2: Use crumb + cookie in subsequent requests
curl -s -b "$COOKIE_JAR" -X POST "http://localhost:8080/job/my-job/build" \
  -u admin:PASSWORD \
  -H "Jenkins-Crumb:$CRUMB"
```

### Creating Jobs via API

When sending Pipeline XML config, use `--data-binary` (not `-d`) to preserve newlines in Groovy scripts, and wrap the script in `<![CDATA[...]]>`:

```xml
<definition class="org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition">
  <script><![CDATA[
pipeline {
    agent any
    stages {
        stage('Build') {
            steps { sh 'echo hello' }
        }
    }
}
]]></script>
  <sandbox>true</sandbox>
</definition>
```

```bash
# IMPORTANT: Use --data-binary to preserve newlines
curl -s -b "$COOKIE_JAR" -X POST \
  "http://localhost:8080/createItem?name=my-pipeline" \
  -u admin:PASSWORD \
  -H "Jenkins-Crumb:$CRUMB" \
  -H "Content-Type: application/xml" \
  --data-binary @job-config.xml
```

---

## Jenkins Container — Docker-in-Docker Setup

The Jenkins LTS image does **not** include Docker CLI. To run `docker build` / `docker push` from Pipeline:

### Required Volume Mounts (docker-compose.infra.yml)

```yaml
jenkins:
  volumes:
    - jenkins_home:/var/jenkins_home
    - /var/run/docker.sock:/var/run/docker.sock   # Docker daemon socket
    - /usr/bin/docker:/usr/bin/docker:ro           # Docker CLI binary
    - /usr/libexec/docker/cli-plugins:/usr/libexec/docker/cli-plugins:ro  # docker compose plugin
```

> **Note**: The `cli-plugins` mount is required for `docker compose` commands
> inside Jenkins Pipeline. Without it, `docker compose run` will fail with
> "unknown flag" errors.

### Docker Socket Permission Fix

The Jenkins container user cannot access docker.sock by default. Use `group_add` to add the jenkins user to the host's docker group:

```bash
# Find the docker group GID on the host
stat -c '%g' /var/run/docker.sock
```

```yaml
jenkins:
  group_add:
    - "${DOCKER_GID:-999}"  # host docker group GID
```

> **Note**: The `entrypoint chmod 666` approach does NOT work reliably because
> the Jenkins image runs the entrypoint as the `jenkins` user (non-root),
> so chmod silently fails. `group_add` is the correct solution.

### Mounting Project Directories

For `dir('/path/on/host')` to work in Pipelines, the host path must be mounted into Jenkins:

```yaml
jenkins:
  volumes:
    - /home/user/project:/home/user/project   # Same path inside and outside
```

---

## Built-in Node — Agent Mode

### NORMAL vs EXCLUSIVE Mode

| Mode | `agent any` | `agent { label 'built-in' }` | Use Case |
|------|-------------|-------------------------------|----------|
| **NORMAL** | Runs on built-in | Runs on built-in | Single-node / dev environment |
| **EXCLUSIVE** | **Will NOT run** | Runs on built-in | Multi-node / production (needs separate agents) |

**Warning:** Setting the built-in node to EXCLUSIVE mode without additional agents will cause all `agent any` pipelines to hang indefinitely in the queue.

### Dismissing Admin Monitors

Jenkins shows security warnings (built-in node, CSP, etc.) that can be dismissed via Groovy Script Console:

```groovy
import jenkins.model.Jenkins
def monitors = Jenkins.instance.getExtensionList(hudson.model.AdministrativeMonitor.class)
def targets = ["ControllerExecutorsNoAgents", "ControllerExecutorsAgents",
               "CspRecommendation", "ResourceDomainRecommendation"]
monitors.each { m ->
    targets.each { t ->
        if (m.getClass().getName().contains(t)) m.disable(true)
    }
}
```

---

## Windows Agent Pattern (TESTED)

Windows pipelines use `agent { label 'windows' }` and `bat` commands instead of `sh`.

### Key Differences from Linux Pipelines

| Aspect | Linux (Rocky VM) | Windows Agent |
|--------|-----------------|---------------|
| Agent | `agent any` | `agent { label 'windows' }` |
| Shell | `sh "..."` | `bat "..."` |
| Paths | `/home/user/...` | `C:\\Users\\user\\...` |
| Build tool | Docker compose | Native `dotnet` CLI |
| Output | Docker image → registry | EXE + MSIX artifacts |

### Windows Pipeline Pattern

```groovy
pipeline {
    agent { label 'windows' }
    environment {
        PROJECT_DIR = 'C:\\Users\\johnc\\devops-test\\{{APP_NAME}}'
    }
    stages {
        stage('Build') {
            steps {
                dir("${PROJECT_DIR}") {
                    bat "dotnet build -c Release -p:Platform=x64 -maxcpucount:1"
                }
            }
        }
    }
}
```

### Windows Agent Setup

| Setting | Value |
|---------|-------|
| Credentials | `windows-ssh` (SSH key) |
| SSH User | `johnc` |
| Host | `192.168.11.115` |
| Labels | `windows` |
| Executors | 2 |
| Remote Root | `C:\Users\johnc\jenkins-agent` |
| .NET SDK | 10.0 |

> **Note**: Use `-maxcpucount:1` on machines with limited RAM (8GB) to prevent OOM during builds.

---

## Mac Mini Agent Pattern (TESTED)

iOS/macOS pipelines use `agent { label 'macos' }` and native Xcode tools.

### Mac Mini Pipeline Pattern

```groovy
pipeline {
    agent { label "macos" }
    environment {
        PATH = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
    }
    stages {
        stage("Build") {
            steps {
                dir("${WORKSPACE}") {
                    sh "xcodebuild -project {{XCODE_PROJECT}} -scheme {{XCODE_SCHEME}} -configuration Release -destination 'generic/platform=iOS' CODE_SIGNING_ALLOWED=NO build 2>&1 | tail -20"
                }
            }
        }
        stage("Test") {
            steps {
                dir("${WORKSPACE}") {
                    sh "xcodebuild -project {{XCODE_PROJECT}} -scheme {{XCODE_SCHEME}} -destination 'platform=iOS Simulator,name=iPhone 16' test 2>&1 | tail -30"
                }
            }
        }
    }
}
```

### Mac Mini Agent Setup

| Setting | Value |
|---------|-------|
| Credentials | `macmini-ssh` (SSH key at `~/.ssh/macmini.key`) |
| SSH User | `jrjohn` |
| Host | `192.168.11.104` |
| Labels | `macos`, `ios` |
| Executors | 2 |
| Remote Root | `/Users/jrjohn/jenkins-agent` |
| Java Path | `/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home/bin/java` |
| Xcode | 26.2 (App Store) |

> **Tip**: `CODE_SIGNING_ALLOWED=NO` skips code signing for CI builds. Use Fastlane for signed release builds.
