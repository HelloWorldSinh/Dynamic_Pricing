# Công cụ cào giá điện thoại CellphoneS

Phần triển khai này cung cấp công cụ bất đồng bộ để cào danh mục điện thoại
CellphoneS. Mỗi kết quả lưu nhãn tình trạng hàng trên trang, trạng thái đã
chuẩn hóa, thời điểm ghi nhận, URL sản phẩm và các cờ mô tả tình trạng máy.

Công cụ chưa tạo bảng cơ sở dữ liệu và không ghi đè lịch sử giá. Giao diện
`append-only sink` tùy chọn là điểm tích hợp với dịch vụ cào dữ liệu dùng chung
khi dịch vụ và schema được bổ sung.

## Cài đặt

Cần Python 3.11 trở lên. Cài các thư viện cần thiết và Chromium:

```powershell
python -m pip install -r backend/requirements.txt
python -m playwright install chromium
```

## Chạy cào dữ liệu có giới hạn

Chạy lệnh sau từ thư mục gốc của repository:

```powershell
python -m backend.app.scrapers.cellphones --max-load-more-clicks 2 --max-products 60
```

Mặc định, công cụ chờ ngẫu nhiên từ 2 đến 5 giây trước mỗi lần yêu cầu tải thêm
sản phẩm. Dùng `--price-region` để ghi nhận khu vực giá đã cấu hình. Sản phẩm
không có nhãn tình trạng hàng được giữ với trạng thái `unknown` và không được
dùng để so sánh tự động cho đến khi xác minh.

## Kiểm thử bộ phân tích

```powershell
python -m unittest discover -s backend/tests -v
```
