## Lab 2 — SPIRE Server and Agent

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
