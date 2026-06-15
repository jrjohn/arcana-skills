// ce-kafka-bridge — thin HTTP -> Kafka producer for CloudEvent ingestion + a
// periodic sweep heartbeat.
//
// (1) Jenkins RunListener HTTP POSTs a structured CloudEvent; this bridge produces
//     it to Kafka (acks=all) so events are DURABLE (survive sf-ci restart) and
//     REPLAYABLE (retained log for problem-tracking). Tiny + restart-stable.
//       POST /jenkins/build  body=CloudEvent JSON -> produce, 202 on broker ack
//       GET  /healthz                             -> {"ok":true}
//
// (2) A heartbeat thread emits a `ci_sweep_requested` CloudEvent every
//     SWEEP_INTERVAL_SECS, driving the event-started ci-sweep workflow. This is
//     the timer that replaced the OS cron daily-run: the tick is a few lines here,
//     the sweep LOGIC lives in the observable SonataFlow workflow.

use std::time::{Duration, SystemTime, UNIX_EPOCH};
use rdkafka::config::ClientConfig;
use rdkafka::producer::{BaseProducer, BaseRecord, Producer};
use tiny_http::{Server, Response, Method, Header};

fn env(k: &str, d: &str) -> String { std::env::var(k).unwrap_or_else(|_| d.to_string()) }

fn make_producer(bootstrap: &str) -> BaseProducer {
    ClientConfig::new()
        .set("bootstrap.servers", bootstrap)
        .set("message.timeout.ms", "10000")
        .set("acks", "all")
        .set("retries", "5")
        .create()
        .expect("kafka producer creation failed")
}

fn main() {
    let bootstrap = env("KAFKA_BOOTSTRAP", "kafka:9092");
    let topic = env("KAFKA_TOPIC", "ci.build.completed");
    let port = env("PORT", "8088");
    let addr = format!("0.0.0.0:{}", port);

    // --- sweep heartbeat thread (the cron replacement) ---
    let sweep_topic = env("SWEEP_TOPIC", "ci.sweep.requested");
    let sweep_interval: u64 = env("SWEEP_INTERVAL_SECS", "21600").parse().unwrap_or(21600); // 6h
    if sweep_interval > 0 {
        let hb_bootstrap = bootstrap.clone();
        std::thread::spawn(move || {
            let hb = make_producer(&hb_bootstrap);
            println!("[ce-kafka-bridge] sweep heartbeat every {}s -> {}", sweep_interval, sweep_topic);
            loop {
                std::thread::sleep(Duration::from_secs(sweep_interval));
                let ts = SystemTime::now().duration_since(UNIX_EPOCH).map(|d| d.as_secs()).unwrap_or(0);
                let ce = format!(
                    "{{\"specversion\":\"1.0\",\"type\":\"ci_sweep_requested\",\"source\":\"ce-kafka-bridge\",\"id\":\"sweep-{}\",\"datacontenttype\":\"application/json\",\"data\":{{\"reason\":\"scheduled-sweep\"}}}}",
                    ts);
                let _ = hb.send(BaseRecord::<str, str>::to(&sweep_topic).payload(&ce).key("sweep"));
                match hb.flush(Duration::from_secs(10)) {
                    Ok(_) => println!("[ce-kafka-bridge] sweep tick -> {} (id sweep-{})", sweep_topic, ts),
                    Err(e) => println!("[ce-kafka-bridge] sweep tick flush error: {}", e),
                }
            }
        });
    }

    let producer = make_producer(&bootstrap);
    let server = Server::http(&addr).expect("http bind failed");
    let json_ct: Header = "Content-Type: application/json".parse().unwrap();
    println!("[ce-kafka-bridge] {} -> kafka {} topic {}", addr, bootstrap, topic);

    for mut req in server.incoming_requests() {
        let method = req.method().clone();
        let url = req.url().to_string();
        if method == Method::Get && url == "/healthz" {
            let _ = req.respond(Response::from_string("{\"ok\":true}").with_header(json_ct.clone()));
            continue;
        }
        if !(method == Method::Post && url == "/jenkins/build") {
            let _ = req.respond(Response::from_string("{\"error\":\"not found\"}")
                .with_status_code(404).with_header(json_ct.clone()));
            continue;
        }
        let mut body = String::new();
        if req.as_reader().read_to_string(&mut body).is_err() {
            let _ = req.respond(Response::from_string("{\"error\":\"read failed\"}")
                .with_status_code(400).with_header(json_ct.clone()));
            continue;
        }
        let key = serde_json::from_str::<serde_json::Value>(&body).ok()
            .and_then(|v| v.get("jobref").and_then(|j| j.as_str()).map(String::from))
            .unwrap_or_default();
        let send = producer.send(BaseRecord::to(&topic).payload(&body).key(&key));
        if let Err((e, _)) = send {
            let msg = format!("{{\"error\":\"enqueue failed: {}\"}}", e);
            println!("[ce-kafka-bridge] enqueue error: {}", e);
            let _ = req.respond(Response::from_string(msg).with_status_code(500).with_header(json_ct.clone()));
            continue;
        }
        match producer.flush(Duration::from_secs(10)) {
            Ok(_) => {
                println!("[ce-kafka-bridge] POST /jenkins/build -> {} (key={})", topic, key);
                let _ = req.respond(Response::from_string("{\"accepted\":true}")
                    .with_status_code(202).with_header(json_ct.clone()));
            }
            Err(e) => {
                let msg = format!("{{\"error\":\"kafka flush failed: {}\"}}", e);
                println!("[ce-kafka-bridge] flush error: {}", e);
                let _ = req.respond(Response::from_string(msg).with_status_code(500).with_header(json_ct.clone()));
            }
        }
    }
}
