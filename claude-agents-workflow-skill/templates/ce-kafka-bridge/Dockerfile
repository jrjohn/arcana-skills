FROM rust:1-bookworm AS build
RUN apt-get update && apt-get install -y --no-install-recommends cmake build-essential && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY Cargo.toml .
COPY src ./src
RUN cargo build --release

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates libsasl2-2 && rm -rf /var/lib/apt/lists/*
COPY --from=build /src/target/release/ce-kafka-bridge /usr/local/bin/ce-kafka-bridge
EXPOSE 8088
ENTRYPOINT ["/usr/local/bin/ce-kafka-bridge"]
