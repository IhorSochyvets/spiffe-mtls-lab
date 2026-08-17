# SPIFFE and SPIRE Lab
The lab to implement SPIFFE and SPIRE for docker compose application


# SPIFFE / SPIRE mTLS Lab

Learning project for experimenting with:

- Docker Compose
- Microservices
- TLS
- mTLS
- SPIFFE
- SPIRE
- X.509 SVIDs
- Envoy
- Workload identity

## Lab 1

Lab 1 implements the application without TLS or SPIFFE.

Architecture:

```text
Browser
   |
   | HTTP
   v
Frontend / Nginx
   |
   | HTTP
   v
Backend / FastAPI
   |
   | Plain PostgreSQL TCP
   v
PostgreSQL
```

## Start

```bash
docker compose up --build
```

Open:

```text
http://localhost:8080
```

## Test backend through frontend

```bash
curl http://localhost:8080/api/
```

Expected response:

```json
{
  "service": "backend",
  "status": "ok",
  "lab": "Lab 1",
  "transport": "HTTP",
  "mtls": false,
  "spiffe": false
}
```

## Test database path

```bash
curl http://localhost:8080/api/messages
```

Traffic flow:

```text
curl
  |
  v
localhost:8080
  |
  v
frontend
  |
  | HTTP
  v
backend:8000
  |
  | PostgreSQL
  v
database:5432
```

## View containers

```bash
docker compose ps
```

## View logs

```bash
docker compose logs -f
```

Or:

```bash
docker compose logs -f frontend
docker compose logs -f backend
docker compose logs -f database
```

## Stop

```bash
docker compose down
```

Remove PostgreSQL data as well:

```bash
docker compose down -v
```

## Planned labs

### Lab 1

Plain communication.

```text
FE -- HTTP --> BE -- PostgreSQL --> DB
```

### Lab 2

Add SPIRE Server and SPIRE Agent.

### Lab 3

Assign workload identities:

```text
spiffe://lab.local/frontend
spiffe://lab.local/backend
spiffe://lab.local/database
```

### Lab 4

Enable mTLS between frontend and backend.

```text
FE == mTLS ==> BE
```

### Lab 5

Enable mTLS between backend and database.

```text
BE == mTLS ==> DB
```

### Lab 6

Authorize connections using SPIFFE IDs.

### Lab 7

Test certificate rotation and invalid workload identities.

This sequence also teaches the important conceptual separation between **SPIFFE**, which defines workload identity and APIs, **SPIRE**, which implements those APIs and performs attestation/credential issuance, and **mTLS**, which consumes those identities to authenticate and encrypt connections.

[1]: https://spiffe.io/docs/latest/spire-about/spire-concepts/?utm_source=chatgpt.com "SPIRE Concepts | SPIFFE"
[2]: https://spiffe.io/docs/latest/deploying/configuring/?utm_source=chatgpt.com "Configuring SPIRE | SPIFFE"
[3]: https://spiffe.io/docs/latest/spiffe-specs/spiffe_workload_endpoint/?utm_source=chatgpt.com "SPIFFE Workload Endpoint | SPIFFE"
[4]: https://spiffe.io/docs/latest/spire-about/use-cases/?utm_source=chatgpt.com "SPIRE Use Cases | SPIFFE"
[5]: https://spiffe.io/docs/latest/try/spire101/?utm_source=chatgpt.com "Quickstart for Docker | SPIFFE"
