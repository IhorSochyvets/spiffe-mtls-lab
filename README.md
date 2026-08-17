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

### Lab 1 — Frontend, Backend and Database

Lab 1 creates the basic application without SPIFFE, SPIRE or mTLS.

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
   | PostgreSQL
   v
Database / PostgreSQL
```

### 1. Start Lab

```bash
docker compose up -d --build
```

Verify:

```bash
docker compose ps
```

Frontend, backend and database should be running.

### 2. Test Frontend

Open in a browser:

```text
http://localhost:8080
```

### 3. Test Backend

The frontend proxies `/api/` to the backend:

```bash
curl http://localhost:8080/api/
```

Expected result:

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

### 4. Test Database

Test the complete FE → BE → DB path:

```bash
curl http://localhost:8080/api/messages
```

Expected result contains messages loaded from PostgreSQL.

### Lab 1 Result

```text
[✓] Frontend
[✓] Backend
[✓] PostgreSQL
[✓] FE → BE communication
[✓] BE → DB communication
[ ] SPIRE
[ ] SPIFFE identities
[ ] mTLS
```

All internal communication is still plaintext.

### Lab 2 — SPIRE Server and Agent

Lab 2 adds the SPIRE Server and SPIRE Agent.

```text
SPIRE Server
     ^
     |
     | Node Attestation
     |
SPIRE Agent
```

### 1. Start SPIRE Server

```bash
docker compose up -d spire-server
```

Verify:

```bash
docker compose ps spire-server
```

### 2. Generate Agent Join Token

```bash
docker compose exec spire-server \
  /opt/spire/bin/spire-server token generate \
  -socketPath /tmp/spire-server/private/api.sock
```

Example:

```text
Token: 7471264b-e009-475d-8e6e-a0f35bd9059c
```

The join token is temporary and can only be used once.

### 3. Bootstrap SPIRE Agent

Use the generated token:

```bash
docker compose run --rm spire-agent \
  -config /run/spire/config/agent.conf \
  -joinToken YOUR_TOKEN
```

Leave the agent running.

### 4. Verify Agent

In another terminal:

```bash
docker compose exec spire-server \
  /opt/spire/bin/spire-server agent list \
  -socketPath /tmp/spire-server/private/api.sock
```

Expected result:

```text
Found 1 attested agent:

SPIFFE ID         : spiffe://lab.local/spire/agent/join_token/...
Attestation type  : join_token
Agent version     : 1.15.2
```

### 5. Start Agent Normally

After the first successful attestation, the agent state is persisted.

Stop the interactive agent and start it normally:

```bash
docker compose up -d spire-agent
```

The join token is no longer required.

### Lab 2 Result

```text
[✓] SPIRE Server
[✓] SPIRE Agent
[✓] Node attestation
[✓] Agent SVID
[ ] Workload identities
[ ] mTLS
```

Frontend → Backend → Database communication is still unchanged and plaintext.

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
