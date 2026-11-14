"""
Module: views/ac_single_phase_view.py
Chức năng: Giao diện người dùng cho Phân hệ 3 - Trở kháng & Công suất mạch RLC 1 pha,
Tính bù công suất phản kháng cosφ (chọn Tụ bù kVAR & Aptomat bảo vệ tụ), kèm Công cụ đổi nhanh đơn vị kỹ thuật điện.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from utils.validation import validate_float, validate_ratio, ValidationError
from utils.exporter import format_record_as_text
from modules.ac_single_phase import (
    calc_impedance_and_power,
    calc_reactive_compensation,
    convert_electrical_unit
)


class ACSinglePhaseView(ttk.Frame):
    def __init__(self, parent, on_calculation_done=None):
        super().__init__(parent, padding=12)
        self.on_calculation_done = on_calculation_done
        self.last_record = None
        self._build_ui()

    def _build_ui(self):
        header = ttk.Label(
            self,
            text="PHÂN HỆ 3: MẠCH XOAY CHIỀU 1 PHA (RLC), BÙ CÔNG SUẤT PHẢN KHÁNG COSφ & CHỌN TỤ BÙ",
            style="ModuleHeader.TLabel"
        )
        header.pack(anchor="w", pady=(0, 8))

        top_container = ttk.Frame(self)
        top_container.pack(fill="x", pady=(0, 10))

        notebook = ttk.Notebook(top_container)
        notebook.pack(side="left", fill="both", expand=True, padx=(0, 8))

        # Tab 1: Bù công suất phản kháng cosφ & Chọn Tụ bù
        tab_comp = ttk.Frame(notebook, padding=10)
        notebook.add(tab_comp, text="1. Tính Bù cosφ & Chọn Tụ Bù + CB")
        self._build_tab_compensation(tab_comp)

        # Tab 2: Trở kháng & Công suất mạch RLC 1 pha
        tab_rlc = ttk.Frame(notebook, padding=10)
        notebook.add(tab_rlc, text="2. Mạch RLC Nối Tiếp 1 Pha")
        self._build_tab_rlc(tab_rlc)

        # Công cụ phụ trợ: Chuyển đổi nhanh đơn vị kỹ thuật điện (bên phải)
        conv_frame = ttk.LabelFrame(top_container, text="Công Cụ Đổi Đơn Vị Nhanh", padding=10)
        conv_frame.pack(side="right", fill="y")
        self._build_unit_converter(conv_frame)

        # Khu vực hiển thị kết quả
        res_frame = ttk.LabelFrame(self, text="Kết Quả Tính Toán & Khuyến Nghị Tụ Bù / Aptomat Bảo Vệ Tụ", padding=8)
        res_frame.pack(fill="both", expand=True)

        self.txt_result = tk.Text(
            res_frame, height=14, font=("Consolas", 10), bg="#0f172a", fg="#e2e8f0",
            insertbackground="white", relief="flat", padx=10, pady=8
        )
        self.txt_result.pack(fill="both", expand=True)
        self.txt_result.insert("1.0", "Nhập thông số bù công suất phản kháng hoặc mạch RLC 1 pha và nhấn nút 'Tính Toán'...")
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

    # --- TAB 1: BÙ CÔNG SUẤT PHẢN KHÁNG ---
    def _build_tab_compensation(self, parent):
        ttk.Label(parent, text="Công suất tác dụng P (kW):").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.ent_c_pkw = ttk.Entry(parent, width=16)
        self.ent_c_pkw.insert(0, "50.0")
        self.ent_c_pkw.grid(row=0, column=1, padx=5, pady=4)

        ttk.Label(parent, text="Điện áp lưới U (V):").grid(row=0, column=2, sticky="w", padx=5, pady=4)
        self.ent_c_u = ttk.Entry(parent, width=16)
        self.ent_c_u.insert(0, "220")
        self.ent_c_u.grid(row=0, column=3, padx=5, pady=4)

        ttk.Label(parent, text="Hệ số cosφ1 trước khi bù:").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        self.ent_c_cos1 = ttk.Entry(parent, width=16)
        self.ent_c_cos1.insert(0, "0.70")
        self.ent_c_cos1.grid(row=1, column=1, padx=5, pady=4)

        ttk.Label(parent, text="Hệ số cosφ2 mục tiêu (sau bù):").grid(row=1, column=2, sticky="w", padx=5, pady=4)
        self.ent_c_cos2 = ttk.Entry(parent, width=16)
        self.ent_c_cos2.insert(0, "0.95")
        self.ent_c_cos2.grid(row=1, column=3, padx=5, pady=4)

        ttk.Label(parent, text="Tần số lưới f (Hz):").grid(row=2, column=0, sticky="w", padx=5, pady=4)
        self.ent_c_f = ttk.Entry(parent, width=16)
        self.ent_c_f.insert(0, "50")
        self.ent_c_f.grid(row=2, column=1, padx=5, pady=4)

        btn = ttk.Button(
            parent, text="Tính Dung Lượng Bù Qc (kVAR), C (µF) & Chọn Tụ Bù",
            style="Accent.TButton", command=self._run_compensation
        )
        btn.grid(row=2, column=2, columnspan=2, sticky="ew", padx=5, pady=6)

    def _run_compensation(self):
        try:
            p_kw = validate_float(self.ent_c_pkw.get(), "Công suất P (kW)")
            u = validate_float(self.ent_c_u.get(), "Điện áp U (V)")
            cos1 = validate_ratio(self.ent_c_cos1.get(), "Hệ số cosφ1 ban đầu")
            cos2 = validate_ratio(self.ent_c_cos2.get(), "Hệ số cosφ2 mục tiêu")
            f = validate_float(self.ent_c_f.get(), "Tần số f (Hz)")
            rec = calc_reactive_compensation(p_kw, cos1, cos2, f, u)
            self._display_record(rec)
        except (ValidationError, ValueError) as e:
            messagebox.showerror("Lỗi nhập liệu", str(e))

    # --- TAB 2: MẠCH RLC 1 PHA ---
    def _build_tab_rlc(self, parent):
        ttk.Label(parent, text="Điện áp nguồn U (V):").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.ent_rlc_u = ttk.Entry(parent, width=15)
        self.ent_rlc_u.insert(0, "220")
        self.ent_rlc_u.grid(row=0, column=1, padx=5, pady=4)

        ttk.Label(parent, text="Tần số f (Hz):").grid(row=0, column=2, sticky="w", padx=5, pady=4)
        self.ent_rlc_f = ttk.Entry(parent, width=15)
        self.ent_rlc_f.insert(0, "50")
        self.ent_rlc_f.grid(row=0, column=3, padx=5, pady=4)

        ttk.Label(parent, text="Điện trở R (Ω):").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        self.ent_rlc_r = ttk.Entry(parent, width=15)
        self.ent_rlc_r.insert(0, "12")
        self.ent_rlc_r.grid(row=1, column=1, padx=5, pady=4)

        ttk.Label(parent, text="Điện cảm L (mH):").grid(row=1, column=2, sticky="w", padx=5, pady=4)
        self.ent_rlc_l = ttk.Entry(parent, width=15)
        self.ent_rlc_l.insert(0, "50")
        self.ent_rlc_l.grid(row=1, column=3, padx=5, pady=4)

        ttk.Label(parent, text="Điện dung C (µF):").grid(row=2, column=0, sticky="w", padx=5, pady=4)
        self.ent_rlc_c = ttk.Entry(parent, width=15)
        self.ent_rlc_c.insert(0, "300")
        self.ent_rlc_c.grid(row=2, column=1, padx=5, pady=4)

        btn = ttk.Button(
            parent, text="Tính Trở Kháng Z, Góc φ & Công Suất 1 Pha",
            style="Accent.TButton", command=self._run_rlc
        )
        btn.grid(row=2, column=2, columnspan=2, sticky="ew", padx=5, pady=6)

    def _run_rlc(self):
        try:
            u = validate_float(self.ent_rlc_u.get(), "Điện áp U (V)")
            f = validate_float(self.ent_rlc_f.get(), "Tần số f (Hz)")
            r = validate_float(self.ent_rlc_r.get(), "Điện trở R (Ω)", allow_zero=True)
            l_mh = validate_float(self.ent_rlc_l.get(), "Điện cảm L (mH)", allow_zero=True)
            c_uf = validate_float(self.ent_rlc_c.get(), "Điện dung C (µF)", allow_zero=True)
            rec = calc_impedance_and_power(u, r, l_mh, c_uf, f)
            self._display_record(rec)
        except (ValidationError, ValueError) as e:
            messagebox.showerror("Lỗi nhập liệu", str(e))

    # --- CÔNG CỤ ĐỔI ĐƠN VỊ NHANH ---
    def _build_unit_converter(self, parent):
        ttk.Label(parent, text="Giá trị cần đổi:").pack(anchor="w", pady=(0, 2))
        self.ent_conv_val = ttk.Entry(parent, width=20)
        self.ent_conv_val.insert(0, "15")
        self.ent_conv_val.pack(fill="x", pady=(0, 6))

        ttk.Label(parent, text="Chọn kiểu quy đổi:").pack(anchor="w", pady=(0, 2))
        self.cmb_conv_type = ttk.Combobox(
            parent,
            values=[
                "kW sang Mã lực (HP)", "Mã lực (HP) sang kW", "W sang kW", "kW sang W",
                "A sang kA", "kA sang A", "µF sang mF", "mF sang µF",
                "µF sang F", "F sang µF", "mH sang H", "H sang mH"
            ],
            state="readonly", width=20
        )
        self.cmb_conv_type.current(0)
        self.cmb_conv_type.pack(fill="x", pady=(0, 6))

        btn_conv = ttk.Button(parent, text="Chuyển Đổi Đơn Vị", command=self._run_unit_conv)
        btn_conv.pack(fill="x", pady=(0, 6))

        self.lbl_conv_res = ttk.Label(parent, text="15 kW = 20.1153 HP", font=("Segoe UI", 9, "bold"), foreground="#0284c7")
        self.lbl_conv_res.pack(anchor="w")

    def _run_unit_conv(self):
        try:
            val = validate_float(self.ent_conv_val.get(), "Giá trị quy đổi", allow_zero=True, positive_only=False)
            ctype = self.cmb_conv_type.get()
            res, unit = convert_electrical_unit(val, ctype)
            src_unit = ctype.split("sang")[0].strip()
            self.lbl_conv_res.config(text=f"{val} {src_unit} = {res} {unit}")
        except (ValidationError, ValueError) as e:
            messagebox.showerror("Lỗi đổi đơn vị", str(e))
