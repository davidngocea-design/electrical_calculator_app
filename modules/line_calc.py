"""
Module: modules/line_calc.py
Chức năng:
  - Tính dòng điện tính toán Itt (1 pha hoặc 3 pha)
  - Chọn MCCB tổng và RCCB/ELCB chống dòng rò
  - Tính tiết diện sơ bộ theo mật độ dòng kinh tế Jcp VÀ kiểm tra điều kiện phát nóng lâu dài (Icp >= Idm MCCB)
  - Vòng lặp tự động tăng cấp tiết diện dây S trong catalog chuẩn cho đến khi độ sụt áp ΔU% <= ngưỡng cho phép
  - Tính tổn thất công suất trên đường dây ΔP
"""

import math
from utils.history import load_catalog, save_calculation_record

RESISTIVITY = {
    "Cu": 0.0172,  # Đồng: 0.0172 Ω·mm²/m
    "Al": 0.0280   # Nhôm: 0.0280 Ω·mm²/m
}
REACTANCE_PER_KM = 0.08  # Điện kháng đường dây hạ thế trung bình x0 = 0.08 Ω/km


def calc_voltage_drop_for_section(i_tt, l_m, s_mm2, u_v, cos_phi, phase_type="3P", material="Cu"):
    """
    Tính độ sụt áp ΔU (V), ΔU (%) và tổn thất công suất ΔP (W) cho một tiết diện S cụ thể.
    """
    rho = RESISTIVITY.get(material, 0.0172)
    r_line = rho * (l_m / s_mm2)
    x_line = (REACTANCE_PER_KM / 1000.0) * l_m
    sin_phi = math.sqrt(max(0.0, 1.0 - cos_phi ** 2))

    is_3p = str(phase_type).upper().startswith("3")
    coeff_u = math.sqrt(3.0) if is_3p else 2.0
    coeff_p = 3.0 if is_3p else 2.0

    delta_u_v = coeff_u * i_tt * (r_line * cos_phi + x_line * sin_phi)
    delta_u_percent = (delta_u_v / u_v) * 100.0
    delta_p_w = coeff_p * (i_tt ** 2) * r_line

    return {
        "r_line_ohm": r_line,
        "x_line_ohm": x_line,
        "delta_u_v": delta_u_v,
        "delta_u_percent": delta_u_percent,
        "delta_p_w": delta_p_w
    }


def optimize_cable_and_protection(
    p_kw,
    l_m,
    u_v=380.0,
    cos_phi=0.85,
    phase_type="3P",
    material="Cu",
    j_cp=5.0,
    max_vdrop_percent=5.0,
    env_type="industrial"
):
    """
    Thuật toán tổng hợp chọn cáp điện, kiểm tra phát nóng, lặp tối ưu sụt áp và chọn MCCB/RCCB.
    """
    is_3p = str(phase_type).upper().startswith("3")
    if is_3p:
        i_tt = (p_kw * 1000.0) / (math.sqrt(3.0) * u_v * cos_phi)
        phase_label = "Mạng 3 Pha (3P+N)"
        cores_str = "4×"
    else:
        i_tt = (p_kw * 1000.0) / (u_v * cos_phi)
        phase_label = "Mạng 1 Pha (1P+N)"
        cores_str = "2×"

    catalog = load_catalog()
    mccb_list = catalog.get("mccb_ratings_a", [16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 400])
    req_mccb_a = 1.25 * i_tt
    selected_mccb_a = next((cb for cb in mccb_list if cb >= req_mccb_a), mccb_list[-1])

    s_prelim_j = i_tt / j_cp

    cables = catalog.get("cables", [])
    amp_key = "ampacity_cu_a" if material == "Cu" else "ampacity_al_a"
    mat_label = "Đồng (Cu)" if material == "Cu" else "Nhôm (Al)"

    min_ampacity_target = max(selected_mccb_a, req_mccb_a)
    start_idx = 0
    for idx, c in enumerate(cables):
        if c["section_mm2"] >= s_prelim_j and c[amp_key] >= min_ampacity_target:
            start_idx = idx
            break
    else:
        start_idx = len(cables) - 1

    initial_cable = cables[start_idx]
    initial_metrics = calc_voltage_drop_for_section(
        i_tt, l_m, initial_cable["section_mm2"], u_v, cos_phi, phase_type, material
    )

    iteration_steps = []
    chosen_idx = start_idx
    for idx in range(start_idx, len(cables)):
        cand = cables[idx]
        metrics = calc_voltage_drop_for_section(
            i_tt, l_m, cand["section_mm2"], u_v, cos_phi, phase_type, material
        )
        passed = metrics["delta_u_percent"] <= max_vdrop_percent
        iteration_steps.append({
            "Tiết diện (mm²)": cand["section_mm2"],
            "Dòng cho phép (A)": cand[amp_key],
            "Sụt áp (V)": round(metrics["delta_u_v"], 2),
            "Tỷ lệ sụt áp (%)": round(metrics["delta_u_percent"], 2),
            "Tổn thất công suất (W)": round(metrics["delta_p_w"], 2),
            "Kết luận": "ĐẠT CHUẨN" if passed else "KHÔNG ĐẠT (Tăng cấp tiết diện)"
        })
        chosen_idx = idx
        if passed:
            break

    final_cable = cables[chosen_idx]
    final_metrics = calc_voltage_drop_for_section(
        i_tt, l_m, final_cable["section_mm2"], u_v, cos_phi, phase_type, material
    )

    if str(env_type).lower().startswith("res") or str(env_type).lower() == "dân dụng":
        rccb_str = f"Aptomat chống rò RCCB/ELCB {selected_mccb_a} A - Dòng rò tác động 30 mA (Bảo vệ con người / Dân dụng)"
    else:
        rccb_str = f"Aptomat chống rò RCCB/ELCB {selected_mccb_a} A - Dòng rò tác động 100 mA / 300 mA (Chống cháy nổ Công nghiệp)"

    status_note = (
        f"Đạt chuẩn sụt áp cho phép (ΔU% = {final_metrics['delta_u_percent']:.2f}% ≤ {max_vdrop_percent}%)"
        if final_metrics["delta_u_percent"] <= max_vdrop_percent
        else f"Cảnh báo: Đã chọn tiết diện lớn nhất ({final_cable['section_mm2']} mm²) nhưng ΔU% = {final_metrics['delta_u_percent']:.2f}% (Cần đi cáp chập đôi)"
    )

    tom_tat_vong_lap = " -> ".join(
        f"[{step['Tiết diện (mm²)']} mm²: ΔU = {step['Tỷ lệ sụt áp (%)']}% ({step['Kết luận']})]"
        for step in iteration_steps
    )

    return save_calculation_record(
        module_id="Đường dây - Sụt áp và Chọn cáp",
        module_name="Tính Đường Dây, Tối Ưu Sụt Áp & Chọn Cáp / MCCB",
        user_inputs={
            "Công suất tính toán P (kW)": f"{round(p_kw, 3)} kW",
            "Chiều dài tuyến cáp L (m)": f"{round(l_m, 2)} m",
            "Điện áp định mức lưới U (V)": f"{round(u_v, 2)} V",
            "Hệ số công suất cosφ": f"{round(cos_phi, 4)}",
            "Hệ thống cung cấp điện": phase_label,
            "Vật liệu ruột dẫn cáp": mat_label,
            "Mật độ dòng kinh tế Jcp (A/mm²)": f"{round(j_cp, 2)} A/mm²",
            "Giới hạn sụt áp cho phép ΔUmax (%)": f"{round(max_vdrop_percent, 2)} %"
        },
        calculation_results={
            "Dòng điện làm việc tính toán Itt (A)": f"{round(i_tt, 3)} A",
            "Tiết diện sơ bộ theo mật độ dòng Jcp (mm²)": f"{round(s_prelim_j, 2)} mm²",
            "Tiết diện cáp thỏa phát nóng ban đầu (mm²)": f"{initial_cable['section_mm2']} mm² (Sụt áp ban đầu: {initial_metrics['delta_u_percent']:.2f}%)",
            "Tiết diện cáp chuẩn sau tối ưu sụt áp (mm²)": f"{final_cable['section_mm2']} mm²",
            "Dòng điện phát nóng lâu dài cho phép của cáp (A)": f"{final_cable[amp_key]} A",
            "Độ sụt áp thực tế trên đường dây ΔU (V)": f"{round(final_metrics['delta_u_v'], 3)} V",
            "Tỷ lệ sụt áp thực tế ΔU (%)": f"{round(final_metrics['delta_u_percent'], 3)} %",
            "Tổn thất công suất tác dụng trên dây ΔP (W)": f"{round(final_metrics['delta_p_w'], 2)} W",
            "Quá trình lặp kiểm tra tiết diện": tom_tat_vong_lap
        },
        equipment_recommendation={
            "Quy cách cáp điện khuyến nghị": f"Cáp {mat_label} {cores_str}{final_cable['section_mm2']} mm² (Dòng cho phép Icp = {final_cable[amp_key]} A)",
            "Aptomat khối bảo vệ tổng (MCCB)": f"MCCB {'3P' if is_3p else '2P'} {selected_mccb_a} A (Yêu cầu tối thiểu {req_mccb_a:.2f} A)",
            "Thiết bị bảo vệ chống dòng rò (RCCB/ELCB)": rccb_str,
            "Kết luận kiểm tra kỹ thuật": status_note
        },
        extra_data={"Các bước lặp": iteration_steps}
    )
