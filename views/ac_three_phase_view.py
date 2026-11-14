"""
Module: views/ac_three_phase_view.py
Chức năng: Giao diện người dùng cho Phân hệ 2 - Mạch xoay chiều 3 pha (Sao/Tam giác, P-Q-S),
Động cơ không đồng bộ 3 pha (Chọn Contactor + Rơ le nhiệt), Máy biến áp và Xuất Báo Cáo.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from utils.validation import validate_float, validate_int, validate_ratio, ValidationError
from utils.exporter import format_record_as_text, export_record_to_file
from modules.ac_three_phase import (
    calc_3phase_relations,
    calc_3phase_power,
    calc_motor_params,
    calc_transformer_ratio
)


class ACThreePhaseView(ttk.Frame):
    def __init__(self, parent, on_calculation_done=None, on_send_current_to_line=None):
        super().__init__(parent, padding=12)
        self.on_calculation_done = on_calculation_done
        self.on_send_current_to_line = on_send_current_to_line
        self.last_record = None
        self._build_ui()

    def _build_ui(self):
        header_frame = ttk.Frame(self)
        header_frame.pack(fill="x", pady=(0, 8))

        header = ttk.Label(
            header_frame,
            text="PHÂN HỆ 2: MẠCH XOAY CHIỀU 3 PHA, ĐỘNG CƠ KĐB & TRA CỨU CONTACTOR + RƠ LE NHIỆT",
            style="ModuleHeader.TLabel"
        )
        header.pack(side="left")

        btn_export = ttk.Button(
            header_frame, text="Xuất Báo Cáo (.TXT / .CSV / .JSON)", command=self._export_current_report
        )
        btn_export.pack(side="right", padx=4)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="x", expand=False, pady=(0, 10))

        # Tab 1: Động cơ không đồng bộ 3 pha
        tab_motor = ttk.Frame(notebook, padding=10)
        notebook.add(tab_motor, text="1. Động Cơ 3 Pha & Chọn Khởi Động Từ")
        self._build_tab_motor(tab_motor)

        # Tab 2: Quan hệ Dòng & Áp Sao (Y) / Tam Giác (Δ)
        tab_rel = ttk.Frame(notebook, padding=10)
        notebook.add(tab_rel, text="2. Đấu Hình Sao (Y) / Tam Giác (Δ)")
        self._build_tab_relations(tab_rel)

        # Tab 3: Công suất 3 pha P, Q, S
        tab_pow = ttk.Frame(notebook, padding=10)
        notebook.add(tab_pow, text="3. Công Suất 3 Pha (P, Q, S)")
        self._build_tab_power(tab_pow)

        # Tab 4: Máy biến áp lý tưởng
        tab_tf = ttk.Frame(notebook, padding=10)
        notebook.add(tab_tf, text="4. Tỷ Số Máy Biến Áp")
        self._build_tab_transformer(tab_tf)

        # Khu vực hiển thị kết quả
        res_frame = ttk.LabelFrame(self, text="Kết Quả Tính Toán & Khuyến Nghị Bộ Khởi Động Từ (Contactor + Rơ le nhiệt)", padding=8)
        res_frame.pack(fill="both", expand=True)

        self.txt_result = tk.Text(
            res_frame, height=14, font=("Consolas", 10), bg="#0f172a", fg="#e2e8f0",
            insertbackground="white", relief="flat", padx=10, pady=8
        )
        self.txt_result.pack(fill="both", expand=True)
        self.txt_result.insert("1.0", "Nhập thông số động cơ 3 pha hoặc mạch 3 pha và nhấn nút 'Tính Toán'...")
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

    def _export_current_report(self):
        if not self.last_record:
            messagebox.showwarning("Chưa có dữ liệu", "Vui lòng thực hiện ít nhất một phép tính trước khi xuất báo cáo!")
            return
        filepath = filedialog.asksaveasfilename(
            title="Lưu Báo Cáo Kỹ Thuật Điện",
            defaultextension=".txt",
            initialfile="BaoCaoKyThuatDien.txt",
            filetypes=[
                ("Báo cáo văn bản (*.txt)", "*.txt"),
                ("Bảng tính Excel CSV (*.csv)", "*.csv"),
                ("Tệp dữ liệu JSON (*.json)", "*.json")
            ]
        )
        if filepath:
            export_record_to_file(self.last_record, filepath)
            messagebox.showinfo("Xuất báo cáo thành công", f"Đã lưu báo cáo kết quả tại: {filepath}")

    # --- TAB 1: ĐỘNG CƠ 3 PHA ---
    def _build_tab_motor(self, parent):
        ttk.Label(parent, text="Công suất cơ định mức Pđm (kW):").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.ent_m_pkw = ttk.Entry(parent, width=15)
        self.ent_m_pkw.insert(0, "11.0")
        self.ent_m_pkw.grid(row=0, column=1, padx=5, pady=4)

        ttk.Label(parent, text="Điện áp dây Ud (V):").grid(row=0, column=2, sticky="w", padx=5, pady=4)
        self.ent_m_ud = ttk.Entry(parent, width=15)
        self.ent_m_ud.insert(0, "380")
        self.ent_m_ud.grid(row=0, column=3, padx=5, pady=4)

        ttk.Label(parent, text="Tần số lưới f (Hz):").grid(row=0, column=4, sticky="w", padx=5, pady=4)
        self.ent_m_f = ttk.Entry(parent, width=12)
        self.ent_m_f.insert(0, "50")
        self.ent_m_f.grid(row=0, column=5, padx=5, pady=4)

        ttk.Label(parent, text="Số đôi cực từ p (ví dụ 2 -> 4 cực):").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        self.ent_m_poles = ttk.Entry(parent, width=15)
        self.ent_m_poles.insert(0, "2")
        self.ent_m_poles.grid(row=1, column=1, padx=5, pady=4)

        ttk.Label(parent, text="Tốc độ quay thực tế n (vòng/phút):").grid(row=1, column=2, sticky="w", padx=5, pady=4)
        self.ent_m_n = ttk.Entry(parent, width=15)
        self.ent_m_n.insert(0, "1450")
        self.ent_m_n.grid(row=1, column=3, padx=5, pady=4)

        ttk.Label(parent, text="Hệ số công suất cosφ (0 - 1):").grid(row=2, column=0, sticky="w", padx=5, pady=4)
        self.ent_m_cosphi = ttk.Entry(parent, width=15)
        self.ent_m_cosphi.insert(0, "0.85")
        self.ent_m_cosphi.grid(row=2, column=1, padx=5, pady=4)

        ttk.Label(parent, text="Hiệu suất động cơ η (0 - 1):").grid(row=2, column=2, sticky="w", padx=5, pady=4)
        self.ent_m_eff = ttk.Entry(parent, width=15)
        self.ent_m_eff.insert(0, "0.89")
        self.ent_m_eff.grid(row=2, column=3, padx=5, pady=4)

        btn_calc = ttk.Button(
            parent, text="Tính Động Cơ & Chọn Contactor + Rơ Le Nhiệt",
            style="Accent.TButton", command=self._run_motor
        )
        btn_calc.grid(row=3, column=0, columnspan=4, sticky="ew", padx=5, pady=6)

        btn_transfer = ttk.Button(
            parent, text="Chuyển sang Phân hệ 4 (Tính Cáp & Sụt Áp)",
            command=self._transfer_to_line_module
        )
        btn_transfer.grid(row=3, column=4, columnspan=2, sticky="ew", padx=5, pady=6)

    def _run_motor(self):
        try:
            p_kw = validate_float(self.ent_m_pkw.get(), "Công suất định mức Pđm (kW)")
            u_d = validate_float(self.ent_m_ud.get(), "Điện áp dây Ud (V)")
            f = validate_float(self.ent_m_f.get(), "Tần số f (Hz)")
            p_pairs = validate_int(self.ent_m_poles.get(), "Số đôi cực p")
            n_real = validate_float(self.ent_m_n.get(), "Tốc độ thực tế n (vòng/phút)")
            cos_phi = validate_ratio(self.ent_m_cosphi.get(), "Hệ số công suất cosφ")
            eff = validate_ratio(self.ent_m_eff.get(), "Hiệu suất η")

            rec = calc_motor_params(f, p_pairs, n_real, p_kw, u_d, cos_phi, eff)
            self._display_record(rec)
        except (ValidationError, ValueError) as e:
            messagebox.showerror("Lỗi nhập liệu", str(e))

    def _transfer_to_line_module(self):
        try:
            p_kw = validate_float(self.ent_m_pkw.get(), "Công suất định mức Pđm (kW)")
            u_d = validate_float(self.ent_m_ud.get(), "Điện áp dây Ud (V)")
            cos_phi = validate_ratio(self.ent_m_cosphi.get(), "Hệ số công suất cosφ")
            eff = validate_ratio(self.ent_m_eff.get(), "Hiệu suất η")
            p_elec_kw = round(p_kw / eff, 3)
            if self.on_send_current_to_line:
                self.on_send_current_to_line(p_elec_kw, u_d, cos_phi, "3P")
        except (ValidationError, ValueError) as e:
            messagebox.showerror("Lỗi dữ liệu", str(e))

    # --- TAB 2: QUAN HỆ SAO / TAM GIÁC ---
    def _build_tab_relations(self, parent):
        ttk.Label(parent, text="Điện áp dây Ud (V):").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.ent_rel_ud = ttk.Entry(parent, width=18)
        self.ent_rel_ud.insert(0, "380")
        self.ent_rel_ud.grid(row=0, column=1, padx=5, pady=4)

        ttk.Label(parent, text="Dòng điện dây Id (A):").grid(row=0, column=2, sticky="w", padx=5, pady=4)
        self.ent_rel_id = ttk.Entry(parent, width=18)
        self.ent_rel_id.insert(0, "25")
        self.ent_rel_id.grid(row=0, column=3, padx=5, pady=4)

        ttk.Label(parent, text="Kiểu đấu dây 3 pha:").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        self.cmb_rel_conn = ttk.Combobox(parent, values=["Y - Đấu Hình Sao", "Δ - Đấu Hình Tam Giác"], state="readonly", width=22)
        self.cmb_rel_conn.current(0)
        self.cmb_rel_conn.grid(row=1, column=1, padx=5, pady=4)

        btn = ttk.Button(parent, text="Tính Up, Ip & Chọn Contactor", style="Accent.TButton", command=self._run_relations)
        btn.grid(row=1, column=2, columnspan=2, sticky="ew", padx=5, pady=6)

    def _run_relations(self):
        try:
            ud = validate_float(self.ent_rel_ud.get(), "Điện áp dây Ud (V)")
            id_a = validate_float(self.ent_rel_id.get(), "Dòng điện dây Id (A)")
            conn = "Y" if self.cmb_rel_conn.get().startswith("Y") else "Delta"
            rec = calc_3phase_relations(ud, id_a, conn)
            self._display_record(rec)
        except (ValidationError, ValueError) as e:
            messagebox.showerror("Lỗi nhập liệu", str(e))

    # --- TAB 3: CÔNG SUẤT 3 PHA ---
    def _build_tab_power(self, parent):
        ttk.Label(parent, text="Điện áp dây Ud (V):").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.ent_pow_ud = ttk.Entry(parent, width=18)
        self.ent_pow_ud.insert(0, "380")
        self.ent_pow_ud.grid(row=0, column=1, padx=5, pady=4)

        ttk.Label(parent, text="Dòng điện dây Id (A):").grid(row=0, column=2, sticky="w", padx=5, pady=4)
        self.ent_pow_id = ttk.Entry(parent, width=18)
        self.ent_pow_id.insert(0, "32")
        self.ent_pow_id.grid(row=0, column=3, padx=5, pady=4)

        ttk.Label(parent, text="Hệ số công suất cosφ:").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        self.ent_pow_cos = ttk.Entry(parent, width=18)
        self.ent_pow_cos.insert(0, "0.85")
        self.ent_pow_cos.grid(row=1, column=1, padx=5, pady=4)

        btn = ttk.Button(parent, text="Tính Công Suất P, Q, S (3 Pha)", style="Accent.TButton", command=self._run_power)
        btn.grid(row=1, column=2, columnspan=2, sticky="ew", padx=5, pady=6)

    def _run_power(self):
        try:
            ud = validate_float(self.ent_pow_ud.get(), "Điện áp dây Ud (V)")
            id_a = validate_float(self.ent_pow_id.get(), "Dòng điện dây Id (A)")
            cos_phi = validate_ratio(self.ent_pow_cos.get(), "Hệ số công suất cosφ")
            rec = calc_3phase_power(ud, id_a, cos_phi)
            self._display_record(rec)
        except (ValidationError, ValueError) as e:
            messagebox.showerror("Lỗi nhập liệu", str(e))

    # --- TAB 4: MÁY BIẾN ÁP ---
    def _build_tab_transformer(self, parent):
        ttk.Label(parent, text="Điện áp sơ cấp U1 (V):").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.ent_tf_u1 = ttk.Entry(parent, width=16)
        self.ent_tf_u1.insert(0, "22000")
        self.ent_tf_u1.grid(row=0, column=1, padx=5, pady=4)

        ttk.Label(parent, text="Điện áp thứ cấp U2 (V):").grid(row=0, column=2, sticky="w", padx=5, pady=4)
        self.ent_tf_u2 = ttk.Entry(parent, width=16)
        self.ent_tf_u2.insert(0, "400")
        self.ent_tf_u2.grid(row=0, column=3, padx=5, pady=4)

        ttk.Label(parent, text="Số vòng dây sơ cấp N1 (vòng):").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        self.ent_tf_n1 = ttk.Entry(parent, width=16)
        self.ent_tf_n1.insert(0, "1100")
        self.ent_tf_n1.grid(row=1, column=1, padx=5, pady=4)

        ttk.Label(parent, text="Dòng điện sơ cấp I1 (A):").grid(row=1, column=2, sticky="w", padx=5, pady=4)
        self.ent_tf_i1 = ttk.Entry(parent, width=16)
        self.ent_tf_i1.insert(0, "10")
        self.ent_tf_i1.grid(row=1, column=3, padx=5, pady=4)

        btn = ttk.Button(parent, text="Tính Tỷ Số Biến Áp k, N2 & I2", style="Accent.TButton", command=self._run_transformer)
        btn.grid(row=2, column=0, columnspan=4, sticky="ew", padx=5, pady=6)

    def _run_transformer(self):
        try:
            u1 = validate_float(self.ent_tf_u1.get(), "Điện áp sơ cấp U1 (V)")
            u2 = validate_float(self.ent_tf_u2.get(), "Điện áp thứ cấp U2 (V)")
            n1 = validate_float(self.ent_tf_n1.get(), "Số vòng sơ cấp N1")
            i1 = validate_float(self.ent_tf_i1.get(), "Dòng sơ cấp I1 (A)")
            rec = calc_transformer_ratio(u1, u2, n1, i1)
            self._display_record(rec)
        except (ValidationError, ValueError) as e:
            messagebox.showerror("Lỗi nhập liệu", str(e))
