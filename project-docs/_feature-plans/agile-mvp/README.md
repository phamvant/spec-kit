# Agile MVP

Thư mục này lưu kế hoạch thiết kế lớp Agile cho Spec Kit.

## Tài liệu

- [MVP implementation plan](./mvp-implementation-plan.md): phạm vi, kiến trúc,
  work breakdown, kiểm thử và điều kiện hoàn thành MVP.
- [Approved decisions](./decisions.md): namespace, schema, lifecycle, IDs,
  coverage, evidence, ledger và CLI contracts đã chốt.
- [MVP task breakdown](./mvp-tasks.md): task IDs, dependencies, parallel work
  boundaries, merge slices và definition of done.
- [Post-MVP backlog](./post-mvp-backlog.md): các capability đã được xác định
  nhưng chủ động chưa đưa vào MVP.

## Mục tiêu

MVP bổ sung một lớp quản trị requirements toàn sản phẩm lên workflow theo
feature hiện tại của Spec Kit, gồm:

1. Registry requirements toàn sản phẩm với ID ổn định.
2. Traceability từ requirement toàn sản phẩm xuống feature.
3. Impact analysis trước khi tạo hoặc thay đổi feature.
4. Audit tổng thể bằng cả kiểm tra deterministic và phân tích semantic.
5. Change ledger append-only sau khi feature được xác minh.
6. CI-compatible validation và audit output.

## Nguyên tắc quản lý scope

`mvp-implementation-plan.md` là nguồn xác định phạm vi MVP. Capability chỉ có
trong `post-mvp-backlog.md` không được đưa vào MVP nếu chưa có quyết định thay
đổi scope được ghi lại trong phần Decision Log của kế hoạch.
