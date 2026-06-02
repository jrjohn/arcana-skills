//! Workflow monitoring REST API controller (read-only).
//!
//! Engine-agnostic read layer over the Kogito **Data Index**: the same
//! endpoints surface instances from the BPMN engine (human/role decision
//! flows) and from SonataFlow (automated flows), because both feed the Data
//! Index. The dashboard polls these endpoints; nothing here drives an engine.
//!
//! Endpoints (mounted under `/api/v1/workflows`):
//!   GET /processes               list process instances (filter: status, role)
//!   GET /processes/:id           one instance + variables
//!   GET /processes/:id/timeline  node + user-task timeline (for flow highlight)
//!   GET /definitions/:id/graph   definition nodes + per-node role (edges: B.2)

use axum::{
    extract::{Path, Query, State},
    http::StatusCode,
    response::IntoResponse,
    routing::get,
    Json, Router,
};
use serde::{Deserialize, Serialize};
use serde_json::{json, Map, Value};

use crate::state::AppState;

/// Create the workflows router.
pub fn router() -> Router<AppState> {
    Router::new()
        .route("/processes", get(list_processes))
        .route("/processes/:id", get(get_process))
        .route("/processes/:id/timeline", get(process_timeline))
        .route("/definitions/:id/graph", get(definition_graph))
}

// ============================================================================
// Request/Response types
// ============================================================================

/// Query parameters for the process list.
#[derive(Debug, Deserialize)]
pub struct ProcessListParams {
    /// Comma-separated states (e.g. `ACTIVE,ERROR`). Case-insensitive.
    pub status: Option<String>,
    /// Filter to instances that have a user task owned by this group/role.
    pub role: Option<String>,
    #[serde(default = "default_limit")]
    pub limit: i64,
    #[serde(default)]
    pub offset: i64,
}

fn default_limit() -> i64 {
    50
}

#[derive(Debug, Serialize)]
struct ErrorBody {
    error: String,
    code: String,
}

fn upstream_error(msg: String) -> (StatusCode, Json<ErrorBody>) {
    (
        StatusCode::BAD_GATEWAY,
        Json(ErrorBody {
            error: msg,
            code: "DATA_INDEX_ERROR".to_string(),
        }),
    )
}

/// Pull an array out of a GraphQL `data` object by key, defaulting to empty.
fn array_at(data: &Value, key: &str) -> Vec<Value> {
    data.get(key)
        .and_then(Value::as_array)
        .cloned()
        .unwrap_or_default()
}

/// Map every known processId to its engine label, derived from the Data Index
/// `ProcessDefinition.type` (BPMN engine vs SonataFlow). One cheap query covers
/// all definitions across both engines.
async fn engine_type_map(
    client: &crate::clients::WorkflowClient,
) -> std::collections::HashMap<String, String> {
    let mut m = std::collections::HashMap::new();
    if let Ok(d) = client
        .query("{ ProcessDefinitions { id type } }", json!({}))
        .await
    {
        for def in array_at(&d, "ProcessDefinitions") {
            if let (Some(id), Some(t)) = (
                def.get("id").and_then(Value::as_str),
                def.get("type").and_then(Value::as_str),
            ) {
                m.insert(id.to_string(), engine_label(t));
            }
        }
    }
    m
}

/// Map a Data Index definition type to our engine label.
fn engine_label(t: &str) -> String {
    match t {
        "BPMN" => "bpmn".to_string(),     // Kogito BPMN (human/role flows)
        "SW" => "swf".to_string(),        // SonataFlow (automated flows)
        other => other.to_lowercase(),
    }
}

/// Name of the node a process instance is currently sitting at: the entered-but-
/// not-exited node with the latest `enter` timestamp. `None` once the instance
/// has left every node (completed/aborted).
fn current_node(process: &Value) -> Option<String> {
    process
        .get("nodes")
        .and_then(Value::as_array)?
        .iter()
        .filter(|n| {
            n.get("enter").and_then(Value::as_str).is_some()
                && n.get("exit").map(Value::is_null).unwrap_or(true)
        })
        .max_by_key(|n| n.get("enter").and_then(Value::as_str).unwrap_or("").to_string())
        .and_then(|n| n.get("name").and_then(Value::as_str).map(str::to_string))
}

// ============================================================================
// Handlers
// ============================================================================

/// List process instances, newest first. Engine-agnostic.
async fn list_processes(
    State(state): State<AppState>,
    Query(params): Query<ProcessListParams>,
) -> impl IntoResponse {
    let client = &state.workflow_client;

    // Optional state filter -> Data Index `ProcessInstanceState` enum array.
    let states: Option<Vec<String>> = params.status.as_ref().map(|s| {
        s.split(',')
            .map(|t| t.trim().to_uppercase())
            .filter(|t| !t.is_empty())
            .collect()
    });

    let query = if states.is_some() {
        r#"query($state: [ProcessInstanceState!], $limit: Int, $offset: Int) {
            ProcessInstances(where: {state: {in: $state}}, orderBy: {start: DESC},
                             pagination: {limit: $limit, offset: $offset}) {
                id processId processName state start end businessKey
                nodes { name type enter exit }
            }
        }"#
    } else {
        r#"query($limit: Int, $offset: Int) {
            ProcessInstances(orderBy: {start: DESC},
                             pagination: {limit: $limit, offset: $offset}) {
                id processId processName state start end businessKey
                nodes { name type enter exit }
            }
        }"#
    };

    let vars = match &states {
        Some(s) => json!({ "state": s, "limit": params.limit, "offset": params.offset }),
        None => json!({ "limit": params.limit, "offset": params.offset }),
    };

    let data = match client.query(query, vars).await {
        Ok(d) => d,
        Err(e) => return upstream_error(e).into_response(),
    };
    let mut processes = array_at(&data, "ProcessInstances");

    // Optional role filter: keep instances that have a user task for this group.
    if let Some(role) = params.role.as_ref().filter(|r| !r.is_empty()) {
        let role_q = r#"query($groups: [String!]) {
            UserTaskInstances(where: {potentialGroups: {containsAny: $groups}}) {
                processInstanceId
            }
        }"#;
        match client.query(role_q, json!({ "groups": [role] })).await {
            Ok(d) => {
                let allowed: std::collections::HashSet<String> = array_at(&d, "UserTaskInstances")
                    .iter()
                    .filter_map(|t| t.get("processInstanceId").and_then(Value::as_str))
                    .map(|s| s.to_string())
                    .collect();
                processes.retain(|p| {
                    p.get("id")
                        .and_then(Value::as_str)
                        .map(|id| allowed.contains(id))
                        .unwrap_or(false)
                });
            }
            Err(e) => return upstream_error(e).into_response(),
        }
    }

    // Annotate each instance: engine (BPMN vs SWF), and the current node + its
    // role (so the list shows "where it is" and "who owns it" without N+1 calls).
    let engines = engine_type_map(client).await;
    for p in processes.iter_mut() {
        let process_id = p
            .get("processId")
            .and_then(Value::as_str)
            .unwrap_or("")
            .to_string();
        let current = current_node(p);
        let current_role = current.as_ref().and_then(|name| {
            state
                .bpmn_repo
                .get(&process_id)
                .and_then(|b| b.role_by_name.get(name).cloned())
        });
        let engine = engines.get(&process_id).cloned();
        if let Some(obj) = p.as_object_mut() {
            obj.insert(
                "engine".to_string(),
                engine.map(Value::String).unwrap_or(Value::Null),
            );
            obj.insert(
                "currentNode".to_string(),
                current.map(Value::String).unwrap_or(Value::Null),
            );
            obj.insert(
                "currentRole".to_string(),
                current_role.map(Value::String).unwrap_or(Value::Null),
            );
            obj.remove("nodes"); // keep the list payload lean
        }
    }

    let total = processes.len();
    Json(json!({ "processes": processes, "total": total })).into_response()
}

/// Get a single process instance with its variables.
async fn get_process(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> impl IntoResponse {
    let query = r#"query($id: String) {
        ProcessInstances(where: {id: {equal: $id}}) {
            id processId processName state start end businessKey variables
        }
    }"#;

    let data = match state.workflow_client.query(query, json!({ "id": id })).await {
        Ok(d) => d,
        Err(e) => return upstream_error(e).into_response(),
    };

    match array_at(&data, "ProcessInstances").into_iter().next() {
        Some(mut p) => {
            let process_id = p.get("processId").and_then(Value::as_str).unwrap_or("").to_string();
            let engine = engine_type_map(&state.workflow_client).await.remove(&process_id);
            if let Some(obj) = p.as_object_mut() {
                obj.insert(
                    "engine".to_string(),
                    engine.map(Value::String).unwrap_or(Value::Null),
                );
            }
            Json(p).into_response()
        }
        None => (
            StatusCode::NOT_FOUND,
            Json(ErrorBody {
                error: format!("process instance {id} not found"),
                code: "NOT_FOUND".to_string(),
            }),
        )
            .into_response(),
    }
}

/// Timeline of nodes + user tasks for a process instance (drives flow highlight).
async fn process_timeline(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> impl IntoResponse {
    let query = r#"query($id: String) {
        ProcessInstances(where: {id: {equal: $id}}) {
            id processId state start end
            nodes { id name type enter exit }
        }
        UserTaskInstances(where: {processInstanceId: {equal: $id}}, orderBy: {started: ASC}) {
            id name state potentialGroups actualOwner started completed
        }
    }"#;

    let data = match state.workflow_client.query(query, json!({ "id": id })).await {
        Ok(d) => d,
        Err(e) => return upstream_error(e).into_response(),
    };

    let instance = match array_at(&data, "ProcessInstances").into_iter().next() {
        Some(i) => i,
        None => {
            return (
                StatusCode::NOT_FOUND,
                Json(ErrorBody {
                    error: format!("process instance {id} not found"),
                    code: "NOT_FOUND".to_string(),
                }),
            )
                .into_response()
        }
    };
    let nodes = instance.get("nodes").cloned().unwrap_or_else(|| json!([]));
    let tasks = array_at(&data, "UserTaskInstances");

    Json(json!({
        "id": instance.get("id"),
        "processId": instance.get("processId"),
        "state": instance.get("state"),
        "start": instance.get("start"),
        "end": instance.get("end"),
        "nodes": nodes,
        "tasks": tasks,
    }))
    .into_response()
}

/// Definition graph: nodes (each annotated with the responsible role), edges
/// (sequence flows), and process-level roles. Node list/types come from the
/// Data Index; edges and authoritative per-node roles come from the parsed
/// BPMN (its `GroupId` data inputs cover every node, even ones no instance has
/// reached yet); instance-observed groups are used as a fallback.
async fn definition_graph(
    State(state): State<AppState>,
    Path(id): Path<String>,
) -> impl IntoResponse {
    let query = r#"query($id: String) {
        ProcessDefinitions(where: {id: {equal: $id}}) {
            id name version roles
            nodes { id name type uniqueId }
        }
        UserTaskInstances(where: {processId: {equal: $id}}) {
            name potentialGroups
        }
    }"#;

    let data = match state.workflow_client.query(query, json!({ "id": &id })).await {
        Ok(d) => d,
        Err(e) => return upstream_error(e).into_response(),
    };

    let def = match array_at(&data, "ProcessDefinitions").into_iter().next() {
        Some(d) => d,
        None => {
            return (
                StatusCode::NOT_FOUND,
                Json(ErrorBody {
                    error: format!("process definition {id} not found"),
                    code: "NOT_FOUND".to_string(),
                }),
            )
                .into_response()
        }
    };

    // Fallback: node name -> first group observed on its user-task instances.
    let mut role_by_name: std::collections::HashMap<String, String> =
        std::collections::HashMap::new();
    for t in array_at(&data, "UserTaskInstances") {
        let name = t.get("name").and_then(Value::as_str).unwrap_or("");
        let group = t
            .get("potentialGroups")
            .and_then(Value::as_array)
            .and_then(|g| g.first())
            .and_then(Value::as_str);
        if let (false, Some(g)) = (name.is_empty(), group) {
            role_by_name
                .entry(name.to_string())
                .or_insert_with(|| g.to_string());
        }
    }

    // Authoritative: BPMN edges + node-id -> role (GroupId data input).
    let bpmn = state.bpmn_repo.get(&id);
    let edges = bpmn
        .map(|b| serde_json::to_value(&b.edges).unwrap_or_else(|_| json!([])))
        .unwrap_or_else(|| json!([]));

    let nodes: Vec<Value> = def
        .get("nodes")
        .and_then(Value::as_array)
        .cloned()
        .unwrap_or_default()
        .into_iter()
        .map(|n| {
            let mut obj: Map<String, Value> = n.as_object().cloned().unwrap_or_default();
            let node_id = obj.get("id").and_then(Value::as_str).unwrap_or("");
            let name = obj.get("name").and_then(Value::as_str).unwrap_or("");
            // prefer BPMN (by node id), fall back to instance-observed (by name)
            let role = bpmn
                .and_then(|b| b.node_roles.get(node_id).cloned())
                .or_else(|| role_by_name.get(name).cloned());
            obj.insert(
                "role".to_string(),
                role.map(Value::String).unwrap_or(Value::Null),
            );
            Value::Object(obj)
        })
        .collect();

    Json(json!({
        "id": def.get("id"),
        "name": def.get("name"),
        "version": def.get("version"),
        "roles": def.get("roles"),
        "nodes": nodes,
        "edges": edges,
    }))
    .into_response()
}
