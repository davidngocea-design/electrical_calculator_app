"""
File chính: main.py
Chức năng:
  - Khởi tạo cửa sổ chính Phần Mềm Tra Cứu & Tính Toán Kỹ Thuật Điện - Điện Tử
  - Thanh điều hướng Sidebar chuyển đổi giữa 4 phân hệ tính toán
  - Khung quản lý Lịch sử tính toán bên phải, xem lại chi tiết và Xuất báo cáo nhanh
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

REQUIRED_FOLDERS = ["utils", "modules", "views"]
missing_folders = [f for f in REQUIRED_FOLDERS if not os.path.isdir(os.path.join(BASE_DIR, f))]
if missing_folders or ("Temp" in BASE_DIR and ".zip" in BASE_DIR.lower()):
    _root = tk.Tk()
    _root.withdraw()
    messagebox.showerror(
        "Lỗi: Chưa Giải Nén File ZIP!",
        "Bạn đang bấm chạy trực tiếp file main.py từ bên trong file nén (.ZIP) hoặc thiếu thư mục con!\n\n"
        "CÁCH KHẮC PHỤC:\n"
        "1. Nhấp chuột phải vào file .ZIP tải về.\n"
        "2. Chọn 'Extract All...' (hoặc WinRAR -> Extract Here / Giải nén ở đây).\n"
        "3. Mở thư mục ĐÃ GIẢI NÉN rồi mới chạy file main.py."
    )
    sys.exit(1)

from utils.history import load_history, clear_history, ensure_data_files
from utils.exporter import format_record_as_text, export_record_to_file
from views.dc_safety_view import DCSafetyView
from views.ac_three_phase_view import ACThreePhaseView
from views.ac_single_phase_view import ACSinglePhaseView
from views.line_calc_view import LineCalcView


class ElectricalCalculatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        ensure_data_files()
        self.title("Phần Mềm Tra Cứu & Tính Toán Kỹ Thuật Điện - Điện Tử")
        self.geometry("1260x760")
        self.minsize(1100, 680)
        self.configure(bg="#f1f5f9")

        self.selected_history_record = None
        self._configure_styles()
        self._build_layout()
        self._refresh_history_list()
        self.show_frame("dc_safety")

    def _configure_styles(self):
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")

        style.configure("TFrame", background="#f8fafc")
        style.configure("TLabelframe", background="#f8fafc")
        style.configure("TLabelframe.Label", background="#f8fafc", foreground="#0f172a", font=("Segoe UI", 10, "bold"))
        style.configure("TLabel", background="#f8fafc", foreground="#1e293b", font=("Segoe UI", 10))
        style.configure("ModuleHeader.TLabel", background="#f8fafc", foreground="#0369a1", font=("Segoe UI", 12, "bold"))
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), background="#0284c7", foreground="white", padding=6)
        style.map("Accent.TButton", background=[("active", "#0369a1")])

        style.configure("Nav.TButton", font=("Segoe UI", 10, "bold"), padding=10, anchor="w")
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), background="#e2e8f0", foreground="#0f172a")
        style.configure("Treeview", font=("Segoe UI", 9), rowheight=24)

    def _build_layout(self):
        # 1. Thanh điều hướng bên trái (Sidebar)
        sidebar = tk.Frame(self, bg="#0f172a", width=260)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        logo_text = "⚡ KỸ THUẬT ĐIỆN" + chr(10) + "PHẦN MỀM TÍNH TOÁN"
        lbl_logo = tk.Label(
            sidebar,
            text=logo_text,
            bg="#0f172a", fg="#38bdf8",
            font=("Segoe UI", 13, "bold"),
            pady=18
        )
        lbl_logo.pack(fill="x")

        tk.Frame(sidebar, bg="#334155", height=1).pack(fill="x", padx=12, pady=(0, 12))

        nav_items = [
            ("dc_safety", "1. Mạch DC, Ắc Quy & MCB"),
            ("ac_three_phase", "2. Mạch AC 3 Pha & Động Cơ"),
            ("ac_single_phase", "3. Mạch AC 1 Pha & Bù cosφ"),
            ("line_calc", "4. Đường Dây & Sụt Áp")
        ]

        self.nav_buttons = {}
        for key, label in nav_items:
            btn = tk.Button(
                sidebar,
                text=label,
                bg="#1e293b", fg="#f8fafc",
                activebackground="#0284c7", activeforeground="white",
                relief="flat", bd=0, padx=14, pady=12,
                justify="left", anchor="w",
                font=("Segoe UI", 10, "bold"),
                cursor="hand2",
                command=lambda k=key: self.show_frame(k)
            )
            btn.pack(fill="x", padx=10, pady=4)
            self.nav_buttons[key] = btn

        # Nút xuất báo cáo tổng ở Sidebar
        tk.Frame(sidebar, bg="#334155", height=1).pack(fill="x", padx=12, pady=12)
        btn_export_any = tk.Button(
            sidebar,
            text="📄 Xuất Báo Cáo Đang Chọn",
            bg="#059669", fg="white",
            activebackground="#047857", activeforeground="white",
            relief="flat", bd=0, padx=12, pady=10,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
            command=self._export_selected_record
        )
        btn_export_any.pack(fill="x", padx=10, pady=4)

        # 2. Khu vực trung tâm chứa các giao diện chức năng
        self.center_container = ttk.Frame(self)
        self.center_container.pack(side="left", fill="both", expand=True)

        # 3. Khung Lịch sử tính toán bên phải
        history_panel = ttk.LabelFrame(self, text="Lịch Sử Tính Toán", padding=8)
        history_panel.pack(side="right", fill="y", padx=6, pady=6)

        self.lst_history = tk.Listbox(
            history_panel, width=34, height=22,
            font=("Segoe UI", 9), bg="#ffffff", fg="#1e293b",
            selectbackground="#0284c7", selectforeground="white"
        )
        self.lst_history.pack(fill="both", expand=True, pady=(0, 6))
        self.lst_history.bind("<<ListboxSelect>>", self._on_history_select)

        btn_view_hist = ttk.Button(history_panel, text="Xem Chi Tiết Bản Ghi", command=self._view_history_popup)
        btn_view_hist.pack(fill="x", pady=2)

        btn_clear_hist = ttk.Button(history_panel, text="Xóa Lịch Sử", command=self._clear_all_history)
        btn_clear_hist.pack(fill="x", pady=2)

        # Khởi tạo 4 màn hình chức năng
        self.frames = {
            "dc_safety": DCSafetyView(self.center_container, on_calculation_done=self._on_new_calculation),
            "ac_three_phase": ACThreePhaseView(
                self.center_container,
                on_calculation_done=self._on_new_calculation,
                on_send_current_to_line=self._handle_motor_to_line_transfer
            ),
            "ac_single_phase": ACSinglePhaseView(self.center_container, on_calculation_done=self._on_new_calculation),
            "line_calc": LineCalcView(self.center_container, on_calculation_done=self._on_new_calculation)
        }

        for frame in self.frames.values():
            frame.place(relx=0, rely=0, relwidth=1, relheight=1)

    def show_frame(self, key):
        for k, btn in self.nav_buttons.items():
            if k == key:
                btn.configure(bg="#0284c7", fg="white")
            else:
                btn.configure(bg="#1e293b", fg="#f8fafc")
        self.frames[key].tkraise()

    def _handle_motor_to_line_transfer(self, p_elec_kw, u_d, cos_phi, phase_type):
        """Liên thông dữ liệu từ Phân hệ 2 (Động cơ) sang Phân hệ 4 (Tính Cáp & Sụt áp)."""
        self.show_frame("line_calc")
        self.frames["line_calc"].load_external_load(p_elec_kw, u_d, cos_phi, phase_type)

    def _on_new_calculation(self, record):
        self.selected_history_record = record
        self._refresh_history_list()

    def _refresh_history_list(self):
        self.history_data = load_history()
        self.lst_history.delete(0, "end")
        for idx, item in enumerate(self.history_data, start=1):
            ts_raw = item.get("Thời gian tính toán", item.get("timestamp", ""))
            ts = ts_raw[-8:] if len(ts_raw) >= 8 else ts_raw
            mod_name = item.get("Tên chức năng", item.get("module_name", ""))
            self.lst_history.insert("end", f"{idx}. [{ts}] {mod_name[:26]}")

    def _on_history_select(self, _event=None):
        sel = self.lst_history.curselection()
        if not sel:
            return
        idx = sel[0]
        if 0 <= idx < len(self.history_data):
            self.selected_history_record = self.history_data[idx]

    def _view_history_popup(self):
        if not self.selected_history_record:
            messagebox.showinfo("Lịch sử", "Hãy chọn một bản ghi trong danh sách Lịch sử bên phải!")
            return
        ts = self.selected_history_record.get("Thời gian tính toán", self.selected_history_record.get("timestamp", ""))
        top = tk.Toplevel(self)
        top.title(f"Chi Tiết Bản Ghi - {ts}")
        top.geometry("680x500")
        txt = tk.Text(top, font=("Consolas", 10), bg="#0f172a", fg="#e2e8f0", padx=12, pady=12)
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", format_record_as_text(self.selected_history_record))
        txt.config(state="disabled")

    def _export_selected_record(self):
        if not self.selected_history_record:
            messagebox.showwarning("Chưa có dữ liệu", "Hãy thực hiện một phép tính hoặc chọn một mục trong Lịch sử!")
            return
        filepath = filedialog.asksaveasfilename(
            title="Xuất Báo Cáo Kỹ Thuật Điện",
            defaultextension=".txt",
            initialfile="BaoCaoKyThuatDien.txt",
            filetypes=[
                ("Báo cáo văn bản (*.txt)", "*.txt"),
                ("Bảng tính Excel CSV (*.csv)", "*.csv"),
                ("Tệp dữ liệu JSON (*.json)", "*.json")
            ]
        )
        if filepath:
            export_record_to_file(self.selected_history_record, filepath)
            messagebox.showinfo("Thành công", f"Đã xuất file báo cáo tại: {filepath}")

    def _clear_all_history(self):
        if messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa toàn bộ lịch sử tính toán?"):
            clear_history()
            self.selected_history_record = None
            self._refresh_history_list()


if __name__ == "__main__":
    app = ElectricalCalculatorApp()
    app.mainloop()
