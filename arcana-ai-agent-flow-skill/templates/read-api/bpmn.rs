//! BPMN definition parsing for the flow-diagram graph.
//!
//! The Kogito Data Index exposes a definition's *nodes* but not its *edges*
//! (sequence flows). The BPMN file is the authoritative source for both the
//! flow topology and the per-node role (each user task carries a `GroupId`
//! data input, e.g. `ai` / `jenkins`). This module parses the BPMN files in a
//! configured directory once at startup and indexes them by process id.
//!
//! Only the read-side shape the dashboard needs is extracted; nothing here
//! executes or mutates a process.

use std::collections::HashMap;
use std::path::Path;

/// A directed sequence flow between two nodes.
#[derive(Clone, Debug, serde::Serialize)]
pub struct Edge {
    pub id: String,
    pub source: String,
    pub target: String,
}

/// Parsed view of one BPMN process definition.
#[derive(Clone, Debug, Default)]
pub struct BpmnProcess {
    pub edges: Vec<Edge>,
    /// node id -> role/group (from each user task's `GroupId` data input)
    pub node_roles: HashMap<String, String>,
    /// node name -> role/group (instance node events identify nodes by name)
    pub role_by_name: HashMap<String, String>,
}

/// In-memory index of BPMN definitions keyed by `<process id>`.
#[derive(Clone, Default)]
pub struct BpmnRepository {
    processes: HashMap<String, BpmnProcess>,
}

impl BpmnRepository {
    /// Load every `*.bpmn` / `*.bpmn2` under `BPMN_DIR`
    /// (default `./kogito-bpmn/src/main/resources`). Missing dir -> empty repo
    /// (the graph endpoint then simply returns no edges).
    pub fn from_env() -> Self {
        let dir = std::env::var("BPMN_DIR")
            .unwrap_or_else(|_| "./kogito-bpmn/src/main/resources".to_string());
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
            } else if matches!(
                path.extension().and_then(|s| s.to_str()),
                Some("bpmn") | Some("bpmn2")
            ) {
                if let Ok(xml) = std::fs::read_to_string(&path) {
                    for (id, proc) in parse_bpmn(&xml) {
                        self.processes.insert(id, proc);
                    }
                }
            }
        }
    }

    /// Look up a parsed process by its id.
    pub fn get(&self, process_id: &str) -> Option<&BpmnProcess> {
        self.processes.get(process_id)
    }
}

/// Parse all `<process>` elements in a BPMN document into [`BpmnProcess`] views.
///
/// Matching is by element *local name* so the `bpmn2:` / `bpmn:` prefix the
/// file happens to use does not matter.
fn parse_bpmn(xml: &str) -> Vec<(String, BpmnProcess)> {
    let doc = match roxmltree::Document::parse(xml) {
        Ok(d) => d,
        Err(_) => return Vec::new(),
    };

    let mut out = Vec::new();
    for process in doc
        .descendants()
        .filter(|n| n.is_element() && n.tag_name().name() == "process")
    {
        let process_id = match process.attribute("id") {
            Some(id) => id.to_string(),
            None => continue,
        };

        let mut bpmn = BpmnProcess::default();

        // Edges: every sequenceFlow's sourceRef/targetRef are node ids.
        for flow in process
            .descendants()
            .filter(|n| n.is_element() && n.tag_name().name() == "sequenceFlow")
        {
            if let (Some(source), Some(target)) =
                (flow.attribute("sourceRef"), flow.attribute("targetRef"))
            {
                bpmn.edges.push(Edge {
                    id: flow.attribute("id").unwrap_or("").to_string(),
                    source: source.to_string(),
                    target: target.to_string(),
                });
            }
        }

        // Per-node role: each userTask binds a `GroupId` data input via a
        // dataInputAssociation whose <from> holds the group literal (e.g. "ai").
        for task in process
            .descendants()
            .filter(|n| n.is_element() && n.tag_name().name() == "userTask")
        {
            let task_id = match task.attribute("id") {
                Some(id) => id,
                None => continue,
            };
            if let Some(role) = extract_group_id(&task) {
                bpmn.node_roles.insert(task_id.to_string(), role.clone());
                if let Some(name) = task.attribute("name") {
                    bpmn.role_by_name.insert(name.to_string(), role);
                }
            }
        }

        out.push((process_id, bpmn));
    }
    out
}

/// Find the `GroupId` data input value for a user task.
///
/// Locates the `dataInput` named `GroupId`, then the `dataInputAssociation`
/// whose `<targetRef>` points at it, and returns its `<assignment><from>` text.
fn extract_group_id(task: &roxmltree::Node) -> Option<String> {
    // id of the dataInput named "GroupId"
    let group_input_id = task
        .descendants()
        .filter(|n| n.is_element() && n.tag_name().name() == "dataInput")
        .find(|n| n.attribute("name") == Some("GroupId"))
        .and_then(|n| n.attribute("id"))?;

    for assoc in task
        .descendants()
        .filter(|n| n.is_element() && n.tag_name().name() == "dataInputAssociation")
    {
        let targets_group = assoc
            .descendants()
            .filter(|n| n.is_element() && n.tag_name().name() == "targetRef")
            .any(|n| n.text().map(str::trim) == Some(group_input_id));
        if !targets_group {
            continue;
        }
        let from_text = assoc
            .descendants()
            .filter(|n| n.is_element() && n.tag_name().name() == "from")
            .find_map(|n| n.text())
            .map(|t| t.trim().to_string())
            .filter(|t| !t.is_empty());
        if from_text.is_some() {
            return from_text;
        }
    }
    None
}
