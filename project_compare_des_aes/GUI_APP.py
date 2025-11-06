import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import time, base64, threading, csv, os, random, string
import matplotlib.pyplot as plt
from AES import AESCipher
from DES import DESCipher
from docx import Document

class CompareApp:
    def __init__(self, root):
        self.root = root
        self.root.title("So sánh AES và DES - Encryption Performance Tool")
        self.root.geometry("950x680")
        self.root.configure(bg="#1e1e1e")

        self.aes = AESCipher()
        self.des = DESCipher()

        self.time_aes = 0
        self.time_des = 0

        # Notebook (tab control)
        self.tab_control = ttk.Notebook(self.root)
        self.tab_control.pack(expand=1, fill="both")

        self.tab_main = tk.Frame(self.tab_control, bg="#222")
        self.tab_benchmark = tk.Frame(self.tab_control, bg="#222")
        self.tab_structure = tk.Frame(self.tab_control, bg="#222")

        self.tab_control.add(self.tab_main, text="Encrypt / Decrypt")
        self.tab_control.add(self.tab_benchmark, text="Benchmark")
        self.tab_control.add(self.tab_structure, text="Structure")

        self.create_main_tab()
        self.create_benchmark_tab()
        self.create_structure_tab()

    # =========================================================
    # ================== TAB 1: Encrypt/Decrypt ================
    # =========================================================
    def create_main_tab(self):
        tk.Label(self.tab_main, text="Nhập hoặc chọn file cần mã hóa:",
                 fg="white", bg="#222", font=("Arial", 12)).pack(pady=10)

        file_frame = tk.Frame(self.tab_main, bg="#222")
        file_frame.pack()
        tk.Button(file_frame, text="Chọn file", command=self.load_file, bg="#555", fg="white").pack(side="left", padx=5)
        self.file_label = tk.Label(file_frame, text="(Chưa chọn file)", fg="gray", bg="#222")
        self.file_label.pack(side="left", padx=5)

        self.input_text = tk.Text(self.tab_main, height=4, width=100)
        self.input_text.pack(pady=5)

        frame = tk.Frame(self.tab_main, bg="#333")
        frame.pack(pady=15, fill="both", expand=True)

        # AES Frame
        self.left = tk.LabelFrame(frame, text="AES", fg="cyan", bg="#333", font=("Arial", 12))
        self.left.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        self.key_aes = tk.StringVar()
        tk.Button(self.left, text="Sinh khóa AES", command=self.gen_aes_key, bg="cyan").pack(pady=5)
        tk.Entry(self.left, textvariable=self.key_aes, width=50).pack(pady=5)
        self.result_aes = tk.Text(self.left, height=12, width=45)
        self.result_aes.pack(pady=5)
        self.progress_aes = ttk.Progressbar(self.left, length=250, mode="determinate")
        self.progress_aes.pack(pady=5)

        # DES Frame
        self.right = tk.LabelFrame(frame, text="DES", fg="orange", bg="#333", font=("Arial", 12))
        self.right.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        self.key_des = tk.StringVar()
        tk.Button(self.right, text="Sinh khóa DES", command=self.gen_des_key, bg="orange").pack(pady=5)
        tk.Entry(self.right, textvariable=self.key_des, width=50).pack(pady=5)
        self.result_des = tk.Text(self.right, height=12, width=45)
        self.result_des.pack(pady=5)
        self.progress_des = ttk.Progressbar(self.right, length=250, mode="determinate")
        self.progress_des.pack(pady=5)

        # Buttons
        tk.Button(self.tab_main, text="Mã hóa", command=self.encrypt_compare, bg="green", fg="white", width=15).pack(pady=5)
        tk.Button(self.tab_main, text="Giải mã", command=self.decrypt_compare, bg="red", fg="white", width=15).pack(pady=5)

    # =========================================================
    # ================= TAB 2: Benchmark ======================
    # =========================================================
    def create_benchmark_tab(self):
        tk.Label(self.tab_benchmark, text="Chế độ Benchmark: đo hiệu năng AES vs DES",
                 fg="white", bg="#222", font=("Arial", 14, "bold")).pack(pady=15)

        tk.Button(self.tab_benchmark, text="Chạy Benchmark", command=self.run_benchmark, bg="#008CBA", fg="white",
                  font=("Arial", 12)).pack(pady=10)

        self.benchmark_output = tk.Text(self.tab_benchmark, width=100, height=20, bg="#111", fg="white")
        self.benchmark_output.pack(pady=10)

    # =========================================================
    # ================= TAB 3: Structure ======================
    # =========================================================
    def create_structure_tab(self):
        info = """
        🔐 AES (Advanced Encryption Standard)
        • Kích thước khối: 128 bit
        • Kích thước khóa: 128, 192 hoặc 256 bit
        • Số vòng lặp: 10 / 12 / 14 tùy độ dài khóa
        • Cấu trúc: SubBytes → ShiftRows → MixColumns → AddRoundKey
        • Ưu điểm: Bảo mật cao, tốc độ nhanh, chuẩn hiện đại.

        🔒 DES (Data Encryption Standard)
        • Kích thước khối: 64 bit
        • Kích thước khóa: 56 bit (thực tế 64 nhưng 8 bit parity)
        • Số vòng lặp: 16
        • Cấu trúc: Feistel Network (chia trái-phải, hoán vị và XOR khóa)
        • Nhược điểm: Bảo mật thấp (dễ bị brute-force), chuẩn cũ.

        💡 Nhận xét:
        • AES nhanh hơn đáng kể trên khối lượng dữ liệu lớn.
        • DES chỉ nên dùng cho nghiên cứu hoặc môi trường nhỏ.
        """
        tk.Label(self.tab_structure, text=info, justify="left", fg="white", bg="#222",
                 font=("Consolas", 12), padx=20, pady=20).pack(anchor="w")


    def load_file(self):
        path = filedialog.askopenfilename(title="Chọn file văn bản",
                                          filetypes=[("Text", "*.txt"), ("Word", "*.docx")])
        if not path:
            return
        content = ""
        if path.endswith(".txt"):
            content = open(path, "r", encoding="utf-8").read()
        else:
            doc = Document(path)
            content = "\n".join([p.text for p in doc.paragraphs])
        self.input_text.delete("1.0", "end")
        self.input_text.insert("1.0", content)
        self.file_label.config(text=f"Đã chọn: {os.path.basename(path)}", fg="lightgreen")

    def gen_aes_key(self):
        self.key_aes.set(self.aes.generate_key())

    def gen_des_key(self):
        self.key_des.set(self.des.generate_key())

    def animate_progress(self, bar):
        bar["value"] = 0
        for i in range(100):
            bar["value"] = i + 1
            bar.update()
            time.sleep(0.005)

    # --- Encrypt ---
    def encrypt_compare(self):
        text = self.input_text.get("1.0", "end").strip()
        if not text:
            messagebox.showwarning("Lỗi", "Chưa có dữ liệu!")
            return

        self.result_aes.delete("1.0", "end")
        self.result_des.delete("1.0", "end")

        t_aes = threading.Thread(target=self.thread_encrypt, args=("AES", text))
        t_des = threading.Thread(target=self.thread_encrypt, args=("DES", text))
        t_aes.start()
        t_des.start()

    def thread_encrypt(self, algo, text):
        if algo == "AES":
            start = time.time()
            self.animate_progress(self.progress_aes)
            ct = self.aes.encrypt(text)
            self.time_aes = time.time() - start
            self.result_aes.insert("end", f"Ciphertext:\n{ct}\n\nThời gian: {self.time_aes:.6f}s")
        else:
            start = time.time()
            self.animate_progress(self.progress_des)
            ct = self.des.encrypt(text)
            self.time_des = time.time() - start
            self.result_des.insert("end", f"Ciphertext:\n{ct}\n\nThời gian: {self.time_des:.6f}s")

    # --- Decrypt ---
    def decrypt_compare(self):
        aes_ct = self.result_aes.get("1.0", "end").strip().split("\n")[1] if "Ciphertext" in self.result_aes.get("1.0", "end") else ""
        des_ct = self.result_des.get("1.0", "end").strip().split("\n")[1] if "Ciphertext" in self.result_des.get("1.0", "end") else ""
        if not aes_ct or not des_ct:
            messagebox.showwarning("Lỗi", "Không có dữ liệu mã hóa!")
            return

        threading.Thread(target=self.thread_decrypt, args=("AES", aes_ct)).start()
        threading.Thread(target=self.thread_decrypt, args=("DES", des_ct)).start()

    def thread_decrypt(self, algo, ct):
        if algo == "AES":
            self.animate_progress(self.progress_aes)
            pt = self.aes.decrypt(ct)
            self.result_aes.insert("end", f"\n[Giải mã AES]: {pt}")
        else:
            self.animate_progress(self.progress_des)
            pt = self.des.decrypt(ct)
            self.result_des.insert("end", f"\n[Giải mã DES]: {pt}")


    def run_benchmark(self):
        threading.Thread(target=self.benchmark_process).start()

    def benchmark_process(self):
        sizes = [1024, 10_000, 100_000, 1_000_000]
        results = []

        self.benchmark_output.delete("1.0", "end")
        self.benchmark_output.insert("end", "Đang chạy benchmark...\n")

        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        csv_path = os.path.join(desktop_path, "benchmark_results.csv")

        for size in sizes:
            data = ''.join(random.choices(string.ascii_letters + string.digits, k=size))

            # AES
            start = time.time()
            self.aes.encrypt(data)
            aes_time = time.time() - start

            # DES
            start = time.time()
            self.des.encrypt(data)
            des_time = time.time() - start

            results.append([size, aes_time, des_time])
            self.benchmark_output.insert("end", f"{size} bytes -> AES: {aes_time:.6f}s, DES: {des_time:.6f}s\n")

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Size(Bytes)", "AES_Time", "DES_Time"])
            writer.writerows(results)

        self.plot_benchmark(results)
        messagebox.showinfo("Hoàn tất", "Benchmark đã hoàn thành và lưu ra benchmark_results.csv!")

    def plot_benchmark(self, results):
        sizes = [r[0] for r in results]
        aes_t = [r[1] for r in results]
        des_t = [r[2] for r in results]

        plt.figure(figsize=(7, 5))
        plt.plot(sizes, aes_t, label="AES", marker="o", color="cyan")
        plt.plot(sizes, des_t, label="DES", marker="o", color="orange")
        plt.xlabel("Dung lượng dữ liệu (bytes)")
        plt.ylabel("Thời gian mã hóa (s)")
        plt.title("So sánh hiệu năng AES vs DES")
        plt.legend()
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.show()


# ================= RUN ==================
if __name__ == "__main__":
    root = tk.Tk()
    app = CompareApp(root)
    root.mainloop()
