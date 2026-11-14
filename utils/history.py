"""
Module: utils/history.py
Chức năng: Đọc/Ghi lịch sử tính toán và tự động khôi phục dữ liệu thiết bị chuẩn (catalog.json) nếu bị thiếu.
"""

import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")
CATALOG_FILE = os.path.join(DATA_DIR, "catalog.json")

DEFAULT_CATALOG = {
    "mcb_ratings_a": [6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125],
    "mcb_breaking_capacity_ka": [4.5, 6.0, 10.0, 15.0, 25.0, 36.0, 50.0],
    "fuse_ratings_a": [2, 4, 6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100],
    "contactors": [
        {"model": "LC1D09 (9A)", "rated_a": 9},
        {"model": "LC1D12 (12A)", "rated_a": 12},
        {"model": "LC1D18 (18A)", "rated_a": 18},
        {"model": "LC1D25 (25A)", "rated_a": 25},
        {"model": "LC1D32 (32A)", "rated_a": 32},
        {"model": "LC1D40 (40A)", "rated_a": 40},
        {"model": "LC1D50 (50A)", "rated_a": 50},
        {"model": "LC1D65 (65A)", "rated_a": 65},
        {"model": "LC1D80 (80A)", "rated_a": 80},
        {"model": "LC1D95 (95A)", "rated_a": 95},
        {"model": "LC1D115 (115A)", "rated_a": 115},
        {"model": "LC1D150 (150A)", "rated_a": 150}
    ],
    "thermal_relays": [
        {"model": "LRD06 (1.0 - 1.6A)", "min_a": 1.0, "max_a": 1.6},
        {"model": "LRD07 (1.6 - 2.5A)", "min_a": 1.6, "max_a": 2.5},
        {"model": "LRD08 (2.5 - 4.0A)", "min_a": 2.5, "max_a": 4.0},
        {"model": "LRD10 (4.0 - 6.0A)", "min_a": 4.0, "max_a": 6.0},
        {"model": "LRD12 (5.5 - 8.0A)", "min_a": 5.5, "max_a": 8.0},
        {"model": "LRD14 (7.0 - 10.0A)", "min_a": 7.0, "max_a": 10.0},
        {"model": "LRD16 (9.0 - 13.0A)", "min_a": 9.0, "max_a": 13.0},
        {"model": "LRD21 (12.0 - 18.0A)", "min_a": 12.0, "max_a": 18.0},
        {"model": "LRD22 (16.0 - 24.0A)", "min_a": 16.0, "max_a": 24.0},
        {"model": "LRD32 (23.0 - 32.0A)", "min_a": 23.0, "max_a": 32.0},
        {"model": "LRD35 (30.0 - 38.0A)", "min_a": 30.0, "max_a": 38.0},
        {"model": "LRD340 (30.0 - 40.0A)", "min_a": 30.0, "max_a": 40.0},
        {"model": "LRD350 (37.0 - 50.0A)", "min_a": 37.0, "max_a": 50.0},
        {"model": "LRD365 (48.0 - 65.0A)", "min_a": 48.0, "max_a": 65.0},
        {"model": "LRD3363 (63.0 - 80.0A)", "min_a": 63.0, "max_a": 80.0},
        {"model": "LRD3365 (80.0 - 104.0A)", "min_a": 80.0, "max_a": 104.0},
        {"model": "LRD4367 (95.0 - 120.0A)", "min_a": 95.0, "max_a": 120.0},
        {"model": "LRD4369 (110.0 - 140.0A)", "min_a": 110.0, "max_a": 140.0}
    ],
    "capacitors_kvar": [1.0, 2.5, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 40.0, 50.0, 60.0, 75.0, 100.0],
    "cables": [
        {"section_mm2": 1.5, "ampacity_cu_a": 18, "ampacity_al_a": 14},
        {"section_mm2": 2.5, "ampacity_cu_a": 25, "ampacity_al_a": 19},
        {"section_mm2": 4.0, "ampacity_cu_a": 34, "ampacity_al_a": 26},
        {"section_mm2": 6.0, "ampacity_cu_a": 44, "ampacity_al_a": 34},
        {"section_mm2": 10.0, "ampacity_cu_a": 61, "ampacity_al_a": 47},
        {"section_mm2": 16.0, "ampacity_cu_a": 82, "ampacity_al_a": 63},
        {"section_mm2": 25.0, "ampacity_cu_a": 108, "ampacity_al_a": 83},
        {"section_mm2": 35.0, "ampacity_cu_a": 135, "ampacity_al_a": 104},
        {"section_mm2": 50.0, "ampacity_cu_a": 168, "ampacity_al_a": 129},
        {"section_mm2": 70.0, "ampacity_cu_a": 207, "ampacity_al_a": 159},
        {"section_mm2": 95.0, "ampacity_cu_a": 250, "ampacity_al_a": 192},
        {"section_mm2": 120.0, "ampacity_cu_a": 292, "ampacity_al_a": 225},
        {"section_mm2": 150.0, "ampacity_cu_a": 335, "ampacity_al_a": 258},
        {"section_mm2": 185.0, "ampacity_cu_a": 382, "ampacity_al_a": 294},
        {"section_mm2": 240.0, "ampacity_cu_a": 453, "ampacity_al_a": 348}
    ],
    "mccb_ratings_a": [16, 20, 25, 32, 40, 50, 63, 75, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630]
}


def ensure_data_files():
    """Tự động tạo thư mục data, catalog.json và history.json nếu bị thiếu."""
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(CATALOG_FILE):
        with open(CATALOG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CATALOG, f, ensure_ascii=False, indent=2)
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)


def load_catalog():
    """Đọc dữ liệu danh mục thiết bị chuẩn từ data/catalog.json."""
    ensure_data_files()
    try:
        with open(CATALOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return DEFAULT_CATALOG


def load_history():
    """Đọc danh sách lịch sử tính toán từ data/history.json."""
    ensure_data_files()
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        return []


def save_calculation_record(module_id, module_name, user_inputs, calculation_results, equipment_recommendation, extra_data=None):
    """
    Đóng gói kết quả bằng tiếng Việt 100% và lưu vào data/history.json.
    """
    ensure_data_files()
    record = {
        "Thời gian tính toán": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Mã chức năng": module_id,
        "Tên chức năng": module_name,
        "Thông số đầu vào": user_inputs,
        "Kết quả tính toán": calculation_results,
        "Khuyến nghị thiết bị": equipment_recommendation
    }
    if extra_data:
        record["Dữ liệu bổ sung"] = extra_data

    history = load_history()
    history.insert(0, record)
    history = history[:100]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)
    return record


def clear_history():
    """Xóa toàn bộ lịch sử tính toán."""
    ensure_data_files()
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)
