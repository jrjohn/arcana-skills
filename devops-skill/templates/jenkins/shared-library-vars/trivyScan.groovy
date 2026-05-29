// ============================================
// Shared Library: trivyScan
// Run Trivy security scan on Docker image
// ============================================
// Usage: trivyScan(image: "${PROJECT_NAME}:${BUILD_NUMBER}")
// Usage: trivyScan(image: 'myapp:1.2.3', severity: 'CRITICAL,HIGH')

def call(Map config = [:]) {
    def image = config.image
    def severity = config.severity ?: 'CRITICAL'
    def exitCode = config.exitCode ?: '1'

    if (!image) {
        error "trivyScan: 'image' parameter is required"
    }

    echo "Scanning image: ${image} (severity: ${severity})"
    sh """
        docker run --rm \
            -v /var/run/docker.sock:/var/run/docker.sock \
            aquasec/trivy:latest image \
            --exit-code ${exitCode} \
            --severity ${severity} \
            ${image}
    """

    echo "Security scan PASSED: ${image}"
}
