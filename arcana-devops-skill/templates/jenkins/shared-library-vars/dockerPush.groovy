// ============================================
// Shared Library: dockerPush
// Tag and push image to registry
// ============================================
// Usage: dockerPush(tag: env.BUILD_NUMBER)
// Usage: dockerPush(tag: '1.2.3', registry: 'registry.example.com:5000')

def call(Map config = [:]) {
    def tag = config.tag ?: env.BUILD_NUMBER
    def project = config.project ?: env.PROJECT_NAME
    def registry = config.registry ?: env.REGISTRY_CRED

    echo "Pushing to registry: ${registry}/${project}:${tag}"
    sh """
        docker tag ${project}:${tag} ${registry}/${project}:${tag}
        docker push ${registry}/${project}:${tag}
    """

    echo "Push complete: ${registry}/${project}:${tag}"
}
