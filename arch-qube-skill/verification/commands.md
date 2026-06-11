# Architecture Qube — Commands

Copy-paste commands to install, scan, and integrate. Source: [`jrjohn/arcana-arch-qube`](https://github.com/jrjohn/arcana-arch-qube).

## Install
```bash
git clone https://github.com/jrjohn/arcana-arch-qube.git
cd arcana-arch-qube
python -m venv .venv && source .venv/bin/activate   # Python ≥ 3.10
pip install -e .
arch-qube --help
```

## Scan
```bash
# Fast local AST-only (free, ~0.5s)
arch-qube scan ./src --framework <fw> --no-ai

# Full AST + AI semantic
ANTHROPIC_API_KEY=sk-ant-... arch-qube scan ./src --framework <fw>

# PR / CI: changed files only, fail the build on regression
arch-qube scan ./src --framework <fw> --ci --diff-only --base-branch main

# Custom threshold + all reports
arch-qube scan ./src -f <fw> --threshold 90 \
  --format json,markdown,sonar,junit,badge -o arch-qube-reports/

# fw ∈ angular react vue ios android harmonyos windows
#      springboot python go rust nodejs stm32 esp32
```

## Custom rules / profiles
```bash
arch-qube scan ./src -f springboot --rules my-rules/ --profiles my-profiles/
```

## Jenkins (Arcana fleet stage)
```groovy
stage('Architecture Qube') {
    steps {
        sh '''arch-qube scan ./src \
                --framework ${FRAMEWORK} --ci --diff-only \
                --format json,markdown,sonar,junit'''
    }
    post { always {
        junit 'arch-qube-reports/arch-qube-junit.xml'
        archiveArtifacts 'arch-qube-reports/**'
    } }
}
```

## SonarQube
```properties
# sonar-project.properties
sonar.externalIssuesReportPaths=arch-qube-reports/arch-qube-sonar.json
```

## Pre-commit hook
```bash
# .git/hooks/pre-commit  (chmod +x)
#!/bin/sh
arch-qube scan ./src --framework angular --no-ai --ci --diff-only
```

## GitHub Actions
```yaml
- name: Architecture Qube
  run: arch-qube scan ./src -f react --ci --diff-only
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

## Tests (when modifying arch-qube itself)
```bash
pip install -e ".[dev]"
pytest -q           # tests/test_rules.py test_scanner.py test_ai.py
```

## Sanity checks
```bash
arch-qube scan ./src -f <fw> --no-ai; echo "exit=$?"   # 0 PASS / 1 FAIL / 2 ERROR
arch-qube scan ./does-not-exist -f vue; echo $?         # expect 2 (ERROR)
```
