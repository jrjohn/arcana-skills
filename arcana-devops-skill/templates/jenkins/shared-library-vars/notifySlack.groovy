// ============================================
// Shared Library: notifySlack
// Send build/deploy notification to Slack
// ============================================
// Usage: notifySlack(status: 'SUCCESS')
// Usage: notifySlack(status: 'FAILED', channel: '#deployments')

def call(Map config = [:]) {
    def status = config.status ?: 'UNKNOWN'
    def channel = config.channel ?: '#ci-cd'
    def project = config.project ?: env.PROJECT_NAME ?: 'unknown'
    def tag = config.tag ?: env.BUILD_NUMBER ?: 'unknown'
    def environment = config.environment ?: params.ENVIRONMENT ?: 'unknown'

    def color = status == 'SUCCESS' ? 'good' : 'danger'
    def emoji = status == 'SUCCESS' ? ':white_check_mark:' : ':x:'
    def message = "${emoji} *${status}*: ${project}:${tag} → ${environment}\n" +
                  "Build: <${env.BUILD_URL}|#${env.BUILD_NUMBER}>"

    echo "Slack notification: ${status} → ${channel}"

    // Uncomment when Slack plugin is configured:
    // slackSend(color: color, channel: channel, message: message)

    // Fallback: log to console
    echo message
}
