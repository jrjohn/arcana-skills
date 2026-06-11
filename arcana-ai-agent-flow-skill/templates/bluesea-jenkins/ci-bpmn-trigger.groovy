// Arcana CI trigger (v7, 2026-06-08): two paths, both through the BPMN engine.
//   * non-SUCCESS build  -> ci-flow BPMN remediation instance (v4 behaviour, unchanged).
//   * SUCCESS PR build    -> agent-task-node /task/merge for AI autonomous merge of a
//     verified-green PR -> start a merge-flow BPMN instance (engine-tracked,
//     dashboard-visible). The worker dispatches its Merge(ai) task to
//     agent-task-node /task/merge. FLEET-WIDE (*-app-pipeline-mb and ios *-app-mb).
//     The agent re-checks gh pr state before merging,
//     so a repeated green build on an already-merged PR is a safe no-op.
//
// (v4 note) on a non-SUCCESS build, create a ci-flow
// BPMN instance on the workflow engine. The BPMN flow + task-worker now own
// diagnose(Triage=ai)/build(Build=jenkins)/decide(Decide=ai) — this REPLACES the
// old inline routine diagnose/fix (CiRoutineTrigger). Never blocks the build.
//
// v4: DEDUP — skip spawning when an ACTIVE ci-flow instance already exists for
// the same job (go PR-13 failing 3x used to spawn 3 duplicate instances that the
// single-threaded worker then churned through). Checked against the data-index;
// fail-open (a dedup-check error still spawns, so remediation is never lost).
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
import hudson.model.TaskListener

class CiBpmnTrigger extends RunListener<Run> {
    CiBpmnTrigger() { super(Run.class) }
    @Override void onFinalized(Run run) {
        try {
            def result = run.getResult()?.toString() ?: "UNKNOWN"
            def job = run.getParent().getFullName()
            def num = run.getNumber()
            if (result == "SUCCESS") {
                // Green PR build (any arcana app pipeline) -> AI autonomous merge.
                String prUrl = null
                try { prUrl = run.getEnvironment(TaskListener.NULL).get("CHANGE_URL") } catch (Throwable e) {}
                if (prUrl && (job ==~ /.*-app(-pipeline)?-mb\/.*/)) {   // fleet-wide green-PR auto-merge
                    Thread.start {
                        try {
                            def mbody = [subject: "merge ${job} #${num}".toString(), job: job, prUrl: prUrl]
                            def mc = new URL("http://aaf-kogito-bpmn:8080/merge-flow").openConnection()
                            mc.setRequestMethod("POST")
                            mc.setRequestProperty("Content-Type", "application/json")
                            mc.setConnectTimeout(8000); mc.setReadTimeout(15000); mc.setDoOutput(true)
                            mc.getOutputStream().withWriter("UTF-8") { it << JsonOutput.toJson(mbody) }
                            def mcode = mc.getResponseCode()
                            println("[ci-merge-trigger] ${job} #${num} green PR ${prUrl} -> merge-flow instance HTTP ${mcode}")
                        } catch (Throwable mt) {
                            println("[ci-merge-trigger] async error ${job} #${num}: ${mt}")
                        }
                    }
                }
                return
            }
            def buildUrl = "http://jenkins:8080/jenkins/" + run.getUrl()
            Thread.start {
                try {
                    // v4 dedup: one ACTIVE remediation per job. Query the data-index
                    // for ACTIVE ci-flow instances and skip if any is already on this
                    // job. Fail-open: if the check itself errors, spawn as before.
                    try {
                        def dq = JsonOutput.toJson([query:
                            '{ ProcessInstances(where:{and:[{processId:{equal:"ci-flow"}},{state:{equal:ACTIVE}}]}){ variables } }'])
                        def dconn = new URL("http://aaf-data-index:8080/graphql").openConnection()
                        dconn.setRequestMethod("POST")
                        dconn.setRequestProperty("Content-Type", "application/json")
                        dconn.setConnectTimeout(5000); dconn.setReadTimeout(10000); dconn.setDoOutput(true)
                        dconn.getOutputStream().withWriter("UTF-8") { it << dq }
                        def dresp = dconn.getInputStream().getText("UTF-8")
                        if (dresp.contains('"job":"' + job + '"')) {
                            println("[ci-bpmn-trigger] ${job} #${num} (${result}) -> SKIP (dedup: ACTIVE ci-flow already remediating this job)")
                            return
                        }
                    } catch (Throwable dt) {
                        println("[ci-bpmn-trigger] dedup check failed (${dt}) — spawning anyway")
                    }
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
println("[ci-bpmn-trigger] registered v7 (red build -> ci-flow; green PR fleet-wide -> merge-flow BPMN -> AI autonomous merge)")
