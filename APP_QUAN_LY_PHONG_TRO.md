# Đề xuất app quản lý phòng trọ

## 1) Mục tiêu
Xây dựng một app giúp chủ trọ quản lý:
- Phòng và tình trạng trống/đang thuê.
- Người thuê và hợp đồng.
- Điện, nước, dịch vụ theo tháng.
- Thu tiền, công nợ, lịch sử thanh toán.
- Thông báo đến người thuê.

## 2) Chức năng cốt lõi (MVP)

### 2.1 Quản lý phòng
- Tạo/sửa/xóa phòng.
- Gắn giá thuê, tiền cọc, diện tích, số người tối đa.
- Trạng thái: `available`, `occupied`, `maintenance`.

### 2.2 Quản lý người thuê & hợp đồng
- Hồ sơ người thuê: họ tên, CCCD, số điện thoại, ngày vào ở.
- Hợp đồng: ngày bắt đầu/kết thúc, tiền cọc, chu kỳ thu tiền.
- Lưu ảnh giấy tờ (tuỳ chọn giai đoạn 2).

### 2.3 Ghi chỉ số & tính tiền
- Nhập chỉ số điện nước hàng tháng.
- Cấu hình đơn giá điện/nước theo từng nhà trọ.
- Tự động tính tổng tiền: tiền phòng + điện + nước + dịch vụ.

### 2.4 Thu tiền & công nợ
- Tạo phiếu thu theo tháng.
- Trạng thái hóa đơn: `unpaid`, `partial`, `paid`, `overdue`.
- Theo dõi số còn nợ.

### 2.5 Báo cáo
- Doanh thu theo tháng/quý.
- Tỷ lệ lấp đầy phòng.
- Danh sách phòng nợ quá hạn.

## 3) Thiết kế dữ liệu gợi ý

### Bảng `rooms`
- `id` (PK)
- `code` (VD: P101)
- `price`
- `deposit_required`
- `status`
- `created_at`, `updated_at`

### Bảng `tenants`
- `id` (PK)
- `full_name`
- `phone`
- `id_number`
- `dob`
- `created_at`, `updated_at`

### Bảng `contracts`
- `id` (PK)
- `room_id` (FK -> rooms.id)
- `tenant_id` (FK -> tenants.id)
- `start_date`, `end_date`
- `rent_price`
- `deposit_amount`
- `status`

### Bảng `meter_readings`
- `id` (PK)
- `room_id` (FK)
- `month` (YYYY-MM)
- `electric_old`, `electric_new`
- `water_old`, `water_new`

### Bảng `invoices`
- `id` (PK)
- `room_id` (FK)
- `contract_id` (FK)
- `billing_month`
- `room_fee`, `electric_fee`, `water_fee`, `service_fee`
- `total_amount`, `paid_amount`, `status`

## 4) API mẫu (REST)
- `GET /rooms`, `POST /rooms`, `PATCH /rooms/:id`
- `GET /tenants`, `POST /tenants`
- `POST /contracts`
- `POST /meter-readings`
- `POST /invoices/generate?month=YYYY-MM`
- `POST /payments`

## 5) Công nghệ đề xuất
- **Frontend**: React + Next.js + Tailwind.
- **Backend**: Node.js (NestJS/Express) hoặc Laravel.
- **Database**: PostgreSQL.
- **Auth**: JWT + refresh token.
- **Deploy**: Docker + VPS (hoặc Railway/Render).

## 6) Lộ trình phát triển nhanh (4 tuần)
- **Tuần 1**: Thiết kế DB + auth + CRUD phòng/người thuê.
- **Tuần 2**: Hợp đồng + ghi chỉ số điện nước.
- **Tuần 3**: Tạo hóa đơn + thu tiền + công nợ.
- **Tuần 4**: Báo cáo + tinh chỉnh UI + phân quyền.

## 7) Mở rộng sau MVP
- Tích hợp Zalo/SMS nhắc đóng tiền.
- Thanh toán online (Momo, VNPay).
- App mobile cho người thuê tự xem hóa đơn.

## 8) Demo giao diện chạy được trên máy
- File demo: `demo/quan-ly-phong-tro-ui.html`
- Script chạy nhanh local: `scripts/run_quan_ly_phong_tro_demo.sh`
- Demo có thể dùng thử ngay:
  - Thêm phòng.
  - Tạo hóa đơn theo tháng với điện/nước/dịch vụ.
  - Tự động tính tổng tiền + trạng thái thanh toán.
  - Dashboard KPI cập nhật theo dữ liệu.
  - Dữ liệu lưu bằng `localStorage` trên trình duyệt.

### Cách chạy local
1. Mở terminal tại thư mục repo.
2. Chạy lệnh:
   ```bash
   ./scripts/run_quan_ly_phong_tro_demo.sh
   ```
3. Mở trình duyệt vào:
   ```
   http://127.0.0.1:4173/demo/quan-ly-phong-tro-ui.html
   ```

> Có thể đổi port, ví dụ:
```bash
./scripts/run_quan_ly_phong_tro_demo.sh 8080
```
