---
title: Dynamic Pricing - Trung tâm Tài liệu & Kiến trúc
project: Dynamic-Pricing
source: notion
notion_url: https://app.notion.com/p/Dynamic-Pricing-3e2a38d78df28056a0c4cbd51ea8e431
tags:
  - dynamic-pricing
  - index
  - hub
date: 2026-10-01
---

# 🚀 Dynamic Pricing System – Master Hub

> **Tổng quan:** Dynamic Pricing là hệ thống hỗ trợ định giá bán lẻ tự động. Hệ thống thu thập giá thị trường đối thủ (CellphoneS, Hoàng Hà Mobile), đối chiếu với dữ liệu tồn kho và nhu cầu thị trường của FPT Shop để đưa ra các gợi ý điều chỉnh giá tối ưu theo 9 kịch bản nghiệp vụ.

---

## 📚 1. Kiến trúc & Ma trận Định giá (Core Engine)
- 📊 [[Khám phá Dữ liệu & Ma trận Định giá]] *(Sơ đồ luồng, ma trận 9 kịch bản, công thức Composite Score)*
- 🏗️ [[Thiết kế Cơ sở Dữ liệu Toàn diện]] *(Mô hình dữ liệu PostgreSQL, pgvector, schema tables)*
- ⚙️ [[Giải thích Kiến trúc Backend và Chi tiết Codebase]] *(Cấu trúc FastAPI, Services, Repositories)*
- 🛠️ [[Tech stacks]] *(Ngăn xếp công nghệ: Python FastAPI, Crawlee, PostgreSQL, Docker)*

---

## 🕷️ 2. Thu thập Dữ liệu & So khớp SKU
- 🎯 [[Tiêu chí Matching SKU]] *(Đặc tả toàn bộ 9 tiêu chí matching, ma trận phân tầng, công thức tính điểm & rào cản)*
- 🤖 [[Hiểu code cào dữ liệu và map sku]] *(Chi tiết thuật toán Regex Part-Number & Levenshtein)*
- 📖 [[Crawling & SKU Matcher Guide]] *(Runbook hướng dẫn chạy lệnh cào và kiểm thử)*

---

## 📋 3. Quản lý Dự án & Tiến độ (Scrum / Agile)
- 📝 [[Product Backlog – Dynamic Pricing]] *(Chi tiết danh sách PBI và tiêu chuẩn nghiệm thu)*
- 🏃 [[Sprint Plan – Dynamic Pricing System]] *(Kế hoạch phân bổ Sprint và Milestone)*
- 📊 [[WBS Pricing]] *(Phân rã đầu việc WBS: HaiNN58 & SinhDTD)*
- 📑 [[Báo cáo chi tiết về Dynamic Pricing]] *(Nghiên cứu ban đầu & phân tích thị trường)*

---

## 🔗 Liên kết Mã nguồn Trực tiếp (Local Codebase)
- Run pipeline Hoàng Hà: `run_hoangha_pipeline.py`
- Core Config: `app/core/config.py`
- Scraper Service: `app/services/crawler_service.py`
- SKU Matcher: `app/services/sku_matcher.py`
- Test Suite: `tests/test_sku_matcher.py`
