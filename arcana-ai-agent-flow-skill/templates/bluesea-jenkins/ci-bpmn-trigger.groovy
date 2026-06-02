// Arcana CI trigger (B2, 2026-06-02 v3): on a non-SUCCESS build, create a ci-flow
// BPMN instance on the workflow engine. The BPMN flow + task-worker now own
// diagnose(Triage=ai)/build(Build=jenkins)/decide(Decide=ai) — this REPLACES the
// old inline routine diagnose/fix (CiRoutineTrigger). Never blocks the build.
//
// Install (bluesea, John `!`):
//   docker cp ci-bpmn-trigger.groovy jenkins:/var/jenkins_home/init.groovy.d/ci-routine-trigger.groovy
//   docker exec jenkins rm -f /var/jenkins_home/init.groovy.d/ci-routine-trigger.groovy.bak 2>/dev/null
//   # apply live without restart via the script console (or restart Jenkins):
//   cat ci-bpmn-trigger.groovy | docker exec -i jenkins sh -c 'cat > /tmp/t.groovy' && \
//     curl -s -u admin:$TOKEN --data-urlencode "script=$(docker exec jenkins cat /tmp/t.groovy)" \
//       http://localhost:8080/jenkins/scriptText
import hudson.model.Run
import hudson.model.listeners.RunListener
import groovy.json.JsonOutput

class CiBpmnTrigger extends RunListener<Run> {
    CiBpmnTrigger() { super(Run.class) }
    @Override void onFinalized(Run run) {
        try {
            def result = run.getResult()?.toString() ?: "UNKNOWN"
            if (result == "SUCCESS") return
            def job = run.getParent().getFullName()
            def num = run.getNumber()
            def buildUrl = "http://jenkins:8080/jenkins/" + run.getUrl()
            Thread.start {
                try {
                    def body = [subject: "${job} #${num} ${result}".toString(),
                                job: job, buildUrl: buildUrl, result: result]
                    def conn = new URL("http://aaf-kogito-bpmn:8080/ci-flow").openConnection()
                    conn.setRequestMethod("POST")
                    conn.setRequestProperty("Content-Type", "application/json")
                    conn.setConnectTimeout(8000); conn.setReadTimeout(15000); conn.setDoOutput(true)
                    conn.getOutputStream().withWriter("UTF-8") { it << JsonOutput.toJson(body) }
                    def code = conn.getResponseCode()
                    println("[ci-bpmn-trigger] ${job} #${num} (${result}) -> ci-flow instance HTTP ${code}")
                } catch (Throwable t) {
                    println("[ci-bpmn-trigger] async error ${job} #${num}: ${t}")
                }
            }
        } catch (Throwable t) {
            println("[ci-bpmn-trigger] onFinalized error: ${t}")
        }
    }
}
// idempotent re-register: remove the old inline-routine listener AND any prior bpmn one
def __el = RunListener.all()
new ArrayList(__el).findAll { it.getClass().getSimpleName() in ["CiRoutineTrigger", "CiBpmnTrigger"] }.each { __el.remove(it) }
__el.add(new CiBpmnTrigger())
println("[ci-bpmn-trigger] registered v3 (B2: red build -> ci-flow BPMN instance; inline routine removed)")
