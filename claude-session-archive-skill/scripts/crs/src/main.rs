// crs — Rust port of claude-session-archive Python helpers.
//
// Subcommands:
//   build         JSONL → SQLite incremental ingest + optional embed + refresh auto_recent
//   csearch       FTS5 lexical search
//   vsearch       semantic KNN search (over msg_vec)
//   vsearch-since time-bounded vsearch (used by gen-recent)
//   gen-recent    replace gen-recent-context.sh (skip-guard + vsearch + write file)
//   embed-missing parallel backfill of msg → msg_vec (replaces embed_parallel.py)
//   embed-text    debug helper — embed one string and print first 5 dims

use anyhow::{Context, Result, anyhow, bail};
use chrono::{Local, Utc};
use clap::{Parser, Subcommand};
use rusqlite::{Connection, OpenFlags, params};
use serde::Deserialize;
use serde_json::Value;
use std::env;
use std::fs;
use std::io::{BufRead, BufReader, Read, Write};
use std::path::{Path, PathBuf};
use std::sync::Mutex;
use std::time::SystemTime;

const OLLAMA_URL: &str = "http://localhost:11434/api/embed";
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
    },
    /// FTS5 lexical search
    Csearch {
        query: String,
        project: Option<String>,
        #[arg(long, default_value = "20")]
        limit: usize,
    },
    /// Semantic KNN search
    Vsearch {
        query: String,
        project: Option<String>,
        #[arg(long, default_value = "10")]
        limit: usize,
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
    },
    /// Embed one string and print first 5 dims (debug helper)
    EmbedText { text: String },
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
    let resp: EmbedResponse = client.post(OLLAMA_URL).json(&body).send()?.error_for_status()?.json()?;
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

fn vec_to_blob(v: &[f32]) -> Vec<u8> {
    let mut out = Vec::with_capacity(v.len() * 4);
    for f in v {
        out.extend_from_slice(&f.to_le_bytes());
    }
    out
}

// ─────────────────────────── csearch ───────────────────────────

fn cmd_csearch(query: &str, project: Option<&str>, limit: usize) -> Result<()> {
    let conn = open_db_readonly()?;
    let sql = match project {
        Some(_) => {
            "SELECT substr(m.ts,1,16), m.project, m.role, COALESCE(m.tool_name,'-'), \
             substr(replace(replace(m.content, X'0A',' '), X'09',' '),1,180) \
             FROM msg m WHERE m.rowid IN (SELECT rowid FROM msg_fts WHERE content MATCH ?1) \
             AND m.project LIKE ?2 ORDER BY m.ts DESC LIMIT ?3"
        }
        None => {
            "SELECT substr(m.ts,1,16), m.project, m.role, COALESCE(m.tool_name,'-'), \
             substr(replace(replace(m.content, X'0A',' '), X'09',' '),1,180) \
             FROM msg m WHERE m.rowid IN (SELECT rowid FROM msg_fts WHERE content MATCH ?1) \
             ORDER BY m.ts DESC LIMIT ?2"
        }
    };
    let mut stmt = conn.prepare(sql)?;
    let proj_pat = project.map(|p| format!("%{}%", p));
    let rows = if let Some(pat) = &proj_pat {
        stmt.query_map(params![query, pat, limit as i64], |r| {
            Ok((
                r.get::<_, String>(0)?,
                r.get::<_, String>(1)?,
                r.get::<_, String>(2)?,
                r.get::<_, String>(3)?,
                r.get::<_, String>(4)?,
            ))
        })?
        .collect::<Result<Vec<_>, _>>()?
    } else {
        stmt.query_map(params![query, limit as i64], |r| {
            Ok((
                r.get::<_, String>(0)?,
                r.get::<_, String>(1)?,
                r.get::<_, String>(2)?,
                r.get::<_, String>(3)?,
                r.get::<_, String>(4)?,
            ))
        })?
        .collect::<Result<Vec<_>, _>>()?
    };

    if rows.is_empty() {
        eprintln!("(no results)");
        return Ok(());
    }
    for (ts, proj, role, tool, content) in rows {
        let proj_short = proj.trim_start_matches('-').chars().take(40).collect::<String>();
        let tag = if tool == "-" { role } else { format!("{}/{}", role, tool) };
        println!("{}  [{}]  {}  {}", ts, proj_short, tag, content.trim());
    }
    Ok(())
}

// ─────────────────────────── vsearch ───────────────────────────

fn cmd_vsearch(query: &str, project: Option<&str>, limit: usize) -> Result<()> {
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

// ─────────────────────────── vsearch-since ───────────────────────────

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
    let db = archive.join("sessions.db");
    if !db.exists() {
        log_line("SKIP", "no session.db");
        return Ok(());
    }

    let mem_dir = home().join(format!(".claude/projects/{}/memory", slug));
    let pending = mem_dir.join("project_pending.md");
    let out_file = mem_dir.join("auto_recent.md");

    if !mem_dir.is_dir() {
        log_line("SKIP", &format!("unknown project slug={} (no memory dir)", slug));
        return Ok(());
    }

    // Skip guard
    let force_env = env::var("FORCE_REGEN").map(|v| v == "1").unwrap_or(false);
    if !force && !force_env && out_file.exists() {
        let last_gen_ts = mtime_secs(&out_file);
        let pending_ts = if pending.exists() { mtime_secs(&pending) } else { 0 };
        let conn = open_db_readonly()?;
        let latest_msg_ts: i64 = conn
            .query_row(
                "SELECT IFNULL(strftime('%s', MAX(ts)), 0) FROM msg WHERE project = ?1",
                params![slug],
                |r| r.get::<_, String>(0).map(|s| s.parse::<i64>().unwrap_or(0))
                       .or_else(|_| r.get::<_, i64>(0)),
            )
            .unwrap_or(0);
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

fn cmd_build(no_embed: bool, no_refresh: bool, workers: usize) -> Result<()> {
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
            if let Err(e) = cmd_embed_missing(workers, 0) {
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

// ─────────────────────────── embed-missing ───────────────────────────

fn cmd_embed_missing(workers: usize, limit: usize) -> Result<()> {
    let conn = open_db_with_vec()?;

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
         WHERE v.rowid IS NULL AND length(m.content) >= 5 \
         ORDER BY m.rowid DESC {}",
        limit_clause
    );
    let mut stmt = conn.prepare(&select_sql)?;
    let jobs: Vec<(i64, String)> = stmt
        .query_map([], |r| Ok((r.get::<_, i64>(0)?, r.get::<_, String>(1)?)))?
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

// ─────────────────────────── embed-text (debug) ───────────────────────────

fn cmd_embed_text(text: &str) -> Result<()> {
    let client = http_client()?;
    let v = embed_text(&client, text)?;
    println!("dim={} first5={:?}", v.len(), &v[..5.min(v.len())]);
    Ok(())
}

// ─────────────────────────── main ───────────────────────────

fn main() -> Result<()> {
    let cli = Cli::parse();
    match cli.cmd {
        Cmd::Build { no_embed, no_refresh, workers } => cmd_build(no_embed, no_refresh, workers),
        Cmd::Csearch { query, project, limit } => cmd_csearch(&query, project.as_deref(), limit),
        Cmd::Vsearch { query, project, limit } => cmd_vsearch(&query, project.as_deref(), limit),
        Cmd::VsearchSince { query, project, hours, limit, min_len, max_len, max_distance, max_snippet, knn } => {
            let lines = cmd_vsearch_since(&query, &project, hours, limit, min_len, max_len, max_distance, max_snippet, knn)?;
            for l in lines { println!("{}", l); }
            Ok(())
        }
        Cmd::GenRecent { force } => cmd_gen_recent(force),
        Cmd::EmbedMissing { workers, limit } => cmd_embed_missing(workers, limit),
        Cmd::EmbedText { text } => cmd_embed_text(&text),
    }
}
