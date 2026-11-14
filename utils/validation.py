"""
Module: utils/validation.py
Chức năng: Kiểm tra tính hợp lệ của dữ liệu đầu vào từ giao diện (Chống nhập chữ, số âm, chia cho 0, sai miền giá trị).
"""

class ValidationError(Exception):
    """Ngoại lệ tùy chỉnh cho lỗi nhập liệu của người dùng."""
    pass


def validate_float(value_str, field_name, allow_zero=False, positive_only=True):
    """
    Chuyển đổi chuỗi từ ô nhập liệu sang số thực (float) và kiểm tra điều kiện.
    """
    if value_str is None or str(value_str).strip() == "":
        raise ValidationError(f"Trường '{field_name}' không được để trống!")
    
    cleaned = str(value_str).strip().replace(",", ".")
    try:
        val = float(cleaned)
    except ValueError:
        raise ValidationError(f"Trường '{field_name}' phải là một số hợp lệ (Giá trị đang nhập: '{value_str}')!")

    if positive_only:
        if allow_zero and val < 0:
            raise ValidationError(f"Trường '{field_name}' không được là số âm (phải lớn hơn hoặc bằng 0)!")
        elif not allow_zero and val <= 0:
            raise ValidationError(f"Trường '{field_name}' phải lớn hơn 0!")

    return val


def validate_int(value_str, field_name, positive_only=True):
    """
    Chuyển đổi chuỗi sang số nguyên (ví dụ: số đôi cực từ p).
    """
    if value_str is None or str(value_str).strip() == "":
        raise ValidationError(f"Trường '{field_name}' không được để trống!")
    try:
        val = int(float(str(value_str).strip()))
    except ValueError:
        raise ValidationError(f"Trường '{field_name}' phải là số nguyên!")
    if positive_only and val <= 0:
        raise ValidationError(f"Trường '{field_name}' phải là số nguyên dương (lớn hơn 0)!")
    return val


def validate_ratio(value_str, field_name, min_val=0.01, max_val=1.0):
    """
    Kiểm tra các hệ số như cosφ, hiệu suất η, hệ số xả sâu DoD (nằm trong khoảng (0, 1] hoặc (0, 100]).
    Tự động chuẩn hóa nếu người dùng nhập phần trăm (ví dụ 85 -> 0.85).
    """
    val = validate_float(value_str, field_name, allow_zero=False, positive_only=True)
    if 1.0 < val <= 100.0:
        val = val / 100.0
    if not (min_val <= val <= max_val):
        raise ValidationError(
            f"Trường '{field_name}' phải nằm trong khoảng từ {min_val} đến {max_val} (hoặc {min_val*100:.0f}% - {max_val*100:.0f}%)!"
        )
    return val


def validate_float_list(list_str, field_name):
    """
    Kiểm tra chuỗi danh sách các số cách nhau bởi dấu phẩy hoặc chấm phẩy (ví dụ: '10, 20, 30').
    """
    if list_str is None or str(list_str).strip() == "":
        raise ValidationError(f"Trường '{field_name}' không được để trống!")
    
    raw_items = str(list_str).replace(";", ",").split(",")
    result = []
    for idx, item in enumerate(raw_items, start=1):
        item_clean = item.strip()
        if not item_clean:
            continue
        val = validate_float(item_clean, f"{field_name} (phần tử thứ {idx})", allow_zero=False, positive_only=True)
        result.append(val)
    
    if not result:
        raise ValidationError(f"Trường '{field_name}' phải chứa ít nhất 1 giá trị số hợp lệ!")
    return result
