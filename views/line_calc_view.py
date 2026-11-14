"""
Module: views/line_calc_view.py
Chức năng: Giao diện người dùng cho Phân hệ 4 - Tính chọn tiết diện cáp theo phát nóng (Icp) & mật độ dòng (Jcp),
vòng lặp tự động tăng cấp tiết diện dây để thỏa mãn độ sụt áp ΔU% <= 5%, chọn MCCB tổng và RCCB/ELCB.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from utils.validation import validate_float, validate_ratio, ValidationError
from utils.exporter import format_record_as_text
from modules.line_calc import optimize_cable_and_protection


class LineCalcView(ttk.Frame):
    def __init__(self, parent, on_calculation_done=None):
        super().__init__(parent, padding=12)
        self.on_calculation_done = on_calculation_done
        self.last_record = None
        self._build_ui()

    def _build_ui(self):
        header = ttk.Label(
            self,
            text="PHÂN HỆ 4: TÍNH ĐƯỜNG DÂY, VÒNG LẶP TỐI ƯU SỤT ÁP (ΔU% ≤ 5%) & CHỌN CÁP / MCCB",
            style="ModuleHeader.TLabel"
        )
        header.pack(anchor="w", pady=(0, 8))

        form_frame = ttk.LabelFrame(self, text="Thông Số Tuyến Cáp & Phụ Tải", padding=10)
        form_frame.pack(fill="x", pady=(0, 8))

        ttk.Label(form_frame, text="Công suất tải P (kW):").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.ent_pkw = ttk.Entry(form_frame, width=14)
        self.ent_pkw.insert(0, "35.0")
        self.ent_pkw.grid(row=0, column=1, padx=5, pady=4)

        ttk.Label(form_frame, text="Chiều dài tuyến cáp L (m):").grid(row=0, column=2, sticky="w", padx=5, pady=4)
        self.ent_len = ttk.Entry(form_frame, width=14)
        self.ent_len.insert(0, "250.0")
        self.ent_len.grid(row=0, column=3, padx=5, pady=4)

        ttk.Label(form_frame, text="Hệ thống pha:").grid(row=0, column=4, sticky="w", padx=5, pady=4)
        self.cmb_phase = ttk.Combobox(form_frame, values=["3 Pha (380V)", "1 Pha (220V)"], state="readonly", width=18)
        self.cmb_phase.current(0)
        self.cmb_phase.grid(row=0, column=5, padx=5, pady=4)
        self.cmb_phase.bind("<<ComboboxSelected>>", self._on_phase_change)

        ttk.Label(form_frame, text="Điện áp định mức U (V):").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        self.ent_u = ttk.Entry(form_frame, width=14)
        self.ent_u.insert(0, "380")
        self.ent_u.grid(row=1, column=1, padx=5, pady=4)

        ttk.Label(form_frame, text="Hệ số công suất cosφ:").grid(row=1, column=2, sticky="w", padx=5, pady=4)
        self.ent_cos = ttk.Entry(form_frame, width=14)
        self.ent_cos.insert(0, "0.85")
        self.ent_cos.grid(row=1, column=3, padx=5, pady=4)

        ttk.Label(form_frame, text="Vật liệu ruột dẫn:").grid(row=1, column=4, sticky="w", padx=5, pady=4)
        self.cmb_mat = ttk.Combobox(form_frame, values=["Đồng (Cu)", "Nhôm (Al)"], state="readonly", width=18)
        self.cmb_mat.current(0)
        self.cmb_mat.grid(row=1, column=5, padx=5, pady=4)

        ttk.Label(form_frame, text="Mật độ dòng Jcp (A/mm²):").grid(row=2, column=0, sticky="w", padx=5, pady=4)
        self.ent_jcp = ttk.Entry(form_frame, width=14)
        self.ent_jcp.insert(0, "5.0")
        self.ent_jcp.grid(row=2, column=1, padx=5, pady=4)

        ttk.Label(form_frame, text="Sụt áp cho phép ΔUmax (%):").grid(row=2, column=2, sticky="w", padx=5, pady=4)
        self.ent_max_du = ttk.Entry(form_frame, width=14)
        self.ent_max_du.insert(0, "5.0")
        self.ent_max_du.grid(row=2, column=3, padx=5, pady=4)

        ttk.Label(form_frame, text="Môi trường lắp đặt:").grid(row=2, column=4, sticky="w", padx=5, pady=4)
        self.cmb_env = ttk.Combobox(form_frame, values=["Công nghiệp (RCCB 100/300mA)", "Dân dụng (RCCB 30mA)"], state="readonly", width=18)
        self.cmb_env.current(0)
        self.cmb_env.grid(row=2, column=5, padx=5, pady=4)

        btn_run = ttk.Button(
            form_frame,
            text="Chạy Vòng Lặp Tối Ưu Tiết Diện Cáp & Chọn MCCB / RCCB",
            style="Accent.TButton",
            command=self._run_optimization
        )
        btn_run.grid(row=3, column=0, columnspan=6, sticky="ew", padx=5, pady=6)

        # Bảng hiển thị các bước lặp tăng cấp tiết diện dây
        iter_frame = ttk.LabelFrame(self, text="Bảng Truy Vết Vòng Lặp Tăng Cấp Tiết Diện Theo Điều Kiện Sụt Áp", padding=6)
        iter_frame.pack(fill="x", pady=(0, 8))

        cols = ("section", "ampacity", "du_v", "du_pct", "dp_w", "status")
        self.tree_iter = ttk.Treeview(iter_frame, columns=cols, show="headings", height=4)
        self.tree_iter.heading("section", text="Tiết diện S (mm²)")
        self.tree_iter.heading("ampacity", text="Dòng phát nóng Icp (A)")
        self.tree_iter.heading("du_v", text="Độ sụt áp ΔU (V)")
        self.tree_iter.heading("du_pct", text="Tỷ lệ ΔU (%)")
        self.tree_iter.heading("dp_w", text="Tổn thất ΔP (W)")
        self.tree_iter.heading("status", text="Đánh giá điều kiện")

        for col, w in zip(cols, (120, 140, 120, 110, 120, 190)):
            self.tree_iter.column(col, width=w, anchor="center")
        self.tree_iter.pack(fill="x")

        # Khu vực hiển thị báo cáo chi tiết
        res_frame = ttk.LabelFrame(self, text="Chi Tiết Kết Quả & Khuyến Nghị Cáp Điện + MCCB / ELCB", padding=8)
        res_frame.pack(fill="both", expand=True)

        self.txt_result = tk.Text(
            res_frame, height=9, font=("Consolas", 10), bg="#0f172a", fg="#e2e8f0",
            insertbackground="white", relief="flat", padx=10, pady=8
        )
        self.txt_result.pack(fill="both", expand=True)
        self.txt_result.insert("1.0", "Nhập thông số đường dây và nhấn nút chạy tối ưu để xem các bước lặp chọn cáp...")
        self.txt_result.config(state="disabled")

    def _on_phase_change(self, _event=None):
        if self.cmb_phase.get().startswith("3"):
            self.ent_u.delete(0, "end")
            self.ent_u.insert(0, "380")
        else:
            self.ent_u.delete(0, "end")
            self.ent_u.insert(0, "220")

    def load_external_load(self, p_kw, u_v, cos_phi, phase_type="3P"):
        """Nhận dữ liệu chuyển tiếp từ Phân hệ 2 (Động cơ 3 pha)."""
        self.ent_pkw.delete(0, "end")
        self.ent_pkw.insert(0, str(p_kw))
        self.ent_u.delete(0, "end")
        self.ent_u.insert(0, str(u_v))
        self.ent_cos.delete(0, "end")
        self.ent_cos.insert(0, str(cos_phi))
        self.cmb_phase.current(0 if phase_type == "3P" else 1)
        self._run_optimization()

    def _run_optimization(self):
        try:
            p_kw = validate_float(self.ent_pkw.get(), "Công suất tải P (kW)")
            l_m = validate_float(self.ent_len.get(), "Chiều dài tuyến cáp L (m)")
            u_v = validate_float(self.ent_u.get(), "Điện áp định mức U (V)")
            cos_phi = validate_ratio(self.ent_cos.get(), "Hệ số công suất cosφ")
            j_cp = validate_float(self.ent_jcp.get(), "Mật độ dòng Jcp (A/mm²)")
            max_du = validate_float(self.ent_max_du.get(), "Sụt áp cho phép ΔUmax (%)")

            phase_type = "3P" if self.cmb_phase.get().startswith("3") else "1P"
            material = "Cu" if "Đồng" in self.cmb_mat.get() else "Al"
            env_type = "industrial" if "Công nghiệp" in self.cmb_env.get() else "residential"

            rec = optimize_cable_and_protection(
                p_kw=p_kw,
                l_m=l_m,
                u_v=u_v,
                cos_phi=cos_phi,
                phase_type=phase_type,
                material=material,
                j_cp=j_cp,
                max_vdrop_percent=max_du,
                env_type=env_type
            )

            # Cập nhật bảng vòng lặp
            for row in self.tree_iter.get_children():
                self.tree_iter.delete(row)

            iterations = rec.get("Dữ liệu bổ sung", {}).get("Các bước lặp", [])
            for step in iterations:
                self.tree_iter.insert(
                    "", "end",
                    values=(
                        f"{step['Tiết diện (mm²)']} mm²",
                        f"{step['Dòng cho phép (A)']} A",
                        f"{step['Sụt áp (V)']} V",
                        f"{step['Tỷ lệ sụt áp (%)']} %",
                        f"{step['Tổn thất công suất (W)']} W",
                        step["Kết luận"]
                    )
                )

            self.last_record = rec
            text = format_record_as_text(rec)
            self.txt_result.config(state="normal")
            self.txt_result.delete("1.0", "end")
            self.txt_result.insert("1.0", text)
            self.txt_result.config(state="disabled")

            if self.on_calculation_done:
                self.on_calculation_done(rec)

        except (ValidationError, ValueError) as e:
            messagebox.showerror("Lỗi nhập liệu", str(e))
