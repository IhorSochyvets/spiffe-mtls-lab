# SPIFFE and SPIRE Lab
The lab to implement SPIFFE and SPIRE for docker compose application

Yes — this is a very good lab for learning both **mTLS mechanics** and **workload identity**. I’d build it so that SPIRE, rather than manually generated certificates, ultimately becomes the source of identity and certificates.

A practical target architecture is:

```text
                           Trust Domain: lab.local

                         +----------------+
                         |  SPIRE Server  |
                         |     (CA)       |
                         +-------+--------+
                                 |
                          node attestation
                                 |
                         +-------v--------+
                         |  SPIRE Agent   |
                         |                |
                         | Workload API   |
                         | api.sock       |
                         +---+--------+---+
                             |        |
                  X509-SVID  |        | X509-SVID
                             |        |
            +----------------v+      +v----------------+
Browser --->| Frontend / FE   | mTLS | Backend / BE    |
            |                 +----->+                 |
            | spiffe://       |      | spiffe://       |
            | lab.local/fe    |      | lab.local/be    |
            +-----------------+      +-------+---------+
                                             |
                                             | mTLS
                                             |
                                     +-------v---------+
                                     | Database        |
                                     |                 |
                                     | spiffe://       |
                                     | lab.local/db    |
                                     +-----------------+
```

SPIRE is designed specifically for this pattern: workloads are attested at runtime and receive short-lived, automatically rotated **X.509-SVIDs** that can be used for mTLS. ([Spiffe][1])

I would use something simple like **React/Nginx → Node/Go/Python API → PostgreSQL**. The actual application languages matter much less than the networking and identity setup.

One important distinction: the browser itself should **not** get a SPIFFE identity. Treat `FE` here as the frontend server/container, such as Nginx or a small BFF. The browser talks ordinary HTTPS to the frontend, while the server-side FE container uses its SPIFFE identity when calling BE.

For the lab, I'd use these identities:

```text
spiffe://lab.local/fe
spiffe://lab.local/be
spiffe://lab.local/db
```

SPIRE registration entries map those SPIFFE IDs to workload selectors. SPIRE's Docker workload attestor can identify containers using Docker properties such as labels and image IDs, which makes it well suited to this Compose environment. ([Spiffe][2])

For example, your Compose services could carry labels along these lines:

```yaml
services:

  frontend:
    labels:
      spiffe.workload: frontend

  backend:
    labels:
      spiffe.workload: backend

  database:
    labels:
      spiffe.workload: database
```

Then SPIRE's logical registration would be:

```text
docker label: spiffe.workload:frontend
        ↓
spiffe://lab.local/fe

docker label: spiffe.workload:backend
        ↓
spiffe://lab.local/be

docker label: spiffe.workload:database
        ↓
spiffe://lab.local/db
```

The lab should be built in roughly four stages.

**Stage 1 — plain Docker Compose**

Get this working first:

```text
FE ----HTTP----> BE ----TCP----> PostgreSQL
```

For example:

```yaml
services:

  frontend:
    build: ./frontend
    ports:
      - "8080:8080"
    depends_on:
      - backend
    networks:
      - lab

  backend:
    build: ./backend
    environment:
      DB_HOST: database
    depends_on:
      - database
    networks:
      - lab

  database:
    image: postgres:18
    environment:
      POSTGRES_USER: lab
      POSTGRES_PASSWORD: lab
      POSTGRES_DB: lab
    networks:
      - lab

networks:
  lab:
```

Don't introduce TLS yet. Make sure:

```text
browser → FE → BE → DB
```

works end-to-end.

**Stage 2 — add SPIRE**

Add:

```text
spire-server
spire-agent
```

The server acts as the signing authority, while the agent exposes the local SPIFFE Workload API to workloads. SPIRE expects an agent on every node hosting workloads. In a single-host Compose lab, one agent is therefore enough. ([Spiffe][1])

Your Compose topology becomes:

```text
services:
    spire-server
    spire-agent
    frontend
    backend
    database
```

The Workload API should normally be exposed using a Unix domain socket. The SPIFFE specification explicitly recommends UDS where possible. ([Spiffe][3])

Something conceptually like:

```text
/run/spire/sockets/agent.sock
```

gets mounted into the workloads that need SPIFFE credentials.

The SPIRE agent additionally needs access to the Docker daemon so the Docker workload attestor can determine which container is requesting an identity:

```text
/var/run/docker.sock
```

For a learning lab this is acceptable; it is something you'd treat much more carefully in a production design.

**Stage 3 — prove identities before doing mTLS**

Before touching TLS, make sure each workload actually receives the correct SVID.

You should be able to prove:

```text
frontend
   ↓
SPIRE Agent
   ↓
X509-SVID
SPIFFE ID = spiffe://lab.local/fe
```

and similarly:

```text
backend  → spiffe://lab.local/be
database → spiffe://lab.local/db
```

This part is important because it separates:

```text
identity problem
```

from:

```text
TLS problem
```

SPIRE workload attestation works by examining the calling workload, producing selectors, matching those selectors against registration entries, and returning the corresponding SVID. ([Spiffe][1])

**Stage 4 — introduce mTLS**

Then change:

```text
FE ------- HTTP -------> BE
BE ------- TCP --------> DB
```

into:

```text
FE ======== mTLS ======> BE
BE ======== mTLS ======> DB
```

But authentication should be based on the **SPIFFE identity**, not merely "certificate signed by my CA."

For FE → BE:

```text
Frontend presents:

spiffe://lab.local/fe
```

Backend accepts only:

```text
spiffe://lab.local/fe
```

And Backend presents:

```text
spiffe://lab.local/be
```

Frontend accepts only:

```text
spiffe://lab.local/be
```

Likewise:

```text
BE → DB

client identity:
spiffe://lab.local/be

server identity:
spiffe://lab.local/db
```

That distinction is what makes the lab particularly useful. You're moving from:

```text
"the connection is encrypted"
```

to:

```text
"I cryptographically know which workload is on
the other end of this encrypted connection."
```

There's also a design choice I'd recommend for the **first version**: use **Envoy sidecars** to terminate SPIFFE mTLS instead of immediately modifying every application.

SPIRE explicitly supports either having applications consume credentials directly from the Workload API or using a proxy such as Envoy to establish mTLS on their behalf. ([Spiffe][4])

That would give you:

```text
              localhost                 mTLS
FE app  ----------------> FE Envoy =================>
                                             BE Envoy
                                                |
                                                | localhost
                                                v
                                             BE app


              localhost                 mTLS
BE app  ----------------> BE Envoy =================>
                                             DB Envoy
                                                |
                                                | localhost
                                                v
                                            PostgreSQL
```

So your eventual Compose lab becomes approximately:

```text
spire-server
spire-agent

frontend
frontend-envoy

backend
backend-envoy

postgres
postgres-envoy
```

Each Envoy talks to SPIRE's Workload API and gets the certificate/key/bundle needed for its workload identity.

This is pedagogically nice because you can inspect the layers separately:

```text
Application
    ↓
Envoy
    ↓
SPIFFE/SPIRE identity
    ↓
X.509-SVID
    ↓
TLS 1.3
    ↓
Docker network
```

Then, as an **advanced exercise**, remove Envoy for one hop and have the application consume the SPIFFE Workload API directly. That shows the difference between application-native SPIFFE and proxy-based SPIFFE.

A particularly useful final test matrix would be:

```text
FE → BE
correct FE SVID
✓ allowed

random-container → BE
no valid SVID
✗ TLS rejected

DB → BE
valid SVID but wrong identity
✗ authorization rejected

BE → DB
correct BE SVID
✓ allowed

FE → DB
valid FE SVID but unauthorized identity
✗ rejected

expired/rotated certificate
✓ SPIRE automatically supplies replacement
```

That last set of tests is where the lab becomes much more valuable than merely configuring TLS.

The current SPIFFE documentation lists **SPIRE v1.15.2** and provides both a Docker quickstart and additional Docker Compose examples, so you have a current official reference implementation to compare against as you build this. ([Spiffe][5])

I'd structure the repository like this:

```text
spiffe-mtls-lab/
│
├── docker-compose.yml
│
├── README.md
│
├── spire/
│   ├── server.conf
│   ├── agent.conf
│   └── entries/
│
├── frontend/
│   ├── Dockerfile
│   └── ...
│
├── backend/
│   ├── Dockerfile
│   └── ...
│
├── database/
│   └── ...
│
└── envoy/
    ├── frontend-envoy.yaml
    ├── backend-envoy.yaml
    └── database-envoy.yaml
```

And the progression becomes:

```text
LAB 1
Docker Compose
FE → BE → DB

        ↓

LAB 2
SPIRE Server + Agent
workload attestation

        ↓

LAB 3
FE, BE, DB receive unique SPIFFE IDs

        ↓

LAB 4
FE ⇄ BE mTLS using X509-SVID

        ↓

LAB 5
BE ⇄ DB mTLS using X509-SVID

        ↓

LAB 6
authorization based on SPIFFE ID

        ↓

LAB 7
certificate rotation + attack/failure tests
```

This sequence also teaches the important conceptual separation between **SPIFFE**, which defines workload identity and APIs, **SPIRE**, which implements those APIs and performs attestation/credential issuance, and **mTLS**, which consumes those identities to authenticate and encrypt connections.

[1]: https://spiffe.io/docs/latest/spire-about/spire-concepts/?utm_source=chatgpt.com "SPIRE Concepts | SPIFFE"
[2]: https://spiffe.io/docs/latest/deploying/configuring/?utm_source=chatgpt.com "Configuring SPIRE | SPIFFE"
[3]: https://spiffe.io/docs/latest/spiffe-specs/spiffe_workload_endpoint/?utm_source=chatgpt.com "SPIFFE Workload Endpoint | SPIFFE"
[4]: https://spiffe.io/docs/latest/spire-about/use-cases/?utm_source=chatgpt.com "SPIRE Use Cases | SPIFFE"
[5]: https://spiffe.io/docs/latest/try/spire101/?utm_source=chatgpt.com "Quickstart for Docker | SPIFFE"
