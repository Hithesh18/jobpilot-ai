Read-only audit task (DO NOT modify any files, and DO NOT output any proprietary business secrets, API keys, credentials, internal URLs, or customer names):

Scan this entire repository / workspace (`package.json`, lockfiles, `tsconfig.json`, `pyproject.toml` / `requirements.txt`, `Dockerfile`s, `docker-compose`, Kubernetes / `Helm` charts, GitHub Actions / GitLab CI workflows, database schemas/migrations, caching/queue modules, auth/middleware, and test configs) to build a 100% factual **Production Tech Stack & Engineering Profile** for my resume tailoring and job-search prioritization.

Output a clean Markdown document titled `# Current Company Verified Production Tech Stack` with these exact 4 sections:

1. **Exact Technologies Used in Production (Categorized)**
   - **Languages & Runtimes:** (exact versions where visible, e.g., TypeScript, JavaScript/Node.js, SQL, Python, Go, Java, etc.)
   - **Frontend Frameworks, UI & State Management:** (e.g., Vue 3, Pinia, React, Next.js, Vite, Tailwind, component libraries, charting)
   - **Backend Frameworks, APIs & Validation:** (e.g., Express.js, NestJS, Fastify, FastAPI, REST, OpenAPI/Swagger, WebSockets, Zod)
   - **Databases, ORMs & Query Layers:** (e.g., MongoDB aggregations/indexes, PostgreSQL, MSSQL, MySQL, Prisma/TypeORM/Drizzle)
   - **Caching, Queues & Event Streaming:** (e.g., Redis cache-aside, Redis Streams consumer groups, BullMQ, Kafka, GCP Pub/Sub, retry/DLQ patterns)
   - **Auth, Multi-Tenancy & Security:** (e.g., JWT, OAuth2/OIDC, RBAC, tenant isolation, rate limiting, billing/payment integrity)
   - **Cloud, Containers, CI/CD & Observability:** (e.g., Docker, Kubernetes, Helm, GCP/AWS/Azure, GitHub Actions/GitLab CI, structured logging, metrics/alerting)
   - **Testing & Code Quality:** (e.g., Jest, Vitest, Playwright, Supertest, ESLint)
   - **AI / LLM / Developer Tooling (if any in repo):** (e.g., RAG, embeddings, vector search, LangChain, LangGraph, MCP, LLM evals)

2. **Real Architecture & Engineering Patterns Implemented Here**
   - Summarize 6–8 concrete, generic (non-confidential) engineering patterns present in this codebase (e.g., multi-tenant data isolation, atomic concurrency/idempotency in billing, Redis cache-aside + DB aggregation optimization, ack-after-persist event consumers, zero-downtime Helm/K8s deployments).

3. **ATS Keyword Synonyms & Exact Punctuation Equivalents**
   - List standard industry keywords in job descriptions that map 1:1 to what is genuinely implemented in this repo without exaggerating or claiming unverified languages.

4. **Top Priority Job Role Titles to Target First**
   - Rank the top 6 job titles & stack combinations where my hands-on experience in this codebase gives me the highest interview conversion rate.
