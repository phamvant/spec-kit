# Product Governance — Post-MVP Backlog

**Status:** Captured, not committed  
**Created:** 2026-06-19  
**MVP boundary:** [mvp-implementation-plan.md](./mvp-implementation-plan.md)

Tài liệu này lưu các capability có giá trị nhưng không thuộc MVP. Thứ tự dưới
đây là dependency-oriented, không phải cam kết lịch phát hành.

## Prioritization Fields

Mỗi backlog item có:

- **Value:** tác động tới product governance.
- **Dependency:** capability cần có trước.
- **Exit signal:** điều kiện đủ để cân nhắc đưa vào planning.

## Horizon 1 — Hardening after MVP

### PG-101 — Release baselines

Freeze requirement versions, constitution version, feature set, commit và
evidence thành một product baseline có digest.

Value: trả lời chính xác release implement phiên bản product contract nào.

Dependency: registry, ledger và audit MVP ổn định.

Exit signal: ít nhất hai feature đã đi qua full MVP workflow.

### PG-102 — Requirement revision history

Lưu revision bất biến cho từng requirement thay vì chỉ trạng thái mới nhất.

Bao gồm:

- field-level diff;
- effective date;
- author/approver;
- supersession chain;
- reason for change.

Dependency: baseline model.

### PG-103 — Merge-aware ledger

Xử lý nhiều branch cùng append ledger:

- branch-local event IDs hoặc UUID;
- deterministic merge;
- duplicate reconciliation;
- tamper-evident hash chain tùy chọn.

Dependency: dữ liệu thực tế từ ledger MVP.

### PG-104 — Incremental index and audit cache

Chỉ scan artifact thay đổi thay vì toàn bộ repo.

Dependency: audit metrics chứng minh full scan là bottleneck.

### PG-105 — Automated legacy backfill

Phân tích `specs/*` cũ, đề xuất global requirements và trace links để human
approve.

Dependency: semantic audit đạt độ ổn định chấp nhận được.

## Horizon 2 — Product team expansion

### PG-201 — Formal Product Manager agent

Quản lý goals, personas, journeys, capability map và prioritization.

Agent chỉ đề xuất mutation; deterministic registry vẫn là writer.

### PG-202 — Requirements Architect agent

Chuyên decomposition, deduplication, dependency và cross-feature traceability.

### PG-203 — Solution Architect agent

Phân tích shared interfaces, domain invariants, architecture constraints và
cross-feature migration.

### PG-204 — Verification agent

Sinh verification plan từ requirement methods, thu thập evidence và đánh giá
coverage.

### PG-205 — Independent Product Auditor agent

Chạy read-only, không dùng cùng prompt/context với implementation agent, tạo
semantic findings có confidence và evidence.

### PG-206 — Release Manager agent

Chuẩn bị baseline, release notes, known gaps và go/no-go recommendation.

Dependency chung: role permissions và artifact ownership model.

## Horizon 3 — Rich requirement model

### PG-301 — Product goal and KPI hierarchy

Trace:

```text
goal → outcome/KPI → capability → requirement → feature → evidence
```

MVP không tính business KPI là implementation coverage.

### PG-302 — Personas and journey model

First-class personas, journeys, touchpoints và mapping tới requirements.

### PG-303 — Quality attribute scenarios

Mô hình stimulus, environment, response và measure cho performance,
availability, security và operability.

### PG-304 — Compliance control mapping

Map requirement/evidence tới control frameworks như SOC 2, ISO 27001 hoặc
organization-specific policies.

### PG-305 — Risk register

Trace risk → mitigation requirement → feature → evidence → residual risk.

### PG-306 — Assumption and hypothesis lifecycle

Quản lý product assumptions, validation experiments và decisions khi giả định
được xác nhận hoặc bác bỏ.

## Horizon 4 — Deeper code and test traceability

### PG-401 — Test manifest integration

Test metadata tham chiếu requirement IDs trực tiếp thay vì chỉ file paths.

### PG-402 — Source annotation support

Optional source-level annotations cho requirement IDs, có lint rule chống
stale references.

### PG-403 — Runtime evidence ingestion

Nhập metrics, traces, synthetic tests hoặc production checks làm evidence cho
quality requirements.

### PG-404 — Change impact from code diff

Phân tích git diff để đề xuất affected requirements/features trước review.

### PG-405 — Bidirectional drift detection

Phát hiện:

- spec có nhưng code thiếu;
- code có behavior không được spec yêu cầu;
- test expectation mâu thuẫn requirement;
- changelog khác implementation delta.

## Horizon 5 — Multi-project and integrations

### PG-501 — Multi-repository product graph

Global product registry liên kết nhiều repo/service.

### PG-502 — Jira/Linear/GitHub Projects sync

Đồng bộ hierarchy và status nhưng không biến external tracker thành nguồn duy
nhất nếu chưa có reconciliation policy.

### PG-503 — API/schema registry integration

Phát hiện cross-feature và cross-service contract compatibility.

### PG-504 — Organization-level policy packs

Reusable presets cho security, compliance, architecture và domain standards.

### PG-505 — Federated product catalogs

Nhiều product registry với dependency và ownership boundaries.

## Horizon 6 — User experience

### PG-601 — Product governance dashboard

Hiển thị:

- requirement hierarchy;
- coverage;
- open findings;
- feature impact graph;
- release readiness.

### PG-602 — Interactive graph editor

Human review và chỉnh relationship graph với schema validation.

### PG-603 — Audit trend reports

Theo dõi coverage, drift và finding aging qua thời gian.

### PG-604 — IDE integrations

Hiển thị requirement context và traceability ngay tại code/spec.

## Deferred Architecture Questions

Các câu hỏi sau không được quyết định vội trong MVP:

1. Requirement revision dùng event sourcing hoàn toàn hay snapshot + history?
2. Ledger dùng monotonic integer, UUIDv7 hay content hash khi hỗ trợ multi-branch?
3. Product registry nằm trong từng repo hay một governance repo riêng?
4. Semantic audit có cần model/provider policy riêng?
5. Evidence production có expiry hoặc freshness window không?
6. Baseline ký bằng digest thông thường hay cryptographic signature?
7. External tracker là mirror hay được phép trở thành co-authoritative source?
8. Coverage có weighting theo priority/risk hay chỉ raw percentage?

## Promotion Rule

Một backlog item chỉ được chuyển vào implementation plan khi:

1. Có problem statement và evidence về nhu cầu.
2. Dependency đã hoàn thành.
3. Có owner.
4. Có acceptance criteria.
5. Có migration và compatibility impact.
6. Được thêm vào Decision Log của implementation plan tương ứng.
