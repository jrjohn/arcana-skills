//! SonataFlow (CNCF Serverless Workflow) definition parsing for the flow-diagram.
//!
//! The Kogito Data Index exposes a SonataFlow definition's *nodes* but not its
//! *edges*. Unlike BPMN, the topology lives in the `.sw.yaml`/`.sw.json` file as
//! `start` + per-state `transition` + `end`. This parses those into logical
//! edges **by state name** (Start→<start>, <state>→<transition>, <end>→End);
//! the controller maps the names onto the Data Index node ids.

use std::collections::HashMap;
use std::path::Path;
use serde_json::Value;

/// Parsed topology of one serverless workflow.
#[derive(Clone, Debug, Default)]
pub struct SwfProcess {
    pub start_state: Option<String>,
    /// (from-state, to-state) by state name
    pub transitions: Vec<(String, String)>,
    /// states with `end: true`
    pub end_states: Vec<String>,
}

/// In-memory index of serverless workflows keyed by `id`.
#[derive(Clone, Default)]
pub struct SwfRepository {
    processes: HashMap<String, SwfProcess>,
}

impl SwfRepository {
    /// Load every `*.sw.yaml` / `*.sw.json` under `SWF_DIR`
    /// (default `./kogito-swf/src/main/resources`). Missing dir -> empty.
    pub fn from_env() -> Self {
        let dir = std::env::var("SWF_DIR")
            .unwrap_or_else(|_| "./kogito-swf/src/main/resources".to_string());
        let mut repo = Self::default();
        repo.load_dir(Path::new(&dir));
        repo
    }

    fn load_dir(&mut self, dir: &Path) {
        let entries = match std::fs::read_dir(dir) {
            Ok(e) => e,
            Err(_) => return,
        };
        for entry in entries.flatten() {
            let path = entry.path();
            if path.is_dir() {
                self.load_dir(&path);
                continue;
            }
            let name = path.file_name().and_then(|s| s.to_str()).unwrap_or("");
            if !(name.ends_with(".sw.yaml") || name.ends_with(".sw.yml") || name.ends_with(".sw.json")) {
                continue;
            }
            if let Ok(text) = std::fs::read_to_string(&path) {
                if let Some((id, proc)) = parse_swf(&text) {
                    self.processes.insert(id, proc);
                }
            }
        }
    }

    pub fn get(&self, process_id: &str) -> Option<&SwfProcess> {
        self.processes.get(process_id)
    }
}

/// A `start` / `transition` field may be a bare state-name string or an object
/// (`{stateName: X}` / `{nextState: X}`); pull the state name out of either.
fn state_ref(v: &Value) -> Option<String> {
    match v {
        Value::String(s) => Some(s.clone()),
        Value::Object(o) => o
            .get("stateName")
            .or_else(|| o.get("nextState"))
            .and_then(Value::as_str)
            .map(str::to_string),
        _ => None,
    }
}

fn parse_swf(text: &str) -> Option<(String, SwfProcess)> {
    // serde_json::Value implements Deserialize, so serde_yaml can target it;
    // this also parses `.sw.json` (JSON is a YAML subset).
    let doc: Value = serde_yaml::from_str(text).ok()?;
    let id = doc.get("id").and_then(Value::as_str)?.to_string();

    let mut p = SwfProcess {
        start_state: doc.get("start").and_then(state_ref),
        ..Default::default()
    };

    if let Some(states) = doc.get("states").and_then(Value::as_array) {
        for st in states {
            let name = match st.get("name").and_then(Value::as_str) {
                Some(n) => n.to_string(),
                None => continue,
            };
            if let Some(to) = st.get("transition").and_then(state_ref) {
                p.transitions.push((name.clone(), to));
            }
            let is_end = match st.get("end") {
                Some(Value::Bool(b)) => *b,
                Some(Value::Object(_)) => true,
                _ => false,
            };
            if is_end {
                p.end_states.push(name);
            }
        }
    }
    Some((id, p))
}
