# Product Governance MVP — Approved Decisions

**Status:** Approved  
**Approved:** 2026-06-19  
**Applies to:** [mvp-implementation-plan.md](./mvp-implementation-plan.md)

## D001 — Extension identity and command namespace

- Extension ID: `product-governance`.
- Public commands: `speckit.product-governance.init`,
  `speckit.product-governance.requirement`,
  `speckit.product-governance.impact`,
  `speckit.product-governance.validate`,
  `speckit.product-governance.verify`,
  `speckit.product-governance.changelog` và
  `speckit.product-governance.audit`.
- Python package name: `product_governance`.

Namespace này tuân thủ rule của extension API: segment namespace phải khớp
`extension.id`.

## D002 — Schema validation

MVP thêm dependency `jsonschema` và dùng JSON Schema Draft 2020-12 cho machine
artifacts. Unsupported `schema_version` phải fail rõ ràng trước domain
validation.

## D003 — Requirement lifecycle

Allowed transitions:

```text
proposed → reviewed
reviewed → proposed | approved
approved → implementing | deprecated
implementing → approved | implemented | deprecated
implemented → implementing | verified | deprecated
verified → deprecated
deprecated → retired
```

- Chỉ deterministic CLI được mutate status.
- `verified` yêu cầu evidence `passed` hợp lệ.
- `retired` là terminal.
- Agent chỉ được đề xuất transition.

## D004 — Requirement ID allocation

- Format: `PRD-<CAPABILITY>-<SEQUENCE>`.
- `<CAPABILITY>` là uppercase alphanumeric token.
- `<SEQUENCE>` zero-padded tối thiểu ba chữ số và tăng riêng theo capability.
- `requirements.yml` giữ high-water mark theo capability trong
  `id_sequences`; allocator không suy ra sequence chỉ từ requirement hiện còn.
- MVP không hỗ trợ delete requirement. Requirement không còn hiệu lực phải đi
  qua `deprecated → retired`.
- Manual edit làm ID thấp hơn high-water mark, duplicate ID hoặc sequence state
  không nhất quán phải làm validation fail; allocator không tái sử dụng ID.

## D005 — Feature trace storage

- `spec.md` chứa Product Traceability section có cấu trúc để human review.
- `feature-trace.json` là machine-readable canonical artifact cho tooling.
- Deterministic writer cập nhật hai artifact trong một operation và ghi digest
  của structured section vào sidecar.
- Validator báo drift khi parsed section, sidecar hoặc digest không khớp.
- Canonical array order là lexicographic theo requirement ID.

## D006 — Coverage policy

- `implements` được tính implementation coverage.
- `impacts` không được tính coverage.
- Mặc định `refines` một mình không được tính; policy có thể cấu hình.
- Feature coverage denominator là requirements có status `approved`.
- Verification coverage denominator là requirements có status `implemented`.
- Denominator rỗng trả `ratio: null`, `covered: 0`, `total: 0`.
- JSON giữ `covered`, `total` dạng integer và `ratio` dạng number từ `0` đến
  `1`; presentation mới làm tròn phần trăm.

## D007 — Verification, audit, and ledger order

Canonical order:

```text
verify → approval gate → pre-change audit → append ledger
       → post-change integrity validation
```

Nếu pre-change audit fail thì không append. Nếu post-change validation fail,
event đã append không bị xóa; report và remediation guidance phải được giữ.

## D008 — Exit codes and audit threshold

- `0`: operation hợp lệ/thành công.
- `1`: validation hoặc audit findings đạt blocking threshold.
- `2`: invalid invocation hoặc infrastructure failure.
- Audit threshold mặc định block `critical` và `high`.
- Threshold có thể cấu hình thành chỉ `critical`.
- Semantic audit dùng cùng output contract; low-confidence semantic finding
  không tự nâng thành `critical`.

## D009 — Ledger concurrency

- Validate toàn ledger trước append.
- Dùng exclusive file lock phù hợp platform và write-under-lock.
- Không lấy được lock trong timeout phải fail an toàn với exit `2`; không append
  không khóa.
- Append phải flush và `fsync` trước success.
- Full merge-aware, cross-branch reconciliation vẫn là post-MVP.

## D010 — Verification references

MVP hỗ trợ:

- `path`: local path, phải nằm trong project root và tồn tại khi verify;
- `url`: syntactically valid absolute HTTP(S) URL;
- `test`: non-empty test identifier;
- `commit`: non-empty commit reference.

Validator không thực hiện network request và không chứng minh semantic
completeness của URL, test ID hoặc commit.

## D011 — Deterministic CLI delivery

MVP dùng extension-local Python entrypoint:

```text
python .specify/extensions/product-governance/scripts/product_governance/cli.py
```

Không thêm core `specify product` subcommand trong MVP. Core chỉ thay đổi nếu
implementation chứng minh extension point hiện tại không đủ; thay đổi đó phải
là prerequisite PR riêng.

## Dependency consequence

Các quyết định domain D002–D006 đủ để bắt đầu schema và deterministic core.
D007–D010 chặn phần audit/verification/ledger tương ứng. D001 và D011 chỉ chặn
public extension command surface, preset và workflow; chúng không chặn domain
library.
