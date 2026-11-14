"""
Module: modules/ac_three_phase.py
Chức năng:
  - Quan hệ điện áp/dòng điện 3 pha đấu Sao (Y) và Tam giác (Δ)
  - Tính bộ ba công suất P, Q, S mạch 3 pha
  - Tính thông số Động cơ không đồng bộ 3 pha và tra chọn Contactor + Rơ le nhiệt
  - Tính tỷ số máy biến áp lý tưởng
"""

import math
from utils.history import load_catalog, save_calculation_record


def select_contactor_and_relay(i_dm_motor):
    """
    Tra bảng chọn Contactor (I_contactor >= 1.25 * I_dm) và Rơ le nhiệt (I_min <= I_dm <= I_max).
    """
    catalog = load_catalog()
    req_contactor_a = 1.25 * i_dm_motor

    contactors = catalog.get("contactors", [])
    chosen_contactor = next((c for c in contactors if c["rated_a"] >= req_contactor_a), None)
    if chosen_contactor:
        contactor_str = f"Khởi động từ (Contactor) 3P {chosen_contactor['model']} (Yêu cầu tối thiểu {req_contactor_a:.2f} A)"
    else:
        contactor_str = f"Contactor công suất lớn từ {req_contactor_a:.1f} A trở lên"

    relays = catalog.get("thermal_relays", [])
    chosen_relay = next((r for r in relays if r["min_a"] <= i_dm_motor <= r["max_a"]), None)
    if chosen_relay:
        relay_str = f"Rơ le nhiệt {chosen_relay['model']} (Cài đặt dòng tác động tại {i_dm_motor:.2f} A)"
    else:
        fallback = next((r for r in relays if r["max_a"] >= i_dm_motor), None)
        relay_str = (
            f"Rơ le nhiệt {fallback['model']} (Chỉnh tại {i_dm_motor:.2f} A)"
            if fallback else f"Rơ le nhiệt điện tử dải trên {i_dm_motor:.1f} A"
        )

    return {
        "Khởi động từ (Contactor)": contactor_str,
        "Rơ le nhiệt bảo vệ quá tải": relay_str
    }


def calc_3phase_relations(ud, id_line, connection_type="Y"):
    """
    Tính Up, Ip theo kiểu đấu Sao (Y) hoặc Tam giác (Δ).
    """
    conn = connection_type.upper().strip()
    sqrt3 = math.sqrt(3.0)
    if conn in ("Y", "SAO", "STAR"):
        up = ud / sqrt3
        ip = id_line
        conn_label = "Đấu Hình Sao (Y)"
    else:
        up = ud
        ip = id_line / sqrt3
        conn_label = "Đấu Hình Tam Giác (Δ)"

    z_phase = up / ip if ip > 0 else 0.0

    return save_calculation_record(
        module_id="Mạch 3 Pha - Đấu Sao và Tam Giác",
        module_name="Quan Hệ Dòng & Áp Mạch 3 Pha (Sao / Tam Giác)",
        user_inputs={
            "Điện áp dây Ud (V)": f"{round(ud, 2)} V",
            "Dòng điện dây Id (A)": f"{round(id_line, 3)} A",
            "Kiểu đấu dây 3 pha": conn_label
        },
        calculation_results={
            "Điện áp pha Up (V)": f"{round(up, 3)} V",
            "Dòng điện pha Ip (A)": f"{round(ip, 3)} A",
            "Tổng trở mỗi pha Zp (Ω)": f"{round(z_phase, 4)} Ω"
        },
        equipment_recommendation=select_contactor_and_relay(id_line)
    )


def calc_3phase_power(ud, id_line, cos_phi):
    """
    Tính bộ ba công suất 3 pha P, Q, S.
    """
    sqrt3 = math.sqrt(3.0)
    sin_phi = math.sqrt(max(0.0, 1.0 - cos_phi ** 2))
    s_va = sqrt3 * ud * id_line
    p_w = s_va * cos_phi
    q_var = s_va * sin_phi

    return save_calculation_record(
        module_id="Mạch 3 Pha - Công suất P Q S",
        module_name="Tính Công Suất Mạch Điện 3 Pha (P, Q, S)",
        user_inputs={
            "Điện áp dây Ud (V)": f"{round(ud, 2)} V",
            "Dòng điện dây Id (A)": f"{round(id_line, 3)} A",
            "Hệ số công suất cosφ": f"{round(cos_phi, 4)}"
        },
        calculation_results={
            "Công suất tác dụng P (kW)": f"{round(p_w / 1000.0, 4)} kW",
            "Công suất phản kháng Q (kVAR)": f"{round(q_var / 1000.0, 4)} kVAR",
            "Công suất biểu kiến S (kVA)": f"{round(s_va / 1000.0, 4)} kVA",
            "Hệ số sinφ": f"{round(sin_phi, 4)}"
        },
        equipment_recommendation=select_contactor_and_relay(id_line)
    )


def calc_motor_params(f, p, n_real, p_kw, u_d, cos_phi, eff):
    """
    Tính toán Động cơ không đồng bộ 3 pha.
    """
    n_s = (60.0 * f) / p
    if n_real >= n_s:
        raise ValueError(f"Tốc độ thực tế n ({n_real} vòng/phút) phải nhỏ hơn tốc độ đồng bộ ns ({n_s:.0f} vòng/phút) đối với động cơ không đồng bộ!")

    slip_percent = ((n_s - n_real) / n_s) * 100.0
    torque_nm = 9550.0 * (p_kw / n_real)
    i_dm = (p_kw * 1000.0) / (math.sqrt(3.0) * u_d * cos_phi * eff)
    p_elec_kw = p_kw / eff

    equip = select_contactor_and_relay(i_dm)

    return save_calculation_record(
        module_id="Mạch 3 Pha - Động cơ không đồng bộ",
        module_name="Tính Toán Động Cơ Không Đồng Bộ 3 Pha",
        user_inputs={
            "Công suất cơ định mức Pđm (kW)": f"{round(p_kw, 3)} kW",
            "Điện áp dây định mức Ud (V)": f"{round(u_d, 2)} V",
            "Tần số lưới điện f (Hz)": f"{round(f, 2)} Hz",
            "Số đôi cực từ p": f"{int(p)} đôi cực ({int(2*p)} cực)",
            "Tốc độ quay thực tế n (vòng/phút)": f"{round(n_real, 1)} vòng/phút",
            "Hệ số công suất cosφ": f"{round(cos_phi, 4)}",
            "Hiệu suất động cơ η": f"{round(eff * 100, 1)} % (Hệ số {round(eff, 4)})"
        },
        calculation_results={
            "Dòng điện định mức động cơ Iđm (A)": f"{round(i_dm, 3)} A",
            "Tốc độ từ trường quay đồng bộ ns (vòng/phút)": f"{round(n_s, 1)} vòng/phút",
            "Hệ số trượt tốc độ s (%)": f"{round(slip_percent, 3)} %",
            "Mô-men xoắn định mức trên trục M (N·m)": f"{round(torque_nm, 3)} N·m",
            "Công suất điện tiêu thụ đầu vào P1 (kW)": f"{round(p_elec_kw, 3)} kW"
        },
        equipment_recommendation=equip
    )


def calc_transformer_ratio(u1, u2, n1, i1_a=10.0):
    """
    Tính tỷ số máy biến áp lý tưởng: k = U1 / U2 = N1 / N2 = I2 / I1.
    """
    k = u1 / u2
    n2 = n1 / k
    i2_a = i1_a * k
    s_kva = (u1 * i1_a) / 1000.0

    return save_calculation_record(
        module_id="Mạch 3 Pha - Máy biến áp",
        module_name="Tính Tỷ Số Máy Biến Áp Lý Tưởng",
        user_inputs={
            "Điện áp cuộn sơ cấp U1 (V)": f"{round(u1, 2)} V",
            "Điện áp cuộn thứ cấp U2 (V)": f"{round(u2, 2)} V",
            "Số vòng dây sơ cấp N1 (vòng)": f"{round(n1, 1)} vòng",
            "Dòng điện sơ cấp I1 (A)": f"{round(i1_a, 3)} A"
        },
        calculation_results={
            "Hệ số biến áp k (U1 / U2)": f"{round(k, 4)}",
            "Số vòng dây thứ cấp N2 (vòng)": f"{round(n2, 2)} vòng",
            "Dòng điện thứ cấp I2 (A)": f"{round(i2_a, 3)} A",
            "Công suất biểu kiến định mức S (kVA)": f"{round(s_kva, 3)} kVA"
        },
        equipment_recommendation={
            "Phân loại máy biến áp": "Máy biến áp Hạ áp (k > 1)" if k > 1 else ("Máy biến áp Tăng áp (k < 1)" if k < 1 else "Máy biến áp Cách ly (k = 1)")
        }
    )
