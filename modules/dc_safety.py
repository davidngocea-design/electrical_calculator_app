"""
Module: modules/dc_safety.py
Chức năng:
  - Tính định luật Ohm DC (I = U/R, P = U*I, A = P*t)
  - Tính điện trở dây dẫn theo nhiệt độ (R0 = rho * l / S, RT = R0 * [1 + alpha * (T - 20)])
  - Tính điện trở tương đương ghép nối tiếp / song song
  - Tính thời gian xả ắc quy có xét hệ số xả sâu DoD (t = V * Ah * DoD * eta / P)
  - Tính dòng ngắn mạch và tra cứu chọn MCB / Cầu chì
"""

from utils.history import load_catalog, save_calculation_record


def select_mcb_and_fuse(i_tt_a, i_nk_ka=0.0):
    """
    Tra cứu chọn MCB và Cầu chì từ catalog.json:
      - Dòng định mức MCB >= 1.25 * Dòng tính toán
      - Dòng cắt ngắn mạch Icu >= Dòng ngắn mạch Ink (kA)
    """
    catalog = load_catalog()
    req_current = 1.25 * i_tt_a

    mcb_ratings = catalog.get("mcb_ratings_a", [6, 10, 16, 20, 25, 32, 40, 50, 63])
    selected_mcb_a = next((r for r in mcb_ratings if r >= req_current), None)
    mcb_str = (
        f"Aptomat MCB {selected_mcb_a} A (Yêu cầu tối thiểu {req_current:.2f} A)"
        if selected_mcb_a else f"Vượt dải MCB chuẩn (Cần dùng MCCB từ {req_current:.2f} A trở lên)"
    )

    icu_ratings = catalog.get("mcb_breaking_capacity_ka", [4.5, 6.0, 10.0, 15.0, 25.0])
    selected_icu = next((icu for icu in icu_ratings if icu >= i_nk_ka), None)
    if i_nk_ka > 0:
        icu_str = (
            f"Dòng cắt ngắn mạch Icu = {selected_icu} kA (Dòng ngắn mạch tính toán = {i_nk_ka:.2f} kA)"
            if selected_icu else f"Cần máy cắt ACB/MCCB dòng cắt cao (lớn hơn {i_nk_ka:.2f} kA)"
        )
    else:
        icu_str = "Dòng cắt tiêu chuẩn 6.0 kA (Chưa xét ngắn mạch)"

    fuse_ratings = catalog.get("fuse_ratings_a", [2, 4, 6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100])
    selected_fuse_a = next((f for f in fuse_ratings if f >= req_current), None)
    fuse_str = f"Cầu chì bảo vệ {selected_fuse_a} A" if selected_fuse_a else f"Cầu chì công nghiệp trên {req_current:.1f} A"

    return {
        "Aptomat bảo vệ (MCB)": mcb_str,
        "Khả năng cắt ngắn mạch (Icu)": icu_str,
        "Cầu chì khuyến nghị": fuse_str
    }


def calc_dc_ohm(u, r, t_hours=1.0):
    """
    Tính toán theo định luật Ohm DC:
      I = U / R (A), P = U * I (W), A = P * t (Wh & kWh)
    """
    i = u / r
    p_w = u * i
    a_wh = p_w * t_hours
    a_kwh = a_wh / 1000.0

    equip = select_mcb_and_fuse(i_tt_a=i, i_nk_ka=0.0)
    return save_calculation_record(
        module_id="Mạch DC - Định luật Ohm",
        module_name="Định luật Ohm DC & Công suất - Điện năng",
        user_inputs={
            "Điện áp nguồn U (V)": f"{round(u, 4)} V",
            "Điện trở tải R (Ω)": f"{round(r, 4)} Ω",
            "Thời gian làm việc t (giờ)": f"{round(t_hours, 4)} giờ"
        },
        calculation_results={
            "Cường độ dòng điện I (A)": f"{round(i, 4)} A",
            "Công suất tiêu thụ P (W)": f"{round(p_w, 4)} W",
            "Điện năng tiêu thụ A (Wh)": f"{round(a_wh, 4)} Wh",
            "Điện năng tiêu thụ A (kWh)": f"{round(a_kwh, 6)} kWh"
        },
        equipment_recommendation=equip
    )


def calc_wire_resistance(rho, l, s, temp=20.0, alpha=0.00393):
    """
    Tính điện trở dây dẫn và biến thiên theo nhiệt độ:
      R0 = rho * (l / S) tại 20 độ C
      RT = R0 * [1 + alpha * (T - 20)]
    """
    r_20 = rho * (l / s)
    r_temp = r_20 * (1.0 + alpha * (temp - 20.0))
    inc_pct = ((r_temp - r_20) / r_20) * 100.0 if r_20 > 0 else 0.0

    return save_calculation_record(
        module_id="Mạch DC - Điện trở dây dẫn",
        module_name="Điện trở dây dẫn & Biến thiên theo nhiệt độ",
        user_inputs={
            "Điện trở suất ρ (Ω·mm²/m)": f"{round(rho, 6)} Ω·mm²/m",
            "Chiều dài dây dẫn l (m)": f"{round(l, 3)} m",
            "Tiết diện dây dẫn S (mm²)": f"{round(s, 3)} mm²",
            "Nhiệt độ làm việc T (°C)": f"{round(temp, 2)} °C",
            "Hệ số nhiệt điện trở α (1/°C)": f"{round(alpha, 6)} /°C"
        },
        calculation_results={
            "Điện trở dây ở 20°C (R20)": f"{round(r_20, 6)} Ω",
            "Điện trở dây ở nhiệt độ làm việc R(T)": f"{round(r_temp, 6)} Ω",
            "Tỷ lệ biến thiên điện trở (%)": f"{round(inc_pct, 3)} %"
        },
        equipment_recommendation={
            "Đánh giá thông số dây dẫn": f"Dây tiết diện {s} mm² dài {l} m tại {temp}°C có điện trở {r_temp:.5f} Ω"
        }
    )


def calc_resistor_group(resistors_list, mode="series", u_supply=None):
    """
    Tính điện trở tương đương Rtd ghép nối tiếp hoặc song song.
    """
    mode_clean = mode.lower().strip()
    if mode_clean == "series":
        r_eq = sum(resistors_list)
        mode_vn = "Ghép nối tiếp"
    else:
        inv_sum = sum(1.0 / r for r in resistors_list)
        r_eq = 1.0 / inv_sum if inv_sum > 0 else 0.0
        mode_vn = "Ghép song song"

    results = {
        "Kiểu đấu nối điện trở": mode_vn,
        "Số lượng điện trở thành phần": f"{len(resistors_list)} điện trở",
        "Điện trở tương đương (Rtđ)": f"{round(r_eq, 6)} Ω"
    }
    equip = {"Thông số mạng điện trở": f"Điện trở tương đương Rtđ = {r_eq:.4f} Ω ({mode_vn})"}

    if u_supply is not None and u_supply > 0 and r_eq > 0:
        i_total = u_supply / r_eq
        p_total = u_supply * i_total
        results["Dòng điện tổng toàn mạch I (A)"] = f"{round(i_total, 4)} A"
        results["Công suất tiêu thụ tổng P (W)"] = f"{round(p_total, 4)} W"
        equip.update(select_mcb_and_fuse(i_tt_a=i_total))

    return save_calculation_record(
        module_id="Mạch DC - Ghép điện trở",
        module_name="Ghép Điện Trở Nối Tiếp / Song Song",
        user_inputs={
            "Danh sách các điện trở (Ω)": ", ".join(f"{r} Ω" for r in resistors_list),
            "Sơ đồ ghép nối": mode_vn,
            "Điện áp nguồn cấp U (V)": f"{u_supply} V" if u_supply else "Không cấp nguồn"
        },
        calculation_results=results,
        equipment_recommendation=equip
    )


def calc_battery_life(capacity_ah, voltage, power_load, dod=0.8, efficiency=0.9):
    """
    Tính thời gian xả ắc quy:
      t = (V * Ah * DoD * eta) / P (giờ)
    """
    usable_energy_wh = voltage * capacity_ah * dod * efficiency
    time_hours = usable_energy_wh / power_load
    discharge_current_a = power_load / (voltage * efficiency)

    equip = select_mcb_and_fuse(i_tt_a=discharge_current_a)
    equip["Thiết bị bảo vệ mạch ắc quy"] = f"Cầu chì DC / MCB DC bảo vệ nhánh ắc quy (Dòng xả: {discharge_current_a:.2f} A)"

    return save_calculation_record(
        module_id="Mạch DC - Pin và Ắc quy",
        module_name="Tính Thời Gian Xả Pin / Ắc Quy & Bảo Vệ",
        user_inputs={
            "Dung lượng bình ắc quy C (Ah)": f"{round(capacity_ah, 2)} Ah",
            "Điện áp định mức ắc quy V (V)": f"{round(voltage, 2)} V",
            "Công suất tải tiêu thụ P (W)": f"{round(power_load, 2)} W",
            "Hệ số xả sâu cho phép (DoD)": f"{round(dod * 100, 1)} % (Hệ số {round(dod, 3)})",
            "Hiệu suất bộ chuyển đổi (η)": f"{round(efficiency * 100, 1)} % (Hệ số {round(efficiency, 3)})"
        },
        calculation_results={
            "Điện năng khả dụng thực tế (Wh)": f"{round(usable_energy_wh, 2)} Wh",
            "Dòng điện xả từ ắc quy (A)": f"{round(discharge_current_a, 3)} A",
            "Thời gian duy trì cấp điện (giờ)": f"{round(time_hours, 3)} giờ",
            "Thời gian duy trì cấp điện (phút)": f"{round(time_hours * 60.0, 1)} phút"
        },
        equipment_recommendation=equip
    )


def calc_short_circuit(up, z_total, i_load_a=10.0):
    """
    Tính dòng ngắn mạch đơn giản và chọn MCB/Cầu chì.
    """
    i_nk_a = up / z_total
    i_nk_ka = i_nk_a / 1000.0
    equip = select_mcb_and_fuse(i_tt_a=i_load_a, i_nk_ka=i_nk_ka)

    return save_calculation_record(
        module_id="Mạch DC - Ngắn mạch và MCB",
        module_name="Tính Dòng Ngắn Mạch & Chọn MCB / Cầu Chì",
        user_inputs={
            "Điện áp pha Up (V)": f"{round(up, 2)} V",
            "Tổng trở mạch vòng ngắn mạch ZΣ (Ω)": f"{round(z_total, 5)} Ω",
            "Dòng điện làm việc của tải Itt (A)": f"{round(i_load_a, 2)} A"
        },
        calculation_results={
            "Dòng điện ngắn mạch Ink (A)": f"{round(i_nk_a, 2)} A",
            "Dòng điện ngắn mạch Ink (kA)": f"{round(i_nk_ka, 4)} kA",
            "Dòng định mức MCB tối thiểu (1.25 × Itt)": f"{round(1.25 * i_load_a, 2)} A"
        },
        equipment_recommendation=equip
    )
