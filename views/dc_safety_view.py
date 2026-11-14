"""
Module: views/dc_safety_view.py
Chức năng: Giao diện người dùng cho Phân hệ 1 - Mạch điện một chiều (DC), Điện trở dây dẫn, Ghép điện trở, Ắc quy & Ngắn mạch/MCB.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from utils.validation import validate_float, validate_ratio, validate_float_list, ValidationError
from utils.exporter import format_record_as_text
from modules.dc_safety import (
    calc_dc_ohm,
    calc_wire_resistance,
    calc_resistor_group,
    calc_battery_life,
    calc_short_circuit
)


class DCSafetyView(ttk.Frame):
    def __init__(self, parent, on_calculation_done=None):
        super().__init__(parent, padding=12)
        self.on_calculation_done = on_calculation_done
        self.last_record = None
        self._build_ui()

    def _build_ui(self):
        header = ttk.Label(
            self,
            text="PHÂN HỆ 1: MẠCH ĐIỆN MỘT CHIỀU (DC), ẮC QUY & BẢO VỆ NGẮN MẠCH (MCB / CẦU CHÌ)",
            style="ModuleHeader.TLabel"
        )
        header.pack(anchor="w", pady=(0, 8))

        notebook = ttk.Notebook(self)
        notebook.pack(fill="x", expand=False, pady=(0, 10))

        # Tab 1: Định luật Ohm DC
        tab_ohm = ttk.Frame(notebook, padding=10)
        notebook.add(tab_ohm, text="1. Định luật Ohm DC")
        self._build_tab_ohm(tab_ohm)

        # Tab 2: Điện trở dây dẫn theo nhiệt độ
        tab_wire = ttk.Frame(notebook, padding=10)
        notebook.add(tab_wire, text="2. Điện trở dây dẫn R(T)")
        self._build_tab_wire(tab_wire)

        # Tab 3: Ghép điện trở nối tiếp / song song
        tab_group = ttk.Frame(notebook, padding=10)
        notebook.add(tab_group, text="3. Ghép Điện trở (Rtđ)")
        self._build_tab_group(tab_group)

        # Tab 4: Thời gian xả Pin / Ắc quy
        tab_bat = ttk.Frame(notebook, padding=10)
        notebook.add(tab_bat, text="4. Pin & Ắc quy (DoD)")
        self._build_tab_battery(tab_bat)

        # Tab 5: Dòng ngắn mạch & Chọn MCB/Cầu chì
        tab_sc = ttk.Frame(notebook, padding=10)
        notebook.add(tab_sc, text="5. Ngắn mạch & Chọn MCB")
        self._build_tab_short_circuit(tab_sc)

        # Khu vực hiển thị kết quả
        res_frame = ttk.LabelFrame(self, text="Kết Quả Tính Toán & Khuyến Nghị Khí Cụ Điện", padding=8)
        res_frame.pack(fill="both", expand=True)

        self.txt_result = tk.Text(
            res_frame, height=14, font=("Consolas", 10), bg="#0f172a", fg="#e2e8f0",
            insertbackground="white", relief="flat", padx=10, pady=8
        )
        self.txt_result.pack(fill="both", expand=True)
        self.txt_result.insert("1.0", "Chọn một thẻ chức năng phía trên, nhập thông số và nhấn nút 'Tính Toán'...")
        self.txt_result.config(state="disabled")

    def _display_record(self, record):
        self.last_record = record
        text = format_record_as_text(record)
        self.txt_result.config(state="normal")
        self.txt_result.delete("1.0", "end")
        self.txt_result.insert("1.0", text)
        self.txt_result.config(state="disabled")
        if self.on_calculation_done:
            self.on_calculation_done(record)

    # --- TAB 1: OHM DC ---
    def _build_tab_ohm(self, parent):
        ttk.Label(parent, text="Điện áp U (V):").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.ent_ohm_u = ttk.Entry(parent, width=18)
        self.ent_ohm_u.insert(0, "24")
        self.ent_ohm_u.grid(row=0, column=1, padx=5, pady=4)

        ttk.Label(parent, text="Điện trở tải R (Ω):").grid(row=0, column=2, sticky="w", padx=5, pady=4)
        self.ent_ohm_r = ttk.Entry(parent, width=18)
        self.ent_ohm_r.insert(0, "4.8")
        self.ent_ohm_r.grid(row=0, column=3, padx=5, pady=4)

        ttk.Label(parent, text="Thời gian làm việc t (giờ):").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        self.ent_ohm_t = ttk.Entry(parent, width=18)
        self.ent_ohm_t.insert(0, "5")
        self.ent_ohm_t.grid(row=1, column=1, padx=5, pady=4)

        btn = ttk.Button(parent, text="Tính Định Luật Ohm & Chọn MCB", style="Accent.TButton", command=self._run_ohm)
        btn.grid(row=1, column=2, columnspan=2, sticky="ew", padx=5, pady=6)

    def _run_ohm(self):
        try:
            u = validate_float(self.ent_ohm_u.get(), "Điện áp U (V)")
            r = validate_float(self.ent_ohm_r.get(), "Điện trở R (Ω)")
            t = validate_float(self.ent_ohm_t.get(), "Thời gian t (giờ)")
            rec = calc_dc_ohm(u, r, t)
            self._display_record(rec)
        except (ValidationError, ValueError) as e:
            messagebox.showerror("Lỗi nhập liệu", str(e))

    # --- TAB 2: ĐIỆN TRỞ DÂY DẪN ---
    def _build_tab_wire(self, parent):
        ttk.Label(parent, text="Vật liệu dây dẫn:").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.cmb_wire_mat = ttk.Combobox(
            parent, values=["Đồng (ρ = 0.0172 Ω·mm²/m)", "Nhôm (ρ = 0.0280 Ω·mm²/m)", "Tùy chỉnh"], state="readonly", width=24
        )
        self.cmb_wire_mat.current(0)
        self.cmb_wire_mat.grid(row=0, column=1, padx=5, pady=4)
        self.cmb_wire_mat.bind("<<ComboboxSelected>>", self._on_wire_mat_change)

        ttk.Label(parent, text="Điện trở suất ρ (Ω·mm²/m):").grid(row=0, column=2, sticky="w", padx=5, pady=4)
        self.ent_wire_rho = ttk.Entry(parent, width=16)
        self.ent_wire_rho.insert(0, "0.0172")
        self.ent_wire_rho.grid(row=0, column=3, padx=5, pady=4)

        ttk.Label(parent, text="Chiều dài dây dẫn l (m):").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        self.ent_wire_l = ttk.Entry(parent, width=18)
        self.ent_wire_l.insert(0, "100")
        self.ent_wire_l.grid(row=1, column=1, padx=5, pady=4)

        ttk.Label(parent, text="Tiết diện dây dẫn S (mm²):").grid(row=1, column=2, sticky="w", padx=5, pady=4)
        self.ent_wire_s = ttk.Entry(parent, width=16)
        self.ent_wire_s.insert(0, "4.0")
        self.ent_wire_s.grid(row=1, column=3, padx=5, pady=4)

        ttk.Label(parent, text="Nhiệt độ làm việc T (°C):").grid(row=2, column=0, sticky="w", padx=5, pady=4)
        self.ent_wire_temp = ttk.Entry(parent, width=18)
        self.ent_wire_temp.insert(0, "70")
        self.ent_wire_temp.grid(row=2, column=1, padx=5, pady=4)

        ttk.Label(parent, text="Hệ số nhiệt α (1/°C):").grid(row=2, column=2, sticky="w", padx=5, pady=4)
        self.ent_wire_alpha = ttk.Entry(parent, width=16)
        self.ent_wire_alpha.insert(0, "0.00393")
        self.ent_wire_alpha.grid(row=2, column=3, padx=5, pady=4)

        btn = ttk.Button(parent, text="Tính Điện Trở Dây Dẫn R(T)", style="Accent.TButton", command=self._run_wire)
        btn.grid(row=3, column=0, columnspan=4, sticky="ew", padx=5, pady=6)

    def _on_wire_mat_change(self, _event=None):
        sel = self.cmb_wire_mat.get()
        if "Đồng" in sel:
            self.ent_wire_rho.delete(0, "end")
            self.ent_wire_rho.insert(0, "0.0172")
            self.ent_wire_alpha.delete(0, "end")
            self.ent_wire_alpha.insert(0, "0.00393")
        elif "Nhôm" in sel:
            self.ent_wire_rho.delete(0, "end")
            self.ent_wire_rho.insert(0, "0.0280")
            self.ent_wire_alpha.delete(0, "end")
            self.ent_wire_alpha.insert(0, "0.00403")

    def _run_wire(self):
        try:
            rho = validate_float(self.ent_wire_rho.get(), "Điện trở suất ρ")
            l_m = validate_float(self.ent_wire_l.get(), "Chiều dài dây l (m)")
            s_mm2 = validate_float(self.ent_wire_s.get(), "Tiết diện dây S (mm²)")
            temp = validate_float(self.ent_wire_temp.get(), "Nhiệt độ T (°C)", allow_zero=True, positive_only=False)
            alpha = validate_float(self.ent_wire_alpha.get(), "Hệ số nhiệt α")
            rec = calc_wire_resistance(rho, l_m, s_mm2, temp, alpha)
            self._display_record(rec)
        except (ValidationError, ValueError) as e:
            messagebox.showerror("Lỗi nhập liệu", str(e))

    # --- TAB 3: GHÉP ĐIỆN TRỞ ---
    def _build_tab_group(self, parent):
        ttk.Label(parent, text="Danh sách điện trở (Ω, cách nhau dấu phẩy):").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.ent_grp_list = ttk.Entry(parent, width=32)
        self.ent_grp_list.insert(0, "10, 20, 30")
        self.ent_grp_list.grid(row=0, column=1, columnspan=2, sticky="ew", padx=5, pady=4)

        ttk.Label(parent, text="Sơ đồ ghép nối:").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        self.cmb_grp_mode = ttk.Combobox(parent, values=["Ghép nối tiếp", "Ghép song song"], state="readonly", width=22)
        self.cmb_grp_mode.current(0)
        self.cmb_grp_mode.grid(row=1, column=1, sticky="w", padx=5, pady=4)

        ttk.Label(parent, text="Điện áp nguồn cấp U (V - Tùy chọn):").grid(row=2, column=0, sticky="w", padx=5, pady=4)
        self.ent_grp_u = ttk.Entry(parent, width=18)
        self.ent_grp_u.insert(0, "120")
        self.ent_grp_u.grid(row=2, column=1, sticky="w", padx=5, pady=4)

        btn = ttk.Button(parent, text="Tính Điện Trở Tương Đương (Rtđ)", style="Accent.TButton", command=self._run_group)
        btn.grid(row=2, column=2, sticky="ew", padx=5, pady=6)

    def _run_group(self):
        try:
            r_list = validate_float_list(self.ent_grp_list.get(), "Danh sách điện trở")
            mode = "series" if "nối tiếp" in self.cmb_grp_mode.get().lower() else "parallel"
            u_str = self.ent_grp_u.get().strip()
            u_val = validate_float(u_str, "Điện áp nguồn U (V)") if u_str else None
            rec = calc_resistor_group(r_list, mode, u_val)
            self._display_record(rec)
        except (ValidationError, ValueError) as e:
            messagebox.showerror("Lỗi nhập liệu", str(e))

    # --- TAB 4: PIN & ẮC QUY ---
    def _build_tab_battery(self, parent):
        ttk.Label(parent, text="Dung lượng bình C (Ah):").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.ent_bat_ah = ttk.Entry(parent, width=16)
        self.ent_bat_ah.insert(0, "100")
        self.ent_bat_ah.grid(row=0, column=1, padx=5, pady=4)

        ttk.Label(parent, text="Điện áp bình V (V):").grid(row=0, column=2, sticky="w", padx=5, pady=4)
        self.ent_bat_v = ttk.Entry(parent, width=16)
        self.ent_bat_v.insert(0, "12")
        self.ent_bat_v.grid(row=0, column=3, padx=5, pady=4)

        ttk.Label(parent, text="Công suất tải tiêu thụ P (W):").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        self.ent_bat_p = ttk.Entry(parent, width=16)
        self.ent_bat_p.insert(0, "200")
        self.ent_bat_p.grid(row=1, column=1, padx=5, pady=4)

        ttk.Label(parent, text="Hệ số xả sâu DoD (0.1 - 1.0):").grid(row=1, column=2, sticky="w", padx=5, pady=4)
        self.ent_bat_dod = ttk.Entry(parent, width=16)
        self.ent_bat_dod.insert(0, "0.8")
        self.ent_bat_dod.grid(row=1, column=3, padx=5, pady=4)

        ttk.Label(parent, text="Hiệu suất bộ đổi điện η (0.1 - 1.0):").grid(row=2, column=0, sticky="w", padx=5, pady=4)
        self.ent_bat_eff = ttk.Entry(parent, width=16)
        self.ent_bat_eff.insert(0, "0.9")
        self.ent_bat_eff.grid(row=2, column=1, padx=5, pady=4)

        btn = ttk.Button(parent, text="Tính Thời Gian Xả Ắc Quy & Chọn Bảo Vệ", style="Accent.TButton", command=self._run_battery)
        btn.grid(row=2, column=2, columnspan=2, sticky="ew", padx=5, pady=6)

    def _run_battery(self):
        try:
            ah = validate_float(self.ent_bat_ah.get(), "Dung lượng ắc quy (Ah)")
            v = validate_float(self.ent_bat_v.get(), "Điện áp ắc quy (V)")
            p = validate_float(self.ent_bat_p.get(), "Công suất tải P (W)")
            dod = validate_ratio(self.ent_bat_dod.get(), "Hệ số xả sâu DoD")
            eff = validate_ratio(self.ent_bat_eff.get(), "Hiệu suất η")
            rec = calc_battery_life(ah, v, p, dod, eff)
            self._display_record(rec)
        except (ValidationError, ValueError) as e:
            messagebox.showerror("Lỗi nhập liệu", str(e))

    # --- TAB 5: NGẮN MẠCH & CHỌN MCB ---
    def _build_tab_short_circuit(self, parent):
        ttk.Label(parent, text="Điện áp pha Up (V):").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.ent_sc_up = ttk.Entry(parent, width=16)
        self.ent_sc_up.insert(0, "220")
        self.ent_sc_up.grid(row=0, column=1, padx=5, pady=4)

        ttk.Label(parent, text="Tổng trở mạch vòng ngắn mạch ZΣ (Ω):").grid(row=0, column=2, sticky="w", padx=5, pady=4)
        self.ent_sc_z = ttk.Entry(parent, width=16)
        self.ent_sc_z.insert(0, "0.045")
        self.ent_sc_z.grid(row=0, column=3, padx=5, pady=4)

        ttk.Label(parent, text="Dòng điện làm việc tính toán Itt (A):").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        self.ent_sc_itt = ttk.Entry(parent, width=16)
        self.ent_sc_itt.insert(0, "18.5")
        self.ent_sc_itt.grid(row=1, column=1, padx=5, pady=4)

        btn = ttk.Button(parent, text="Tính Dòng Ngắn Mạch Ink & Tra Chọn MCB / Cầu Chì", style="Accent.TButton", command=self._run_sc)
        btn.grid(row=1, column=2, columnspan=2, sticky="ew", padx=5, pady=6)

    def _run_sc(self):
        try:
            up = validate_float(self.ent_sc_up.get(), "Điện áp pha Up (V)")
            z_tot = validate_float(self.ent_sc_z.get(), "Tổng trở ngắn mạch ZΣ (Ω)")
            i_tt = validate_float(self.ent_sc_itt.get(), "Dòng điện làm việc Itt (A)")
            rec = calc_short_circuit(up, z_tot, i_tt)
            self._display_record(rec)
        except (ValidationError, ValueError) as e:
            messagebox.showerror("Lỗi nhập liệu", str(e))
