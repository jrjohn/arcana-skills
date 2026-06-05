// ============================================
// Shared Library: healthCheck
// Wait for health endpoint to respond OK
// ============================================
// Usage: healthCheck(url: 'http://app.example.com/health')
// Usage: healthCheck(url: env.HEALTH_CHECK_URL, timeout: 120)

def call(Map config = [:]) {
    def url = config.url
    def timeoutSeconds = config.timeout ?: 120

    if (!url) {
        error "healthCheck: 'url' parameter is required"
    }

    echo "Health check: ${url} (timeout: ${timeoutSeconds}s)"

    timeout(time: timeoutSeconds, unit: 'SECONDS') {
        waitUntil(initialRecurrencePeriod: 5000) {
            def status = sh(
                script: "curl -sf ${url} > /dev/null 2>&1",
                returnStatus: true
            )
            return status == 0
        }
    }

    echo "Health check PASSED: ${url}"
}
