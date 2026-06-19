# Agile MVP — Task Breakdown

**Status:** Ready for execution
**Created:** 2026-06-19  
**Source plan:** [mvp-implementation-plan.md](./mvp-implementation-plan.md)  
**Scope boundary:** [post-mvp-backlog.md](./post-mvp-backlog.md)

## 1. Task Format

```text
- [ ] PG### [P?] [Milestone] Action with exact output path
```

- `[P]`: có thể thực hiện song song sau khi dependency của phase đã hoàn thành.
- Mỗi task phải tạo ra code, test, fixture, documentation hoặc decision record có
  thể review độc lập.
- Test task phải được viết trước hoặc cùng PR với implementation tương ứng.
- Không task nào được đưa capability chỉ có trong post-MVP backlog vào public
  contract.

## 2. Approved Decisions

Các decision được chốt trong [decisions.md](./decisions.md). Chúng không tạo
một global blocker: task chỉ bị chặn bởi decision của domain mà task sử dụng.

- [x] PG001 [M0] Chốt extension identity `agile` và public command
  namespace `speckit.agile.*`.
- [x] PG002 [P] [M0] Chốt schema validation strategy: thêm dependency
  `jsonschema`, dùng JSON Schema Draft 2020-12 và giữ compatibility Python 3.11+.
- [x] PG003 [P] [M0] Chốt lifecycle transition table đầy đủ, gồm actor/action nào
  được phép chuyển sang `deprecated` và `retired`, và quy tắc evidence cho
  `implemented`/`verified`.
- [x] PG004 [P] [M0] Chốt ID allocation contract: capability token, zero-padding,
  source of truth cho sequence, behavior khi ID bị xóa thủ công, và cách bảo đảm
  ID retired không được tái sử dụng.
- [x] PG005 [P] [M0] Chốt structured Product Traceability section trong `spec.md`,
  canonical ordering, sidecar synchronization, digest/drift rule và atomic
  update behavior.
- [x] PG006 [P] [M0] Chốt coverage policy cho `refines`, denominator rỗng, status
  được tính, và rounding/JSON numeric representation.
- [x] PG007 [P] [M0] Chốt ordering thành
  `verify → approval gate → pre-change audit → ledger append → post-change
  validation`.
- [x] PG008 [P] [M0] Chốt audit severity threshold config và exit-code contract
  cho `validate`, deterministic `audit`, semantic `audit`, invocation error và
  infrastructure error.
- [x] PG009 [P] [M0] Chốt ledger locking/atomic append strategy trên Linux,
  macOS và Windows; xác định behavior được hỗ trợ khi concurrent writers không
  có portable lock.
- [x] PG010 [P] [M0] Chốt verification reference types và validation rules:
  local path, URL, commit, test identifier; path nào bắt buộc tồn tại và thời
  điểm kiểm tra.
- [x] PG011 [P] [M0] Chốt deterministic CLI delivery: extension-local Python
  entrypoint là MVP contract; chỉ mở core CLI task nếu extension API không thể
  đáp ứng command invocation hoặc CI use case.
- [x] PG012 [M0] Cập nhật Decision Log trong
  `mvp-implementation-plan.md`, loại bỏ mọi `Proposed` decision chặn code và ghi
  rõ deferred decisions.

**Checkpoint M0:** Hoàn thành. Schema, deterministic core, audit,
verification/ledger và extension surface có thể triển khai theo dependency riêng.

## 3. Schema, Fixtures, and Package Skeleton

- [x] PG013 [M0] Tạo `decisions.md` với template gồm context, options, decision,
  consequences và date; ghi kết quả PG001–PG011.
- [ ] PG014 [P] [M0] Tạo extension package skeleton tại path đã chốt, gồm
  `extension.yml`, `README.md`, config, `commands/`, `scripts/`, `schemas/` và
  `templates/`, chưa đăng ký vào bundled assets.
- [ ] PG015 [P] [M0] Tạo Python package skeleton
  `scripts/agile/` với `__init__.py`, `cli.py`, `models.py`,
  `io.py`, `registry.py`, `graph.py`, `trace.py`, `coverage.py`, `verification.py`,
  `ledger.py`, `audit.py`, `reporting.py` và `errors.py`.
- [ ] PG016 [P] [M0] Tạo schema `requirements.schema.json` cho registry, field
  enums, ID pattern, lifecycle status và verification method.
- [ ] PG017 [P] [M0] Tạo schema `relationships.schema.json` cho edge types và
  endpoint shape.
- [ ] PG018 [P] [M0] Tạo schema `feature-trace.schema.json` cho implements,
  refines, impacts và unaffected.
- [ ] PG019 [P] [M0] Tạo schema `verification.schema.json` cho per-requirement
  pass/fail/not-run evidence.
- [ ] PG020 [P] [M0] Tạo schema `ledger-event.schema.json`, gồm idempotency key
  và optional correction reference theo decision.
- [ ] PG021 [P] [M0] Tạo schema `audit-report.schema.json` cho findings, evidence,
  severity, confidence, operation metadata và coverage summary.
- [ ] PG022 [P] [M0] Tạo valid/invalid fixtures cho từng schema dưới
  `tests/extensions/agile/fixtures/schemas/`.
- [ ] PG023 [M0] Viết schema contract tests trong
  `tests/extensions/agile/test_schemas.py`, bao phủ unsupported
  `schema_version`, missing fields, invalid enum, duplicate-like fixture input
  và malformed JSON/YAML.

## 4. Deterministic Domain Core

- [ ] PG024 [P] [M1] Viết failing tests cho typed model construction,
  normalization và serialization trong `test_models.py`.
- [ ] PG025 [P] [M1] Viết failing lifecycle table tests cho mọi allowed/forbidden
  transition trong `test_lifecycle.py`.
- [ ] PG026 [P] [M1] Viết failing path-safety và atomic-write tests trong
  `test_io.py`, gồm traversal ra ngoài project root và interrupted replacement.
- [ ] PG027 [M1] Implement structured domain errors và stable error codes trong
  `errors.py`; map schema, domain, invocation và infrastructure failures.
- [ ] PG028 [M1] Implement typed models và enum parsing trong `models.py`, không
  phụ thuộc agent integration hoặc CLI presentation.
- [ ] PG029 [M1] Implement project-root discovery, YAML/JSON load, schema-version
  guard, safe-path resolution và atomic YAML/JSON write trong `io.py`.
- [ ] PG030 [M1] Implement lifecycle state machine trong `registry.py` theo
  transition table PG003.
- [ ] PG031 [M1] Implement requirement ID allocator trong `registry.py`; scan
  toàn registry, không reuse ID retired và fail trên inconsistent manual state.
- [ ] PG032 [M1] Implement registry operations add, mutable update, transition,
  deprecate, list và show; cấm thay đổi ID qua update.
- [ ] PG033 [P] [M1] Viết failing graph tests trong `test_graph.py`: unknown
  endpoint, self-edge, duplicate, `parent_of` cycle, `depends_on` cycle,
  conflict normalization và supersedes validation.
- [ ] PG034 [M1] Implement relationship graph builder và deterministic traversal
  trong `graph.py`; output ordering phải stable.
- [ ] PG035 [P] [M1] Viết failing trace round-trip/drift tests trong
  `test_trace.py`, gồm malformed Markdown section và sidecar mismatch.
- [ ] PG036 [M1] Implement structured `spec.md` trace parser/writer và atomic
  `feature-trace.json` synchronization trong `trace.py`.
- [ ] PG037 [M1] Implement aggregate validator trong `cli.py`/domain service cho
  registry, relationships, trace links, verification links và ledger integrity.
- [ ] PG038 [M1] Add deterministic `--json`, operation ID, changed-files, no-op
  và exit-code output contract cho domain CLI.
- [ ] PG039 [M1] Run focused M1 tests and record exact command/results in the
  implementation PR.

**Checkpoint M1:** Một temporary project có thể init artifacts thủ công, thêm
requirements, build graph, tạo trace sidecar và validate hoàn toàn không cần
agent.

## 5. Coverage and Deterministic Audit

- [ ] PG040 [P] [M2] Tạo golden product fixture dưới
  `tests/extensions/agile/fixtures/golden_product/` với 2
  capabilities, 6 requirements và 2 traced features.
- [ ] PG041 [P] [M2] Viết failing scanner tests cho missing/malformed trace,
  verification và ledger artifacts trong `test_scanners.py`.
- [ ] PG042 [P] [M2] Viết exact coverage tests trong `test_coverage.py`, gồm
  breakdown theo priority, type, capability, status, empty denominator và
  configurable `refines`.
- [ ] PG043 [M2] Implement bounded scanners cho `.product/` và
  `specs/*/feature-trace.json`; reject symlink/path escape theo contract.
- [ ] PG044 [M2] Implement feature và verification coverage calculator trong
  `coverage.py`; persist generated `.product/coverage.json` atomically.
- [ ] PG045 [P] [M2] Viết one-fixture-per-rule tests cho toàn bộ deterministic
  audit table trong `test_audit_rules.py`.
- [ ] PG046 [M2] Implement deterministic findings trong `audit.py`, stable rule
  IDs, evidence paths, severity và remediation hint.
- [ ] PG047 [P] [M2] Viết JSON schema/golden Markdown rendering tests trong
  `test_reporting.py`.
- [ ] PG048 [M2] Implement JSON và Markdown audit renderers trong `reporting.py`,
  gồm escaping content và deterministic ordering.
- [ ] PG049 [M2] Implement read-only assertion harness: snapshot/hash project
  artifacts trước/sau audit và fail test nếu audit mutation ngoài report output.
- [ ] PG050 [M2] Implement audit threshold configuration và CI exit behavior
  theo PG008.
- [ ] PG051 [M2] Add performance smoke fixture/metric cho bounded repository
  scan; chỉ ghi baseline, không thêm cache/index hậu MVP.

**Checkpoint M2:** CI có thể tính coverage và chạy deterministic audit, tạo
JSON/Markdown report với stable exit code.

## 6. Verification and Ledger

- [ ] PG052 [P] [M3] Viết failing evidence writer/validator tests trong
  `test_verification.py`, gồm missing implements evidence, fail, not-run,
  unknown requirement, invalid commit và missing local reference.
- [ ] PG053 [M3] Implement verification evidence creation/update trong
  `verification.py`; preserve valid user data và atomic write.
- [ ] PG054 [M3] Implement verification gate service yêu cầu `passed` evidence
  cho mọi required `implements` link trước khi cho phép changelog.
- [ ] PG055 [P] [M3] Viết failing ledger tests trong `test_ledger.py`: first
  event, monotonic ID, duplicate idempotency key, semantic duplicate, malformed
  trailing line, correction chain và unknown corrected event.
- [ ] PG056 [P] [M3] Viết platform-appropriate concurrent append tests; skip có
  lý do rõ ràng nếu platform không hỗ trợ locking strategy đã chốt.
- [ ] PG057 [M3] Implement ledger full-file integrity scan trước mutation trong
  `ledger.py`; không append nếu ledger hiện tại malformed.
- [ ] PG058 [M3] Implement locked/atomic JSONL append, monotonic event ID và
  deterministic idempotency key trong `ledger.py`.
- [ ] PG059 [M3] Implement correction event validation; không sửa/xóa event cũ.
- [ ] PG060 [M3] Implement human-readable changelog summary renderer; ledger
  JSONL vẫn là canonical.
- [ ] PG061 [M3] Implement post-append integrity validation và operation logging
  gồm event ID, idempotency key, path, feature và requirement count.
- [ ] PG062 [M3] Add crash/interruption test proving partial append không được
  coi là valid success và có actionable recovery error.

**Checkpoint M3:** Verified evidence là prerequisite bắt buộc; append lặp lại
không tạo duplicate; ledger history không bị rewrite.

## 7. Extension Package and Commands

- [ ] PG063 [P] [M4] Viết extension manifest validation test và command inventory
  test trong `test_extension_package.py`.
- [ ] PG064 [M4] Hoàn thiện `extension.yml` với namespace đã chốt, seven commands,
  config template, compatibility version và tags.
- [ ] PG065 [P] [M4] Implement `.product/` templates: `product.md`,
  `glossary.md`, empty valid registries, ledger placeholder policy,
  reports `.gitkeep` và schema-version marker.
- [ ] PG066 [P] [M4] Implement feature templates: `proposal-template.md`,
  `impact-template.md` và `verification-template.json`.
- [ ] PG067 [M4] Implement extension config với coverage policy, audit threshold,
  paths và supported schema version; preserve user edits on upgrade/install.
- [ ] PG068 [M4] Implement product init command template; call deterministic
  script, refuse overwrite without `--force`, validate after creation.
- [ ] PG069 [M4] Implement requirement command template cho add/update/transition/
  deprecate/list/show; all mutations phải gọi deterministic CLI.
- [ ] PG070 [M4] Implement impact command template tạo proposal, impact,
  candidate trace và machine summary nhưng không auto-approve.
- [ ] PG071 [M4] Implement validate command template chỉ dispatch deterministic
  validation và faithfully return findings/exit status.
- [ ] PG072 [M4] Implement verify command template thu thập evidence và gọi
  deterministic writer/gate.
- [ ] PG073 [M4] Implement changelog command template thực hiện preconditions,
  pre-change audit, append và post-change validation.
- [ ] PG074 [M4] Implement audit command template: deterministic layer trước,
  bounded semantic layer sau, merge findings mà không mutate source artifacts.
- [ ] PG075 [P] [M4] Add Bash launcher under `scripts/bash/` và PowerShell launcher
  under `scripts/powershell/`; tránh shell interpolation của user content.
- [ ] PG076 [P] [M4] Add command-content tests kiểm tra script paths, placeholders,
  forbidden direct registry/ledger edits và required output artifacts.
- [ ] PG077 [M4] Add install/uninstall/config-preservation integration tests cho
  Markdown, TOML, YAML và skills integrations.
- [ ] PG078 [M4] Manually install extension into temporary projects for at least
  one markdown integration and one skills integration; record command files and
  uninstall result.

**Checkpoint M4:** Extension cài/gỡ sạch và cung cấp đủ command surface; mọi
machine mutation đi qua deterministic package.

## 8. Product SDD Preset

- [ ] PG079 [P] [M5] Tạo `presets/product-sdd/preset.yml` và README với explicit
  dependency/compatibility on product extension.
- [ ] PG080 [P] [M5] Viết preset resolution/install/remove tests trong
  `tests/presets/test_product_sdd_preset.py`.
- [ ] PG081 [M5] Override/compose `speckit.specify` để require product registry,
  run impact first, inject Product Traceability và generate sidecar.
- [ ] PG082 [M5] Override/compose `speckit.plan` để load bounded linked
  requirements, capability impact, constitution, interfaces và migration risk.
- [ ] PG083 [M5] Override/compose `speckit.tasks` để enforce requirement/story
  reference hoặc `[INTERNAL]` trên mọi implementation task.
- [ ] PG084 [M5] Override/compose `speckit.analyze` để report global linkage,
  cross-feature conflict candidates, requirement-to-task coverage và stale
  impact.
- [ ] PG085 [M5] Override/compose `speckit.implement` để load bounded context,
  preserve task progress, emit implementation summary và cấm status
  verification mutation.
- [ ] PG086 [M5] Add actionable failure tests khi preset active nhưng extension
  missing/disabled hoặc registry invalid.
- [ ] PG087 [M5] Add restoration test proving preset removal restores prior
  command resolution without deleting product artifacts.

## 9. Product Feature Workflow

- [ ] PG088 [P] [M5] Tạo
  `workflows/product-feature-cycle/workflow.yml` với required inputs,
  compatibility metadata và sequence theo PG007.
- [ ] PG089 [P] [M5] Tạo workflow validation tests cho command references,
  extension/preset prerequisites và gate placement.
- [ ] PG090 [M5] Add happy-path workflow test qua impact, three approval gates,
  specify/plan/tasks/analyze/implement, verification gate, pre-audit, append và
  post-validation.
- [ ] PG091 [P] [M5] Add parameterized rejection tests cho từng human gate; assert
  downstream steps không chạy.
- [ ] PG092 [P] [M5] Add resume tests từ từng paused gate và assert completed
  steps không tạo duplicate mutation.
- [ ] PG093 [P] [M5] Add verification-fail và pre-audit-fail tests; assert ledger
  không append.
- [ ] PG094 [P] [M5] Add post-append validation-fail test; preserve ledger event,
  preserve report và return failed run với remediation guidance.

**Checkpoint M5:** Product workflow resumable, human-gated và không thể append
changelog trước verification + pre-change audit.

## 10. Packaging, E2E, and Documentation

- [ ] PG095 [P] [M6] Add product extension, preset và workflow vào wheel bundled
  assets trong `pyproject.toml` only after package tests pass.
- [ ] PG096 [P] [M6] Add/update built-in catalog entries only if the approved
  distribution decision requires catalog discovery; validate catalog schema.
- [ ] PG097 [M6] Build wheel/sdist and assert all extension schemas, scripts,
  templates, preset files and workflow files are present.
- [ ] PG098 [M6] Expand golden fixture into full E2E sample with 2 capabilities,
  6 requirements, 2 features, verification evidence, ledger event và one
  injectable semantic conflict.
- [ ] PG099 [M6] Add E2E scenario: init → add requirements → impact → trace
  validation → simulated implementation → verify → append → passing audit.
- [ ] PG100 [M6] Add E2E negative scenario: inject conflict/broken trace and
  assert audit report, severity, exit code and no unintended mutation.
- [ ] PG101 [P] [M6] Write extension quickstart and artifact reference in the
  extension README.
- [ ] PG102 [P] [M6] Write command reference with human/JSON output and exit
  codes.
- [ ] PG103 [P] [M6] Write CI integration guide using deterministic entrypoint;
  agent runtime must not be required.
- [ ] PG104 [P] [M6] Write existing-project migration guide, unsupported
  automatic backfill behavior and recommended manual ordering.
- [ ] PG105 [P] [M6] Write disable/uninstall/opt-out behavior; confirm
  `.product/` artifacts are preserved.
- [ ] PG106 [P] [M6] Write authoring rules for requirement statements, owners,
  source links, trace relations and evidence references.
- [ ] PG107 [M6] Run focused extension/preset/workflow suites, then full
  `uv run pytest`; classify failures as regression, flaky or unrelated before
  merge.
- [ ] PG108 [M6] Run manual command tests required by `CONTRIBUTING.md` and
  capture agent, OS/shell, commands and produced artifacts.
- [ ] PG109 [M6] Audit public docs, examples, schemas and CLI help against
  post-MVP backlog; remove accidental release baseline, field history,
  multi-repo, dashboard, telemetry or semantic source verification promises.
- [ ] PG110 [M6] Update MVP acceptance checklist in
  `mvp-implementation-plan.md` with evidence links to tests, fixtures and docs.

## 11. Dependency and Delivery Slices

```text
D002–D005 → schemas + M1 deterministic core
M1 + D006 + D008 → M2 coverage + audit
M1 + D007–D010 → M3 verification + ledger
M1–M3 + D001 + D011 → M4 extension commands
M4 → M5 preset + workflow
M4 + M5 → M6 packaging + E2E + docs
```

Recommended independently mergeable slices:

1. **PR 1 — Contracts and schemas:** PG001–PG023.
2. **PR 2 — Registry, lifecycle, graph and trace:** PG024–PG039.
3. **PR 3 — Coverage and deterministic audit:** PG040–PG051.
4. **PR 4 — Verification and ledger:** PG052–PG062.
5. **PR 5 — Extension package and commands:** PG063–PG078.
6. **PR 6 — Product preset:** PG079–PG087.
7. **PR 7 — Product workflow:** PG088–PG094.
8. **PR 8 — Bundling, E2E and documentation:** PG095–PG110.

Do not bundle core CLI changes into these slices unless PG011 demonstrates a
missing extension point. If a core change is required, isolate it in a separate
prerequisite PR with regression tests.

## 12. Parallel Work Boundaries

Sau khi các decision liên quan đã được chốt:

- Schema files PG016–PG021 có thể làm song song, nhưng PG023 là integration gate.
- Model/lifecycle/I/O tests PG024–PG026 có thể làm song song.
- Graph PG033–PG034 và trace PG035–PG036 có thể làm song song sau models/I/O.
- Coverage fixtures/tests PG040–PG042 có thể làm song song.
- Verification PG052–PG054 và ledger PG055–PG062 có thể làm song song sau M1,
  nhưng changelog integration cần cả hai.
- Command content PG068–PG074 nên chia theo file; manifest PG064 và shared config
  PG067 phải ổn định trước install tests.
- Preset command overrides PG081–PG085 có thể author song song sau preset
  contract PG079–PG080.
- Workflow negative/resume tests PG091–PG094 có thể làm song song sau workflow
  skeleton PG088–PG090.

Không chạy song song các task cùng mutate:

- `extension.yml`;
- `preset.yml`;
- `workflow.yml`;
- `pyproject.toml`;
- shared fixture registry/ledger.

## 13. Definition of Done per Task

Một task chỉ được đánh dấu hoàn thành khi:

1. Output path tồn tại và được review.
2. Test liên quan pass trên Python 3.11+.
3. Error behavior có assertion, không chỉ happy path.
4. User-controlled paths/content không được execute hoặc thoát project root.
5. JSON/YAML output deterministic với cùng input.
6. Không thêm implicit agent mutation vào registry, lifecycle hoặc ledger.
7. Public behavior được cập nhật trong docs nếu task thay đổi contract.
