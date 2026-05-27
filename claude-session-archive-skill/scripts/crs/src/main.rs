// crs — Rust port of claude-session-archive Python helpers.
//
// Subcommands:
//   build         JSONL → SQLite (or PG with --features pg-backend) incremental ingest
//   csearch       FTS5 lexical search
//   vsearch       semantic KNN search (over msg_vec)
//   vsearch-since time-bounded vsearch (used by gen-recent)
//   gen-recent    replace gen-recent-context.sh (skip-guard + vsearch + write file)
//   embed-missing parallel backfill of msg → msg_vec (replaces embed_parallel.py)
//   embed-text    debug helper — embed one string and print first 5 dims
//   doctor        health check (tooling / DB / schedule / hooks / Ollama / stale)
//   prune-vec     drop msg_vec rows whose rowid no longer exists in msg
//
// Optional with --features pg-backend (see references/pg-backend.md):
//   pgsearch      Query remote PG+pgvector (auto-uses pgsearchd daemon if running)
//   pgsearchd     Run pgsearch daemon (persistent r2d2 connection pool over unix socket)

use anyhow::{Context, Result, anyhow, bail};
use base64::Engine as _;
use chrono::{Local, Utc};
use clap::{Parser, Subcommand};
use rusqlite::{Connection, OpenFlags, params};
use serde::Deserialize;
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::collections::HashSet;
use std::env;
use std::fs;
use std::io::{BufRead, BufReader, Read, Write};
use std::path::{Path, PathBuf};
use std::sync::Mutex;
use std::time::SystemTime;

const OLLAMA_URL_DEFAULT: &str = "http://localhost:11434/api/embed";

fn ollama_url() -> String {
    // Env override priority: CRS_OLLAMA_URL (full URL incl. /api/embed)
    //   > OLLAMA_HOST (host root, append /api/embed)
    //   > default localhost. Lets containerized deploys point at e.g. http://ollama:11434
    if let Ok(u) = std::env::var("CRS_OLLAMA_URL") { return u; }
    if let Ok(h) = std::env::var("OLLAMA_HOST") {
        let trimmed = h.trim_end_matches('/');
        return format!("{}/api/embed", trimmed);
    }
    OLLAMA_URL_DEFAULT.to_string()
}
const MODEL: &str = "bge-m3";
const VEC_DIM: usize = 1024;

// ─────────────────────────── CLI ───────────────────────────

#[derive(Parser)]
#[command(name = "crs", about = "Rust port of claude-session-archive helpers")]
struct Cli {
    #[command(subcommand)]
    cmd: Cmd,
}

#[derive(Subcommand)]
enum Cmd {
    /// Incremental JSONL → SQLite ingest (replaces build.py)
    Build {
        /// Skip the post-ingest embed step
        #[arg(long)]
        no_embed: bool,
        /// Skip the post-ingest auto_recent refresh
        #[arg(long)]
        no_refresh: bool,
        /// Embed-missing parallelism
        #[arg(long, default_value = "8")]
        workers: usize,
        /// Comma-separated project-name prefixes to constrain the post-ingest
        /// embed-missing phase. Without this, embed-missing picks every
        /// row with embedding IS NULL globally (cross-host contention).
        /// Example for Mac:     '-Users-jrjohn'
        /// Example for bluesea: '-root,-workspace-arcana-book,-data'
        #[arg(long = "project-prefix")]
        project_prefix: Option<String>,
    },
    /// FTS5 lexical search
    Csearch {
        query: String,
        project: Option<String>,
        #[arg(long, default_value = "20")]
        limit: usize,
        /// Exclude image_ocr rows from results (default: include with rank de-emphasis)
        #[arg(long = "no-img")]
        no_img: bool,
        /// Truncate to 180-char snippet per hit. Use for credential / short-token lookups
        /// where full content is noise. Default since v1.17 is full content.
        #[arg(long)]
        snippet: bool,
        /// Deprecated since v1.17 — full is now the default, this flag is a no-op kept
        /// for backwards compat with old scripts / docs.
        #[arg(long)]
        full: bool,
        /// Prefix each hit with `id=<rowid> sid=<session_id[..8]>` for level-2 drill-down
        #[arg(long = "with-id")]
        with_id: bool,
    },
    /// Semantic KNN search
    Vsearch {
        query: String,
        project: Option<String>,
        #[arg(long, default_value = "10")]
        limit: usize,
        /// Exclude image_ocr rows from results (default: include with rank de-emphasis)
        #[arg(long = "no-img")]
        no_img: bool,
    },
    /// Time-bounded semantic search (used by gen-recent)
    VsearchSince {
        #[arg(long)]
        query: String,
        #[arg(long)]
        project: String,
        #[arg(long, default_value = "48")]
        hours: i64,
        #[arg(long, default_value = "10")]
        limit: usize,
        #[arg(long = "min-len", default_value = "30")]
        min_len: usize,
        #[arg(long = "max-len", default_value = "600")]
        max_len: usize,
        #[arg(long = "max-distance", default_value = "0.65")]
        max_distance: f64,
        #[arg(long = "max-snippet", default_value = "180")]
        max_snippet: usize,
        #[arg(long, default_value = "400")]
        knn: usize,
    },
    /// Replace gen-recent-context.sh — skip-guard + vsearch + write auto_recent.md
    GenRecent {
        #[arg(long)]
        force: bool,
    },
    /// Parallel embed of unembedded msg rows
    EmbedMissing {
        #[arg(long, default_value = "8")]
        workers: usize,
        #[arg(long, default_value = "0")]
        limit: usize,
        /// Comma-separated project-name prefixes to constrain which rows to
        /// embed. Without this, picks every msg with embedding IS NULL.
        #[arg(long = "project-prefix")]
        project_prefix: Option<String>,
    },
    /// Embed one string and print first 5 dims (debug helper)
    EmbedText { text: String },
    /// OCR image content blocks referenced by [IMG:<sha>] sentinels in msg.content,
    /// inserting results into image_ocr_cache + image_ocr. Mirrors embed-missing.
    #[cfg(feature = "pg-backend")]
    OcrMissing {
        #[arg(long, default_value = "2")]
        workers: usize,
        #[arg(long, default_value = "0")]
        limit: usize,
        /// Comma-separated project-name prefixes — same semantics as
        /// embed-missing. Limits OCR to rows whose jsonl is on the
        /// local filesystem (Mac vs bluesea split).
        #[arg(long = "project-prefix")]
        project_prefix: Option<String>,
    },
    /// Health check — verify install state, schedule, hooks, model, DB consistency
    Doctor,
    /// Prune stale rowids from msg_vec (rowid present in msg_vec but not in msg)
    PruneVec {
        /// Show what would be deleted without modifying the DB
        #[arg(long)]
        dry_run: bool,
    },
    /// Query remote PG+pgvector. Auto-uses daemon if running. (pg-backend feature)
    #[cfg(feature = "pg-backend")]
    Pgsearch {
        query: String,
        /// Lexical FTS (default if no mode flag)
        #[arg(long)]
        fts: bool,
        /// Vector semantic (Ollama bge-m3 1024d)
        #[arg(long)]
        vec: bool,
        /// RRF hybrid (vec 0.7 + fts 0.3)
        #[arg(long)]
        hybrid: bool,
        #[arg(long, default_value = "10")]
        limit: usize,
        /// JSON output instead of formatted
        #[arg(long)]
        json: bool,
        /// Skip daemon, force direct TLS connection
        #[arg(long)]
        no_daemon: bool,
        /// Exclude image_ocr rows from results (default: include with rank de-emphasis)
        #[arg(long = "no-img")]
        no_img: bool,
    },
    /// Run pgsearch daemon (r2d2 connection pool over unix socket). (pg-backend + unix)
    #[cfg(all(feature = "pg-backend", unix))]
    Pgsearchd {
        /// Pool size (default 4)
        #[arg(long, default_value = "4")]
        pool_size: u32,
        /// Foreground mode (don't detach). Default behavior.
        #[arg(long, hide = true)]
        foreground: bool,
    },
}

// ─────────────────────────── helpers ───────────────────────────

fn home() -> PathBuf {
    dirs::home_dir().expect("$HOME unresolved")
}

fn db_path() -> PathBuf {
    if let Ok(p) = env::var("CRS_DB") {
        if !p.is_empty() {
            return PathBuf::from(p);
        }
    }
    home().join("claude-archive/sessions.db")
}

/// Register sqlite-vec as an auto-extension. Called once at process start.
/// After this, every new sqlite3 Connection auto-loads vec0 — no dylib at runtime.
fn register_vec_extension() {
    use rusqlite::ffi::{sqlite3, sqlite3_api_routines, sqlite3_auto_extension};
    use std::sync::Once;
    type EntryPoint = unsafe extern "C" fn(
        *mut sqlite3,
        *mut *mut std::os::raw::c_char,
        *const sqlite3_api_routines,
    ) -> std::os::raw::c_int;
    static REG: Once = Once::new();
    REG.call_once(|| unsafe {
        let f: EntryPoint = std::mem::transmute(sqlite_vec::sqlite3_vec_init as *const ());
        sqlite3_auto_extension(Some(f));
    });
}

fn open_db_with_vec() -> Result<Connection> {
    register_vec_extension();
    let conn = Connection::open_with_flags(
        db_path(),
        OpenFlags::SQLITE_OPEN_READ_WRITE | OpenFlags::SQLITE_OPEN_NO_MUTEX | OpenFlags::SQLITE_OPEN_URI,
    )
    .with_context(|| format!("opening {}", db_path().display()))?;
    conn.pragma_update(None, "mmap_size", 536_870_912i64)?;
    conn.pragma_update(None, "cache_size", -524_288i64)?;
    conn.execute_batch(
        "CREATE VIRTUAL TABLE IF NOT EXISTS msg_vec USING vec0(embedding float[1024] distance_metric=cosine)",
    )?;
    Ok(conn)
}

#[cfg(not(feature = "pg-backend"))]
fn open_db_readonly() -> Result<Connection> {
    let conn = Connection::open_with_flags(
        db_path(),
        OpenFlags::SQLITE_OPEN_READ_ONLY | OpenFlags::SQLITE_OPEN_NO_MUTEX,
    )?;
    conn.pragma_update(None, "mmap_size", 536_870_912i64)?;
    Ok(conn)
}

#[derive(Deserialize)]
struct EmbedResponse {
    embeddings: Vec<Vec<f32>>,
}

fn http_client() -> Result<reqwest::blocking::Client> {
    Ok(reqwest::blocking::Client::builder()
        .timeout(std::time::Duration::from_secs(60))
        .build()?)
}

fn embed_text(client: &reqwest::blocking::Client, text: &str) -> Result<Vec<f32>> {
    let body = serde_json::json!({ "model": MODEL, "input": text });
    let resp: EmbedResponse = client.post(&ollama_url()).json(&body).send()?.error_for_status()?.json()?;
    let v = resp
        .embeddings
        .into_iter()
        .next()
        .ok_or_else(|| anyhow!("ollama returned no embedding"))?;
    if v.len() != VEC_DIM {
        bail!("expected {}-dim vector, got {}", VEC_DIM, v.len());
    }
    Ok(v)
}

#[cfg(not(feature = "pg-backend"))]
fn vec_to_blob(v: &[f32]) -> Vec<u8> {
    let mut out = Vec::with_capacity(v.len() * 4);
    for f in v {
        out.extend_from_slice(&f.to_le_bytes());
    }
    out
}

// ─────────────────────────── csearch ───────────────────────────

#[cfg(not(feature = "pg-backend"))]
fn cmd_csearch(query: &str, project: Option<&str>, limit: usize, _no_img: bool, snippet: bool, with_id: bool) -> Result<()> {
    let conn = open_db_readonly()?;
    // Always pull the full content + rowid + session_id; truncation now happens in
    // Rust so `--full` can opt out of it. Newline/tab flattening still done in SQL.
    let sql = match project {
        Some(_) => {
            "SELECT m.rowid, m.session_id, substr(m.ts,1,16), m.project, m.role, COALESCE(m.tool_name,'-'), \
             replace(replace(m.content, X'0A',' '), X'09',' ') \
             FROM msg m WHERE m.rowid IN (SELECT rowid FROM msg_fts WHERE content MATCH ?1) \
             AND m.project LIKE ?2 ORDER BY m.ts DESC LIMIT ?3"
        }
        None => {
            "SELECT m.rowid, m.session_id, substr(m.ts,1,16), m.project, m.role, COALESCE(m.tool_name,'-'), \
             replace(replace(m.content, X'0A',' '), X'09',' ') \
             FROM msg m WHERE m.rowid IN (SELECT rowid FROM msg_fts WHERE content MATCH ?1) \
             ORDER BY m.ts DESC LIMIT ?2"
        }
    };
    let mut stmt = conn.prepare(sql)?;
    let proj_pat = project.map(|p| format!("%{}%", p));
    let map_row = |r: &rusqlite::Row<'_>| -> rusqlite::Result<(i64, String, String, String, String, String, String)> {
        Ok((
            r.get::<_, i64>(0)?,
            r.get::<_, String>(1)?,
            r.get::<_, String>(2)?,
            r.get::<_, String>(3)?,
            r.get::<_, String>(4)?,
            r.get::<_, String>(5)?,
            r.get::<_, String>(6)?,
        ))
    };
    let rows = if let Some(pat) = &proj_pat {
        stmt.query_map(params![query, pat, limit as i64], map_row)?
            .collect::<Result<Vec<_>, _>>()?
    } else {
        stmt.query_map(params![query, limit as i64], map_row)?
            .collect::<Result<Vec<_>, _>>()?
    };

    if rows.is_empty() {
        eprintln!("(no results)");
        return Ok(());
    }
    for (rowid, sid, ts, proj, role, tool, content) in rows {
        let proj_short = proj.trim_start_matches('-').chars().take(40).collect::<String>();
        let tag = if tool == "-" { role } else { format!("{}/{}", role, tool) };
        let body = content.trim();
        let body = if snippet {
            body.chars().take(180).collect::<String>()
        } else {
            body.to_string()
        };
        if with_id {
            let sid_short: String = sid.chars().take(8).collect();
            println!("{}  [{}]  id={} sid={}  {}  {}", ts, proj_short, rowid, sid_short, tag, body);
        } else {
            println!("{}  [{}]  {}  {}", ts, proj_short, tag, body);
        }
    }
    Ok(())
}

#[cfg(feature = "pg-backend")]
fn cmd_csearch(query: &str, project: Option<&str>, limit: usize, no_img: bool, snippet: bool, with_id: bool) -> Result<()> {
    let (rows, _conn_ms, _q_ms, _src) = pg_search_dispatch("fts", query, project, limit, false, !no_img)?;
    if rows.is_empty() { eprintln!("(no results)"); return Ok(()); }
    if snippet && !with_id {
        for r in &rows { println!("{}", fmt_pg_row(r, 180)); }
        return Ok(());
    }
    // Default (full content) or --with-id path: inline format so we can show id+sid and/or skip the snippet cap.
    for r in &rows {
        let ts_str = match r.ts {
            Some(t) => t.format("%Y-%m-%dT%H:%M").to_string(),
            None    => "----------------".to_string(),
        };
        let proj_short: String = r.project.trim_start_matches('-').chars().take(40).collect();
        let tag = match r.tool_name.as_deref() {
            Some(t) if !t.is_empty() && t != "-" => format!("{}/{}", r.role, t),
            _ => r.role.clone(),
        };
        let body_raw = r.content.replace('\n', " ").replace('\t', " ");
        let body = if snippet { body_raw.chars().take(180).collect() } else { body_raw };
        if with_id {
            let id_str = r.id.map(|n| n.to_string()).unwrap_or_else(|| "-".to_string());
            let sid_short: String = r.session_id.chars().take(8).collect();
            println!("{}  [{}]  id={} sid={}  {}  {}", ts_str, proj_short, id_str, sid_short, tag, body);
        } else {
            println!("{}  [{}]  {}  {}", ts_str, proj_short, tag, body);
        }
    }
    Ok(())
}

// ─────────────────────────── vsearch ───────────────────────────

#[cfg(not(feature = "pg-backend"))]
fn cmd_vsearch(query: &str, project: Option<&str>, limit: usize, _no_img: bool) -> Result<()> {
    let conn = open_db_with_vec()?;
    let client = http_client()?;
    let qemb = embed_text(&client, query)?;
    let blob = vec_to_blob(&qemb);

    let sql = "WITH knn AS (SELECT rowid, distance FROM msg_vec WHERE embedding MATCH ?1 AND k = ?2 ORDER BY distance) \
               SELECT substr(m.ts,1,16), m.project, m.role, COALESCE(m.tool_name,'-'), \
                      printf('%.3f', knn.distance), \
                      substr(replace(replace(m.content, X'0A',' '), X'09',' '),1,200) \
               FROM knn JOIN msg m ON m.rowid = knn.rowid \
               WHERE (?3 IS NULL OR m.project LIKE ?3) \
               ORDER BY knn.distance LIMIT ?4";
    let mut stmt = conn.prepare(sql)?;
    let pool = (limit as i64).max(40) * 4;
    let proj_pat: Option<String> = project.map(|p| format!("%{}%", p));
    let rows = stmt
        .query_map(
            params![blob, pool, proj_pat, limit as i64],
            |r| {
                Ok((
                    r.get::<_, String>(0)?,
                    r.get::<_, String>(1)?,
                    r.get::<_, String>(2)?,
                    r.get::<_, String>(3)?,
                    r.get::<_, String>(4)?,
                    r.get::<_, String>(5)?,
                ))
            },
        )?
        .collect::<Result<Vec<_>, _>>()?;

    for (ts, proj, role, tool, sim, content) in rows {
        let proj_short = proj.trim_start_matches('-').chars().take(40).collect::<String>();
        let tag = if tool == "-" { role } else { format!("{}/{}", role, tool) };
        println!("{}  [{}]  {}  (d={})  {}", ts, proj_short, tag, sim, content.trim());
    }
    Ok(())
}

#[cfg(feature = "pg-backend")]
fn cmd_vsearch(query: &str, project: Option<&str>, limit: usize, no_img: bool) -> Result<()> {
    // hybrid (RRF: vec 0.7 + fts 0.3) so a query containing a literal identifier
    // (工號/IP/hostname) still surfaces the exact-match row even when semantic
    // phrasing pulls a generic roster/list above it. ~150ms slower than pure vec.
    let (rows, _conn_ms, _q_ms, _src) = pg_search_dispatch("hybrid", query, project, limit, false, !no_img)?;
    for r in &rows { println!("{}", fmt_pg_row(r, 200)); }
    Ok(())
}

// ─────────────────────────── vsearch-since ───────────────────────────

#[cfg(not(feature = "pg-backend"))]
#[allow(clippy::too_many_arguments)]
fn cmd_vsearch_since(
    query: &str,
    project: &str,
    hours: i64,
    limit: usize,
    min_len: usize,
    max_len: usize,
    max_distance: f64,
    max_snippet: usize,
    knn: usize,
) -> Result<Vec<String>> {
    let conn = open_db_with_vec()?;
    let client = http_client()?;
    let qemb = embed_text(&client, query)?;
    let blob = vec_to_blob(&qemb);

    let since = (Utc::now() - chrono::Duration::hours(hours)).format("%Y-%m-%dT%H:%M:%S").to_string();
    let proj_pat = format!("%{}%", project);

    let sql = "WITH knn AS (SELECT rowid, distance FROM msg_vec WHERE embedding MATCH ?1 AND k = ?2 ORDER BY distance) \
               SELECT substr(m.ts,1,16), m.role, COALESCE(m.tool_name,'-'), \
                      printf('%.3f', knn.distance), \
                      replace(replace(m.content, X'0A',' '), X'09',' ') \
               FROM knn JOIN msg m ON m.rowid = knn.rowid \
               WHERE m.project LIKE ?3 \
                 AND m.ts >= ?4 \
                 AND knn.distance <= ?5 \
                 AND length(m.content) BETWEEN ?6 AND ?7 \
                 AND m.content NOT LIKE '[TOOL_RESULT]%' \
                 AND m.content NOT LIKE '[TOOL_USE%' \
                 AND m.content NOT LIKE '[THINKING%' \
                 AND m.content NOT LIKE '<%' \
               ORDER BY knn.distance LIMIT ?8";
    let mut stmt = conn.prepare(sql)?;
    let rows = stmt.query_map(
        params![blob, knn as i64, proj_pat, since, max_distance, min_len as i64, max_len as i64, limit as i64],
        |r| Ok((
            r.get::<_, String>(0)?,
            r.get::<_, String>(1)?,
            r.get::<_, String>(2)?,
            r.get::<_, String>(3)?,
            r.get::<_, String>(4)?,
        )),
    )?.collect::<Result<Vec<_>, _>>()?;

    if rows.is_empty() {
        return Ok(vec![format!("_(vsearch-since: no hits in last {}h)_", hours)]);
    }
    let mut out = Vec::with_capacity(rows.len());
    for (ts, role, tool, sim, content) in rows {
        let snippet = content.trim();
        let truncated = if snippet.chars().count() > max_snippet {
            let mut s: String = snippet.chars().take(max_snippet.saturating_sub(3)).collect();
            s.push_str("...");
            s
        } else {
            snippet.to_string()
        };
        let tag = if tool == "-" { role } else { format!("{}/{}", role, tool) };
        out.push(format!("- **{}** `{}` (sim={}) — {}", ts, tag, sim, truncated));
    }
    Ok(out)
}

#[cfg(feature = "pg-backend")]
#[allow(clippy::too_many_arguments)]
fn cmd_vsearch_since(
    query: &str,
    project: &str,
    hours: i64,
    limit: usize,
    min_len: usize,
    max_len: usize,
    max_distance: f64,
    max_snippet: usize,
    knn: usize,
) -> Result<Vec<String>> {
    let _ = knn;  // unused on PG (HNSW handles it internally)
    let mut pg = pg_connect()?;
    let http = http_client()?;
    let qemb = embed_pg_query(&http, query)?;
    let lit = vec_literal(&qemb);

    let since = Utc::now() - chrono::Duration::hours(hours);
    let proj_pat = format!("%{}%", project);

    let sql = format!(
        "SELECT ts, role, COALESCE(tool_name,'-') AS tool,
                content,
                embedding <=> '{lit}'::vector AS dist
         FROM msg
         WHERE project LIKE $1
           AND ts >= $2
           AND embedding IS NOT NULL
           AND length(content) BETWEEN $3 AND $4
           AND content NOT LIKE '[TOOL_RESULT]%'
           AND content NOT LIKE '[TOOL_USE%'
           AND content NOT LIKE '[THINKING%'
           AND content NOT LIKE '<%'
           AND embedding <=> '{lit}'::vector <= $5
         ORDER BY embedding <=> '{lit}'::vector
         LIMIT $6"
    );
    let rows = pg.query(
        &sql,
        &[
            &proj_pat, &since,
            &(min_len as i64), &(max_len as i64),
            &max_distance,
            &(limit as i64),
        ],
    )?;

    if rows.is_empty() {
        return Ok(vec![format!("_(vsearch-since: no hits in last {}h)_", hours)]);
    }
    let mut out = Vec::with_capacity(rows.len());
    for r in rows.iter() {
        let ts: Option<chrono::DateTime<Utc>> = r.get(0);
        let ts_str = ts.map(|t| t.format("%Y-%m-%dT%H:%M").to_string()).unwrap_or_else(|| "----".to_string());
        let role: String = r.get(1);
        let tool: String = r.get(2);
        let content: String = r.get(3);
        let sim: f64 = r.get(4);
        let sim_s = format!("{:.3}", sim);
        let snippet = content.replace('\n', " ").replace('\t', " ");
        let snippet = snippet.trim();
        let truncated = if snippet.chars().count() > max_snippet {
            let mut s: String = snippet.chars().take(max_snippet.saturating_sub(3)).collect();
            s.push_str("...");
            s
        } else {
            snippet.to_string()
        };
        let tag = if tool == "-" { role } else { format!("{}/{}", role, tool) };
        out.push(format!("- **{}** `{}` (sim={}) — {}", ts_str, tag, sim_s, truncated));
    }
    Ok(out)
}

// ─────────────────────────── gen-recent ───────────────────────────

fn log_line(level: &str, msg: &str) {
    let log = home().join("claude-archive/gen-recent-context.log");
    if let Ok(mut f) = fs::OpenOptions::new().create(true).append(true).open(&log) {
        let _ = writeln!(f, "{} [{}] {}", Local::now().format("%Y-%m-%dT%H:%M:%S"), level, msg);
    }
}

fn resolve_slug() -> Result<String> {
    if let Ok(s) = env::var("CLAUDE_PROJECT_SLUG") {
        if !s.is_empty() { return Ok(s); }
    }
    // Try stdin JSON {"cwd": "..."}
    let mut buf = String::new();
    if !atty_stdin() {
        let _ = std::io::stdin().lock().read_to_string(&mut buf);
    }
    let project_dir = if !buf.is_empty() {
        if let Ok(v) = serde_json::from_str::<serde_json::Value>(&buf) {
            v.get("cwd").and_then(|c| c.as_str()).map(|s| s.to_string()).unwrap_or_default()
        } else { String::new() }
    } else { String::new() };
    let dir = if !project_dir.is_empty() {
        project_dir
    } else if let Ok(v) = env::var("CLAUDE_PROJECT_DIR") {
        v
    } else {
        env::current_dir()?.to_string_lossy().to_string()
    };
    let slug = dir.replace(['/', '\\'], "-").replace(':', "");
    Ok(slug)
}

#[cfg(unix)]
fn atty_stdin() -> bool {
    use std::os::fd::AsRawFd;
    unsafe { libc_isatty(std::io::stdin().as_raw_fd()) }
}
#[cfg(not(unix))]
fn atty_stdin() -> bool { true }

#[cfg(unix)]
unsafe fn libc_isatty(fd: i32) -> bool {
    unsafe extern "C" { fn isatty(fd: i32) -> i32; }
    unsafe { isatty(fd) != 0 }
}

fn mtime_secs(p: &Path) -> i64 {
    fs::metadata(p)
        .and_then(|m| m.modified())
        .map(|t| t.duration_since(SystemTime::UNIX_EPOCH).map(|d| d.as_secs() as i64).unwrap_or(0))
        .unwrap_or(0)
}

fn cmd_gen_recent(force: bool) -> Result<()> {
    let slug = resolve_slug()?;
    gen_recent_for_slug(&slug, force)
}

fn gen_recent_for_slug(slug: &str, force: bool) -> Result<()> {
    let archive = home().join("claude-archive");

    let mem_dir = home().join(format!(".claude/projects/{}/memory", slug));
    let pending = mem_dir.join("project_pending.md");
    let out_file = mem_dir.join("auto_recent.md");

    if !mem_dir.is_dir() {
        log_line("SKIP", &format!("unknown project slug={} (no memory dir)", slug));
        return Ok(());
    }

    // Skip guard — only consults local sqlite latest_msg_ts.
    // In pg-backend mode the local sqlite isn't populated; the guard then
    // falls back to pending_mtime only (acceptable: each pending update
    // re-triggers regen, which is the original intent anyway).
    let force_env = env::var("FORCE_REGEN").map(|v| v == "1").unwrap_or(false);
    if !force && !force_env && out_file.exists() {
        let last_gen_ts = mtime_secs(&out_file);
        let pending_ts = if pending.exists() { mtime_secs(&pending) } else { 0 };

        let latest_msg_ts: i64 = {
            #[cfg(not(feature = "pg-backend"))]
            {
                let db = archive.join("sessions.db");
                if !db.exists() {
                    log_line("SKIP", "no session.db");
                    return Ok(());
                }
                let conn = open_db_readonly()?;
                conn.query_row(
                    "SELECT IFNULL(strftime('%s', MAX(ts)), 0) FROM msg WHERE project = ?1",
                    params![slug],
                    |r| r.get::<_, String>(0).map(|s| s.parse::<i64>().unwrap_or(0))
                           .or_else(|_| r.get::<_, i64>(0)),
                ).unwrap_or(0)
            }
            #[cfg(feature = "pg-backend")]
            {
                // Try PG, but don't hard-fail: degrade to pending_mtime-only guard.
                pg_latest_msg_ts(slug).unwrap_or(0)
            }
        };

        if pending_ts <= last_gen_ts && latest_msg_ts <= last_gen_ts {
            log_line(
                "SKIP",
                &format!("no changes (slug={}, last_gen={}, pending={}, latest_msg={})", slug, last_gen_ts, pending_ts, latest_msg_ts),
            );
            return Ok(());
        }
    }

    // Build query from pending "## 待處理" section
    let mut snippets = Vec::new();
    let now = Local::now().format("%Y-%m-%d %H:%M").to_string();

    let mut header = vec![
        "---".to_string(),
        "name: 自動最近 context".to_string(),
        "description: 最近 48h 跟 pending 語意相關的對話 snippets（vsearch ranking）。pending 條目本身請讀 project_pending.md，不要兩邊都讀".to_string(),
        "type: project".to_string(),
        "auto-generated: true".to_string(),
        format!("last-update: {}", now),
        "---".to_string(),
        String::new(),
        "# 🔄 最近 48h 跟 pending 語意相關的訊息".to_string(),
        String::new(),
        "> vsearch on pending → KNN over msg_vec (cosine, max-distance 0.65)。".to_string(),
        format!("> project=`{}`。要改邏輯動 `crs gen-recent`（Rust）。", slug),
        String::new(),
    ];

    if !pending.exists() {
        snippets.push("_(無 pending 檔可當 query seed)_".to_string());
    } else {
        let pending_text = fs::read_to_string(&pending)?;
        let mut in_section = false;
        let mut q = String::new();
        for line in pending_text.lines() {
            if line.starts_with("## 待處理") { in_section = true; continue; }
            if in_section && line.starts_with("## ") { break; }
            if in_section { q.push_str(line); q.push(' '); }
        }
        let q = q.replace(['*', '#', '`'], "");
        let q: String = q.chars().take(1500).collect();
        let q = q.trim().to_string();
        if q.is_empty() {
            snippets.push("_(pending list 空，無 query seed)_".to_string());
        } else {
            match cmd_vsearch_since(&q, slug, 48, 6, 30, 600, 0.65, 140, 400) {
                Ok(lines) => snippets.extend(lines),
                Err(e) => {
                    log_line("ERROR", &format!("vsearch-since failed: {}", e));
                    snippets.push(format!("_(vsearch-since 失敗 — 看 {}/gen-recent-context.log)_", archive.display()));
                }
            }
        }
    }

    header.extend(snippets);
    header.push(String::new());
    header.push("---".to_string());
    header.push("*Regen on SessionStart + 15-min cron, with skip guard. Force: `crs gen-recent --force`*".to_string());

    let body = header.join("\n") + "\n";
    fs::create_dir_all(&mem_dir).ok();
    fs::write(&out_file, &body)?;
    let line_count = body.lines().count();
    log_line("OK", &format!("wrote {} ({} lines, project={})", out_file.display(), line_count, slug));
    println!("wrote {} ({} lines, project={})", out_file.display(), line_count, slug);
    Ok(())
}

// ─────────────────────────── build (JSONL ingest) ───────────────────────────

#[cfg(not(feature = "pg-backend"))]
fn ensure_schema(conn: &Connection) -> Result<()> {
    conn.execute_batch(r#"
        CREATE TABLE IF NOT EXISTS msg (
            session_id TEXT NOT NULL,
            project    TEXT NOT NULL,
            seq        INTEGER NOT NULL,
            ts         TEXT,
            role       TEXT,
            tool_name  TEXT,
            content    TEXT,
            PRIMARY KEY (session_id, seq)
        );
        CREATE INDEX IF NOT EXISTS idx_msg_ts      ON msg(ts);
        CREATE INDEX IF NOT EXISTS idx_msg_project ON msg(project, ts);
        CREATE INDEX IF NOT EXISTS idx_msg_tool    ON msg(tool_name);

        CREATE VIRTUAL TABLE IF NOT EXISTS msg_fts USING fts5(
            content,
            content='msg', content_rowid='rowid',
            tokenize='unicode61 remove_diacritics 2'
        );

        CREATE TRIGGER IF NOT EXISTS msg_ai AFTER INSERT ON msg BEGIN
            INSERT INTO msg_fts(rowid, content) VALUES (new.rowid, new.content);
        END;
        CREATE TRIGGER IF NOT EXISTS msg_ad AFTER DELETE ON msg BEGIN
            INSERT INTO msg_fts(msg_fts, rowid, content) VALUES('delete', old.rowid, old.content);
        END;
        CREATE TRIGGER IF NOT EXISTS msg_au AFTER UPDATE ON msg BEGIN
            INSERT INTO msg_fts(msg_fts, rowid, content) VALUES('delete', old.rowid, old.content);
            INSERT INTO msg_fts(rowid, content) VALUES (new.rowid, new.content);
        END;

        CREATE TABLE IF NOT EXISTS ingest_state (
            file_path TEXT PRIMARY KEY,
            mtime     REAL,
            lines     INTEGER
        );
    "#)?;
    Ok(())
}

fn truncate_chars(s: &str, max: usize) -> String {
    s.chars().take(max).collect()
}

/// Compute the `[IMG:<sha256-hex>]` sentinel for a Claude image content block.
/// Returns None if the block isn't a parseable inline-base64 image.
/// URL-sourced images (`source.type == "url"`) get an `[IMG_URL:<url>]` sentinel
/// instead, since there's no bytes to OCR locally.
fn image_block_sentinel(obj: &serde_json::Map<String, Value>) -> Option<String> {
    let source = obj.get("source")?.as_object()?;
    let src_type = source.get("type").and_then(|v| v.as_str()).unwrap_or("");
    match src_type {
        "base64" => {
            let data = source.get("data").and_then(|v| v.as_str())?;
            let bytes = base64::engine::general_purpose::STANDARD.decode(data).ok()?;
            let mut hasher = Sha256::new();
            hasher.update(&bytes);
            let hex = hasher.finalize().iter().map(|b| format!("{:02x}", b)).collect::<String>();
            Some(format!("[IMG:{}]", hex))
        }
        "url" => {
            let url = source.get("url").and_then(|v| v.as_str())?;
            Some(format!("[IMG_URL:{}]", url))
        }
        _ => None,
    }
}

/// Flatten a Claude Code JSONL record into (role, tool_name, text).
/// Mirrors the Python `flatten_content` precisely, including the quirk where
/// "[TOOL_RESULT] " is inserted at the very front of the parts list.
fn flatten_content(rec: &Value) -> (String, Option<String>, String) {
    let role = rec
        .get("role")
        .and_then(|v| v.as_str())
        .or_else(|| rec.get("type").and_then(|v| v.as_str()))
        .unwrap_or("unknown")
        .to_string();

    let content = rec
        .get("content")
        .or_else(|| rec.get("message").and_then(|m| m.get("content")));

    match content {
        Some(Value::String(s)) => (role, None, s.clone()),
        Some(Value::Array(arr)) => {
            let mut parts: Vec<String> = Vec::with_capacity(arr.len());
            let mut tool_name: Option<String> = None;
            let mut had_tool_result = false;

            for block in arr {
                if let Some(obj) = block.as_object() {
                    let btype = obj.get("type").and_then(|v| v.as_str()).unwrap_or("");
                    match btype {
                        "text" => {
                            if let Some(t) = obj.get("text").and_then(|v| v.as_str()) {
                                parts.push(t.to_string());
                            }
                        }
                        "tool_use" => {
                            let name = obj.get("name").and_then(|v| v.as_str()).unwrap_or("").to_string();
                            tool_name = Some(name.clone());
                            let input_str = serde_json::to_string(obj.get("input").unwrap_or(&Value::Null)).unwrap_or_default();
                            parts.push(format!("[TOOL_USE {}] input={}", name, truncate_chars(&input_str, 4000)));
                        }
                        "tool_result" => {
                            had_tool_result = true;
                            match obj.get("content") {
                                Some(Value::Array(cc)) => {
                                    for ccc in cc {
                                        if let Some(co) = ccc.as_object() {
                                            if co.get("type").and_then(|v| v.as_str()) == Some("text") {
                                                if let Some(tt) = co.get("text").and_then(|v| v.as_str()) {
                                                    parts.push(tt.to_string());
                                                }
                                            } else {
                                                let s = serde_json::to_string(ccc).unwrap_or_default();
                                                parts.push(truncate_chars(&s, 4000));
                                            }
                                        } else {
                                            let s = serde_json::to_string(ccc).unwrap_or_default();
                                            parts.push(truncate_chars(&s, 4000));
                                        }
                                    }
                                }
                                Some(Value::String(s)) => parts.push(s.clone()),
                                Some(other) => parts.push(other.to_string()),
                                None => {}
                            }
                        }
                        "thinking" => {
                            let t = obj.get("thinking").and_then(|v| v.as_str()).unwrap_or("");
                            parts.push(format!("[THINKING] {}", t));
                        }
                        "image" => {
                            // Replace heavy base64 with a short sentinel keyed by SHA256
                            // of the decoded image bytes. Enables image_ocr lookup later
                            // without bloating msg.content. Out-of-band base64 stays in
                            // JSONL on disk; cmd_ocr_missing re-reads it on demand.
                            if let Some(sentinel) = image_block_sentinel(obj) {
                                parts.push(sentinel);
                            } else {
                                // Unparseable image block — fall back to JSON dump,
                                // truncated so a giant base64 string doesn't blow up content.
                                let s = serde_json::to_string(block).unwrap_or_default();
                                parts.push(truncate_chars(&s, 4000));
                            }
                        }
                        _ => {
                            let s = serde_json::to_string(block).unwrap_or_default();
                            parts.push(truncate_chars(&s, 4000));
                        }
                    }
                } else {
                    parts.push(block.to_string());
                }
            }
            if had_tool_result {
                parts.insert(0, "[TOOL_RESULT] ".to_string());
            }
            (role, tool_name, parts.join("\n"))
        }
        _ => {
            let s = serde_json::to_string(rec).unwrap_or_default();
            (role, None, truncate_chars(&s, 8000))
        }
    }
}

#[cfg(not(feature = "pg-backend"))]
fn ingest_file(conn: &Connection, path: &Path) -> Result<usize> {
    let session_id = path.file_stem().and_then(|s| s.to_str()).unwrap_or("unknown").to_string();
    let project = path.parent().and_then(|p| p.file_name()).and_then(|s| s.to_str()).unwrap_or("unknown").to_string();
    let mtime: f64 = fs::metadata(path)?
        .modified()?
        .duration_since(SystemTime::UNIX_EPOCH)?
        .as_secs_f64();

    let prev_mtime: Option<f64> = conn
        .query_row(
            "SELECT mtime FROM ingest_state WHERE file_path = ?1",
            params![path.to_string_lossy().as_ref()],
            |r| r.get::<_, f64>(0),
        )
        .ok();
    if let Some(prev) = prev_mtime {
        if (prev - mtime).abs() < 1e-6 {
            return Ok(0);
        }
    }

    let f = fs::File::open(path)?;
    let reader = BufReader::new(f);

    let tx = conn.unchecked_transaction()?;
    let mut stmt = tx.prepare_cached(
        "INSERT OR REPLACE INTO msg(session_id,project,seq,ts,role,tool_name,content) VALUES(?1,?2,?3,?4,?5,?6,?7)",
    )?;

    let mut new_rows = 0usize;
    for (seq, line) in reader.lines().enumerate() {
        let raw = match line { Ok(l) => l, Err(_) => continue };
        if raw.is_empty() { continue; }
        let rec: Value = match serde_json::from_str(&raw) {
            Ok(v) => v,
            Err(_) => continue,
        };
        let ts = rec.get("timestamp").and_then(|v| v.as_str())
            .or_else(|| rec.get("ts").and_then(|v| v.as_str()))
            .unwrap_or("")
            .to_string();
        let (role, tool_name, content) = flatten_content(&rec);
        let trimmed = content.trim();
        if trimmed.is_empty() { continue; }
        let bounded = truncate_chars(trimmed, 200_000);
        stmt.execute(params![session_id, project, seq as i64, ts, role, tool_name, bounded])?;
        new_rows += 1;
    }
    drop(stmt);

    tx.execute(
        "INSERT OR REPLACE INTO ingest_state(file_path,mtime,lines) VALUES(?1,?2,?3)",
        params![path.to_string_lossy().as_ref(), mtime, new_rows as i64],
    )?;
    tx.commit()?;
    Ok(new_rows)
}

fn collect_jsonl_files() -> Result<Vec<PathBuf>> {
    let root = home().join(".claude/projects");
    let mut out = Vec::new();
    if !root.is_dir() {
        return Ok(out);
    }
    for proj in fs::read_dir(&root)? {
        let proj = proj?;
        if !proj.file_type()?.is_dir() { continue; }
        for f in fs::read_dir(proj.path())? {
            let f = f?;
            let p = f.path();
            if p.extension().and_then(|e| e.to_str()) == Some("jsonl") {
                out.push(p);
            }
        }
    }
    out.sort();
    Ok(out)
}

fn refresh_all_recent_contexts() {
    let proj_root = home().join(".claude/projects");
    if !proj_root.is_dir() { return; }
    let mut refreshed = 0;
    if let Ok(rd) = fs::read_dir(&proj_root) {
        for proj in rd.flatten() {
            let name = match proj.file_name().to_str() { Some(s) => s.to_string(), None => continue };
            if !name.starts_with('-') { continue; }
            if !proj.path().join("memory").is_dir() { continue; }
            // Best-effort — log_line catches errors. We swallow here.
            if gen_recent_for_slug(&name, false).is_ok() {
                refreshed += 1;
            }
        }
    }
    if refreshed > 0 {
        println!("refreshed auto_recent.md for {} project(s)", refreshed);
    }
}

/// Translate `--project-prefix '-a,-b'` into ("AND (project LIKE $N OR project LIKE $N+1 OR ...)", ["a%", "b%", ...])
/// Returns (clause, bind_strings) — placeholder uses 1-based PG syntax `${start_idx + i}`.
/// If prefix is None or empty, returns ("", vec![]).
fn project_prefix_filter_pg(prefix: Option<&str>, start_idx: usize) -> (String, Vec<String>) {
    match prefix {
        Some(s) if !s.trim().is_empty() => {
            let parts: Vec<String> = s.split(',')
                .map(|p| p.trim())
                .filter(|p| !p.is_empty())
                .map(|p| format!("{}%", p))
                .collect();
            if parts.is_empty() { return (String::new(), vec![]); }
            let ors: Vec<String> = (0..parts.len())
                .map(|i| format!("project LIKE ${}", start_idx + i))
                .collect();
            (format!(" AND ({})", ors.join(" OR ")), parts)
        }
        _ => (String::new(), vec![]),
    }
}

fn ollama_up() -> bool {
    let client = reqwest::blocking::Client::builder()
        .timeout(std::time::Duration::from_secs(2))
        .build();
    if let Ok(c) = client {
        if let Ok(r) = c.get("http://localhost:11434/api/tags").send() {
            return r.status().is_success();
        }
    }
    false
}

#[cfg(not(feature = "pg-backend"))]
fn cmd_build(no_embed: bool, no_refresh: bool, workers: usize, project_prefix: Option<String>) -> Result<()> {
    let archive = home().join("claude-archive");
    fs::create_dir_all(&archive)?;
    let conn = Connection::open(db_path())?;
    conn.pragma_update(None, "journal_mode", "WAL")?;
    conn.pragma_update(None, "synchronous", "NORMAL")?;
    conn.pragma_update(None, "cache_size", -524_288i64)?;
    conn.pragma_update(None, "mmap_size", 536_870_912i64)?;
    conn.pragma_update(None, "temp_store", "MEMORY")?;
    ensure_schema(&conn)?;

    let files = collect_jsonl_files()?;
    let mut total_new = 0usize;
    let mut touched = 0usize;
    for path in &files {
        match ingest_file(&conn, path) {
            Ok(0) => {}
            Ok(n) => {
                touched += 1;
                total_new += n;
                let proj_part = path.parent().and_then(|p| p.file_name()).and_then(|s| s.to_str()).unwrap_or("?");
                let file_part = path.file_name().and_then(|s| s.to_str()).unwrap_or("?");
                println!("  +{:6}  {}/{}", n, proj_part, file_part);
            }
            Err(e) => eprintln!("  !! {}: {}", path.display(), e),
        }
    }

    let total: i64 = conn.query_row("SELECT COUNT(*) FROM msg", [], |r| r.get(0))?;
    let sess: i64 = conn.query_row("SELECT COUNT(DISTINCT session_id) FROM msg", [], |r| r.get(0))?;
    let proj: i64 = conn.query_row("SELECT COUNT(DISTINCT project) FROM msg", [], |r| r.get(0))?;
    let db_mb = fs::metadata(db_path())?.len() as f64 / 1024.0 / 1024.0;

    println!("\ntouched {} files, +{} rows", touched, total_new);
    println!("DB total: {} rows across {} sessions / {} projects", total, sess, proj);
    println!("DB path:  {}", db_path().display());
    println!("DB size:  {:.1} MB", db_mb);

    drop(conn);

    if !no_embed {
        if ollama_up() {
            if let Err(e) = cmd_embed_missing(workers, 0, project_prefix.clone()) {
                eprintln!("(embed warning: {})", e);
            }
        } else {
            println!("(skip embedding: ollama not reachable)");
        }
    }

    if !no_refresh {
        refresh_all_recent_contexts();
    }
    Ok(())
}

// ── PG build via daemon pool (unix) ──
// Every PG op in the build path goes through the pgsearchd daemon's resident,
// keepalive'd r2d2 pool over the unix socket — NO bare pg_connect(). This is the
// fix for the embed-missing SSLRead hang (bare keepalive-less connection idle
// during ollama → NAT-evicted → next op blocks ~2h). Daemon down ⇒ Err (no
// fallback by design; a build that can't reach the pool stops instead of
// silently re-opening the broken connection type).
//
// Exception (deliberate, out of the 3-RPC spec): the OCR sub-pass below
// (cmd_ocr_missing / embed_image_ocr_missing) still uses direct connections.
// On this Mac OCR backlog is 0 and those paths short-circuit on empty work
// without a long idle gap, so they don't trigger the hang. Routing OCR's
// multi-table writes through the daemon is a separate, larger change.
#[cfg(all(feature = "pg-backend", unix))]
fn cmd_build(no_embed: bool, no_refresh: bool, workers: usize, project_prefix: Option<String>) -> Result<()> {
    let archive = home().join("claude-archive");
    fs::create_dir_all(&archive)?;

    // CRS_BUILD_DIRECT=1 → bare direct-connect build (no daemon RPC). Set on
    // macOS, where the daemon pool path hangs: a pooled connection sits idle
    // (pool warm / between RPCs), an intermediate NAT evicts it, and macOS has
    // no working TCP keepalive (verified: 0 probes via tcpdump) nor
    // tcp_user_timeout to detect it → the next op blocks in SSLRead ~forever.
    // The bare path avoids idle: ingest holds ONE connection doing continuous
    // INSERTs, and embed-missing (direct) holds NO connection during the ollama
    // phase. bluesea (LAN, no NAT) leaves this unset and uses the daemon pool.
    if build_direct() {
        return cmd_build_direct(no_embed, no_refresh, workers, project_prefix);
    }

    // Pull existing ingest_state mtimes up front (one RPC) so per-file mtime
    // gating happens client-side with no per-file PG round trip. Also creates
    // the ingest_state table daemon-side if missing.
    let state_resp = daemon_rpc(&serde_json::json!({"mode": "ingest_state_select"}))?;
    let mut state_mtimes: std::collections::HashMap<String, f64> = std::collections::HashMap::new();
    if let Some(arr) = state_resp.get("rows").and_then(|v| v.as_array()) {
        for r in arr {
            if let (Some(fp), Some(mt)) = (
                r.get("file_path").and_then(|v| v.as_str()),
                r.get("mtime").and_then(|v| v.as_f64()),
            ) {
                state_mtimes.insert(fp.to_string(), mt);
            }
        }
    }

    let files = collect_jsonl_files()?;
    let mut total_new = 0usize;
    let mut touched = 0usize;
    for path in &files {
        match ingest_file_pg_daemon(path, &state_mtimes) {
            Ok(0) => {}
            Ok(n) => {
                touched += 1;
                total_new += n;
                let proj_part = path.parent().and_then(|p| p.file_name()).and_then(|s| s.to_str()).unwrap_or("?");
                let file_part = path.file_name().and_then(|s| s.to_str()).unwrap_or("?");
                println!("  +{:6}  {}/{}", n, proj_part, file_part);
            }
            Err(e) => eprintln!("  !! {}: {}", path.display(), e),
        }
    }

    let stats = daemon_rpc(&serde_json::json!({"mode": "build_stats"}))?;
    let total    = stats.get("total").and_then(|v| v.as_i64()).unwrap_or(0);
    let sess     = stats.get("sessions").and_then(|v| v.as_i64()).unwrap_or(0);
    let proj     = stats.get("projects").and_then(|v| v.as_i64()).unwrap_or(0);
    let emb_done = stats.get("embedded").and_then(|v| v.as_i64()).unwrap_or(0);
    let db_size  = stats.get("db_size").and_then(|v| v.as_str()).unwrap_or("?");

    println!("\ntouched {} files, +{} rows", touched, total_new);
    println!("PG total: {} rows / {} sessions / {} projects / {} with embedding",
             total, sess, proj, emb_done);
    println!("PG db size: {}", db_size);

    if !no_embed {
        if ollama_up() {
            if let Err(e) = cmd_embed_missing(workers, 0, project_prefix.clone()) {
                eprintln!("(embed warning: {})", e);
            }
        } else {
            println!("(skip embedding: ollama not reachable)");
        }
    }

    // OCR pass — soft-fail (OCR helpers may be missing on a fresh install).
    // Run after embed-missing so newly-OCR'd image_ocr rows get embedded on
    // the next cycle.
    if let Err(e) = cmd_ocr_missing(workers.max(2), 0, project_prefix.clone()) {
        eprintln!("(ocr warning: {})", e);
    }
    // Embed any image_ocr rows we just created.
    if !no_embed && ollama_up() {
        if let Err(e) = embed_image_ocr_missing(workers) {
            eprintln!("(image_ocr embed warning: {})", e);
        }
    }

    if !no_refresh {
        refresh_all_recent_contexts();
    }
    Ok(())
}

// CRS_BUILD_DIRECT=1 selects the bare direct-connect build path (macOS).
#[cfg(all(feature = "pg-backend", unix))]
fn build_direct() -> bool {
    std::env::var("CRS_BUILD_DIRECT").map(|v| v == "1" || v == "true").unwrap_or(false)
}

// Bare direct-connect build (macOS / CRS_BUILD_DIRECT). Ingest holds ONE
// connection doing continuous INSERTs (no idle gap → never NAT-evicted
// mid-build); embed runs through cmd_embed_missing's direct branch which holds
// no connection during the ollama phase.
#[cfg(all(feature = "pg-backend", unix))]
fn cmd_build_direct(no_embed: bool, no_refresh: bool, workers: usize, project_prefix: Option<String>) -> Result<()> {
    let mut pg = AsyncPg::connect()?;
    let files = collect_jsonl_files()?;
    let mut total_new = 0usize;
    let mut touched = 0usize;
    for path in &files {
        match ingest_file_async(&mut pg, path) {
            Ok(0) => {}
            Ok(n) => {
                touched += 1;
                total_new += n;
                let proj_part = path.parent().and_then(|p| p.file_name()).and_then(|s| s.to_str()).unwrap_or("?");
                let file_part = path.file_name().and_then(|s| s.to_str()).unwrap_or("?");
                println!("  +{:6}  {}/{}", n, proj_part, file_part);
            }
            Err(e) => eprintln!("  !! {}: {}", path.display(), e),
        }
    }
    drop(pg); // release before the long embed phase — no idle connection lingering
    println!("\ntouched {} files, +{} rows (direct)", touched, total_new);

    if !no_embed {
        if ollama_up() {
            if let Err(e) = cmd_embed_missing(workers, 0, project_prefix.clone()) {
                eprintln!("(embed warning: {})", e);
            }
        } else {
            println!("(skip embedding: ollama not reachable)");
        }
    }
    if let Err(e) = cmd_ocr_missing(workers.max(2), 0, project_prefix.clone()) {
        eprintln!("(ocr warning: {})", e);
    }
    if !no_embed && ollama_up() {
        if let Err(e) = embed_image_ocr_missing(workers) {
            eprintln!("(image_ocr embed warning: {})", e);
        }
    }
    if !no_refresh {
        refresh_all_recent_contexts();
    }
    Ok(())
}

// Bare direct-connect embed-missing with the idle fix (macOS / CRS_BUILD_DIRECT).
// The original bare embed kept one Mutex<pg_connect> alive across all rayon
// workers — it sat idle during each worker's ollama call (seconds) and got
// NAT-evicted, hanging the next UPDATE in SSLRead. Here NO connection is held
// during embedding: (1) query jobs on a fresh conn then drop it, (2) embed all
// (rayon) holding nothing, (3) batch-UPDATE on a fresh short-lived connection.
#[cfg(all(feature = "pg-backend", unix))]
fn cmd_embed_missing_direct(workers: usize, limit: usize, project_prefix: Option<String>) -> Result<()> {
    let (prefix_clause, prefix_binds) = project_prefix_filter_pg(project_prefix.as_deref(), 1);
    let prefix_params: Vec<&(dyn tokio_postgres::types::ToSql + Sync)> =
        prefix_binds.iter().map(|s| s as &(dyn tokio_postgres::types::ToSql + Sync)).collect();

    let mut pg = AsyncPg::connect()?;
    let pending_sql = format!(
        "SELECT COUNT(*) FROM msg WHERE embedding IS NULL AND length(content) >= 5{}",
        prefix_clause
    );
    let pending: i64 = pg.query_one(&pending_sql, &prefix_params[..])?.get(0);
    if pending <= 0 {
        println!("nothing to embed (prefix={:?})", project_prefix);
        return Ok(());
    }
    let limit_clause = if limit > 0 { format!("LIMIT {}", limit) } else { String::new() };
    let select_sql = format!(
        "SELECT id, content FROM msg WHERE embedding IS NULL AND length(content) >= 5{} ORDER BY id DESC {}",
        prefix_clause, limit_clause
    );
    let rows = pg.query(&select_sql, &prefix_params[..])?;
    let jobs: Vec<(i64, String)> = rows.iter().map(|r| (r.get(0), r.get(1))).collect();
    drop(pg); // ← no connection held during the embed phase

    println!("embed-missing (direct): {} jobs over {} workers", jobs.len(), workers);
    use rayon::prelude::*;
    let pool = rayon::ThreadPoolBuilder::new().num_threads(workers).build()?;
    let results: Vec<(i64, Vec<f32>)> = pool.install(|| {
        jobs.par_iter().filter_map(|(id, content)| {
            let client = http_client().ok()?;
            let snippet: String = content.chars().take(8000).collect();
            match embed_text(&client, &snippet) {
                Ok(v) => Some((*id, v)),
                Err(e) => { eprintln!("embed id={} err={}", id, e); None }
            }
        }).collect()
    });

    // Batch UPDATE through AsyncPg (each batch one timed tx with reconnect-retry).
    // No connection is held during the rayon embed phase above; we open a fresh one
    // here only for the writes.
    const UPD_BATCH: usize = 100;
    let mut pg = AsyncPg::connect()?;
    let mut updated = 0usize;
    for batch in results.chunks(UPD_BATCH) {
        if let Err(e) = pg.update_embeddings(batch) {
            eprintln!("update batch err={}", e);
        }
        updated += batch.len();
        println!("  updated {}/{}", updated, results.len());
    }
    println!("done. updated {} rows.", updated);
    Ok(())
}

// Non-unix PG build: pgsearchd (and the daemon RPC path) is unix-only, so on
// non-unix with pg-backend we retain the original direct-connect build.
#[cfg(all(feature = "pg-backend", not(unix)))]
fn cmd_build(no_embed: bool, no_refresh: bool, workers: usize, project_prefix: Option<String>) -> Result<()> {
    let archive = home().join("claude-archive");
    fs::create_dir_all(&archive)?;

    let mut pg = pg_connect()?;
    pg.batch_execute(
        "CREATE TABLE IF NOT EXISTS ingest_state (
            file_path TEXT PRIMARY KEY,
            mtime DOUBLE PRECISION NOT NULL,
            lines BIGINT NOT NULL
        );",
    )?;

    let files = collect_jsonl_files()?;
    let mut total_new = 0usize;
    let mut touched = 0usize;
    for path in &files {
        match ingest_file_pg(&mut pg, path) {
            Ok(0) => {}
            Ok(n) => {
                touched += 1;
                total_new += n;
                let proj_part = path.parent().and_then(|p| p.file_name()).and_then(|s| s.to_str()).unwrap_or("?");
                let file_part = path.file_name().and_then(|s| s.to_str()).unwrap_or("?");
                println!("  +{:6}  {}/{}", n, proj_part, file_part);
            }
            Err(e) => eprintln!("  !! {}: {}", path.display(), e),
        }
    }

    let total: i64 = pg.query_one("SELECT COUNT(*) FROM msg", &[])?.get(0);
    let sess:  i64 = pg.query_one("SELECT COUNT(DISTINCT session_id) FROM msg", &[])?.get(0);
    let proj:  i64 = pg.query_one("SELECT COUNT(DISTINCT project) FROM msg", &[])?.get(0);
    let emb_done: i64 = pg.query_one("SELECT COUNT(*) FROM msg WHERE embedding IS NOT NULL", &[])?.get(0);
    let db_size: String = pg.query_one("SELECT pg_size_pretty(pg_database_size(current_database()))", &[])?.get(0);

    println!("\ntouched {} files, +{} rows", touched, total_new);
    println!("PG total: {} rows / {} sessions / {} projects / {} with embedding",
             total, sess, proj, emb_done);
    println!("PG db size: {}", db_size);

    drop(pg);

    if !no_embed {
        if ollama_up() {
            if let Err(e) = cmd_embed_missing(workers, 0, project_prefix.clone()) {
                eprintln!("(embed warning: {})", e);
            }
        } else {
            println!("(skip embedding: ollama not reachable)");
        }
    }
    if let Err(e) = cmd_ocr_missing(workers.max(2), 0, project_prefix.clone()) {
        eprintln!("(ocr warning: {})", e);
    }
    if !no_embed && ollama_up() {
        if let Err(e) = embed_image_ocr_missing(workers) {
            eprintln!("(image_ocr embed warning: {})", e);
        }
    }
    if !no_refresh {
        refresh_all_recent_contexts();
    }
    Ok(())
}

/// Parse one JSONL file client-side and ship its rows to the daemon's
/// ingest_rows RPC (one transaction per file, daemon-side, on the pool).
/// mtime gate uses the pre-fetched ingest_state map — no per-file PG read.
#[cfg(all(feature = "pg-backend", unix))]
fn ingest_file_pg_daemon(
    path: &Path,
    state_mtimes: &std::collections::HashMap<String, f64>,
) -> Result<usize> {
    let session_id = path.file_stem().and_then(|s| s.to_str()).unwrap_or("unknown").to_string();
    let project = path.parent().and_then(|p| p.file_name()).and_then(|s| s.to_str()).unwrap_or("unknown").to_string();
    let mtime: f64 = fs::metadata(path)?
        .modified()?
        .duration_since(SystemTime::UNIX_EPOCH)?
        .as_secs_f64();
    let path_str = path.to_string_lossy().to_string();

    // mtime gate (skip if unchanged) — now from the pre-fetched map.
    if let Some(prev) = state_mtimes.get(&path_str) {
        if (prev - mtime).abs() < 1e-6 { return Ok(0); }
    }

    let f = fs::File::open(path)?;
    let reader = BufReader::new(f);

    let san = |s: &str| s.replace('\u{0000}', "");
    let session_id_s = san(&session_id);
    let project_s = san(&project);

    let mut rows: Vec<serde_json::Value> = Vec::new();
    for (seq, line) in reader.lines().enumerate() {
        let raw = match line { Ok(l) => l, Err(_) => continue };
        if raw.is_empty() { continue; }
        let rec: Value = match serde_json::from_str(&raw) { Ok(v) => v, Err(_) => continue };
        let ts_raw = rec.get("timestamp").and_then(|v| v.as_str())
            .or_else(|| rec.get("ts").and_then(|v| v.as_str()))
            .unwrap_or("");
        let (role, tool_name, content) = flatten_content(&rec);
        let trimmed = content.trim();
        if trimmed.is_empty() { continue; }
        let bounded = truncate_chars(trimmed, 200_000);
        // Normalize ts to RFC3339 for the wire (daemon re-parses). Drop unparseable.
        let ts_str: Option<String> = if !ts_raw.is_empty() {
            chrono::DateTime::parse_from_rfc3339(ts_raw).ok()
                .map(|t| t.with_timezone(&Utc).to_rfc3339())
        } else { None };
        rows.push(serde_json::json!({
            "session_id": session_id_s,
            "project": project_s,
            "seq": seq as i64,
            "ts": ts_str,
            "role": san(&role),
            "tool_name": tool_name.as_deref().map(san),
            "content": san(&bounded),
        }));
    }

    // Chunk rows by accumulated content bytes (~128KB) so each ingest_rows RPC
    // stays well under the socket buffer and each daemon-side transaction stays
    // small over the WAN. A single whole-file RPC (this session: 2213 rows ×
    // up to 200K chars = tens of MB on one JSON line) deadlocked daemon↔PG in
    // v1.20 (SSLRead / idle-in-transaction). The LAST chunk carries final:true,
    // which is what upserts ingest_state (mtime gate) — so even a zero-row file
    // still sends one final chunk to record its mtime.
    const INGEST_CHUNK_BYTES: usize = 128 * 1024;
    let mut inserted = 0usize;
    let mut chunk: Vec<serde_json::Value> = Vec::new();
    let mut chunk_bytes = 0usize;
    let send = |chunk: &[serde_json::Value], is_final: bool| -> Result<usize> {
        let req = serde_json::json!({
            "mode": "ingest_rows",
            "file_path": path_str,
            "mtime": mtime,
            "rows": chunk,
            "final": is_final,
        });
        let resp = daemon_rpc(&req)?;
        Ok(resp.get("inserted").and_then(|v| v.as_u64()).unwrap_or(0) as usize)
    };
    for row in rows.into_iter() {
        let rb = row.get("content").and_then(|v| v.as_str()).map(|s| s.len()).unwrap_or(0);
        if chunk_bytes + rb > INGEST_CHUNK_BYTES && !chunk.is_empty() {
            inserted += send(&chunk, false)?;
            chunk.clear();
            chunk_bytes = 0;
        }
        chunk_bytes += rb;
        chunk.push(row);
    }
    // Final chunk (always sent — even if empty — to upsert ingest_state).
    inserted += send(&chunk, true)?;
    Ok(inserted)
}

/// Backfill embeddings on image_ocr rows whose embedding is still NULL.
/// Reuses the same Ollama bge-m3 model as msg embeddings.
#[cfg(feature = "pg-backend")]
fn embed_image_ocr_missing(workers: usize) -> Result<()> {
    let mut pg = pg_connect()?;
    let pending: i64 = pg.query_one(
        "SELECT COUNT(*) FROM image_ocr WHERE embedding IS NULL AND length(content) >= 3",
        &[],
    )?.get(0);
    if pending <= 0 { return Ok(()); }
    let rows = pg.query(
        "SELECT id, content FROM image_ocr
         WHERE embedding IS NULL AND length(content) >= 3
         ORDER BY id DESC",
        &[],
    )?;
    let jobs: Vec<(i64, String)> = rows.iter().map(|r| (r.get(0), r.get(1))).collect();
    drop(pg);

    println!("image_ocr embed: {} jobs over {} workers", jobs.len(), workers);
    use rayon::prelude::*;
    let pool = rayon::ThreadPoolBuilder::new().num_threads(workers).build()?;
    let pg_mu = Mutex::new(pg_connect()?);
    pool.install(|| {
        jobs.par_iter().for_each(|(id, content)| {
            let client = match http_client() { Ok(c) => c, Err(_) => return };
            let snippet: String = content.chars().take(8000).collect();
            match embed_text(&client, &snippet) {
                Ok(v) => {
                    let lit = vec_literal(&v);
                    let sql = format!("UPDATE image_ocr SET embedding = '{lit}'::vector WHERE id = $1");
                    let mut p = pg_mu.lock().unwrap();
                    if let Err(e) = p.execute(&sql, &[id]) {
                        eprintln!("image_ocr update id={} err={}", id, e);
                    }
                }
                Err(e) => eprintln!("image_ocr embed id={} err={}", id, e),
            }
        });
    });
    Ok(())
}

// Direct-connect ingest — only used on non-unix (unix goes through the daemon
// via ingest_file_pg_daemon).
// Bare direct-connect ingest (continuous INSERT on a caller-held connection).
// Used by non-unix builds and by the macOS CRS_BUILD_DIRECT path.
#[cfg(feature = "pg-backend")]
// Used by the non-unix direct build; the unix build goes through ingest_file_async.
#[allow(dead_code)]
fn ingest_file_pg(pg: &mut postgres::Client, path: &Path) -> Result<usize> {
    let session_id = path.file_stem().and_then(|s| s.to_str()).unwrap_or("unknown").to_string();
    let project = path.parent().and_then(|p| p.file_name()).and_then(|s| s.to_str()).unwrap_or("unknown").to_string();
    let mtime: f64 = fs::metadata(path)?
        .modified()?
        .duration_since(SystemTime::UNIX_EPOCH)?
        .as_secs_f64();
    let path_str = path.to_string_lossy().to_string();

    // mtime gate (skip if unchanged)
    if let Some(r) = pg.query_opt("SELECT mtime FROM ingest_state WHERE file_path = $1", &[&path_str])? {
        let prev: f64 = r.get(0);
        if (prev - mtime).abs() < 1e-6 { return Ok(0); }
    }

    let f = fs::File::open(path)?;
    let reader = BufReader::new(f);

    // Batched commit: commit every COMMIT_BATCH rows on a fresh transaction
    // rather than accumulating the whole file in one transaction. A single big
    // transaction over the WAN accumulates uncommitted rows + WAL and stalls
    // near the tail (observed: rows 0-542 INSERT fine, row 543 hangs). Smaller
    // transactions keep each commit cheap. Ingest is idempotent (ON CONFLICT DO
    // NOTHING on session_id,seq) so a partial commit just resumes next run.
    const COMMIT_BATCH: usize = 100;
    let insert_sql =
        "INSERT INTO msg (session_id, project, seq, ts, role, tool_name, content)
         VALUES ($1, $2, $3, $4, $5, $6, $7)
         ON CONFLICT (session_id, seq) DO NOTHING";
    let san = |s: &str| s.replace('\u{0000}', "");
    let session_id_s = san(&session_id);
    let project_s = san(&project);
    let mut new_rows = 0usize;
    let mut in_batch = 0usize;
    let mut tx = pg.transaction()?;
    for (seq, line) in reader.lines().enumerate() {
        let raw = match line { Ok(l) => l, Err(_) => continue };
        if raw.is_empty() { continue; }
        let rec: Value = match serde_json::from_str(&raw) {
            Ok(v) => v,
            Err(_) => continue,
        };
        let ts_raw = rec.get("timestamp").and_then(|v| v.as_str())
            .or_else(|| rec.get("ts").and_then(|v| v.as_str()))
            .unwrap_or("");
        let (role, tool_name, content) = flatten_content(&rec);
        let trimmed = content.trim();
        if trimmed.is_empty() { continue; }
        let bounded = truncate_chars(trimmed, 200_000);
        let ts_opt: Option<chrono::DateTime<Utc>> = if !ts_raw.is_empty() {
            chrono::DateTime::parse_from_rfc3339(ts_raw).ok().map(|t| t.with_timezone(&Utc))
        } else { None };
        let role_s = san(&role);
        let tool_s = tool_name.as_deref().map(san);
        let content_s = san(&bounded);
        tx.execute(insert_sql, &[
            &session_id_s, &project_s, &(seq as i32), &ts_opt,
            &role_s, &tool_s, &content_s,
        ])?;
        new_rows += 1;
        in_batch += 1;
        if in_batch >= COMMIT_BATCH {
            tx.commit()?;
            tx = pg.transaction()?;
            in_batch = 0;
        }
    }

    // Final batch: remaining rows + ingest_state, committed together.
    tx.execute(
        "INSERT INTO ingest_state (file_path, mtime, lines) VALUES ($1, $2, $3)
         ON CONFLICT (file_path) DO UPDATE SET mtime = EXCLUDED.mtime, lines = EXCLUDED.lines",
        &[&path_str, &mtime, &(new_rows as i64)],
    )?;
    tx.commit()?;
    Ok(new_rows)
}

// Async counterpart of ingest_file_pg for the macOS direct build. Same mtime gate
// + (session_id, seq) idempotency, but each COMMIT_BATCH is flushed through
// AsyncPg::ingest_batch (timeout + reconnect-retry) so a server-killed or stalled
// connection is detected and retried instead of hanging forever in SSLRead.
#[cfg(all(feature = "pg-backend", unix))]
fn ingest_file_async(pg: &mut AsyncPg, path: &Path) -> Result<usize> {
    let session_id = path.file_stem().and_then(|s| s.to_str()).unwrap_or("unknown").to_string();
    let project = path.parent().and_then(|p| p.file_name()).and_then(|s| s.to_str()).unwrap_or("unknown").to_string();
    let mtime: f64 = fs::metadata(path)?
        .modified()?
        .duration_since(SystemTime::UNIX_EPOCH)?
        .as_secs_f64();
    let path_str = path.to_string_lossy().to_string();

    if let Some(r) = pg.query_opt("SELECT mtime FROM ingest_state WHERE file_path = $1", &[&path_str])? {
        let prev: f64 = r.get(0);
        if (prev - mtime).abs() < 1e-6 { return Ok(0); }
    }

    let san = |s: &str| s.replace('\u{0000}', "");
    let session_id_s = san(&session_id);
    let project_s = san(&project);

    let f = fs::File::open(path)?;
    let reader = BufReader::new(f);
    const COMMIT_BATCH: usize = 100;
    let mut batch: Vec<AsyncIngestRow> = Vec::with_capacity(COMMIT_BATCH);
    let mut new_rows = 0usize;
    for (seq, line) in reader.lines().enumerate() {
        let raw = match line { Ok(l) => l, Err(_) => continue };
        if raw.is_empty() { continue; }
        let rec: Value = match serde_json::from_str(&raw) { Ok(v) => v, Err(_) => continue };
        let ts_raw = rec.get("timestamp").and_then(|v| v.as_str())
            .or_else(|| rec.get("ts").and_then(|v| v.as_str()))
            .unwrap_or("");
        let (role, tool_name, content) = flatten_content(&rec);
        let trimmed = content.trim();
        if trimmed.is_empty() { continue; }
        let bounded = truncate_chars(trimmed, 200_000);
        let ts_opt: Option<chrono::DateTime<Utc>> = if !ts_raw.is_empty() {
            chrono::DateTime::parse_from_rfc3339(ts_raw).ok().map(|t| t.with_timezone(&Utc))
        } else { None };
        batch.push(AsyncIngestRow {
            seq: seq as i32,
            ts: ts_opt,
            role: san(&role),
            tool: tool_name.as_deref().map(san),
            content: san(&bounded),
        });
        new_rows += 1;
        if batch.len() >= COMMIT_BATCH {
            pg.ingest_batch(&session_id_s, &project_s, &batch, None)?;
            batch.clear();
        }
    }
    // Final flush: remaining rows + ingest_state upsert, committed together (always
    // runs, even with an empty tail, so the mtime gate is recorded).
    pg.ingest_batch(&session_id_s, &project_s, &batch, Some((&path_str, mtime, new_rows as i64)))?;
    Ok(new_rows)
}

// ─────────────────────────── embed-missing ───────────────────────────

#[cfg(not(feature = "pg-backend"))]
fn cmd_embed_missing(workers: usize, limit: usize, project_prefix: Option<String>) -> Result<()> {
    let conn = open_db_with_vec()?;

    // SQLite path doesn't support PG's `~`; translate prefix list to OR'd LIKE clauses.
    let prefix_parts: Vec<String> = project_prefix.as_deref().unwrap_or("").split(',')
        .map(|p| p.trim()).filter(|p| !p.is_empty()).map(|p| format!("{}%", p)).collect();
    let prefix_clause = if prefix_parts.is_empty() { String::new() } else {
        let ors: Vec<String> = (0..prefix_parts.len()).map(|_| "m.project LIKE ?".to_string()).collect();
        format!(" AND ({})", ors.join(" OR "))
    };

    let total: i64 = conn.query_row("SELECT COUNT(*) FROM msg", [], |r| r.get(0))?;
    let done: i64 = conn.query_row("SELECT COUNT(*) FROM msg_vec", [], |r| r.get(0))?;
    let pending: i64 = conn.query_row(
        "SELECT COUNT(*) FROM msg m LEFT JOIN msg_vec v ON v.rowid = m.rowid \
         WHERE v.rowid IS NULL AND length(m.content) >= 5",
        [], |r| r.get(0),
    )?;
    if pending <= 0 {
        println!("nothing to embed: total={} done={} pending={}", total, done, pending);
        return Ok(());
    }

    // Newest-first selection (matching v1.5.0 Python)
    let limit_clause = if limit > 0 { format!("LIMIT {}", limit) } else { String::new() };
    let select_sql = format!(
        "SELECT m.rowid, m.content FROM msg m \
         LEFT JOIN msg_vec v ON v.rowid = m.rowid \
         WHERE v.rowid IS NULL AND length(m.content) >= 5{} \
         ORDER BY m.rowid DESC {}",
        prefix_clause, limit_clause
    );
    let mut stmt = conn.prepare(&select_sql)?;
    let prefix_refs: Vec<&dyn rusqlite::ToSql> = prefix_parts.iter().map(|s| s as &dyn rusqlite::ToSql).collect();
    let jobs: Vec<(i64, String)> = stmt
        .query_map(prefix_refs.as_slice(), |r| Ok((r.get::<_, i64>(0)?, r.get::<_, String>(1)?)))?
        .collect::<Result<_, _>>()?;
    drop(stmt);

    println!("embed-missing: {} jobs over {} workers (newest-first)", jobs.len(), workers);

    use rayon::prelude::*;
    let pool = rayon::ThreadPoolBuilder::new().num_threads(workers).build()?;

    let conn_mu = Mutex::new(conn);
    let counter = Mutex::new(0u64);

    pool.install(|| {
        jobs.par_iter().for_each(|(rowid, content)| {
            let client = http_client().expect("http client");
            // Truncate very long content to keep embedding fast (bge-m3 ctx 8192 tokens, but real-world chars cap)
            let snippet: String = content.chars().take(8000).collect();
            match embed_text(&client, &snippet) {
                Ok(v) => {
                    let blob = vec_to_blob(&v);
                    let c = conn_mu.lock().unwrap();
                    let c_ref = &c;
                    let res = c_ref.execute(
                        "INSERT OR REPLACE INTO msg_vec(rowid, embedding) VALUES (?1, ?2)",
                        params![rowid, blob],
                    ).or_else(|_| {
                        c_ref.execute("DELETE FROM msg_vec WHERE rowid = ?1", params![rowid])?;
                        c_ref.execute(
                            "INSERT INTO msg_vec(rowid, embedding) VALUES (?1, ?2)",
                            params![rowid, blob],
                        )
                    });
                    if let Err(e) = res {
                        eprintln!("insert rowid={} err={}", rowid, e);
                    }
                }
                Err(e) => eprintln!("embed rowid={} err={}", rowid, e),
            }
            let mut n = counter.lock().unwrap();
            *n += 1;
            if *n % 200 == 0 {
                println!("  progress {}/{}", *n, jobs.len());
            }
        });
    });

    println!("done.");
    Ok(())
}

// Number of (id, vec) embed results to accumulate before flushing one
// embed_update RPC to the daemon. Batching avoids a socket round-trip per row
// (460 backlog × 1 RPC each = 460 round-trips) while keeping each transaction
// small enough to commit quickly.
#[cfg(all(feature = "pg-backend", unix))]
const EMBED_FLUSH_BATCH: usize = 50;

/// PG embed-missing — now routed entirely through the pgsearchd daemon pool.
///
/// Old design used bare pg_connect() (a keepalive-less Mutex<Client> shared
/// across rayon workers). While a worker was off in ollama for seconds, that
/// connection sat idle and got NAT-evicted; the next UPDATE blocked in SSLRead
/// for ~2h = the build hang. Now: embed_select to fetch jobs, workers embed in
/// parallel, results batch-flush via embed_update over the daemon's resident
/// keepalive'd pool. No bare connection anywhere ⇒ no hang. Daemon down ⇒ Err.
#[cfg(all(feature = "pg-backend", unix))]
fn cmd_embed_missing(workers: usize, limit: usize, project_prefix: Option<String>) -> Result<()> {
    // macOS bare path: no connection held during embed (idle fix). See
    // cmd_embed_missing_direct. bluesea (LAN) falls through to the daemon path.
    if build_direct() {
        return cmd_embed_missing_direct(workers, limit, project_prefix);
    }

    // Typed prefix list (bare prefixes; daemon parameterizes them server-side).
    let prefixes: Vec<&str> = project_prefix.as_deref().unwrap_or("")
        .split(',').map(|p| p.trim()).filter(|p| !p.is_empty()).collect();

    let select_req = serde_json::json!({
        "mode": "embed_select",
        "prefixes": prefixes,
        "limit": limit,
    });
    let resp = daemon_rpc(&select_req)?;
    let jobs: Vec<(i64, String)> = resp.get("rows").and_then(|v| v.as_array())
        .map(|a| a.iter().filter_map(|r| {
            let id = r.get("id").and_then(|x| x.as_i64())?;
            let content = r.get("content").and_then(|x| x.as_str())?.to_string();
            Some((id, content))
        }).collect())
        .unwrap_or_default();

    if jobs.is_empty() {
        println!("nothing to embed (prefix={:?})", project_prefix);
        return Ok(());
    }

    println!("embed-missing: {} jobs over {} workers (newest-first, prefix={:?}, via daemon)",
             jobs.len(), workers, project_prefix);

    use rayon::prelude::*;
    let pool = rayon::ThreadPoolBuilder::new().num_threads(workers).build()?;
    let batch: Mutex<Vec<(i64, Vec<f32>)>> = Mutex::new(Vec::with_capacity(EMBED_FLUSH_BATCH));
    let counter = Mutex::new(0u64);
    let total_updated = Mutex::new(0i64);

    // Flush helper: drain accumulated (id, vec) pairs to one embed_update RPC.
    let flush = |buf: Vec<(i64, Vec<f32>)>| -> Result<i64> {
        if buf.is_empty() { return Ok(0); }
        let updates: Vec<serde_json::Value> = buf.iter()
            .map(|(id, v)| serde_json::json!({"id": id, "vec": v}))
            .collect();
        let req = serde_json::json!({"mode": "embed_update", "updates": updates});
        let resp = daemon_rpc(&req)?;
        Ok(resp.get("updated").and_then(|v| v.as_i64()).unwrap_or(0))
    };

    pool.install(|| {
        jobs.par_iter().for_each(|(id, content)| {
            let client = http_client().expect("http client");
            let snippet: String = content.chars().take(8000).collect();
            match embed_text(&client, &snippet) {
                Ok(v) => {
                    let to_flush: Option<Vec<(i64, Vec<f32>)>> = {
                        let mut b = batch.lock().unwrap();
                        b.push((*id, v));
                        if b.len() >= EMBED_FLUSH_BATCH {
                            Some(std::mem::take(&mut *b))
                        } else { None }
                    };
                    if let Some(buf) = to_flush {
                        match flush(buf) {
                            Ok(n) => { *total_updated.lock().unwrap() += n; }
                            Err(e) => eprintln!("embed_update flush err={}", e),
                        }
                    }
                }
                Err(e) => eprintln!("embed id={} err={}", id, e),
            }
            let mut n = counter.lock().unwrap();
            *n += 1;
            if *n % 200 == 0 {
                println!("  progress {}/{}", *n, jobs.len());
            }
        });
    });

    // Final flush of the tail (< EMBED_FLUSH_BATCH leftovers).
    let tail = std::mem::take(&mut *batch.lock().unwrap());
    match flush(tail) {
        Ok(n) => { *total_updated.lock().unwrap() += n; }
        Err(e) => eprintln!("embed_update final flush err={}", e),
    }

    println!("done. updated {} rows.", *total_updated.lock().unwrap());
    Ok(())
}

// Non-unix fallback: pgsearchd (and thus the daemon RPC path) is unix-only.
// On non-unix with pg-backend, retain the direct-connect embed-missing.
#[cfg(all(feature = "pg-backend", not(unix)))]
fn cmd_embed_missing(workers: usize, limit: usize, project_prefix: Option<String>) -> Result<()> {
    let mut pg = pg_connect()?;
    let (prefix_clause, prefix_binds) = project_prefix_filter_pg(project_prefix.as_deref(), 1);
    let pending_sql = format!(
        "SELECT COUNT(*) FROM msg WHERE embedding IS NULL AND length(content) >= 5{}",
        prefix_clause
    );
    let prefix_params: Vec<&(dyn postgres::types::ToSql + Sync)> =
        prefix_binds.iter().map(|s| s as &(dyn postgres::types::ToSql + Sync)).collect();
    let pending: i64 = pg.query_one(&pending_sql, &prefix_params[..])?.get(0);
    if pending <= 0 {
        println!("nothing to embed (prefix={:?})", project_prefix);
        return Ok(());
    }
    let limit_clause = if limit > 0 { format!("LIMIT {}", limit) } else { String::new() };
    let select_sql = format!(
        "SELECT id, content FROM msg
         WHERE embedding IS NULL AND length(content) >= 5{}
         ORDER BY id DESC {}",
        prefix_clause, limit_clause
    );
    let rows = pg.query(&select_sql, &prefix_params[..])?;
    let jobs: Vec<(i64, String)> = rows.iter().map(|r| (r.get(0), r.get(1))).collect();
    drop(pg);

    println!("embed-missing: {} jobs over {} workers (newest-first, prefix={:?})",
             jobs.len(), workers, project_prefix);
    use rayon::prelude::*;
    let pool = rayon::ThreadPoolBuilder::new().num_threads(workers).build()?;
    let pg_mu = Mutex::new(pg_connect()?);
    let counter = Mutex::new(0u64);
    pool.install(|| {
        jobs.par_iter().for_each(|(id, content)| {
            let client = http_client().expect("http client");
            let snippet: String = content.chars().take(8000).collect();
            match embed_text(&client, &snippet) {
                Ok(v) => {
                    let lit = vec_literal(&v);
                    let sql = format!("UPDATE msg SET embedding = '{lit}'::vector WHERE id = $1");
                    let mut p = pg_mu.lock().unwrap();
                    if let Err(e) = p.execute(&sql, &[id]) {
                        eprintln!("update id={} err={}", id, e);
                    }
                }
                Err(e) => eprintln!("embed id={} err={}", id, e),
            }
            let mut n = counter.lock().unwrap();
            *n += 1;
            if *n % 200 == 0 { println!("  progress {}/{}", *n, jobs.len()); }
        });
    });
    println!("done.");
    Ok(())
}

// ─────────────────────────── embed-text (debug) ───────────────────────────

fn cmd_embed_text(text: &str) -> Result<()> {
    let client = http_client()?;
    let v = embed_text(&client, text)?;
    println!("dim={} first5={:?}", v.len(), &v[..5.min(v.len())]);
    Ok(())
}

// ─────────────────────────── ocr-missing (PG-backend) ───────────────────────────

/// Dispatch to the platform OCR helper CLI and return recognized text.
///
/// Looks for binaries under `~/claude-archive/bin/`:
///   macOS   → ocr-mac        (Swift / Vision)
///   Windows → ocr-win.ps1    (pwsh + Windows.Media.Ocr)
///   Linux   → ocr-linux.sh   (tesseract chi_tra+eng)
#[cfg(feature = "pg-backend")]
fn run_ocr_cli(image_path: &Path) -> Result<String> {
    let bin_dir = home().join("claude-archive/bin");

    #[cfg(target_os = "macos")]
    let (cmd, args): (PathBuf, Vec<std::ffi::OsString>) = (
        bin_dir.join("ocr-mac"),
        vec![image_path.as_os_str().to_os_string()],
    );

    #[cfg(target_os = "windows")]
    let (cmd, args): (PathBuf, Vec<std::ffi::OsString>) = (
        PathBuf::from("pwsh"),
        vec![
            std::ffi::OsString::from("-NoLogo"),
            std::ffi::OsString::from("-NoProfile"),
            std::ffi::OsString::from("-File"),
            bin_dir.join("ocr-win.ps1").as_os_str().to_os_string(),
            std::ffi::OsString::from("-Path"),
            image_path.as_os_str().to_os_string(),
        ],
    );

    #[cfg(all(unix, not(target_os = "macos")))]
    let (cmd, args): (PathBuf, Vec<std::ffi::OsString>) = (
        bin_dir.join("ocr-linux.sh"),
        vec![image_path.as_os_str().to_os_string()],
    );

    let out = std::process::Command::new(&cmd).args(&args).output()
        .with_context(|| format!("running OCR CLI {}", cmd.display()))?;
    if !out.status.success() {
        let stderr = String::from_utf8_lossy(&out.stderr);
        bail!("OCR CLI exit {}: {}", out.status, stderr.trim());
    }
    Ok(String::from_utf8_lossy(&out.stdout).to_string())
}

/// Extension from media_type, defaulting to ".bin" for unknown types.
#[cfg(feature = "pg-backend")]
fn ext_for_media_type(mt: &str) -> &'static str {
    match mt {
        "image/png"  => "png",
        "image/jpeg" => "jpg",
        "image/gif"  => "gif",
        "image/webp" => "webp",
        "image/bmp"  => "bmp",
        "image/tiff" => "tiff",
        _ => "bin",
    }
}

/// Extract base64 image blocks from a single JSONL line, returning a Vec of
/// (sha256_hex, media_type, raw_bytes) preserving the order they appear.
#[cfg(feature = "pg-backend")]
fn extract_image_blocks(line: &str) -> Vec<(String, String, Vec<u8>)> {
    let rec: Value = match serde_json::from_str(line) { Ok(v) => v, Err(_) => return Vec::new() };
    let content = match rec.get("content").or_else(|| rec.get("message").and_then(|m| m.get("content"))) {
        Some(c) => c,
        None => return Vec::new(),
    };
    let arr = match content.as_array() { Some(a) => a, None => return Vec::new() };

    let mut out = Vec::new();
    for block in arr {
        let obj = match block.as_object() { Some(o) => o, None => continue };
        if obj.get("type").and_then(|v| v.as_str()) != Some("image") { continue; }
        let source = match obj.get("source").and_then(|v| v.as_object()) { Some(s) => s, None => continue };
        if source.get("type").and_then(|v| v.as_str()) != Some("base64") { continue; }
        let data = match source.get("data").and_then(|v| v.as_str()) { Some(d) => d, None => continue };
        let media_type = source.get("media_type").and_then(|v| v.as_str()).unwrap_or("image/png").to_string();
        let bytes = match base64::engine::general_purpose::STANDARD.decode(data) { Ok(b) => b, Err(_) => continue };
        let mut h = Sha256::new();
        h.update(&bytes);
        let hex = h.finalize().iter().map(|b| format!("{:02x}", b)).collect::<String>();
        out.push((hex, media_type, bytes));
    }
    out
}

/// Save image bytes to the content-addressed store at
/// ~/claude-archive/images/<sha[..2]>/<sha>.<ext>, returning the path.
/// Idempotent: skips write if file already present with matching length.
#[cfg(feature = "pg-backend")]
fn save_image_bytes(sha: &str, media_type: &str, bytes: &[u8]) -> Result<PathBuf> {
    let bucket = &sha[..2];
    let dir = home().join("claude-archive/images").join(bucket);
    fs::create_dir_all(&dir)?;
    let path = dir.join(format!("{}.{}", sha, ext_for_media_type(media_type)));
    if let Ok(meta) = fs::metadata(&path) {
        if meta.len() as usize == bytes.len() { return Ok(path); }
    }
    fs::write(&path, bytes)?;
    Ok(path)
}

/// Find the JSONL path for a (project, session_id) pair.
/// Project slug is the directory name under ~/.claude/projects/.
#[cfg(feature = "pg-backend")]
fn jsonl_path_for(project: &str, session_id: &str) -> PathBuf {
    home().join(".claude/projects").join(project).join(format!("{}.jsonl", session_id))
}

#[cfg(feature = "pg-backend")]
fn ocr_engine_name() -> &'static str {
    if cfg!(target_os = "macos") { "apple-vision" }
    else if cfg!(target_os = "windows") { "windows-media-ocr" }
    else { "tesseract" }
}

#[cfg(feature = "pg-backend")]
fn cmd_ocr_missing(workers: usize, limit: usize, project_prefix: Option<String>) -> Result<()> {
    use std::collections::HashMap;

    let mut pg = pg_connect()?;

    // Quick stats
    let cache_total: i64 = pg.query_one("SELECT COUNT(*) FROM image_ocr_cache", &[])?.get(0);
    let ocr_total:   i64 = pg.query_one("SELECT COUNT(*) FROM image_ocr", &[])?.get(0);
    println!("image_ocr_cache: {} rows / image_ocr: {} rows (before)", cache_total, ocr_total);

    // Same prefix filter as embed-missing — bluesea must not try to OCR
    // images from -Users-jrjohn-* msgs whose jsonl lives on Mac (and vice
    // versa). Without this, the foreign host prints "JSONL not found"
    // warnings every cron cycle.
    let (prefix_clause, prefix_binds) = project_prefix_filter_pg(project_prefix.as_deref(), 1);

    // Find msg rows that mention [IMG:...] and are not yet fully OCR'd.
    // We over-select (some rows might already be partially done); per-image
    // dedup happens at the (session_id, parent_seq, image_index) UNIQUE constraint.
    let limit_clause = if limit > 0 { format!("LIMIT {}", limit) } else { String::new() };
    let select_sql = format!(
        "SELECT id, session_id, project, seq, ts, content
         FROM msg
         WHERE content LIKE '%[IMG:%'{}
         ORDER BY id DESC {}",
        prefix_clause, limit_clause
    );
    let prefix_params: Vec<&(dyn postgres::types::ToSql + Sync)> =
        prefix_binds.iter().map(|s| s as &(dyn postgres::types::ToSql + Sync)).collect();
    let candidates = pg.query(&select_sql, &prefix_params[..])?;
    if candidates.is_empty() {
        println!("ocr-missing: no [IMG:...] sentinels in msg.content — nothing to do");
        return Ok(());
    }

    // Pre-fetch which (session_id, parent_seq, image_index) already exist in image_ocr
    let existing_rows = pg.query(
        "SELECT session_id, parent_seq, image_index FROM image_ocr",
        &[],
    )?;
    let mut done_set: HashSet<(String, i32, i32)> = HashSet::new();
    for r in existing_rows {
        done_set.insert((r.get(0), r.get(1), r.get(2)));
    }

    // Pre-fetch cache for fast skip on miss-detection
    let cache_rows = pg.query("SELECT sha256, ocr_text FROM image_ocr_cache", &[])?;
    let mut cache: HashMap<String, String> = HashMap::new();
    for r in cache_rows {
        cache.insert(r.get(0), r.get(1));
    }
    drop(pg);

    // Plan: per-candidate work units
    struct WorkItem {
        session_id: String,
        project: String,
        parent_seq: i32,
        ts: Option<chrono::DateTime<Utc>>,
        image_index: i32,
        sha: String,
        cached_text: Option<String>,
    }

    let mut work: Vec<WorkItem> = Vec::new();

    // For sentinel detection on msg.content side, we scan substring matches
    // and pair each with image_index based on its order in that message.
    for row in &candidates {
        let session_id: String = row.get(1);
        let project:    String = row.get(2);
        let parent_seq: i32    = row.get(3);
        let ts: Option<chrono::DateTime<Utc>> = row.get(4);
        let content:    String = row.get(5);

        // Find all [IMG:<64-hex>] substrings in order.
        let mut shas_in_msg: Vec<String> = Vec::new();
        let bytes = content.as_bytes();
        let mut i = 0;
        while i + 5 < bytes.len() {
            if &bytes[i..i+5] == b"[IMG:" {
                // Expect 64 hex chars then ']'
                if i + 5 + 64 < bytes.len() && bytes[i + 5 + 64] == b']' {
                    let hex = &content[i+5..i+5+64];
                    if hex.chars().all(|c| c.is_ascii_hexdigit()) {
                        shas_in_msg.push(hex.to_ascii_lowercase());
                        i += 5 + 64 + 1;
                        continue;
                    }
                }
            }
            i += 1;
        }
        if shas_in_msg.is_empty() { continue; }

        for (image_index, sha) in shas_in_msg.into_iter().enumerate() {
            let key = (session_id.clone(), parent_seq, image_index as i32);
            if done_set.contains(&key) { continue; }
            let cached_text = cache.get(&sha).cloned();
            work.push(WorkItem {
                session_id: session_id.clone(),
                project: project.clone(),
                parent_seq,
                ts,
                image_index: image_index as i32,
                sha,
                cached_text,
            });
        }
    }

    if work.is_empty() {
        println!("ocr-missing: nothing pending (all [IMG:...] already in image_ocr)");
        return Ok(());
    }
    let cached_hits = work.iter().filter(|w| w.cached_text.is_some()).count();
    println!("ocr-missing: {} pending (cache hits: {}, fresh OCR: {})",
        work.len(), cached_hits, work.len() - cached_hits);

    // For "fresh OCR" items we need raw bytes — load JSONL once per session.
    // Cache hits are processed in one shot at the end (no file IO needed).
    // We do this serially per session for simplicity, parallel inside via rayon
    // is overkill for screenshot OCR (low volume, Apple Vision is already fast).

    use std::collections::BTreeMap;
    // Group fresh-OCR work by (project, session_id) so we read each JSONL once.
    let mut fresh_by_session: BTreeMap<(String, String), Vec<usize>> = BTreeMap::new();
    let mut cached_indices: Vec<usize> = Vec::new();
    for (idx, w) in work.iter().enumerate() {
        if w.cached_text.is_some() {
            cached_indices.push(idx);
        } else {
            fresh_by_session
                .entry((w.project.clone(), w.session_id.clone()))
                .or_default()
                .push(idx);
        }
    }

    // Concurrent OCR using rayon, but only across distinct JSONL files
    // (so within a file we keep a single pass). For our use case each session
    // typically has 0-3 images, so this isn't a big win — but matches the
    // existing embed-missing rayon pattern for consistency.
    use rayon::prelude::*;
    let pool = rayon::ThreadPoolBuilder::new().num_threads(workers).build()?;
    let pg_mu = Mutex::new(pg_connect()?);
    let host = whoami_short();

    // Phase 1: process cached hits (no IO besides INSERTs)
    {
        let mut p = pg_mu.lock().unwrap();
        let mut tx = p.transaction()?;
        let stmt = tx.prepare(
            "INSERT INTO image_ocr (session_id, project, parent_seq, image_index, sha256, ts, content)
             VALUES ($1, $2, $3, $4, $5, $6, $7)
             ON CONFLICT (session_id, parent_seq, image_index) DO NOTHING",
        )?;
        for idx in &cached_indices {
            let w = &work[*idx];
            let text = w.cached_text.as_ref().unwrap();
            tx.execute(&stmt, &[
                &w.session_id, &w.project, &w.parent_seq, &w.image_index,
                &w.sha, &w.ts, &text,
            ])?;
        }
        drop(stmt);
        tx.commit()?;
        if !cached_indices.is_empty() {
            println!("  inserted {} image_ocr rows from cache", cached_indices.len());
        }
    }

    // Phase 2: fresh OCR per session JSONL, parallel across sessions
    let session_work: Vec<((String, String), Vec<usize>)> = fresh_by_session.into_iter().collect();
    pool.install(|| {
        session_work.par_iter().for_each(|((project, session_id), indices)| {
            let jsonl_path = jsonl_path_for(project, session_id);
            if !jsonl_path.exists() {
                eprintln!("  !! JSONL not found: {} (skipping {} items)", jsonl_path.display(), indices.len());
                return;
            }

            // Group target work by parent_seq so we walk the file once
            let mut by_seq: BTreeMap<i32, Vec<usize>> = BTreeMap::new();
            for idx in indices {
                by_seq.entry(work[*idx].parent_seq).or_default().push(*idx);
            }

            let f = match fs::File::open(&jsonl_path) {
                Ok(f) => f,
                Err(e) => { eprintln!("  !! cannot open {}: {}", jsonl_path.display(), e); return; }
            };
            let reader = BufReader::new(f);

            for (seq, line_res) in reader.lines().enumerate() {
                let line = match line_res { Ok(l) => l, Err(_) => continue };
                let seq_i = seq as i32;
                let targets = match by_seq.get(&seq_i) { Some(t) => t, None => continue };

                let blocks = extract_image_blocks(&line);
                if blocks.is_empty() {
                    eprintln!("  !! no image blocks at {}:{} (sentinels expected {})", jsonl_path.display(), seq, targets.len());
                    continue;
                }

                for idx in targets {
                    let w = &work[*idx];
                    let want = w.image_index as usize;
                    let (sha, media_type, bytes) = match blocks.get(want) {
                        Some(t) => t,
                        None => { eprintln!("  !! image_index {} not found in seq {} of {}", want, seq, jsonl_path.display()); continue; }
                    };
                    if sha != &w.sha {
                        eprintln!("  !! sha mismatch at {} seq {} idx {}: expected {} got {}", jsonl_path.display(), seq, want, w.sha, sha);
                        continue;
                    }

                    let saved = match save_image_bytes(sha, media_type, bytes) {
                        Ok(p) => p,
                        Err(e) => { eprintln!("  !! save_image_bytes({}): {}", sha, e); continue; }
                    };

                    let ocr_text = match run_ocr_cli(&saved) {
                        Ok(t) => t,
                        Err(e) => { eprintln!("  !! OCR {}: {}", sha, e); continue; }
                    };
                    let ocr_text = ocr_text.trim().to_string();
                    let width: Option<i32> = None;   // could probe with image crate later
                    let height: Option<i32> = None;
                    let byte_size: i32 = bytes.len() as i32;

                    let mut p = pg_mu.lock().unwrap();
                    let mut tx = match p.transaction() { Ok(t) => t, Err(e) => { eprintln!("  !! begin tx: {}", e); continue; } };
                    let r1 = tx.execute(
                        "INSERT INTO image_ocr_cache (sha256, media_type, width, height, byte_size, ocr_text, engine, ocr_host)
                         VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                         ON CONFLICT (sha256) DO NOTHING",
                        &[&w.sha, media_type, &width, &height, &byte_size, &ocr_text, &ocr_engine_name(), &host],
                    );
                    if let Err(e) = r1 { eprintln!("  !! insert cache {}: {}", w.sha, e); let _ = tx.rollback(); continue; }
                    let r2 = tx.execute(
                        "INSERT INTO image_ocr (session_id, project, parent_seq, image_index, sha256, ts, content)
                         VALUES ($1, $2, $3, $4, $5, $6, $7)
                         ON CONFLICT (session_id, parent_seq, image_index) DO NOTHING",
                        &[&w.session_id, &w.project, &w.parent_seq, &w.image_index, &w.sha, &w.ts, &ocr_text],
                    );
                    if let Err(e) = r2 { eprintln!("  !! insert image_ocr {}: {}", w.sha, e); let _ = tx.rollback(); continue; }
                    if let Err(e) = tx.commit() { eprintln!("  !! commit {}: {}", w.sha, e); continue; }
                    println!("  + {} ({} bytes, {} chars OCR)", &w.sha[..12], byte_size, ocr_text.len());
                }
            }
        });
    });

    println!("ocr-missing: done.");
    Ok(())
}

// ─────────────────────────── doctor ───────────────────────────

fn whoami_short() -> String {
    env::var("USER")
        .or_else(|_| env::var("USERNAME"))
        .unwrap_or_else(|_| "unknown".to_string())
}

fn cmd_doctor() -> Result<()> {
    let archive = home().join("claude-archive");
    let db_p = db_path();
    let mut warns: u32 = 0;
    let mut fails: u32 = 0;

    let mark = |status: char, msg: &str| println!("  {} {}", status, msg);

    println!("==> claude-session-archive doctor");
    println!("    archive: {}", archive.display());
    println!("    db:      {}", db_p.display());
    if cfg!(feature = "pg-backend") {
        println!("    backend: pg-backend feature ENABLED (search routes to PG)");
    } else {
        println!("    backend: sqlite (default)");
    }
    println!();

    // [tooling] cargo (rebuild needs it), sqlite3 + jq optional
    println!("[tooling]");
    let probe = |cmd: &str, optional: bool, warns: &mut u32, fails: &mut u32| {
        let ok = std::process::Command::new(cmd)
            .arg("--version")
            .output()
            .map(|o| o.status.success())
            .unwrap_or(false);
        if ok {
            mark('✓', &format!("{}: present", cmd));
        } else if optional {
            mark('⚠', &format!("{}: missing (optional)", cmd));
            *warns += 1;
        } else {
            mark('✗', &format!("{}: missing (required for rebuild)", cmd));
            *fails += 1;
        }
    };
    probe("cargo", false, &mut warns, &mut fails);
    probe("sqlite3", true, &mut warns, &mut fails);
    if !cfg!(target_os = "windows") {
        probe("jq", true, &mut warns, &mut fails);
    }

    // [storage] dir + DB + perms
    println!("\n[storage]");
    if archive.is_dir() {
        mark('✓', &format!("archive dir exists ({})", archive.display()));
    } else {
        mark('✗', &format!("archive dir missing: {}", archive.display()));
        fails += 1;
    }
    if db_p.is_file() {
        let meta = fs::metadata(&db_p)?;
        let mb = meta.len() as f64 / 1024.0 / 1024.0;
        mark('✓', &format!("db: {:.1} MB", mb));
        #[cfg(unix)]
        {
            use std::os::unix::fs::PermissionsExt;
            let mode = meta.permissions().mode() & 0o777;
            if mode == 0o600 {
                mark('✓', &format!("db perms: 0{:o} (owner-only)", mode));
            } else {
                mark('⚠', &format!("db perms: 0{:o} (recommended 0600 — chmod 600 the file)", mode));
                warns += 1;
            }
        }
    } else {
        mark('✗', &format!("db missing: {}", db_p.display()));
        fails += 1;
    }

    // [database] msg / msg_vec / backlog / stale / latest ts
    if db_p.is_file() {
        println!("\n[database]");
        let conn = open_db_with_vec()?;
        let msg_total: i64 = conn.query_row("SELECT COUNT(*) FROM msg", [], |r| r.get(0))?;
        let vec_total: i64 = conn.query_row("SELECT COUNT(*) FROM msg_vec", [], |r| r.get(0))?;
        mark('•', &format!("msg rows:     {}", msg_total));
        mark('•', &format!("msg_vec rows: {}", vec_total));

        let backlog: i64 = conn.query_row(
            "SELECT COUNT(*) FROM msg m LEFT JOIN msg_vec v ON v.rowid = m.rowid \
             WHERE v.rowid IS NULL AND length(m.content) >= 5",
            [],
            |r| r.get(0),
        )?;
        if backlog > 0 {
            mark('⚠', &format!("embed backlog: {} (run: crs embed-missing)", backlog));
            warns += 1;
        } else {
            mark('✓', "embed backlog: 0");
        }

        // Stale rowids — vec0 LEFT JOIN ... IS NULL is unreliable, scan with HashSet
        let msg_ids: HashSet<i64> = conn
            .prepare("SELECT rowid FROM msg")?
            .query_map([], |r| r.get::<_, i64>(0))?
            .collect::<rusqlite::Result<HashSet<i64>>>()?;
        let stale = conn
            .prepare("SELECT rowid FROM msg_vec")?
            .query_map([], |r| r.get::<_, i64>(0))?
            .filter_map(|r| r.ok())
            .filter(|r| !msg_ids.contains(r))
            .count();
        if stale > 0 {
            mark('⚠', &format!("msg_vec stale rowids: {} (run: crs prune-vec)", stale));
            warns += 1;
        } else {
            mark('✓', "msg_vec stale rowids: 0");
        }

        if let Ok(latest_ts) = conn.query_row::<String, _, _>("SELECT MAX(ts) FROM msg", [], |r| r.get(0)) {
            mark('•', &format!("latest msg ts: {}", latest_ts));
        }
    }

    // [schedule] launchd / cron / Scheduled Task
    println!("\n[schedule]");
    let user = whoami_short();
    if cfg!(target_os = "macos") {
        let label = format!("com.{}.claude-archive", user);
        match std::process::Command::new("launchctl").arg("list").output() {
            Ok(o) if o.status.success() => {
                let s = String::from_utf8_lossy(&o.stdout);
                if s.contains(&label) {
                    mark('✓', &format!("launchd: {} loaded", label));
                } else {
                    mark('✗', &format!("launchd: {} not loaded", label));
                    fails += 1;
                }
            }
            _ => {
                mark('⚠', "launchctl not available");
                warns += 1;
            }
        }
    } else if cfg!(target_os = "linux") {
        match std::process::Command::new("crontab").arg("-l").output() {
            Ok(o) if o.status.success() => {
                let s = String::from_utf8_lossy(&o.stdout);
                if s.contains("crs build") || s.contains("claude-archive") {
                    mark('✓', "cron: crs build entry present");
                } else {
                    mark('✗', "cron: no entry for crs build (run install.sh)");
                    fails += 1;
                }
            }
            _ => {
                mark('⚠', "crontab -l failed (no user crontab?)");
                warns += 1;
            }
        }
    } else if cfg!(target_os = "windows") {
        let out = std::process::Command::new("powershell")
            .args([
                "-NoProfile",
                "-Command",
                "Get-ScheduledTask -TaskName ClaudeArchiveIngest -ErrorAction SilentlyContinue | Select-Object -ExpandProperty TaskName",
            ])
            .output();
        match out {
            Ok(o) => {
                let s = String::from_utf8_lossy(&o.stdout);
                if s.contains("ClaudeArchiveIngest") {
                    mark('✓', "scheduled task: ClaudeArchiveIngest registered");
                } else {
                    mark('✗', "scheduled task: ClaudeArchiveIngest missing (run install.ps1)");
                    fails += 1;
                }
            }
            _ => {
                mark('⚠', "could not query Scheduled Tasks");
                warns += 1;
            }
        }
    }

    // [hooks] SessionStart
    println!("\n[hooks]");
    let settings = home().join(".claude/settings.json");
    if settings.is_file() {
        let s = fs::read_to_string(&settings).unwrap_or_default();
        if s.contains("gen-recent") {
            mark('✓', "SessionStart hook: crs gen-recent present");
        } else {
            mark('⚠', &format!("SessionStart hook missing in {}", settings.display()));
            warns += 1;
        }
    } else {
        mark('⚠', &format!("settings.json not found: {}", settings.display()));
        warns += 1;
    }

    // [ollama] daemon + model
    println!("\n[ollama]");
    let client = http_client()?;
    match client.get("http://localhost:11434/api/tags").send() {
        Ok(resp) if resp.status().is_success() => {
            mark('✓', "daemon: reachable at localhost:11434");
            let body = resp.text().unwrap_or_default();
            if body.contains(MODEL) {
                mark('✓', &format!("model {}: pulled", MODEL));
            } else {
                mark('⚠', &format!("model {} not pulled (run: ollama pull {})", MODEL, MODEL));
                warns += 1;
            }
        }
        _ => {
            mark('⚠', "daemon: not reachable (vsearch / auto_recent will be skipped)");
            warns += 1;
        }
    }

    // [pg-backend] PG connectivity + pgsearchd daemon (only when feature enabled)
    #[cfg(feature = "pg-backend")]
    {
        println!("\n[pg-backend]");
        match pg_config_url() {
            Err(e) => {
                mark('✗', &format!("pg config: {}", e));
                fails += 1;
            }
            Ok(_) => {
                mark('✓', "pg config: env vars present");
                match pg_connect() {
                    Ok(mut c) => {
                        let v: Result<i64, _> = c.query_one("SELECT 1::bigint", &[]).and_then(|r| Ok(r.get(0)));
                        if v.is_ok() {
                            mark('✓', "pg connect: SELECT 1 succeeded");
                            if let Ok(r) = c.query_one("SELECT COUNT(*) FROM msg", &[]) {
                                let n: i64 = r.get(0);
                                mark('•', &format!("pg msg rows: {}", n));
                            }
                        } else {
                            mark('⚠', "pg connect: SELECT 1 failed");
                            warns += 1;
                        }
                    }
                    Err(e) => {
                        mark('✗', &format!("pg connect failed: {}", e));
                        fails += 1;
                    }
                }
                #[cfg(unix)]
                {
                    if let Ok(sock) = pgsearchd_socket_path() {
                        if sock.exists() {
                            mark('✓', &format!("pgsearchd socket: {}", sock.display()));
                        } else {
                            mark('⚠', &format!("pgsearchd socket missing ({}). Run: crs pgsearchd", sock.display()));
                            warns += 1;
                        }
                    }
                }
            }
        }
    }

    println!();
    println!("==> Summary: {} fail / {} warn", fails, warns);
    if fails > 0 {
        std::process::exit(2);
    } else if warns > 0 {
        std::process::exit(1);
    }
    Ok(())
}

// ─────────────────────────── prune-vec ───────────────────────────

fn cmd_prune_vec(dry_run: bool) -> Result<()> {
    let conn = open_db_with_vec()?;

    println!("==> scanning msg_vec for stale rowids...");
    let msg_ids: HashSet<i64> = conn
        .prepare("SELECT rowid FROM msg")?
        .query_map([], |r| r.get::<_, i64>(0))?
        .collect::<rusqlite::Result<HashSet<i64>>>()?;
    let stale: Vec<i64> = conn
        .prepare("SELECT rowid FROM msg_vec")?
        .query_map([], |r| r.get::<_, i64>(0))?
        .filter_map(|r| r.ok())
        .filter(|r| !msg_ids.contains(r))
        .collect();

    println!("    msg rows:     {}", msg_ids.len());
    println!("    stale rowids: {}", stale.len());
    if stale.is_empty() {
        println!("    nothing to prune.");
        return Ok(());
    }
    if dry_run {
        println!("    (dry-run) — no rows deleted. Re-run without --dry-run to apply.");
        return Ok(());
    }

    let mut del_stmt = conn.prepare("DELETE FROM msg_vec WHERE rowid = ?1")?;
    let mut deleted = 0usize;
    let mut errors = 0usize;
    for (i, rowid) in stale.iter().enumerate() {
        match del_stmt.execute(params![rowid]) {
            Ok(_) => deleted += 1,
            Err(e) => {
                errors += 1;
                eprintln!("delete rowid={} err={}", rowid, e);
            }
        }
        if (i + 1) % 500 == 0 {
            println!("  progress {}/{}", i + 1, stale.len());
        }
    }
    println!("    deleted: {}  errors: {}", deleted, errors);
    Ok(())
}

// ─────────────────────────── PG backend (feature-gated) ───────────────────────────
//
// Talks to a remote PostgreSQL + pgvector instance. Connection details from env vars:
//   CRS_PG_URL                           full libpq connection string (overrides components)
//   CRS_PG_HOST / PORT / USER / PASSWORD / DB    individual components
// CRS_PG_PASSWORD is REQUIRED — there is no default. CRS_PG_DB defaults to `archive_main`,
// HOST/PORT/USER default to localhost/5432/archive.
//
// Schema expected on the PG side:
//   CREATE TABLE msg (
//     id BIGSERIAL PRIMARY KEY,
//     session_id TEXT, project TEXT, seq INTEGER,
//     ts TIMESTAMPTZ, role TEXT, tool_name TEXT, content TEXT,
//     content_tsv tsvector GENERATED ALWAYS AS (to_tsvector('simple', content)) STORED,
//     embedding vector(1024)
//   );
//   CREATE INDEX msg_tsv_gin ON msg USING gin(content_tsv);
//   CREATE INDEX msg_embedding_hnsw ON msg USING hnsw(embedding vector_cosine_ops);
//   CREATE UNIQUE INDEX msg_session_seq ON msg(session_id, seq);
//
// See references/pg-backend.md for full setup.

#[cfg(feature = "pg-backend")]
const PG_EMBED_MODEL: &str = "bge-m3";
#[cfg(feature = "pg-backend")]
const PG_VEC_DIM: usize = 1024;

#[cfg(feature = "pg-backend")]
fn pg_config_url() -> Result<String> {
    if let Ok(url) = env::var("CRS_PG_URL") {
        if !url.is_empty() {
            return Ok(url);
        }
    }
    let host = env::var("CRS_PG_HOST").unwrap_or_else(|_| "localhost".to_string());
    let port = env::var("CRS_PG_PORT").unwrap_or_else(|_| "5432".to_string());
    let user = env::var("CRS_PG_USER").unwrap_or_else(|_| "archive".to_string());
    let pass = env::var("CRS_PG_PASSWORD").map_err(|_| {
        anyhow!("CRS_PG_PASSWORD env var required (or set CRS_PG_URL). See references/pg-backend.md")
    })?;
    let db = env::var("CRS_PG_DB").unwrap_or_else(|_| "archive_main".to_string());
    Ok(format!(
        "host={host} port={port} user={user} password={pass} dbname={db} sslmode=require"
    ))
}

#[cfg(feature = "pg-backend")]
fn embed_pg_query(client: &reqwest::blocking::Client, text: &str) -> Result<Vec<f32>> {
    let body = serde_json::json!({ "model": PG_EMBED_MODEL, "input": text });
    let resp: EmbedResponse = client.post(&ollama_url()).json(&body).send()?.error_for_status()?.json()?;
    let v = resp.embeddings.into_iter().next().ok_or_else(|| anyhow!("ollama returned no embedding"))?;
    if v.len() != PG_VEC_DIM {
        bail!("expected {}-dim, got {}", PG_VEC_DIM, v.len());
    }
    Ok(v)
}

#[cfg(feature = "pg-backend")]
fn pg_connect() -> Result<postgres::Client> {
    // TLS via native-tls. Server cert must validate against system trust roots
    // (e.g. Let's Encrypt cert on your VPS hostname).
    let native = native_tls::TlsConnector::new()?;
    let tls = postgres_native_tls::MakeTlsConnector::new(native);
    let url = pg_config_url()?;
    Ok(postgres::Client::connect(&url, tls)?)
}

// ───────── async PG with a userspace timeout (macOS direct-build path) ─────────
// macOS has no TCP_USER_TIMEOUT and its postgres TCP keepalive emits no probes
// (verified: tcpdump shows 0 probes), so a connection the server kills
// (statement_timeout / idle_in_transaction_session_timeout) or that the WAN path
// silently drops leaves the *sync* client blocked forever inside SSLRead — the
// documented rust-postgres infinite-read-timeout hang. tokio::time::timeout gives
// a real userspace deadline: dropping the future cancels the await, so we detect
// the dead connection, reconnect, and retry (ingest is idempotent via ON CONFLICT).
// Scoped to the build_direct path only; search / daemon keep the sync client.
#[cfg(all(feature = "pg-backend", unix))]
struct AsyncPg {
    rt: tokio::runtime::Runtime,
    client: tokio_postgres::Client,
    url: String,
}

#[cfg(all(feature = "pg-backend", unix))]
impl AsyncPg {
    const OP_TIMEOUT: std::time::Duration = std::time::Duration::from_secs(30);
    const CONNECT_TIMEOUT: std::time::Duration = std::time::Duration::from_secs(20);

    fn connect() -> Result<Self> {
        let url = pg_config_url()?;
        let rt = tokio::runtime::Builder::new_current_thread().enable_all().build()?;
        let client = Self::dial(&rt, &url)?;
        Ok(Self { rt, client, url })
    }

    // Open one connection and spawn its driver onto the current-thread runtime.
    // The driver task only advances while we are inside block_on, which is exactly
    // when queries run — fine for this sequential single-connection ingest.
    fn dial(rt: &tokio::runtime::Runtime, url: &str) -> Result<tokio_postgres::Client> {
        let native = native_tls::TlsConnector::new()?;
        let tls = postgres_native_tls::MakeTlsConnector::new(native);
        let url = url.to_string();
        rt.block_on(async move {
            let connect = tokio_postgres::connect(&url, tls);
            let (client, conn) = match tokio::time::timeout(Self::CONNECT_TIMEOUT, connect).await {
                Ok(r) => r?,
                Err(_) => anyhow::bail!("pg connect timed out after {:?}", Self::CONNECT_TIMEOUT),
            };
            tokio::spawn(async move { let _ = conn.await; });
            Ok::<_, anyhow::Error>(client)
        })
    }

    fn reconnect(&mut self) -> Result<()> {
        self.client = Self::dial(&self.rt, &self.url)?;
        Ok(())
    }

    // Run `f` (which drives a block_on to completion → owned Result, no future
    // escapes). On timeout/error: reconnect and run once more. `f` borrows &self
    // (shared rt + client); reconnect is &mut, sequenced after f returns, so the
    // borrows never overlap.
    fn attempt<T>(&mut self, f: impl Fn(&Self) -> Result<T>) -> Result<T> {
        match f(self) {
            Ok(v) => Ok(v),
            Err(e) => {
                eprintln!("  (pg retry after: {e})");
                self.reconnect()?;
                f(self)
            }
        }
    }

    fn query_opt(&mut self, sql: &str, params: &[&(dyn tokio_postgres::types::ToSql + Sync)])
        -> Result<Option<tokio_postgres::Row>> {
        self.attempt(|s| s.rt.block_on(async {
            match tokio::time::timeout(Self::OP_TIMEOUT, s.client.query_opt(sql, params)).await {
                Ok(Ok(v)) => Ok(v),
                Ok(Err(e)) => Err(anyhow::anyhow!("pg query_opt: {e}")),
                Err(_) => Err(anyhow::anyhow!("pg query_opt timed out after {:?}", Self::OP_TIMEOUT)),
            }
        }))
    }
    fn query(&mut self, sql: &str, params: &[&(dyn tokio_postgres::types::ToSql + Sync)])
        -> Result<Vec<tokio_postgres::Row>> {
        self.attempt(|s| s.rt.block_on(async {
            match tokio::time::timeout(Self::OP_TIMEOUT, s.client.query(sql, params)).await {
                Ok(Ok(v)) => Ok(v),
                Ok(Err(e)) => Err(anyhow::anyhow!("pg query: {e}")),
                Err(_) => Err(anyhow::anyhow!("pg query timed out after {:?}", Self::OP_TIMEOUT)),
            }
        }))
    }
    fn query_one(&mut self, sql: &str, params: &[&(dyn tokio_postgres::types::ToSql + Sync)])
        -> Result<tokio_postgres::Row> {
        self.attempt(|s| s.rt.block_on(async {
            match tokio::time::timeout(Self::OP_TIMEOUT, s.client.query_one(sql, params)).await {
                Ok(Ok(v)) => Ok(v),
                Ok(Err(e)) => Err(anyhow::anyhow!("pg query_one: {e}")),
                Err(_) => Err(anyhow::anyhow!("pg query_one timed out after {:?}", Self::OP_TIMEOUT)),
            }
        }))
    }

    // Insert a batch of msg rows + (optionally) the ingest_state upsert, all inside
    // ONE server transaction wrapped in a single timeout. On timeout/error the whole
    // batch is reconnected + retried — safe because INSERT is ON CONFLICT DO NOTHING
    // and the state upsert is idempotent. Keeping each tx small (≤ COMMIT_BATCH rows)
    // also keeps every statement well under the server's 120s statement_timeout and
    // never leaves a transaction idle past the 60s idle_in_transaction timeout.
    fn ingest_batch(
        &mut self,
        session_id: &str,
        project: &str,
        rows: &[AsyncIngestRow],
        final_state: Option<(&str, f64, i64)>,
    ) -> Result<()> {
        if rows.is_empty() && final_state.is_none() { return Ok(()); }
        self.attempt(|s| s.rt.block_on(async {
            // ONE multi-row INSERT per batch = one WAN round trip instead of one per
            // row (the row-at-a-time version made a build over the WAN impractically
            // slow). A single INSERT statement is atomic even under autocommit, so no
            // explicit transaction is needed, and retry stays safe via ON CONFLICT.
            let fut = async {
                if !rows.is_empty() {
                    use std::fmt::Write as _;
                    let mut sql = String::from(
                        "INSERT INTO msg (session_id, project, seq, ts, role, tool_name, content) VALUES ");
                    let mut params: Vec<&(dyn tokio_postgres::types::ToSql + Sync)> =
                        Vec::with_capacity(rows.len() * 7);
                    let mut n = 1;
                    for (i, r) in rows.iter().enumerate() {
                        if i > 0 { sql.push(','); }
                        let _ = write!(sql, "(${},${},${},${},${},${},${})",
                            n, n + 1, n + 2, n + 3, n + 4, n + 5, n + 6);
                        n += 7;
                        params.push(&session_id);
                        params.push(&project);
                        params.push(&r.seq);
                        params.push(&r.ts);
                        params.push(&r.role);
                        params.push(&r.tool);
                        params.push(&r.content);
                    }
                    sql.push_str(" ON CONFLICT (session_id, seq) DO NOTHING");
                    s.client.execute(sql.as_str(), &params).await?;
                }
                if let Some((path, mtime, lines)) = final_state {
                    s.client.execute(
                        "INSERT INTO ingest_state (file_path, mtime, lines) VALUES ($1,$2,$3)
                         ON CONFLICT (file_path) DO UPDATE SET mtime=EXCLUDED.mtime, lines=EXCLUDED.lines",
                        &[&path, &mtime, &lines],
                    ).await?;
                }
                Ok::<(), tokio_postgres::Error>(())
            };
            match tokio::time::timeout(Self::OP_TIMEOUT, fut).await {
                Ok(Ok(())) => Ok(()),
                Ok(Err(e)) => Err(anyhow::anyhow!("pg ingest_batch: {e}")),
                Err(_) => Err(anyhow::anyhow!("pg ingest_batch timed out after {:?}", Self::OP_TIMEOUT)),
            }
        }))
    }

    // Batch-UPDATE embeddings as ONE multi-row UPDATE ... FROM (VALUES ...) = one
    // WAN round trip per batch (timeout + reconnect-retry). Vectors are rendered as
    // text literals and cast to ::vector server-side.
    fn update_embeddings(&mut self, batch: &[(i64, Vec<f32>)]) -> Result<()> {
        if batch.is_empty() { return Ok(()); }
        let lits: Vec<String> = batch.iter().map(|(_, v)| vec_literal(v)).collect();
        self.attempt(|s| s.rt.block_on(async {
            let fut = async {
                use std::fmt::Write as _;
                let mut sql = String::from("UPDATE msg SET embedding = v.emb::vector FROM (VALUES ");
                let mut params: Vec<&(dyn tokio_postgres::types::ToSql + Sync)> =
                    Vec::with_capacity(batch.len() * 2);
                let mut n = 1;
                for (i, ((id, _), lit)) in batch.iter().zip(lits.iter()).enumerate() {
                    if i > 0 { sql.push(','); }
                    let _ = write!(sql, "(${}::bigint,${}::text)", n, n + 1);
                    n += 2;
                    params.push(id);
                    params.push(lit);
                }
                sql.push_str(") AS v(id, emb) WHERE msg.id = v.id");
                s.client.execute(sql.as_str(), &params).await?;
                Ok::<(), tokio_postgres::Error>(())
            };
            match tokio::time::timeout(Self::OP_TIMEOUT, fut).await {
                Ok(Ok(())) => Ok(()),
                Ok(Err(e)) => Err(anyhow::anyhow!("pg update_embeddings: {e}")),
                Err(_) => Err(anyhow::anyhow!("pg update_embeddings timed out after {:?}", Self::OP_TIMEOUT)),
            }
        }))
    }
}

#[cfg(all(feature = "pg-backend", unix))]
struct AsyncIngestRow {
    seq: i32,
    ts: Option<chrono::DateTime<Utc>>,
    role: String,
    tool: Option<String>,
    content: String,
}

#[cfg(feature = "pg-backend")]
fn pg_latest_msg_ts(slug: &str) -> Result<i64> {
    let mut pg = pg_connect()?;
    let row = pg.query_opt(
        "SELECT EXTRACT(EPOCH FROM MAX(ts))::bigint FROM msg WHERE project = $1",
        &[&slug],
    )?;
    Ok(row.and_then(|r| r.get::<_, Option<i64>>(0)).unwrap_or(0))
}

#[cfg(feature = "pg-backend")]
fn vec_literal(v: &[f32]) -> String {
    let mut s = String::with_capacity(v.len() * 12 + 2);
    s.push('[');
    for (i, f) in v.iter().enumerate() {
        if i > 0 { s.push(','); }
        s.push_str(&f.to_string());
    }
    s.push(']');
    s
}

#[cfg(feature = "pg-backend")]
#[derive(Debug, Clone)]
struct PgRow {
    id: Option<i64>,
    ts: Option<chrono::DateTime<Utc>>,
    project: String,
    session_id: String,
    role: String,
    tool_name: Option<String>,
    content: String,
    score: Option<f64>,
}

#[cfg(feature = "pg-backend")]
fn pg_fts(client: &mut postgres::Client, query: &str, project: Option<&str>, limit: usize, include_img: bool) -> Result<Vec<PgRow>> {
    // MATERIALIZED CTE forces planner to use GIN index on content_tsv (otherwise
    // PG walks msg_ts_idx backward + filter, scanning thousands of rows; observed
    // 432ms server, 16K filter rows). With CTE, GIN runs first → small result →
    // sort/dedup (~6ms server-side).
    //
    // Plus two filters baked in:
    //   role IN ('user','assistant')        — skip meta events
    //   DISTINCT ON content (newest kept)   — dedup same-content rows
    //
    // v1.15+: optionally UNION ALL with image_ocr (role='image_ocr'), default ON.
    // FTS path doesn't have a numeric rank, so de-emphasis is implicit (ts DESC
    // sort + DISTINCT ON content puts older noise behind newer real msgs).
    let proj_like: Option<String> = project.map(|p| format!("%{}%", p));
    let sql = if include_img {
        "WITH msg_hits AS MATERIALIZED (
             SELECT id, ts, project, session_id, role, tool_name, content
             FROM msg
             WHERE content_tsv @@ plainto_tsquery('simple', $1)
               AND role IN ('user', 'assistant')
               AND ($2::text IS NULL OR project LIKE $2)
         ),
         img_hits AS MATERIALIZED (
             SELECT id, ts, project, session_id,
                    'image_ocr'::text AS role, NULL::text AS tool_name, content
             FROM image_ocr
             WHERE content_tsv @@ plainto_tsquery('simple', $1)
               AND ($2::text IS NULL OR project LIKE $2)
         ),
         hits AS (
             SELECT * FROM msg_hits
             UNION ALL
             SELECT * FROM img_hits
         ),
         deduped AS (
             SELECT DISTINCT ON (content)
                    id, ts, project, session_id, role, tool_name, content
             FROM hits ORDER BY content, ts DESC
         )
         SELECT id, ts, project, session_id, role, tool_name, content
         FROM deduped ORDER BY ts DESC LIMIT $3"
    } else {
        "WITH hits AS MATERIALIZED (
             SELECT id, ts, project, session_id, role, tool_name, content
             FROM msg
             WHERE content_tsv @@ plainto_tsquery('simple', $1)
               AND role IN ('user', 'assistant')
               AND ($2::text IS NULL OR project LIKE $2)
         ),
         deduped AS (
             SELECT DISTINCT ON (content)
                    id, ts, project, session_id, role, tool_name, content
             FROM hits ORDER BY content, ts DESC
         )
         SELECT id, ts, project, session_id, role, tool_name, content
         FROM deduped ORDER BY ts DESC LIMIT $3"
    };
    let rows = client.query(sql, &[&query, &proj_like, &(limit as i64)])?;
    Ok(rows.iter().map(|r| PgRow {
        id: r.get(0),
        ts: r.get(1),
        project: r.get(2),
        session_id: r.get(3),
        role: r.get(4),
        tool_name: r.get(5),
        content: r.get(6),
        score: None,
    }).collect())
}

#[cfg(feature = "pg-backend")]
fn pg_vec(client: &mut postgres::Client, http: &reqwest::blocking::Client, query: &str, project: Option<&str>, limit: usize, include_img: bool) -> Result<Vec<PgRow>> {
    // HNSW-first plan (MATERIALIZED) — without this, the planner picks Seq Scan
    // when filters are added alongside ORDER BY embedding <=> v, blowing
    // execution from ~20ms (HNSW) to ~6s (seq scan + sort over 100k+ rows).
    //
    // Pipeline:
    //   knn      — HNSW top-N over msg (over_fetch * limit), index hit only
    //   filt     — drop meta-role events (queue-operation, last-prompt, etc.)
    //              that have no real content and dilute the top-K
    //   dedup    — DISTINCT ON (content) keeping the closest occurrence (same
    //              prompt is often stored multiple times: user row + queue-op
    //              row + ai-title row, all bge-m3 embedded identically)
    //
    // Over-fetch needs to be big enough that after role+content filtering we
    // still have `limit` rows. With ~71% user/assistant fraction in the
    // archive (38122 user + 60123 assistant / 138814 with embedding), 100
    // over-fetch typically yields >50 usable rows. ef_search defaults to 40
    // on pgvector HNSW; we bump it inside the session to actually return up
    // to over_fetch candidates.
    let emb = embed_pg_query(http, query)?;
    let lit = vec_literal(&emb);
    let proj_like: Option<String> = project.map(|p| format!("%{}%", p));
    let over_fetch = ((limit * 20).max(100)) as i64;
    // ef_search: pgvector HNSW. Raise so HNSW returns up to over_fetch rows
    // (default 40 caps how many candidates the index walk surfaces). Plain
    // SET (not SET LOCAL) — we are not in a txn; SET persists on this pooled
    // connection but every vsearch resets to the same value, so no leak.
    let ef = std::cmp::max(over_fetch as i32, 100);
    client.execute(&format!("SET hnsw.ef_search = {ef}"), &[]).ok();
    // v1.15+: image_ocr UNION'd in with dist × 1.10 (~score × 0.91 de-emphasis)
    // so UI-screenshot noise doesn't crowd out real conversation rows while
    // still letting data-heavy screenshots (logs, tables) appear in top-N
    // when their raw distance is competitive. Tuned down from 1.25 after
    // observing DNS-log screenshot rank #344 with 1.25 — too aggressive.
    let sql = if include_img {
        format!(
            "WITH msg_knn AS MATERIALIZED (
                 SELECT id, ts, project, session_id, role, tool_name, content,
                        embedding <=> '{lit}'::vector AS dist
                 FROM msg
                 WHERE embedding IS NOT NULL
                   AND ($1::text IS NULL OR project LIKE $1)
                 ORDER BY embedding <=> '{lit}'::vector
                 LIMIT $2
             ),
             img_knn AS MATERIALIZED (
                 SELECT id, ts, project, session_id,
                        'image_ocr'::text AS role, NULL::text AS tool_name, content,
                        (embedding <=> '{lit}'::vector) * 1.10 AS dist
                 FROM image_ocr
                 WHERE embedding IS NOT NULL
                   AND ($1::text IS NULL OR project LIKE $1)
                 ORDER BY embedding <=> '{lit}'::vector
                 LIMIT $2
             ),
             knn AS (
                 SELECT * FROM msg_knn UNION ALL SELECT * FROM img_knn
             ),
             filt AS (SELECT * FROM knn WHERE role IN ('user', 'assistant', 'image_ocr')),
             dedup AS (
                 SELECT DISTINCT ON (content) id, ts, project, session_id, role, tool_name, content, dist
                 FROM filt
                 ORDER BY content, dist
             )
             SELECT id, ts, project, session_id, role, tool_name, content, dist
             FROM dedup
             ORDER BY dist
             LIMIT $3"
        )
    } else {
        format!(
            "WITH knn AS MATERIALIZED (
                 SELECT id, ts, project, session_id, role, tool_name, content,
                        embedding <=> '{lit}'::vector AS dist
                 FROM msg
                 WHERE embedding IS NOT NULL
                   AND ($1::text IS NULL OR project LIKE $1)
                 ORDER BY embedding <=> '{lit}'::vector
                 LIMIT $2
             ),
             filt AS (SELECT * FROM knn WHERE role IN ('user', 'assistant')),
             dedup AS (
                 SELECT DISTINCT ON (content) id, ts, project, session_id, role, tool_name, content, dist
                 FROM filt
                 ORDER BY content, dist
             )
             SELECT id, ts, project, session_id, role, tool_name, content, dist
             FROM dedup
             ORDER BY dist
             LIMIT $3"
        )
    };
    let rows = client.query(&sql, &[&proj_like, &over_fetch, &(limit as i64)])?;
    Ok(rows.iter().map(|r| PgRow {
        id: r.get(0),
        ts: r.get(1),
        project: r.get(2),
        session_id: r.get(3),
        role: r.get(4),
        tool_name: r.get(5),
        content: r.get(6),
        score: Some(r.get::<_, f64>(7)),
    }).collect())
}

#[cfg(feature = "pg-backend")]
fn pg_hybrid(client: &mut postgres::Client, http: &reqwest::blocking::Client, query: &str, project: Option<&str>, limit: usize, include_img: bool) -> Result<Vec<PgRow>> {
    // RRF (Reciprocal Rank Fusion) k=60, weight vec=0.7, fts=0.3
    // image_ocr rows already de-emphasized inside pg_vec (dist × 1.10); FTS path
    // relies on ts-DESC + DISTINCT ON dedup for natural de-emphasis.
    let fts = pg_fts(client, query, project, limit * 3, include_img)?;
    let vec = pg_vec(client, http, query, project, limit * 3, include_img)?;
    use std::collections::HashMap;
    type Key = (Option<chrono::DateTime<Utc>>, String, String);
    let key = |r: &PgRow| -> Key { (r.ts, r.role.clone(), r.content.clone()) };
    let mut scores: HashMap<Key, f64> = HashMap::new();
    let mut keep: HashMap<Key, PgRow> = HashMap::new();
    let k = 60.0_f64;
    for (rank, r) in fts.into_iter().enumerate() {
        let kk = key(&r);
        *scores.entry(kk.clone()).or_insert(0.0) += 0.3 / (k + rank as f64 + 1.0);
        keep.insert(kk, r);
    }
    for (rank, r) in vec.into_iter().enumerate() {
        let kk = key(&r);
        *scores.entry(kk.clone()).or_insert(0.0) += 0.7 / (k + rank as f64 + 1.0);
        keep.insert(kk, r);
    }
    let mut merged: Vec<PgRow> = keep.into_values().collect();
    merged.sort_by(|a, b| {
        let sa = scores.get(&key(a)).copied().unwrap_or(0.0);
        let sb = scores.get(&key(b)).copied().unwrap_or(0.0);
        sb.partial_cmp(&sa).unwrap_or(std::cmp::Ordering::Equal)
    });
    merged.truncate(limit);
    Ok(merged)
}

#[cfg(feature = "pg-backend")]
fn fmt_pg_row(r: &PgRow, snippet: usize) -> String {
    let body: String = r.content.chars().take(snippet).collect::<String>().replace('\n', " ").replace('\t', " ");
    let ts_str = match r.ts {
        Some(t) => t.format("%Y-%m-%dT%H:%M").to_string(),
        None    => "----------------".to_string(),
    };
    let proj_short: String = r.project.trim_start_matches('-').chars().take(40).collect();
    let tag = match r.tool_name.as_deref() {
        Some(t) if !t.is_empty() && t != "-" => format!("{}/{}", r.role, t),
        _ => r.role.clone(),
    };
    match r.score {
        Some(s) => format!("{}  [{}]  {}  (d={:.3})  {}", ts_str, proj_short, tag, s, body),
        None    => format!("{}  [{}]  {}  {}",            ts_str, proj_short, tag, body),
    }
}

// ── pgsearchd daemon socket protocol (unix-only) ──
//
// Request (one line JSON, terminated by \n):
//   {"mode": "fts|vec|hybrid", "query": "...", "limit": 10}
// Response (one line JSON, terminated by \n):
//   {"rows": [{"ts": "...", "role": "...", "content": "...", "score": null|f}], "query_ms": N}

#[cfg(all(feature = "pg-backend", unix))]
fn pgsearchd_socket_path() -> Result<std::path::PathBuf> {
    let cache = dirs::cache_dir().ok_or_else(|| anyhow!("$HOME / cache dir unresolved"))?;
    let dir = cache.join("pgsearchd");
    std::fs::create_dir_all(&dir).ok();
    Ok(dir.join("pgsearchd.sock"))
}

#[cfg(all(feature = "pg-backend", unix))]
type PgPool = r2d2::Pool<r2d2_postgres::PostgresConnectionManager<postgres_native_tls::MakeTlsConnector>>;

#[cfg(all(feature = "pg-backend", unix))]
fn build_pool(size: u32) -> Result<PgPool> {
    let native = native_tls::TlsConnector::new()?;
    let tls = postgres_native_tls::MakeTlsConnector::new(native);
    let url = pg_config_url()?;
    let mut cfg: postgres::Config = url.parse().context("bad PG config")?;
    // Client-side TCP keepalive. Without this, a pooled connection that sits idle
    // (e.g. an embed-missing worker spends seconds in ollama between PG UPDATEs)
    // can be silently evicted by an intermediate NAT (home router / FG / ISP CGN),
    // and the *next* socket op blocks in SSLRead until the OS TCP timeout (~2h on
    // macOS) = the build hang this refactor exists to kill. keepalives_idle=30s
    // forces probes that detect/refresh the connection long before NAT eviction.
    cfg.keepalives(true);
    cfg.keepalives_idle(std::time::Duration::from_secs(30));
    let mgr = r2d2_postgres::PostgresConnectionManager::new(cfg, tls);
    Ok(r2d2::Pool::builder()
        .max_size(size)
        .min_idle(Some(size))                                              // pre-fill
        .idle_timeout(Some(std::time::Duration::from_secs(300)))           // 5min
        .max_lifetime(Some(std::time::Duration::from_secs(1800)))          // 30min recycle
        .build(mgr)?)
}

#[cfg(all(feature = "pg-backend", unix))]
fn rows_to_json(rows: &[PgRow]) -> Vec<serde_json::Value> {
    rows.iter().map(|r| serde_json::json!({
        "id": r.id,
        "ts": r.ts.map(|t| t.to_rfc3339()),
        "project": r.project,
        "session_id": r.session_id,
        "role": r.role,
        "tool_name": r.tool_name,
        "content": r.content,
        "score": r.score,
    })).collect()
}

#[cfg(all(feature = "pg-backend", unix))]
fn rows_from_json(v: &serde_json::Value) -> Vec<PgRow> {
    v.as_array().map(|arr| arr.iter().filter_map(|r| {
        Some(PgRow {
            id: r.get("id").and_then(|x| x.as_i64()),
            ts: r.get("ts").and_then(|x| x.as_str()).and_then(|s| {
                chrono::DateTime::parse_from_rfc3339(s).ok().map(|t| t.with_timezone(&Utc))
            }),
            project: r.get("project").and_then(|x| x.as_str()).unwrap_or("").to_string(),
            session_id: r.get("session_id").and_then(|x| x.as_str()).unwrap_or("").to_string(),
            role: r.get("role").and_then(|x| x.as_str()).unwrap_or("").to_string(),
            tool_name: r.get("tool_name").and_then(|x| x.as_str()).map(|s| s.to_string()),
            content: r.get("content").and_then(|x| x.as_str()).unwrap_or("").to_string(),
            score: r.get("score").and_then(|x| x.as_f64()),
        })
    }).collect()).unwrap_or_default()
}

#[cfg(all(feature = "pg-backend", unix))]
fn handle_client(
    stream: std::os::unix::net::UnixStream,
    pool: PgPool,
    http: std::sync::Arc<reqwest::blocking::Client>,
) -> Result<()> {
    use std::io::{BufRead, BufReader, Write};
    let mut reader = BufReader::new(stream.try_clone()?);
    let mut writer = stream;
    // Build-path write RPCs can carry large payloads (whole-file row batches,
    // embed-update batches with 1024-dim vectors). A single read_line on a
    // small-stack thread is fine, but be explicit that we read one \n-terminated
    // JSON request regardless of size.
    let mut line = String::new();
    reader.read_line(&mut line)?;
    let req: serde_json::Value = serde_json::from_str(&line)?;
    let mode = req.get("mode").and_then(|v| v.as_str()).unwrap_or("fts");

    // ── Build-path typed write RPCs (added for the build→daemon pool refactor) ──
    // These keep ALL build PG operations on the daemon's resident, keepalive'd
    // pool instead of bare pg_connect() — the fix for the embed-missing SSLRead
    // hang. Typed (not raw SQL over socket) to avoid injection.
    match mode {
        "embed_select" => {
            let resp = rpc_embed_select(&pool, &req)?;
            writeln!(writer, "{}", resp)?;
            writer.flush()?;
            return Ok(());
        }
        "embed_update" => {
            let resp = rpc_embed_update(&pool, &req)?;
            writeln!(writer, "{}", resp)?;
            writer.flush()?;
            return Ok(());
        }
        "ingest_rows" => {
            let resp = rpc_ingest_rows(&pool, &req)?;
            writeln!(writer, "{}", resp)?;
            writer.flush()?;
            return Ok(());
        }
        "ingest_state_select" => {
            let resp = rpc_ingest_state_select(&pool, &req)?;
            writeln!(writer, "{}", resp)?;
            writer.flush()?;
            return Ok(());
        }
        "build_stats" => {
            let resp = rpc_build_stats(&pool, &req)?;
            writeln!(writer, "{}", resp)?;
            writer.flush()?;
            return Ok(());
        }
        _ => {}
    }

    // ── Search RPCs (original behavior) ──
    let query = req.get("query").and_then(|v| v.as_str()).unwrap_or("");
    let project = req.get("project").and_then(|v| v.as_str());
    let limit = req.get("limit").and_then(|v| v.as_u64()).unwrap_or(10) as usize;
    // include_img defaults to TRUE (v1.15+) when absent — older clients keep working.
    let include_img = req.get("include_img").and_then(|v| v.as_bool()).unwrap_or(true);

    let t0 = std::time::Instant::now();
    let mut conn = pool.get()?;
    let rows = match mode {
        "vec" => pg_vec(&mut *conn, &http, query, project, limit, include_img)?,
        "hybrid" => pg_hybrid(&mut *conn, &http, query, project, limit, include_img)?,
        _ => pg_fts(&mut *conn, query, project, limit, include_img)?,
    };
    let query_ms = t0.elapsed().as_millis();

    let resp = serde_json::json!({"rows": rows_to_json(&rows), "query_ms": query_ms});
    writeln!(writer, "{}", resp)?;
    writer.flush()?;
    Ok(())
}

// ── Daemon-side build-path RPC handlers ──────────────────────────────────────
//
// All run on the resident r2d2 pool (keepalive'd, TLS pre-warmed). They never
// open a bare connection. Each takes the parsed request Value and returns the
// JSON response Value.

/// embed_select — return up to `limit` unembedded msg rows (newest-first),
/// honoring the same prefix/length filter cmd_embed_missing used to apply
/// client-side. Typed: prefix arrives as an array of bare project prefixes
/// (no SQL), turned into parameterized `project LIKE $n` clauses server-side.
#[cfg(all(feature = "pg-backend", unix))]
fn rpc_embed_select(pool: &PgPool, req: &serde_json::Value) -> Result<serde_json::Value> {
    let limit = req.get("limit").and_then(|v| v.as_u64()).unwrap_or(0) as usize;
    let prefixes: Vec<String> = req.get("prefixes")
        .and_then(|v| v.as_array())
        .map(|a| a.iter().filter_map(|x| x.as_str().map(|s| format!("{}%", s))).collect())
        .unwrap_or_default();

    let prefix_clause = if prefixes.is_empty() {
        String::new()
    } else {
        let ors: Vec<String> = (0..prefixes.len()).map(|i| format!("project LIKE ${}", i + 1)).collect();
        format!(" AND ({})", ors.join(" OR "))
    };
    let binds: Vec<&(dyn postgres::types::ToSql + Sync)> =
        prefixes.iter().map(|s| s as &(dyn postgres::types::ToSql + Sync)).collect();

    let mut conn = pool.get()?;
    let limit_clause = if limit > 0 { format!("LIMIT {}", limit) } else { String::new() };
    let sql = format!(
        "SELECT id, content FROM msg
         WHERE embedding IS NULL AND length(content) >= 5{}
         ORDER BY id DESC {}",
        prefix_clause, limit_clause
    );
    let rows = conn.query(&sql, &binds[..])?;
    let out: Vec<serde_json::Value> = rows.iter().map(|r| {
        let id: i64 = r.get(0);
        let content: String = r.get(1);
        serde_json::json!({"id": id, "content": content})
    }).collect();
    Ok(serde_json::json!({"rows": out}))
}

/// embed_update — batch UPDATE msg.embedding for (id, vec) pairs. Each vec is a
/// JSON array of f32; serialized to a pgvector literal server-side. One pooled
/// connection, one transaction for the whole batch.
#[cfg(all(feature = "pg-backend", unix))]
fn rpc_embed_update(pool: &PgPool, req: &serde_json::Value) -> Result<serde_json::Value> {
    let updates = req.get("updates").and_then(|v| v.as_array())
        .ok_or_else(|| anyhow!("embed_update: missing 'updates' array"))?;
    let mut conn = pool.get()?;
    let mut tx = conn.transaction()?;
    let mut updated = 0i64;
    for u in updates {
        let id = match u.get("id").and_then(|v| v.as_i64()) { Some(i) => i, None => continue };
        let vec: Vec<f32> = match u.get("vec").and_then(|v| v.as_array()) {
            Some(a) => a.iter().filter_map(|x| x.as_f64().map(|f| f as f32)).collect(),
            None => continue,
        };
        if vec.len() != PG_VEC_DIM { eprintln!("embed_update skip id={} bad dim={}", id, vec.len()); continue; }
        let lit = vec_literal(&vec);
        let sql = format!("UPDATE msg SET embedding = '{lit}'::vector WHERE id = $1");
        match tx.execute(&sql, &[&id]) {
            Ok(n) => updated += n as i64,
            Err(e) => eprintln!("embed_update id={} err={}", id, e),
        }
    }
    tx.commit()?;
    Ok(serde_json::json!({"updated": updated}))
}

/// ingest_state_select — return all (file_path, mtime) pairs so the build can do
/// its mtime gate client-side without a per-file PG round trip.
#[cfg(all(feature = "pg-backend", unix))]
fn rpc_ingest_state_select(pool: &PgPool, _req: &serde_json::Value) -> Result<serde_json::Value> {
    let mut conn = pool.get()?;
    // Ensure ingest_state exists (moved here from the old client-side cmd_build).
    conn.batch_execute(
        "CREATE TABLE IF NOT EXISTS ingest_state (
            file_path TEXT PRIMARY KEY,
            mtime DOUBLE PRECISION NOT NULL,
            lines BIGINT NOT NULL
        );",
    )?;
    let rows = conn.query("SELECT file_path, mtime FROM ingest_state", &[])?;
    let out: Vec<serde_json::Value> = rows.iter().map(|r| {
        let fp: String = r.get(0);
        let mtime: f64 = r.get(1);
        serde_json::json!({"file_path": fp, "mtime": mtime})
    }).collect();
    Ok(serde_json::json!({"rows": out}))
}

/// ingest_rows — insert a whole file's parsed rows + upsert its ingest_state in
/// one transaction. Typed: rows arrive as structured fields, never raw SQL.
#[cfg(all(feature = "pg-backend", unix))]
fn rpc_ingest_rows(pool: &PgPool, req: &serde_json::Value) -> Result<serde_json::Value> {
    let file_path = req.get("file_path").and_then(|v| v.as_str())
        .ok_or_else(|| anyhow!("ingest_rows: missing 'file_path'"))?;
    let file_mtime = req.get("mtime").and_then(|v| v.as_f64())
        .ok_or_else(|| anyhow!("ingest_rows: missing 'mtime'"))?;
    let rows = req.get("rows").and_then(|v| v.as_array())
        .ok_or_else(|| anyhow!("ingest_rows: missing 'rows' array"))?;
    // Chunked ingest: build sends a file's rows across multiple ingest_rows RPCs
    // (each bounded ~128KB) to avoid a single multi-MB JSON line over the socket
    // and a single huge cross-WAN transaction (the v1.20 SSLRead/idle-in-txn
    // deadlock). `final` (default true for backward compat) marks the last chunk,
    // which also upserts ingest_state so the mtime gate fires next cycle.
    let is_final = req.get("final").and_then(|v| v.as_bool()).unwrap_or(true);

    let mut conn = pool.get()?;
    let mut tx = conn.transaction()?;
    let mut inserted = 0usize;
    {
        let stmt = tx.prepare(
            "INSERT INTO msg (session_id, project, seq, ts, role, tool_name, content)
             VALUES ($1, $2, $3, $4, $5, $6, $7)
             ON CONFLICT (session_id, seq) DO NOTHING",
        )?;
        for r in rows {
            let session_id = r.get("session_id").and_then(|v| v.as_str()).unwrap_or("");
            let project    = r.get("project").and_then(|v| v.as_str()).unwrap_or("");
            let seq        = r.get("seq").and_then(|v| v.as_i64()).unwrap_or(0) as i32;
            let role       = r.get("role").and_then(|v| v.as_str()).unwrap_or("");
            let tool_name  = r.get("tool_name").and_then(|v| v.as_str());
            let content    = r.get("content").and_then(|v| v.as_str()).unwrap_or("");
            let ts_opt: Option<chrono::DateTime<Utc>> = r.get("ts").and_then(|v| v.as_str())
                .and_then(|s| chrono::DateTime::parse_from_rfc3339(s).ok().map(|t| t.with_timezone(&Utc)));
            tx.execute(&stmt, &[
                &session_id, &project, &seq, &ts_opt, &role, &tool_name, &content,
            ])?;
            inserted += 1;
        }
    }
    // Only the final chunk records ingest_state (mtime gate). `lines` is this
    // chunk's count — informational only; the gate keys on mtime, not lines.
    if is_final {
        tx.execute(
            "INSERT INTO ingest_state (file_path, mtime, lines) VALUES ($1, $2, $3)
             ON CONFLICT (file_path) DO UPDATE SET mtime = EXCLUDED.mtime, lines = EXCLUDED.lines",
            &[&file_path, &file_mtime, &(inserted as i64)],
        )?;
    }
    tx.commit()?;
    Ok(serde_json::json!({"inserted": inserted}))
}

/// build_stats — the summary counts cmd_build prints after ingest.
#[cfg(all(feature = "pg-backend", unix))]
fn rpc_build_stats(pool: &PgPool, _req: &serde_json::Value) -> Result<serde_json::Value> {
    let mut conn = pool.get()?;
    let total: i64 = conn.query_one("SELECT COUNT(*) FROM msg", &[])?.get(0);
    let sess:  i64 = conn.query_one("SELECT COUNT(DISTINCT session_id) FROM msg", &[])?.get(0);
    let proj:  i64 = conn.query_one("SELECT COUNT(DISTINCT project) FROM msg", &[])?.get(0);
    let emb_done: i64 = conn.query_one("SELECT COUNT(*) FROM msg WHERE embedding IS NOT NULL", &[])?.get(0);
    let db_size: String = conn.query_one("SELECT pg_size_pretty(pg_database_size(current_database()))", &[])?.get(0);
    Ok(serde_json::json!({
        "total": total, "sessions": sess, "projects": proj,
        "embedded": emb_done, "db_size": db_size,
    }))
}

#[cfg(all(feature = "pg-backend", unix))]
fn cmd_pgsearchd(pool_size: u32) -> Result<()> {
    let sock = pgsearchd_socket_path()?;
    let _ = std::fs::remove_file(&sock);
    let listener = std::os::unix::net::UnixListener::bind(&sock)?;
    // chmod 600 — user-only access
    use std::os::unix::fs::PermissionsExt;
    std::fs::set_permissions(&sock, std::fs::Permissions::from_mode(0o600))?;
    eprintln!("pgsearchd: listening on {}", sock.display());

    let pool = build_pool(pool_size)?;
    let http = std::sync::Arc::new(http_client()?);

    // Pre-warm pool (force TLS handshakes now, not on first query)
    let warm_t0 = std::time::Instant::now();
    let mut handles = vec![];
    for _ in 0..pool_size {
        let pool = pool.clone();
        handles.push(std::thread::spawn(move || pool.get().map(|c| drop(c))));
    }
    for h in handles { let _ = h.join(); }
    eprintln!("pgsearchd: pool warmed ({} conns) in {}ms", pool_size, warm_t0.elapsed().as_millis());

    for stream in listener.incoming() {
        let stream = stream.context("accept")?;
        let pool = pool.clone();
        let http = http.clone();
        std::thread::spawn(move || {
            if let Err(e) = handle_client(stream, pool, http) {
                eprintln!("pgsearchd: client error: {}", e);
            }
        });
    }
    Ok(())
}

#[cfg(all(feature = "pg-backend", unix))]
fn try_daemon(mode: &str, query: &str, project: Option<&str>, limit: usize, include_img: bool) -> Option<(Vec<PgRow>, u128)> {
    use std::io::{BufRead, BufReader, Write};
    let sock_path = pgsearchd_socket_path().ok()?;
    if !sock_path.exists() { return None; }
    let stream = std::os::unix::net::UnixStream::connect(&sock_path).ok()?;
    stream.set_read_timeout(Some(std::time::Duration::from_secs(60))).ok();
    let mut reader = BufReader::new(stream.try_clone().ok()?);
    let mut writer = stream;
    let req = serde_json::json!({
        "mode": mode, "query": query, "project": project, "limit": limit,
        "include_img": include_img,
    });
    writeln!(writer, "{}", req).ok()?;
    writer.flush().ok()?;
    let mut line = String::new();
    reader.read_line(&mut line).ok()?;
    let resp: serde_json::Value = serde_json::from_str(&line).ok()?;
    let rows = rows_from_json(resp.get("rows")?);
    let query_ms = resp.get("query_ms").and_then(|v| v.as_u64())? as u128;
    Some((rows, query_ms))
}

#[cfg(all(feature = "pg-backend", not(unix)))]
fn try_daemon(_mode: &str, _query: &str, _project: Option<&str>, _limit: usize, _include_img: bool) -> Option<(Vec<PgRow>, u128)> {
    None  // pgsearchd is unix-only; non-unix always falls through to direct connect
}

/// Build-path daemon RPC client: send one typed JSON request, return the parsed
/// JSON response. Unlike try_daemon (search, soft-fails to Option), this is the
/// only path for build writes — daemon unreachable ⇒ Err (NO fallback to bare
/// pg_connect, by design: a build that can't reach the pool should stop, not
/// silently open a keepalive-less connection that re-introduces the hang).
///
/// read_timeout is generous because embed_update batches and large ingest_rows
/// payloads can take longer server-side than a small search query.
#[cfg(all(feature = "pg-backend", unix))]
fn daemon_rpc(req: &serde_json::Value) -> Result<serde_json::Value> {
    use std::io::{BufRead, BufReader, Write};
    let sock_path = pgsearchd_socket_path()?;
    if !sock_path.exists() {
        bail!("pgsearchd socket not found at {} — daemon not running (build requires it; no direct-connect fallback)", sock_path.display());
    }
    let stream = std::os::unix::net::UnixStream::connect(&sock_path)
        .with_context(|| format!("connecting to pgsearchd socket {}", sock_path.display()))?;
    stream.set_read_timeout(Some(std::time::Duration::from_secs(300))).ok();
    let mut reader = BufReader::new(stream.try_clone()?);
    let mut writer = stream;
    writeln!(writer, "{}", req)?;
    writer.flush()?;
    let mut line = String::new();
    let n = reader.read_line(&mut line)?;
    if n == 0 {
        bail!("pgsearchd closed connection without a response (mode={:?})", req.get("mode"));
    }
    let resp: serde_json::Value = serde_json::from_str(&line)
        .with_context(|| "parsing pgsearchd response")?;
    Ok(resp)
}

#[cfg(all(feature = "pg-backend", not(unix)))]
fn daemon_rpc(_req: &serde_json::Value) -> Result<serde_json::Value> {
    bail!("daemon RPC requires unix socket (pgsearchd is unix-only)")
}

/// Shared search dispatcher used by pgsearch / csearch / vsearch.
/// Tries daemon first, falls back to direct PG connection.
#[cfg(feature = "pg-backend")]
fn pg_search_dispatch(mode: &str, query: &str, project: Option<&str>, limit: usize, no_daemon: bool, include_img: bool)
    -> Result<(Vec<PgRow>, u128, u128, &'static str)>
{
    let total_t0 = std::time::Instant::now();
    if !no_daemon {
        if let Some((rows, q)) = try_daemon(mode, query, project, limit, include_img) {
            let total = total_t0.elapsed().as_millis();
            return Ok((rows, total.saturating_sub(q), q, "daemon"));
        }
    }
    let t0 = std::time::Instant::now();
    let mut pg = pg_connect()?;
    let connect_ms = t0.elapsed().as_millis();
    let http = http_client()?;
    let t1 = std::time::Instant::now();
    let rows = match mode {
        "vec" => pg_vec(&mut pg, &http, query, project, limit, include_img)?,
        "hybrid" => pg_hybrid(&mut pg, &http, query, project, limit, include_img)?,
        _ => pg_fts(&mut pg, query, project, limit, include_img)?,
    };
    let query_ms = t1.elapsed().as_millis();
    Ok((rows, connect_ms, query_ms, "direct"))
}

#[cfg(feature = "pg-backend")]
fn cmd_pgsearch(query: &str, mode_fts: bool, mode_vec: bool, mode_hybrid: bool, limit: usize, as_json: bool, no_daemon: bool, no_img: bool) -> Result<()> {
    let mode = if mode_vec { "vec" } else if mode_hybrid { "hybrid" } else { let _ = mode_fts; "fts" };
    let (rows, connect_ms, query_ms, source) = pg_search_dispatch(mode, query, None, limit, no_daemon, !no_img)?;

    if as_json {
        println!("{}", serde_json::to_string_pretty(&serde_json::json!({
            "mode": mode,
            "source": source,
            "count": rows.len(),
            "connect_ms": connect_ms,
            "query_ms": query_ms,
            "results": rows_to_json(&rows),
        }))?);
    } else {
        for r in &rows {
            println!("{}", fmt_pg_row(r, 180));
        }
        eprintln!("\n# {}: {} rows  source={}  connect={}ms  query={}ms",
            mode, rows.len(), source, connect_ms, query_ms);
    }
    Ok(())
}

// ─────────────────────────── main ───────────────────────────

fn main() -> Result<()> {
    let cli = Cli::parse();
    match cli.cmd {
        Cmd::Build { no_embed, no_refresh, workers, project_prefix } => cmd_build(no_embed, no_refresh, workers, project_prefix),
        Cmd::Csearch { query, project, limit, no_img, snippet, full: _full_deprecated, with_id } => cmd_csearch(&query, project.as_deref(), limit, no_img, snippet, with_id),
        Cmd::Vsearch { query, project, limit, no_img } => cmd_vsearch(&query, project.as_deref(), limit, no_img),
        Cmd::VsearchSince { query, project, hours, limit, min_len, max_len, max_distance, max_snippet, knn } => {
            let lines = cmd_vsearch_since(&query, &project, hours, limit, min_len, max_len, max_distance, max_snippet, knn)?;
            for l in lines { println!("{}", l); }
            Ok(())
        }
        Cmd::GenRecent { force } => cmd_gen_recent(force),
        Cmd::EmbedMissing { workers, limit, project_prefix } => cmd_embed_missing(workers, limit, project_prefix),
        Cmd::EmbedText { text } => cmd_embed_text(&text),
        Cmd::Doctor => cmd_doctor(),
        Cmd::PruneVec { dry_run } => cmd_prune_vec(dry_run),
        #[cfg(feature = "pg-backend")]
        Cmd::OcrMissing { workers, limit, project_prefix } => {
            cmd_ocr_missing(workers, limit, project_prefix)?;
            // Also backfill embeddings on any new image_ocr rows
            if ollama_up() { let _ = embed_image_ocr_missing(workers); }
            Ok(())
        }
        #[cfg(feature = "pg-backend")]
        Cmd::Pgsearch { query, fts, vec, hybrid, limit, json, no_daemon, no_img } => cmd_pgsearch(&query, fts, vec, hybrid, limit, json, no_daemon, no_img),
        #[cfg(all(feature = "pg-backend", unix))]
        Cmd::Pgsearchd { pool_size, foreground: _ } => cmd_pgsearchd(pool_size),
    }
}
