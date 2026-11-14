"""
Module: utils/exporter.py
Chức năng: Định dạng hiển thị và xuất báo cáo kết quả tính toán ra file .txt, .csv hoặc .json (100% Tiếng Việt, không có dấu '_').
"""

import csv
import json


def _clean_text(val):
    """Đảm bảo mọi chuỗi hiển thị không còn ký tự gạch dưới '_'."""
    if isinstance(val, list):
        return ", ".join(str(x).replace("_", " ") for x in val)
    return str(val).replace("_", " ")


def format_record_as_text(record):
    """Chuyển đổi 1 bản ghi kết quả thành văn bản báo cáo kỹ thuật 100% tiếng Việt rõ ràng."""
    if not record:
        return "Chưa có dữ liệu tính toán để hiển thị báo cáo."

    thoi_gian = record.get("Thời gian tính toán", record.get("timestamp", "Không xác định"))
    ma_cn = _clean_text(record.get("Mã chức năng", record.get("module_id", "Không xác định")))
    ten_cn = _clean_text(record.get("Tên chức năng", record.get("module_name", "Không xác định")))

    dau_vao = record.get("Thông số đầu vào", record.get("user_inputs", {}))
    ket_qua = record.get("Kết quả tính toán", record.get("calculation_results", {}))
    khuyen_nghi = record.get("Khuyến nghị thiết bị", record.get("equipment_recommendation", {}))

    lines = [
        "=" * 76,
        "           BÁO CÁO KẾT QUẢ TÍNH TOÁN & TRA CỨU KỸ THUẬT ĐIỆN",
        "=" * 76,
        f"Thời gian tính toán : {thoi_gian}",
        f"Mã phân hệ          : {ma_cn}",
        f"Tên chức năng       : {ten_cn}",
        "-" * 76,
        "1. THÔNG SỐ ĐẦU VÀO:"
    ]
    for k, v in dau_vao.items():
        lines.append(f"   - {_clean_text(k):<38}: {_clean_text(v)}")

    lines.append("-" * 76)
    lines.append("2. KẾT QUẢ TÍNH TOÁN:")
    for k, v in ket_qua.items():
        lines.append(f"   - {_clean_text(k):<38}: {_clean_text(v)}")

    lines.append("-" * 76)
    lines.append("3. KHUYẾN NGHỊ THIẾT BỊ & KHÍ CỤ ĐIỆN:")
    for k, v in khuyen_nghi.items():
        lines.append(f"   * {_clean_text(k):<38}: {_clean_text(v)}")

    lines.append("=" * 76)
    return chr(10).join(lines)


def export_record_to_file(record, filepath):
    """
    Lưu bản ghi kết quả ra file (.txt, .json, hoặc .csv) hoàn toàn bằng tiếng Việt.
    """
    ext = filepath.lower().split(".")[-1]
    thoi_gian = record.get("Thời gian tính toán", record.get("timestamp", ""))
    ma_cn = _clean_text(record.get("Mã chức năng", record.get("module_id", "")))
    ten_cn = _clean_text(record.get("Tên chức năng", record.get("module_name", "")))
    dau_vao = record.get("Thông số đầu vào", record.get("user_inputs", {}))
    ket_qua = record.get("Kết quả tính toán", record.get("calculation_results", {}))
    khuyen_nghi = record.get("Khuyến nghị thiết bị", record.get("equipment_recommendation", {}))

    if ext == "json":
        clean_record = {
            "Thời gian tính toán": thoi_gian,
            "Mã chức năng": ma_cn,
            "Tên chức năng": ten_cn,
            "Thông số đầu vào": {_clean_text(k): _clean_text(v) for k, v in dau_vao.items()},
            "Kết quả tính toán": {_clean_text(k): _clean_text(v) for k, v in ket_qua.items()},
            "Khuyến nghị thiết bị": {_clean_text(k): _clean_text(v) for k, v in khuyen_nghi.items()}
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(clean_record, f, ensure_ascii=False, indent=2)
    elif ext == "csv":
        with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Nhóm thông tin", "Thông số", "Giá trị"])
            writer.writerow(["Thông tin chung", "Thời gian tính toán", thoi_gian])
            writer.writerow(["Thông tin chung", "Mã phân hệ", ma_cn])
            writer.writerow(["Thông tin chung", "Tên chức năng", ten_cn])
            for k, v in dau_vao.items():
                writer.writerow(["1. Thông số đầu vào", _clean_text(k), _clean_text(v)])
            for k, v in ket_qua.items():
                writer.writerow(["2. Kết quả tính toán", _clean_text(k), _clean_text(v)])
            for k, v in khuyen_nghi.items():
                writer.writerow(["3. Khuyến nghị thiết bị", _clean_text(k), _clean_text(v)])
    else:
        text_content = format_record_as_text(record)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text_content)
    return filepath
