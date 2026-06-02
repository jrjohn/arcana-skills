# Multi-arch runtime for the Kogito BPMN engine (built jar copied in).
# Build the jar first:  mvn -DskipTests package  (produces target/quarkus-app/)
FROM eclipse-temurin:21-jre
WORKDIR /deployments
COPY target/quarkus-app/lib/ /deployments/lib/
COPY target/quarkus-app/*.jar /deployments/
COPY target/quarkus-app/app/ /deployments/app/
COPY target/quarkus-app/quarkus/ /deployments/quarkus/
EXPOSE 8080
ENV JAVA_OPTS="-Dquarkus.http.host=0.0.0.0"
CMD ["java","-jar","/deployments/quarkus-run.jar"]
