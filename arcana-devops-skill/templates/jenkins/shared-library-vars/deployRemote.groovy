// ============================================
// Shared Library: deployRemote
// Deploy to remote VM via SSH + Docker Compose
// ============================================
// Usage: deployRemote(tag: env.BUILD_NUMBER)
// Usage: deployRemote(tag: '1.2.3', credentialId: 'ssh-prod', composeDir: '/opt/docker/app')

def call(Map config = [:]) {
    def tag = config.tag ?: env.BUILD_NUMBER
    def credentialId = config.credentialId ?: '{{SSH_CREDENTIALS_ID}}'
    def composeDir = config.composeDir ?: '{{REMOTE_COMPOSE_DIR}}'

    echo "Deploying version ${tag} to remote via SSH"

    sshagent(credentials: [credentialId]) {
        sh """
            ssh -o StrictHostKeyChecking=no \$SSH_USER@\$SSH_HOST '
                cd ${composeDir}

                # Save rollback state
                sudo docker compose ps --format json > .rollback-state.json 2>/dev/null || true
                CURRENT_TAG=\$(grep -oP "IMAGE_TAG=\\K[^ ]+" .env 2>/dev/null || echo "unknown")
                echo "\$CURRENT_TAG" > .rollback-tag

                # Update and deploy
                sed -i "s/^IMAGE_TAG=.*/IMAGE_TAG=${tag}/" .env
                sudo docker compose pull
                sudo docker compose up -d --remove-orphans
            '
        """
    }

    echo "Remote deploy initiated: version ${tag}"
}
