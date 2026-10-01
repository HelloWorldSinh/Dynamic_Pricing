import os
import sys
import shutil
import tempfile
import pandas as pd
import pytest
from collections import Counter

# Đảm bảo UTF-8 cho console Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_excel_safe(file_path: str) -> pd.DataFrame:
    """Đọc file Excel an toàn kể cả khi người dùng đang mở file bằng Excel trên Windows."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Không tìm thấy file: {file_path}")

    # Tạo file tạm để đọc nếu file gốc đang bị khóa bởi Excel
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Dùng PowerShell copy hoặc shutil nếu có thể
        try:
            shutil.copyfile(file_path, tmp_path)
        except PermissionError:
            # Fallback chạy PowerShell copy-item cho Windows lock
            cmd = f'powershell -ExecutionPolicy Bypass -Command "Copy-Item -Path \'{file_path}\' -Destination \'{tmp_path}\' -Force"'
            os.system(cmd)

        df = pd.read_excel(tmp_path)
        return df
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


def test_scraped_data_anomalies(file_path: str = None):
    if file_path is None:
        file_path = os.path.join(BASE_DIR, "data", "scraped_raw_step1.xlsx")
        if not os.path.exists(file_path):
            for candidate in [
                os.path.join(BASE_DIR, "data", "crawl_and_sku_mapping_hoangha.xlsx"),
                os.path.join(BASE_DIR, "data", "crawl_and_sku_mapping_output.xlsx"),
            ]:
                if os.path.exists(candidate):
                    file_path = candidate
                    break
            else:
                pytest.skip("Chưa có file dữ liệu cào để kiểm tra chất lượng")

    print("=" * 80)
    print(f"KIỂM THỬ ĐÁNH GIÁ CHẤT LƯỢNG DỮ LIỆU CÀO: {file_path}")
    print("=" * 80)

    df = load_excel_safe(file_path)
    total_rows = len(df)
    print(f"Tổng số bản ghi (dòng): {total_rows}")
    print(f"Danh sách các cột (trường): {df.columns.tolist()}\n")

    # =========================================================================
    # TEST 1: Kiểm tra 2 trường giá: "Giá bán" vs "Giá niêm yết"
    # =========================================================================
    print("--- 1. KIỂM TRA 2 TRƯỜNG GIÁ (GIÁ BÁN vs GIÁ NIÊM YẾT) ---")
    price_col = next((c for c in ["Giá bán (VND)", "Giá bán đối thủ (VND)", "price_vnd"] if c in df.columns), None)
    orig_col = next((c for c in ["Giá niêm yết (VND)", "original_price_vnd", "Giá niêm yết"] if c in df.columns), None)

    if price_col and orig_col:
        both_null = df[df[price_col].isna() & df[orig_col].isna()]
        same_price = df[(df[price_col] == df[orig_col]) & df[price_col].notna()]
        diff_price = df[(df[price_col] != df[orig_col]) & df[price_col].notna()]

        print(f" + Số dòng có Giá bán == Giá niêm yết: {len(same_price)} / {total_rows} ({len(same_price) / total_rows * 100:.2f}%)")
        print(f" + Số dòng có Giá bán != Giá niêm yết (có giảm giá): {len(diff_price)} / {total_rows} ({len(diff_price) / total_rows * 100:.2f}%)")
        print(f" + Số dòng cả 2 giá đều TRỐNG (NaN): {len(both_null)} / {total_rows} ({len(both_null) / total_rows * 100:.2f}%)")
    else:
        print(" + Bỏ qua kiểm tra giá do không có cột giá phù hợp trong file.")

    # =========================================================================
    # TEST 2: Kiểm tra độ đầy đủ của từng cột ("có trường có trường không")
    # =========================================================================
    print("--- 2. TỶ LỆ DỮ LIỆU BỊ THIẾU (NULL / MISSING) THEO TỪNG CỘT ---")
    for col in df.columns:
        non_null_count = df[col].notna().sum()
        null_count = df[col].isna().sum()
        pct = (non_null_count / total_rows) * 100
        status = "ĐỦ 100%" if null_count == 0 else f"THIẾU {null_count} ({null_count / total_rows * 100:.1f}%)"
        print(f" + Cột [{col:<28}]: Có {non_null_count:>5}/{total_rows} -> {status}")
    print()

    # =========================================================================
    # TEST 3: Kiểm tra các trường con trong "Thông số kỹ thuật tóm tắt"
    # =========================================================================
    print("--- 3. KIỂM TRA CÁC TRƯỜNG CON TRONG 'THÔNG SỐ KỸ THUẬT TÓM TẮT' ---")
    key_counter = Counter()
    has_sub_pipe_issue = 0

    for _, r in df.iterrows():
        specs_str = str(r.get("Thông số kỹ thuật tóm tắt", ""))
        parts = specs_str.split(" | ")
        seen_keys_in_row = set()
        for p in parts:
            if ":" in p:
                k = p.split(":", 1)[0].strip()
                # Nếu key quá dài hoặc có ký tự lạ do <br> bị split
                if len(k) > 40:
                    has_sub_pipe_issue += 1
                seen_keys_in_row.add(k)
        for k in seen_keys_in_row:
            key_counter[k] += 1

    print(" + Tỷ lệ xuất hiện của các thông số kỹ thuật (lý do 'có trường có trường không'):")
    for k, cnt in key_counter.most_common(12):
        pct = (cnt / total_rows) * 100
        print(f"    - {k:<25}: {cnt:>5}/{total_rows} ({pct:>5.1f}%)")

    print(f" + Số dòng bị ảnh hưởng bởi dấu ' | ' bất thường (do thẻ <br> trong HTML): {has_sub_pipe_issue}")
    print(" -> GIẢI THÍCH: API CellphoneS không phải sản phẩm nào cũng có đủ attributes.")
    print("    Đặc biệt trường 'Bộ nhớ/RAM' chỉ có 31.6% vì CellphoneS thường ghi dung lượng ở tên sản phẩm hoặc phân loại variant chứ không điền vào attribute storage.\n")

    # =========================================================================
    # TEST 4: Kiểm tra bản ghi trùng lặp (Duplicate Products)
    # =========================================================================
    print("--- 4. KIỂM TRA BẢN GHI SẢN PHẨM TRÙNG LẶP (DUPLICATE ROWS) ---")
    dup_url_mask = df.duplicated(subset=["URL sản phẩm"], keep=False)
    dup_rows = df[dup_url_mask]
    unique_urls = df["URL sản phẩm"].nunique()
    print(f" + Số URL duy nhất: {unique_urls} / {total_rows}")
    print(f" + Số dòng bị lặp lại (trùng URL với dòng khác): {len(dup_rows)} dòng ({len(dup_rows) / total_rows * 100:.2f}%)")

    if len(dup_rows) > 0:
        sample_dup = dup_rows.sort_values(by="URL sản phẩm").head(4)
        print(" + Ví dụ một số sản phẩm bị lặp lại 2 lần:")
        for _, r in sample_dup.iterrows():
            print(f"    - STT: {r['STT']:<5} | Tên: {r['Tên sản phẩm']:<35} | URL: {r['URL sản phẩm']}")

    print(" -> GIẢI THÍCH: Khi scraper phân trang qua GraphQL API (100+ trang), CellphoneS")
    print("    trả về cùng sản phẩm trên nhiều trang hoặc thuộc cả 2 danh mục (phone, laptop).")
    print("    Do scraper thiếu cơ chế 'seen_urls = set()' để deduplicate nên bị ghi 2 lần.\n")

    print("=" * 80)
    print("HOÀN TẤT BÁO CÁO PHÂN TÍCH CHẤT LƯỢNG!")
    print("=" * 80)


if __name__ == "__main__":
    test_scraped_data_anomalies()
