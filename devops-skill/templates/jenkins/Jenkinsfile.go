// TESTED: go-app-pipeline | Rocky VM (ARM64) | ~3s cached | 2026-02-23
// Pattern: agent any + docker compose build + tag + push
// Source: go-app — Go 1.24, multi-stage Dockerfile, compose CI build

pipeline {
    agent any

    environment {
        APP_NAME  = "{{APP_NAME}}"
        REGISTRY  = "{{REGISTRY}}"
        IMAGE_TAG = "${REGISTRY}/arcana/${APP_NAME}"
        VERSION   = "${params.VERSION ?: '1.0.0'}"
    }

    parameters {
        string(name: 'VERSION', defaultValue: '1.0.0', description: 'Image version tag')
    }

    options {
        timeout(time: 10, unit: 'MINUTES')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Compose Build') {
            steps {
                dir("${WORKSPACE}") {
                    sh "VERSION=${VERSION} docker compose -f docker-compose.ci.yml build"
                }
            }
        }

        stage('Tag') {
            steps {
                sh "docker tag ${IMAGE_TAG}:${VERSION} ${IMAGE_TAG}:build-${BUILD_NUMBER}"
            }
        }

        stage('Push') {
            steps {
                sh "docker push ${IMAGE_TAG}:${VERSION}"
                sh "docker push ${IMAGE_TAG}:build-${BUILD_NUMBER}"
            }
        }
    }

    post {
        success { echo "Pipeline SUCCESS - ${APP_NAME}:${VERSION}" }
        failure { echo "Pipeline FAILED" }
        always  { echo "Build number ${BUILD_NUMBER} done" }
    }
}
