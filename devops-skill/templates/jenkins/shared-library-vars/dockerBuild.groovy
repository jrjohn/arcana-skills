// ============================================
// Shared Library: dockerBuild
// Build and tag a Docker image
// ============================================
// Usage: dockerBuild(tag: env.BUILD_NUMBER)
// Usage: dockerBuild(tag: '1.2.3', dockerfile: 'Dockerfile.unified', buildArgs: ['BUILD_ENV=production'])

def call(Map config = [:]) {
    def tag = config.tag ?: env.BUILD_NUMBER
    def project = config.project ?: env.PROJECT_NAME
    def dockerfile = config.dockerfile ?: 'Dockerfile'
    def context = config.context ?: '.'
    def buildArgs = config.buildArgs ?: []

    def argsString = buildArgs.collect { "--build-arg ${it}" }.join(' ')

    echo "Building Docker image: ${project}:${tag}"
    sh """
        docker build \
            ${argsString} \
            -t ${project}:${tag} \
            -f ${dockerfile} \
            ${context}
    """

    echo "Docker image built: ${project}:${tag}"
    return "${project}:${tag}"
}
