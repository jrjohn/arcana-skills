/*
 * jenkins-cloudevent.groovy — global RunListener that emits a CloudEvent on every
 * build completion. One place, no per-Jenkinsfile edits.
 *
 * Path: Jenkins -> ce-kafka-bridge (HTTP) -> Kafka topic ci.build.completed -> SonataFlow.
 * The bridge produces to Kafka with acks=all, so events are DURABLE (survive a
 * SonataFlow restart) and REPLAYABLE (retained log for problem-tracking / audit).
 *
 * Install (persistent):  $JENKINS_HOME/init.groovy.d/ci-cloudevent.groovy
 * Activate now (no restart): paste into Manage Jenkins > Script Console.
 *
 * Emits a structured CloudEvent (application/cloudevents+json). try/catch wraps
 * everything — a notifier must NEVER break a build.
 */
import hudson.model.Run
import hudson.model.listeners.RunListener
import jenkins.model.Jenkins

// devops_default DNS name of the CloudEvent->Kafka bridge (adjust if different).
def CE_INGEST_URL = System.getenv('CE_INGEST_URL') ?: 'http://ce-kafka-bridge:8088/jenkins/build'

class CiCloudEventListener extends RunListener<Run> {
    String endpoint
    // super(Run.class) sets targetType EXPLICITLY. Without it, the no-arg
    // RunListener() infers targetType via generic reflection, which FAILS for a
    // class defined in the Groovy script console (targetType -> null) so Jenkins'
    // `targetType.isInstance(run)` filter silently skips the listener and
    // onFinalized never fires. Explicit Run.class makes it match every build.
    CiCloudEventListener(String endpoint) { super(Run.class); this.endpoint = endpoint }

    @Override
    void onFinalized(Run run) {
        try {
            def job    = run.parent.fullName            // e.g. arcana-cloud-rust/main
            def result = run.result?.toString() ?: 'UNKNOWN'
            def number = run.number
            def branch = run.parent.fullName.contains('/') ?
                         run.parent.fullName.split('/').last() : 'main'
            def buildUrl = (Jenkins.get().rootUrl ?: '') + run.url

            def data = groovy.json.JsonOutput.toJson([
                job: job, result: result, number: number,
                branch: branch, buildUrl: buildUrl
            ])
            // jobref = STABLE correlation key across the original build and its re-build
            // (same job/branch fullName, different number). The workflow's Verify
            // event-state waits for the next event carrying this same jobref.
            // type MUST be dot-free ('ci_build_completed') to match the workflow's
            // event consumer + smallrye channel name.
            def envelope = groovy.json.JsonOutput.toJson([
                specversion    : '1.0',
                type           : 'ci_build_completed',
                source         : 'jenkins/arcana',
                id             : "${job}-${number}".toString(),
                jobref         : job,
                datacontenttype: 'application/json',
                data           : new groovy.json.JsonSlurper().parseText(data)
            ])

            def conn = new URL(endpoint).openConnection()
            conn.requestMethod = 'POST'
            conn.doOutput = true
            conn.connectTimeout = 3000
            conn.readTimeout = 5000
            conn.setRequestProperty('Content-Type', 'application/cloudevents+json')
            conn.outputStream.withWriter('UTF-8') { it << envelope }
            def code = conn.responseCode
            println "[ci-cloudevent] ${job}#${number} ${result} -> ${endpoint} HTTP ${code}"
        } catch (Throwable t) {
            // swallow — never fail a build because of the notifier
            println "[ci-cloudevent] notify failed (ignored): ${t.message}"
        }
    }
}

// Register (idempotent-ish: remove any prior instance first).
def all = RunListener.all()
all.removeAll { it.class.name == 'CiCloudEventListener' }
all.add(new CiCloudEventListener(CE_INGEST_URL))
println "[ci-cloudevent] registered -> ${CE_INGEST_URL}"
