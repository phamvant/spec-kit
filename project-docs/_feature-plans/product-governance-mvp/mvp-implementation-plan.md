# Product Governance MVP — Implementation Plan

**Status:** Approved for implementation
**Created:** 2026-06-19  
**Target repository:** GitHub Spec Kit  
**Primary delivery model:** Extension + preset + workflow  
**Companion backlog:** [post-mvp-backlog.md](./post-mvp-backlog.md)
**Approved contracts:** [decisions.md](./decisions.md)

## 1. Problem Statement

Spec Kit hiện quản lý tốt vòng đời của một feature đang active:

```text
spec.md → plan.md → tasks.md → implementation
```

Constitution cung cấp project-wide governance, nhưng chưa có mô hình first-class
cho:

- requirement hierarchy toàn sản phẩm;
- traceability xuyên nhiều feature;
- coverage của global requirements;
- propagation từ master spec xuống feature;
- impact analysis ở cấp sản phẩm;
- audit giữa requirements, feature artifacts, implementation evidence và
  changelog.

MVP phải bổ sung các capability này mà không phá vỡ core feature workflow và
không buộc mọi người dùng Spec Kit phải sử dụng product governance.

## 2. MVP Outcome

Sau MVP, một project đã bật extension phải có thể:

1. Khởi tạo product governance artifacts.
2. Đăng ký global requirements với ID duy nhất và bất biến.
3. Khai báo một feature `implements`, `refines` hoặc `impacts` requirement nào.
4. Chạy impact analysis trước khi feature đi vào planning.
5. Chặn feature có traceability sai hoặc thiếu.
6. Tính global requirement coverage theo quy tắc xác định.
7. Ghi một change event append-only sau khi feature được verification.
8. Chạy product audit tổng thể và nhận cả Markdown report lẫn JSON dùng cho CI.
9. Chạy một workflow có human gates cho impact, feature spec và verification.

## 3. Non-Goals

Các nội dung sau không thuộc MVP:

- Quản lý release baseline đầy đủ.
- Requirement version history ở cấp field.
- UI/dashboard.
- Đồng bộ Jira, Linear hoặc GitHub Projects.
- Multi-repository product graph.
- Agent chạy song song thực sự.
- Tự động phê duyệt requirement hoặc release.
- Product analytics và telemetry.
- Full source-code semantic verification.
- Tự động migrate requirement schema giữa các major version.
- Thay thế constitution hoặc core `spec.md`.

Các capability này được lưu trong
[post-mvp-backlog.md](./post-mvp-backlog.md).

## 4. Design Principles

### 4.1 Deterministic core, semantic assistance

Python code chịu trách nhiệm cho:

- schema validation;
- cấp và kiểm tra ID;
- lifecycle transition;
- relationship graph;
- orphan và broken-link detection;
- coverage calculation;
- append-only ledger;
- JSON output và process exit code.

Agent commands chịu trách nhiệm cho:

- phân tích semantic impact;
- phát hiện requirement có ý nghĩa mâu thuẫn;
- đề xuất traceability;
- viết report dễ đọc;
- đề xuất remediation.

Agent không được tự thay đổi registry, lifecycle hoặc ledger bằng cách sửa file
trực tiếp. Các mutation phải đi qua deterministic scripts.

### 4.2 Additive architecture

MVP phải được triển khai chủ yếu như:

```text
extension: product-governance
preset:    product-sdd
workflow:  product-feature-cycle
```

Core chỉ nên thay đổi khi thiếu extension point hoặc có bug ngăn cách triển khai
additive.

### 4.3 Markdown for humans, YAML/JSON for machines

- Markdown giải thích intent và product context.
- YAML giữ registry do con người review.
- JSON là generated output cho tooling và CI.
- JSONL là append-only event ledger.

### 4.4 Explicit evidence

`implemented`, `verified` và `released` là các trạng thái khác nhau. MVP chỉ
được chuyển requirement hoặc feature sang `verified` khi có evidence hợp lệ.

### 4.5 Audit is read-only

Audit không tự sửa requirement, feature spec, code hoặc ledger. Nó tạo report
và exit code. Remediation là thao tác riêng.

## 5. Proposed Project Layout

Khi extension được khởi tạo trong project người dùng:

```text
.product/
├── product.md
├── glossary.md
├── requirements.yml
├── relationships.yml
├── coverage.json
├── changes/
│   └── ledger.jsonl
├── reports/
│   └── .gitkeep
└── schemas/
    └── schema-version

specs/
└── 012-example-feature/
    ├── proposal.md
    ├── impact.md
    ├── spec.md
    ├── plan.md
    ├── tasks.md
    └── evidence/
        └── verification.json
```

Trong source repo Spec Kit:

```text
extensions/product-governance/
├── extension.yml
├── README.md
├── product-governance-config.yml
├── commands/
│   ├── speckit.product-governance.init.md
│   ├── speckit.product-governance.requirement.md
│   ├── speckit.product-governance.impact.md
│   ├── speckit.product-governance.validate.md
│   ├── speckit.product-governance.verify.md
│   ├── speckit.product-governance.changelog.md
│   └── speckit.product-governance.audit.md
├── scripts/
│   ├── product_governance/
│   │   ├── __init__.py
│   │   ├── cli.py
│   │   ├── models.py
│   │   ├── registry.py
│   │   ├── graph.py
│   │   ├── coverage.py
│   │   ├── ledger.py
│   │   └── audit.py
│   ├── bash/
│   └── powershell/
├── schemas/
│   ├── requirements.schema.json
│   ├── relationships.schema.json
│   ├── feature-trace.schema.json
│   ├── verification.schema.json
│   ├── ledger-event.schema.json
│   └── audit-report.schema.json
└── templates/
    ├── product-template.md
    ├── proposal-template.md
    ├── impact-template.md
    └── verification-template.json

presets/product-sdd/
├── preset.yml
├── README.md
├── commands/
└── templates/

workflows/product-feature-cycle/
└── workflow.yml
```

Python package có thể được điều chỉnh theo convention đóng gói extension hiện
tại, nhưng domain modules phải giữ ranh giới tương đương để dễ kiểm thử.

## 6. Canonical Data Model

### 6.1 Requirement

`requirements.yml` là registry canonical:

```yaml
schema_version: "1.0"
product:
  id: taskify
  name: Taskify

requirements:
  - id: PRD-AUTH-001
    title: Authenticate users
    description: Users must authenticate before accessing protected data.
    type: functional
    capability: CAP-IDENTITY
    status: approved
    priority: must
    owner: product
    source: product.md#authentication
    verification:
      method: acceptance-test
    depends_on: []
    supersedes: []
    tags: [security, identity]

id_sequences:
  AUTH: 1
```

Các field bắt buộc:

| Field | Rule |
|---|---|
| `id` | Unique, immutable, pattern `PRD-[A-Z0-9]+-[0-9]{3,}` |
| `title` | Không rỗng |
| `description` | Có statement kiểm chứng được |
| `type` | `goal`, `capability`, `functional`, `quality`, `constraint` |
| `status` | Theo lifecycle được hỗ trợ |
| `priority` | `must`, `should`, `could`, `wont` |
| `owner` | Không rỗng |
| `verification.method` | Phương thức xác minh đã biết |

Lifecycle MVP:

```text
proposed → reviewed
reviewed → proposed | approved
approved → implementing | deprecated
implementing → approved | implemented | deprecated
implemented → implementing | verified | deprecated
verified → deprecated
deprecated → retired
```

MVP chưa cung cấp trạng thái `released`; trạng thái này phụ thuộc release
baseline hậu MVP.

Chỉ deterministic CLI được mutate lifecycle. `verified` yêu cầu evidence
`passed` hợp lệ và `retired` là terminal.

### 6.2 Relationships

`relationships.yml` lưu quan hệ không thuộc riêng một requirement:

```yaml
schema_version: "1.0"
relationships:
  - from: PRD-AUTH-002
    type: depends_on
    to: PRD-AUTH-001
```

Relationship types MVP:

- `parent_of`
- `depends_on`
- `conflicts_with`
- `supersedes`

Validator phải phát hiện:

- endpoint không tồn tại;
- self-reference;
- cycle trong `parent_of` và `depends_on`;
- duplicate edge;
- asymmetric conflict declaration và normalize khi build graph.

### 6.3 Feature traceability

Feature traceability được lưu trong `spec.md` để người review nhìn thấy, đồng
thời có generated sidecar `feature-trace.json` để tooling không phụ thuộc parse
Markdown tự do:

```json
{
  "schema_version": "1.0",
  "feature": "012-sso",
  "implements": ["PRD-AUTH-001"],
  "refines": ["PRD-SEC-004"],
  "impacts": ["PRD-AUDIT-002"],
  "unaffected": ["PRD-BILLING-001"]
}
```

`feature-trace.json` là machine-readable canonical artifact. Deterministic
writer cập nhật nó cùng Product Traceability section có cấu trúc trong `spec.md`,
ghi digest của section và sort requirement IDs theo lexicographic order.
Validator phải fail khi section, sidecar hoặc digest bị drift.

### 6.4 Verification evidence

```json
{
  "schema_version": "1.0",
  "feature": "012-sso",
  "verified_at": "2026-06-19T10:00:00Z",
  "commit": "abc123",
  "requirements": {
    "PRD-AUTH-001": {
      "status": "passed",
      "evidence": [
        {
          "type": "test",
          "reference": "tests/auth/test_sso.py"
        }
      ]
    }
  }
}
```

MVP không chứng minh test reference thực sự đầy đủ về mặt semantic, nhưng phải
kiểm tra file/reference tồn tại nếu là local path.

### 6.5 Change event

Mỗi dòng trong `.product/changes/ledger.jsonl`:

```json
{
  "schema_version": "1.0",
  "event_id": "CHG-000142",
  "occurred_at": "2026-06-19T10:05:00Z",
  "event_type": "feature_verified",
  "feature": "012-sso",
  "requirements": ["PRD-AUTH-001"],
  "commit": "abc123",
  "evidence": ["specs/012-sso/evidence/verification.json"],
  "actor": "product-governance"
}
```

Ledger rules:

- append-only;
- `event_id` tăng đơn điệu;
- không sửa hoặc xóa event cũ;
- correction dùng event mới với `corrects_event`;
- append phải atomic;
- duplicate semantic event phải được phát hiện bằng idempotency key.

## 7. Command Surface

### 7.1 `/speckit.product-governance.init`

Tạo `.product/` từ templates.

Done when:

- Không overwrite file người dùng nếu chưa có `--force`.
- Tạo registry hợp lệ nhưng rỗng.
- Chạy validate thành công ngay sau init.

### 7.2 `/speckit.product-governance.requirement`

Agent hỗ trợ diễn giải input; deterministic script thực hiện mutation.

Operations MVP:

- add;
- update nội dung mutable;
- transition status;
- deprecate;
- list/show.

ID chỉ được cấp bởi script.

### 7.3 `/speckit.product-governance.impact`

Input:

- mô tả feature mới hoặc feature directory hiện tại.

Output:

- `proposal.md`;
- `impact.md`;
- candidate `feature-trace.json`;
- finding về affected requirements/capabilities;
- unresolved questions;
- machine-readable summary.

Command không được tự approve traceability.

### 7.4 `/speckit.product-governance.validate`

Deterministic validation:

- schemas;
- IDs;
- lifecycle;
- graph;
- feature trace links;
- verification links;
- ledger integrity.

CLI contract:

```text
exit 0: valid
exit 1: validation findings
exit 2: invalid invocation or infrastructure failure
```

Hỗ trợ `--json`.

### 7.5 `/speckit.product-governance.verify`

Tạo hoặc cập nhật verification evidence cho active feature.

Command phải:

- đọc feature trace;
- yêu cầu evidence cho mỗi `implements` requirement;
- phân biệt pass/fail/not-run;
- không ghi changelog nếu còn required evidence fail hoặc missing.

### 7.6 `/speckit.product-governance.changelog`

Chỉ được append event khi:

- feature trace hợp lệ;
- verification evidence hợp lệ;
- required requirements có trạng thái `passed`;
- commit reference có giá trị;
- cùng idempotency key chưa tồn tại.

Nó generate thêm human-readable summary nhưng ledger là canonical history.

### 7.7 `/speckit.product-governance.audit`

Read-only audit với hai lớp:

1. Deterministic audit.
2. Semantic audit do agent thực hiện từ bounded context.

Output:

```text
.product/reports/audit-<timestamp>.json
.product/reports/audit-<timestamp>.md
```

Severity:

- `critical`: integrity hoặc contradiction làm sai product contract;
- `high`: approved requirement thiếu coverage/evidence;
- `medium`: drift hoặc risk chưa chặn baseline functionality;
- `low`: hygiene/documentation.

CI exit policy mặc định:

- exit 1 nếu có `critical` hoặc `high`;
- configurable để chỉ chặn `critical`.

## 8. Preset Changes

Preset `product-sdd` override hoặc compose các command sau:

### `speckit.specify`

Trước khi tạo spec:

- yêu cầu `.product/requirements.yml`;
- chạy impact analysis;
- đưa Product Traceability section vào spec;
- tạo `feature-trace.json`;
- không cho phép reference requirement không tồn tại.

### `speckit.plan`

Phải đọc:

- linked product requirements;
- affected capabilities;
- `impact.md`;
- constitution.

Plan phải ghi rõ cross-feature interfaces và migration risk khi có.

### `speckit.tasks`

Mỗi task phải có một trong:

- requirement reference;
- user story reference đã map tới requirement;
- marker `[INTERNAL]` cho maintenance không trực tiếp implement requirement.

### `speckit.analyze`

Bổ sung:

- global requirement linkage;
- cross-feature conflict candidates;
- requirement-to-task coverage;
- stale impact analysis.

### `speckit.implement`

Phải:

- đọc bounded product context;
- không tự đổi requirement thành `verified`;
- tạo implementation summary cho verification command;
- giữ core task progress behavior.

## 9. Workflow

`product-feature-cycle`:

```yaml
steps:
  - product impact analysis
  - gate: approve impact and traceability
  - specify
  - gate: approve feature specification
  - plan
  - tasks
  - analyze
  - gate: approve implementation scope
  - implement
  - product verification
  - gate: approve verification evidence
  - append changelog event
  - product audit
```

Workflow phải resumable và không append changelog trước verification gate.

Nếu audit fail:

- run kết thúc failed;
- report được giữ lại;
- ledger event đã append vẫn không bị xóa;
- remediation tạo run mới hoặc resume theo policy được xác định.

Thứ tự canonical đã chốt:

1. verify;
2. approval gate;
3. pre-change audit;
4. append ledger;
5. post-change integrity validation.

Cách này tránh ghi event cho trạng thái product đang invalid.

## 10. Audit Rules

### 10.1 Deterministic rules

| Rule | Default severity |
|---|---|
| Duplicate requirement ID | critical |
| Invalid lifecycle transition | critical |
| Broken relationship endpoint | critical |
| Dependency cycle | critical |
| Feature references unknown requirement | critical |
| Ledger malformed or non-monotonic ID | critical |
| Approved `must` requirement has no feature coverage | high |
| Implemented requirement has no verification evidence | high |
| Verified feature has no ledger event | high |
| Ledger event references missing evidence | high |
| Approved `should` requirement has no coverage | medium |
| Feature task has no traceability and no `[INTERNAL]` marker | medium |
| Deprecated requirement still receives new implementation link | medium |
| Missing owner or source link | medium |

### 10.2 Semantic rules

Agent audit tìm candidate findings:

- hai feature refine cùng requirement theo nghĩa mâu thuẫn;
- thuật ngữ domain drift;
- acceptance behavior xung đột;
- feature impact chưa bao phủ shared entity hoặc interface;
- product requirement và constitution conflict;
- changelog summary không phản ánh feature delta.

Semantic findings phải chứa:

- evidence locations;
- reasoning ngắn;
- confidence;
- recommendation.

Finding confidence thấp không được tự động nâng thành critical nếu deterministic
rule không hỗ trợ.

## 11. Coverage Definition

Coverage MVP phải có công thức rõ:

```text
feature coverage =
  approved requirements có ít nhất một feature implements/refines
  / tổng approved requirements

verification coverage =
  implemented requirements có evidence passed
  / tổng implemented requirements
```

Coverage phải breakdown theo:

- priority;
- type;
- capability;
- status.

`impacts` không được tính là implementation coverage.

`refines` chỉ được tính coverage nếu requirement đó không yêu cầu implementation
trực tiếp hoặc có ít nhất một `implements` link. Policy này phải configurable;
mặc định `refines` một mình không đủ.

Denominator rỗng trả `ratio: null`, `covered: 0`, `total: 0`. JSON giữ count
dạng integer và ratio từ `0` đến `1`; chỉ presentation mới làm tròn phần trăm.

## 12. Implementation Work Breakdown

Danh sách task thực thi chi tiết, dependency và merge slices được quản lý tại
[mvp-tasks.md](./mvp-tasks.md).

### Phase 0 — Decisions and contracts

Deliverables:

- chốt schema v1;
- chốt requirement lifecycle;
- chốt ID strategy;
- chốt feature trace storage;
- chốt audit exit policy;
- tạo JSON schemas;
- ghi decision log.

Acceptance:

- Có fixtures valid/invalid cho mọi schema.
- Không còn unresolved decision chặn code.

### Phase 1 — Deterministic domain library

Implement:

- typed models;
- YAML/JSON loader;
- schema validation;
- ID allocator;
- lifecycle state machine;
- relationship graph;
- feature trace parser/writer;
- structured errors.

Tests:

- unit tests cho model và transition;
- graph cycle tests;
- duplicate/orphan tests;
- round-trip serialization;
- malformed input handling.

Acceptance:

- Library không phụ thuộc agent integration.
- Kết quả ổn định với cùng input.

### Phase 2 — Coverage and audit engine

Implement:

- scan `specs/*/feature-trace.json`;
- verification scanner;
- ledger scanner;
- coverage calculation;
- deterministic audit rules;
- Markdown/JSON report renderer;
- CI exit codes.

Tests:

- golden fixture product;
- exact coverage calculations;
- finding severity;
- report schema;
- no-write assertion cho audit.

### Phase 3 — Ledger and verification

Implement:

- verification evidence writer;
- evidence validation;
- atomic JSONL append;
- monotonic event ID;
- idempotency;
- correction events;
- human changelog renderer.

Tests:

- duplicate invocation;
- interrupted append;
- malformed trailing line;
- correction chain;
- evidence missing/failing;
- concurrent append behavior phù hợp platform support.

### Phase 4 — Extension package and commands

Implement extension manifest, config, templates và bảy commands.

Tests:

- extension package validation;
- install/uninstall;
- registration trên Markdown, TOML, YAML và skills integrations;
- script path rewriting;
- config preservation;
- command references đúng file.

### Phase 5 — Product SDD preset

Implement composed/overridden command templates.

Tests:

- resolution priority;
- install/remove restores previous commands;
- generated spec có Product Traceability;
- plan/tasks/analyze/implement đọc đúng bounded context;
- compatibility khi extension chưa cài phải báo lỗi actionable.

### Phase 6 — Workflow

Implement `product-feature-cycle`.

Tests:

- happy path;
- reject tại mỗi gate;
- resume;
- verification fail;
- audit fail;
- changelog không được append sớm;
- state persistence.

### Phase 7 — End-to-end fixtures and documentation

Tạo sample project có:

- 2 capabilities;
- 6 requirements;
- 2 features;
- một cross-feature conflict;
- verification evidence;
- ledger events.

E2E scenarios:

1. Khởi tạo product.
2. Thêm requirements.
3. Tạo feature có impact analysis.
4. Validate traceability.
5. Implement giả lập và verify.
6. Append ledger.
7. Audit pass.
8. Inject conflict và audit fail.

Documentation:

- quickstart;
- artifact reference;
- command reference;
- CI integration;
- migration/opt-out;
- authoring rules.

## 13. Suggested Test Matrix

| Area | Unit | Integration | E2E |
|---|---:|---:|---:|
| Schemas/models | Required | Required | Covered |
| Lifecycle | Required | Required | Covered |
| Graph | Required | Required | Covered |
| Coverage | Required | Required | Required |
| Ledger | Required | Required | Required |
| Commands | Limited | Required | Required |
| Preset | Limited | Required | Required |
| Workflow | Limited | Required | Required |
| Agent semantic audit | Fixture-based | Required | Smoke |

Agent semantic tests nên kiểm tra output contract và evidence references, không
khẳng định prose phải giống hệt.

## 14. CI Integration

Đề xuất command non-agent:

```bash
specify product validate --json
specify product audit --deterministic --json
```

Nếu extension system hiện chỉ đăng ký agent commands, MVP có thể dùng script
entrypoint:

```bash
python .specify/extensions/product-governance/scripts/product_governance/cli.py \
  audit --json
```

Tuy nhiên CLI-native subcommand là hướng tốt hơn nếu extension API cho phép.
Không nên buộc CI khởi chạy một coding agent để thực hiện deterministic audit.

CI minimum:

```text
validate schemas and graph
→ validate feature traceability
→ compute coverage
→ deterministic audit
→ fail on configured severity
```

## 15. Migration and Compatibility

### Existing projects

`product.init` không tự import feature cũ. Nó tạo report:

- feature directories chưa có trace;
- candidate requirement extraction;
- recommended migration order.

Backfill tự động nằm ngoài MVP; user có thể đăng ký requirements rồi link dần.

### Projects without extension

Core behavior không thay đổi.

### Extension disabled

- Không chạy product hooks.
- Artifact `.product/` được giữ nguyên.
- Core feature workflow tiếp tục hoạt động.

### Schema compatibility

Mọi artifact có `schema_version`.

MVP chỉ hỗ trợ `1.0`; version không hỗ trợ phải fail rõ ràng, không silent parse.

## 16. Security and Integrity

- Reject paths thoát project root.
- Không execute command được lấy từ requirement text.
- Atomic writes cho YAML/JSON mutation.
- Ledger append không dùng shell interpolation từ user input.
- Audit report escape content phù hợp Markdown/JSON.
- Không đưa secrets vào product artifacts.
- Local config chứa credential phải được gitignore.

## 17. Observability

Mỗi deterministic command hỗ trợ:

- human-readable stderr/stdout;
- `--json`;
- stable error code;
- operation ID;
- changed files list;
- no-op indication.

Ledger mutation phải log:

- event ID;
- idempotency key;
- ledger path;
- feature;
- requirement count.

## 18. MVP Acceptance Criteria

MVP hoàn thành khi:

- [ ] Extension cài và gỡ sạch trên các integration format được hỗ trợ.
- [ ] `.product/` được init mà không overwrite nội dung người dùng.
- [ ] Requirement registry và relationships được schema-validate.
- [ ] ID allocator không tạo duplicate và không tái sử dụng ID retired.
- [ ] Feature trace links được validate xuyên toàn bộ `specs/`.
- [ ] Coverage được tính đúng và có JSON output.
- [ ] Verification evidence bắt buộc trước changelog.
- [ ] Ledger append atomic và idempotent.
- [ ] Audit là read-only và phát hiện các fixture violations đã định nghĩa.
- [ ] Preset đưa product context vào core feature workflow.
- [ ] Workflow có đủ human gates và resume đúng.
- [ ] CI có thể chạy deterministic validation không cần agent.
- [ ] Quickstart và migration guide được viết.
- [ ] Post-MVP capability không vô tình xuất hiện trong public MVP contract.

## 19. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Markdown và sidecar drift | Atomic writer + validation digest |
| Agent tạo false-positive semantic findings | Confidence + evidence + không auto-mutate |
| Scope mở rộng thành ALM platform | Non-goals và separate backlog |
| Extension API không hỗ trợ CLI-native command | Script entrypoint trước, core RFC sau |
| Preset command drift với core upgrades | Compatibility tests và version constraints |
| Ledger conflict khi nhiều branch append | Idempotency; hậu MVP xem xét merge-aware ledger |
| Requirement status bị agent tự nâng | Mutation chỉ qua deterministic state machine |
| Audit chậm trên repo lớn | Index/cache hậu MVP; MVP bounded scan và metrics |

## 20. Delivery Milestones

Không gắn estimate theo ngày trước khi đo codebase và team capacity. Theo thứ tự:

1. **M0 — Contracts approved:** schema, lifecycle, IDs, exit policy.
2. **M1 — Deterministic core:** validate, graph, traceability.
3. **M2 — Coverage and audit:** reports và CI.
4. **M3 — Verification and ledger:** evidence, append-only history.
5. **M4 — Extension commands:** installable product-governance package.
6. **M5 — Preset and workflow:** integrated product feature cycle.
7. **M6 — E2E hardening:** fixtures, docs, compatibility matrix.

Mỗi milestone phải merge được độc lập và không yêu cầu capability milestone sau
để test phần đã hoàn thành.

## 21. Decision Log

| Date | Decision | Status |
|---|---|---|
| 2026-06-19 | MVP dùng extension + preset + workflow thay vì fork core | Approved |
| 2026-06-19 | Registry YAML là canonical; reports JSON là generated | Approved |
| 2026-06-19 | Ledger dùng append-only JSONL | Approved |
| 2026-06-19 | Audit read-only; remediation là command riêng | Approved |
| 2026-06-19 | Verification bắt buộc trước changelog event | Approved |
| 2026-06-19 | Release baseline không thuộc MVP | Approved |
| 2026-06-19 | Extension ID là `product-governance`; commands dùng `speckit.product-governance.*` | Approved |
| 2026-06-19 | JSON Schema Draft 2020-12 được validate bằng `jsonschema` | Approved |
| 2026-06-19 | ID dùng high-water mark theo capability và không có delete operation | Approved |
| 2026-06-19 | `feature-trace.json` là machine canonical, đồng bộ digest với `spec.md` | Approved |
| 2026-06-19 | `refines` một mình mặc định không tính coverage | Approved |
| 2026-06-19 | Audit block `critical`/`high`; exit codes là 0/1/2 | Approved |
| 2026-06-19 | Workflow dùng verify → gate → pre-audit → append → post-validate | Approved |
| 2026-06-19 | MVP dùng extension-local Python CLI, không thêm core subcommand | Approved |

Mọi thay đổi scope phải thêm một dòng vào bảng này và cập nhật đồng thời
Non-Goals, Acceptance Criteria và post-MVP backlog.

## 22. First Implementation Slice

Slice đầu tiên nên chỉ gồm:

1. JSON schemas cho requirements, relationships và feature trace.
2. Python loader/validator.
3. ID allocator.
4. Relationship graph validation.
5. CLI/script `validate --json`.
6. Fixtures và tests.

Không bắt đầu bằng agent prompts. Chỉ viết command agents sau khi data contracts
và deterministic API ổn định.
