"""
Module: modules/ac_single_phase.py
Chức năng:
  - Tính trở kháng mạch RLC nối tiếp 1 pha (XL, XC, Z, góc lệch pha φ)
  - Tính dòng điện, hệ số công suất cosφ và công suất P, Q, S mạch 1 pha
  - Tính bù công suất phản kháng (Qc, điện dung C quy đổi chuẩn ra µF)
  - Tra bảng chọn Tụ bù thương mại (kVAR) và CB bảo vệ tụ bù
"""

import math
from utils.history import load_catalog, save_calculation_record


def calc_impedance_and_power(u, r, l_mh=0.0, c_uf=0.0, f=50.0):
    """
    Tính trở kháng & công suất mạch RLC 1 pha.
    """
    l_h = l_mh * 1e-3
    x_l = 2.0 * math.pi * f * l_h if l_h > 0 else 0.0

    if c_uf > 0:
        c_f = c_uf * 1e-6
        x_c = 1.0 / (2.0 * math.pi * f * c_f)
    else:
        x_c = 0.0

    x_total = x_l - x_c
    z = math.sqrt(r ** 2 + x_total ** 2)
    if z <= 0:
        raise ValueError("Tổng trở Z của mạch phải lớn hơn 0!")

    i_a = u / z
    cos_phi = r / z
    sin_phi = abs(x_total) / z
    phi_deg = math.degrees(math.atan2(x_total, r))

    s_va = u * i_a
    p_w = s_va * cos_phi
    q_var = s_va * sin_phi

    catalog = load_catalog()
    mcb_ratings = catalog.get("mcb_ratings_a", [6, 10, 16, 20, 25, 32, 40, 50, 63])
    req_mcb = 1.25 * i_a
    chosen_mcb = next((m for m in mcb_ratings if m >= req_mcb), None)

    nature = "Mạch thuần trở (Dòng điện cùng pha với Điện áp)"
    if x_total > 1e-6:
        nature = "Mạch có tính cảm kháng (Dòng điện trễ pha hơn Điện áp)"
    elif x_total < -1e-6:
        nature = "Mạch có tính dung kháng (Dòng điện sớm pha hơn Điện áp)"

    return save_calculation_record(
        module_id="Mạch 1 Pha - Trở kháng RLC",
        module_name="Tính Trở Kháng & Công Suất Mạch RLC 1 Pha",
        user_inputs={
            "Điện áp nguồn xoay chiều U (V)": f"{round(u, 2)} V",
            "Điện trở thuần R (Ω)": f"{round(r, 4)} Ω",
            "Độ tự cảm cuộn dây L (mH)": f"{round(l_mh, 4)} mH",
            "Điện dung tụ điện C (µF)": f"{round(c_uf, 4)} µF",
            "Tần số dòng điện f (Hz)": f"{round(f, 2)} Hz"
        },
        calculation_results={
            "Cảm kháng cuộn dây XL (Ω)": f"{round(x_l, 4)} Ω",
            "Dung kháng tụ điện XC (Ω)": f"{round(x_c, 4)} Ω",
            "Tổng trở toàn mạch Z (Ω)": f"{round(z, 4)} Ω",
            "Cường độ dòng điện hiệu dụng I (A)": f"{round(i_a, 4)} A",
            "Hệ số công suất cosφ": f"{round(cos_phi, 4)}",
            "Góc lệch pha φ (Độ)": f"{round(phi_deg, 2)}°",
            "Công suất tác dụng P (W)": f"{round(p_w, 3)} W",
            "Công suất phản kháng Q (VAR)": f"{round(q_var, 3)} VAR",
            "Công suất biểu kiến S (VA)": f"{round(s_va, 3)} VA"
        },
        equipment_recommendation={
            "Đặc tính mạch điện": nature,
            "Aptomat bảo vệ nhánh (MCB)": f"MCB 1P/2P {chosen_mcb} A (Dòng tải I = {i_a:.2f} A)" if chosen_mcb else f"MCCB từ {req_mcb:.1f} A trở lên"
        }
    )


def calc_reactive_compensation(p_kw, cos_phi_old, cos_phi_new, f=50.0, u=220.0):
    """
    Tính bù công suất phản kháng nâng cao hệ số cosφ.
    """
    if cos_phi_new <= cos_phi_old:
        raise ValueError(f"Hệ số cosφ mục tiêu ({cos_phi_new}) phải lớn hơn hệ số cosφ ban đầu ({cos_phi_old})!")

    phi1 = math.acos(cos_phi_old)
    phi2 = math.acos(cos_phi_new)
    tan_phi1 = math.tan(phi1)
    tan_phi2 = math.tan(phi2)

    q_c_kvar = p_kw * (tan_phi1 - tan_phi2)
    c_uf = (q_c_kvar * 1e9) / (2.0 * math.pi * f * (u ** 2))
    i_c_calc = (q_c_kvar * 1000.0) / u

    catalog = load_catalog()
    cap_standards = catalog.get("capacitors_kvar", [1.0, 2.5, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 50.0])
    chosen_cap_kvar = next((cap for cap in cap_standards if cap >= q_c_kvar), None)

    if chosen_cap_kvar:
        i_c_actual = (chosen_cap_kvar * 1000.0) / u
        c_actual_uf = (chosen_cap_kvar * 1e9) / (2.0 * math.pi * f * (u ** 2))
        cap_str = f"Tụ bù tiêu chuẩn {chosen_cap_kvar} kVAR (Điện dung tương đương {c_actual_uf:.1f} µF)"
    else:
        n_banks = math.ceil(q_c_kvar / 50.0)
        chosen_cap_kvar = n_banks * 50.0
        i_c_actual = (chosen_cap_kvar * 1000.0) / u
        cap_str = f"Ghép song song {n_banks} bộ tụ bù 50 kVAR (Tổng dung lượng {chosen_cap_kvar} kVAR)"

    req_cb_a = 1.5 * i_c_actual
    mcb_ratings = catalog.get("mcb_ratings_a", []) + catalog.get("mccb_ratings_a", [])
    mcb_ratings = sorted(list(set(mcb_ratings)))
    chosen_cb = next((cb for cb in mcb_ratings if cb >= req_cb_a), None)
    cb_str = (
        f"Aptomat bảo vệ tụ bù {chosen_cb} A (Chọn từ 1.5 × Ic = {req_cb_a:.2f} A)"
        if chosen_cb else f"MCCB bảo vệ tụ bù từ {req_cb_a:.1f} A trở lên"
    )

    return save_calculation_record(
        module_id="Mạch 1 Pha - Bù công suất phản kháng",
        module_name="Tính Bù Công Suất Phản Kháng cosφ & Chọn Tụ Bù",
        user_inputs={
            "Công suất tác dụng của tải P (kW)": f"{round(p_kw, 3)} kW",
            "Hệ số công suất trước khi bù (cosφ1)": f"{round(cos_phi_old, 4)}",
            "Hệ số công suất mục tiêu sau bù (cosφ2)": f"{round(cos_phi_new, 4)}",
            "Điện áp lưới U (V)": f"{round(u, 2)} V",
            "Tần số lưới điện f (Hz)": f"{round(f, 2)} Hz"
        },
        calculation_results={
            "Hệ số tanφ1 (Trước khi bù)": f"{round(tan_phi1, 4)}",
            "Hệ số tanφ2 (Sau khi bù)": f"{round(tan_phi2, 4)}",
            "Dung lượng bù phản kháng cần thiết Qc (kVAR)": f"{round(q_c_kvar, 4)} kVAR",
            "Điện dung tụ bù tính toán C (µF)": f"{round(c_uf, 2)} µF",
            "Dòng điện định mức qua tụ bù lý thuyết (A)": f"{round(i_c_calc, 3)} A",
            "Dòng điện làm việc thực tế của bộ tụ chọn (A)": f"{round(i_c_actual, 3)} A"
        },
        equipment_recommendation={
            "Dung lượng bộ tụ bù khuyến nghị": cap_str,
            "Aptomat đóng cắt & bảo vệ tụ bù": cb_str
        }
    )


def convert_electrical_unit(value, conversion_type):
    """
    Hàm phụ trợ chuyển đổi nhanh đơn vị kỹ thuật điện.
    """
    conversions = {
        "W sang kW": (value / 1000.0, "kW"),
        "kW sang W": (value * 1000.0, "W"),
        "kW sang Mã lực (HP)": (value / 0.7457, "HP"),
        "Mã lực (HP) sang kW": (value * 0.7457, "kW"),
        "A sang kA": (value / 1000.0, "kA"),
        "kA sang A": (value * 1000.0, "A"),
        "µF sang mF": (value / 1000.0, "mF"),
        "mF sang µF": (value * 1000.0, "µF"),
        "µF sang F": (value * 1e-6, "F"),
        "F sang µF": (value * 1e6, "µF"),
        "mH sang H": (value / 1000.0, "H"),
        "H sang mH": (value * 1000.0, "mH")
    }
    if conversion_type not in conversions:
        raise ValueError(f"Kiểu chuyển đổi đơn vị không hợp lệ: {conversion_type}")
    res, unit = conversions[conversion_type]
    return round(res, 6), unit
