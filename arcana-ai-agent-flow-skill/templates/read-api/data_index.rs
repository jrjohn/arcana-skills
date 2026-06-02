//! Thin, read-only client for the Kogito **Data Index** GraphQL endpoint.
//!
//! The Data Index is the unified, queryable layer that both engines feed:
//! the Kogito **BPMN** engine (human/role decision flows) and **SonataFlow**
//! (fully-automated CNCF Serverless Workflows) emit process/task events to
//! Kafka, which the Data Index consumes into PostgreSQL and exposes via
//! GraphQL. This client is engine-agnostic: a `ProcessInstance` is the same
//! shape regardless of which engine produced it.
//!
//! We talk to Data Index's stable GraphQL contract rather than its internal
//! PostgreSQL tables (protobuf blobs) on purpose — the schema is the
//! supported public surface and shields the read-API from engine internals.

use serde_json::{json, Value};

/// Read-only GraphQL client for the Kogito Data Index.
#[derive(Clone)]
pub struct WorkflowClient {
    http: reqwest::Client,
    graphql_url: String,
}

impl WorkflowClient {
    /// Build a client from the `DATA_INDEX_URL` env var
    /// (default `http://localhost:8180`). The `/graphql` path is appended.
    pub fn from_env() -> Self {
        let base = std::env::var("DATA_INDEX_URL")
            .unwrap_or_else(|_| "http://localhost:8180".to_string());
        Self::new(&base)
    }

    /// Build a client against an explicit Data Index base URL.
    pub fn new(base_url: &str) -> Self {
        let graphql_url = format!("{}/graphql", base_url.trim_end_matches('/'));
        Self {
            http: reqwest::Client::new(),
            graphql_url,
        }
    }

    /// Execute a GraphQL query with variables and return the `data` object.
    ///
    /// Returns `Err` on transport failure or any GraphQL `errors` entry so the
    /// controller can surface a clean error response.
    pub async fn query(&self, query: &str, variables: Value) -> Result<Value, String> {
        let resp = self
            .http
            .post(&self.graphql_url)
            .json(&json!({ "query": query, "variables": variables }))
            .send()
            .await
            .map_err(|e| format!("data-index request failed: {e}"))?;

        if !resp.status().is_success() {
            return Err(format!("data-index returned HTTP {}", resp.status()));
        }

        let body: Value = resp
            .json()
            .await
            .map_err(|e| format!("data-index returned non-JSON: {e}"))?;

        if let Some(errors) = body.get("errors") {
            if !errors.is_null() {
                return Err(format!("data-index GraphQL errors: {errors}"));
            }
        }

        Ok(body.get("data").cloned().unwrap_or(Value::Null))
    }
}
