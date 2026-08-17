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
docker compose up -d --build frontend backend database
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

## Lab 3 — Workload Identities

Lab 3 assigns SPIFFE identities to the frontend, backend and database using Docker workload attestation.

```text
Frontend  -> spiffe://lab.local/frontend
Backend   -> spiffe://lab.local/backend
Database  -> spiffe://lab.local/database
```

### 1. Add Workload Labels

Each service has a Docker label:

```yaml
labels:
  spiffe.workload: frontend
```

Use `backend` and `database` respectively for the other services.

### 2. Start Services

```bash
docker compose up -d --force-recreate frontend backend database
```

Make sure SPIRE Server and Agent are running:

```bash
docker compose up -d spire-server spire-agent
```

### 3. Find Agent SPIFFE ID

```bash
docker compose exec spire-server \
  /opt/spire/bin/spire-server agent list \
  -socketPath /tmp/spire-server/private/api.sock
```

Copy the agent's SPIFFE ID. It will look similar to:

```text
spiffe://lab.local/spire/agent/join_token/...
```

### 4. Create Workload Entries

Frontend:

```bash
docker compose exec spire-server \
  /opt/spire/bin/spire-server entry create \
  -socketPath /tmp/spire-server/private/api.sock \
  -parentID 'AGENT_SPIFFE_ID' \
  -spiffeID spiffe://lab.local/frontend \
  -selector docker:label:spiffe.workload:frontend
```

Backend:

```bash
docker compose exec spire-server \
  /opt/spire/bin/spire-server entry create \
  -socketPath /tmp/spire-server/private/api.sock \
  -parentID 'AGENT_SPIFFE_ID' \
  -spiffeID spiffe://lab.local/backend \
  -selector docker:label:spiffe.workload:backend
```

Database:

```bash
docker compose exec spire-server \
  /opt/spire/bin/spire-server entry create \
  -socketPath /tmp/spire-server/private/api.sock \
  -parentID 'AGENT_SPIFFE_ID' \
  -spiffeID spiffe://lab.local/database \
  -selector docker:label:spiffe.workload:database
```

### 5. Verify Entries

```bash
docker compose exec spire-server \
  /opt/spire/bin/spire-server entry show \
  -socketPath /tmp/spire-server/private/api.sock
```

Expected:

```text
Found 3 entries

spiffe://lab.local/frontend
  -> docker:label:spiffe.workload:frontend

spiffe://lab.local/backend
  -> docker:label:spiffe.workload:backend

spiffe://lab.local/database
  -> docker:label:spiffe.workload:database
```

### Lab 3 Result

```text
[✓] SPIRE Server
[✓] SPIRE Agent
[✓] Docker Workload Attestation
[✓] Frontend SPIFFE ID
[✓] Backend SPIFFE ID
[✓] Database SPIFFE ID
[ ] mTLS
```

Application traffic is still unchanged:

```text
Frontend -- HTTP --> Backend -- plaintext --> Database
```

The next lab will use these workload identities to establish mTLS.



### Lab 4  — mTLS between Frontend and Backend

## Goal

Enable mTLS between the frontend and backend using:

- SPIFFE workload identities
- SPIRE Agent
- X.509-SVIDs
- Envoy
- SDS

Traffic flow:

```text
Client
  |
  | HTTP
  v
Frontend / Nginx
  |
  | HTTP
  v
Frontend Envoy
  |
  | mTLS
  v
Backend Envoy
  |
  | HTTP
  v
Backend
  |
  | PostgreSQL (plaintext)
  v
Database

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
