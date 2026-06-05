// ============================================
// Shared Library: rollbackRemote
// Rollback remote VM to previous version via SSH
// ============================================
// Usage: rollbackRemote()
// Usage: rollbackRemote(credentialId: 'ssh-prod', composeDir: '/opt/docker/app')

def call(Map config = [:]) {
    def credentialId = config.credentialId ?: '{{SSH_CREDENTIALS_ID}}'
    def composeDir = config.composeDir ?: '{{REMOTE_COMPOSE_DIR}}'

    echo "Rolling back remote deployment..."

    sshagent(credentials: [credentialId]) {
        sh """
            ssh -o StrictHostKeyChecking=no \$SSH_USER@\$SSH_HOST '
                cd ${composeDir}

                PREV_TAG=\$(cat .rollback-tag 2>/dev/null || echo "")
                if [ -z "\$PREV_TAG" ] || [ "\$PREV_TAG" = "unknown" ]; then
                    echo "No rollback version found — manual intervention required"
                    exit 1
                fi

                echo "Rolling back to: \$PREV_TAG"
                sed -i "s/^IMAGE_TAG=.*/IMAGE_TAG=\$PREV_TAG/" .env
                sudo docker compose pull
                sudo docker compose up -d --remove-orphans
                echo "Rolled back to version: \$PREV_TAG"
            '
        """
    }
}
