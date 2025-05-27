import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
from PIL import Image, ImageTk
import json
import os
import requests
import urllib3

DATA_FILE = 'products.json'
USERS_FILE = 'users.json'

# Tạo file dữ liệu nếu chưa tồn tại
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f)

if not os.path.exists(USERS_FILE):
    default_users = [
        {
            "username": "admin",
            "password": "admin123",
            "name": "Quản trị viên",
            "role": "admin"
        },
        {
            "username": "user1",
            "password": "user123",
            "name": "Người dùng mẫu",
            "role": "user"
        }
    ]
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(default_users, f, ensure_ascii=False, indent=4)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class JSONHandler:
    @staticmethod
    def read(file):
        if not os.path.exists(file):
            with open(file, 'w', encoding='utf-8') as f:
                json.dump([], f)
            return []
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def write(file, data):
        with open(file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

class ProductFetcher:
    @staticmethod
    def fetch_from_api():
        try:
            response = requests.get("https://fakestoreapi.com/products", verify=False)
            if response.status_code == 200:
                products = response.json()
                simplified = [
                    {
                        "id": str(p['id']),
                        "name": p['title'],
                        "price": str(p['price']),
                        "qty": "10"
                    }
                    for p in products
                ]
                JSONHandler.write(DATA_FILE, simplified)
                return True
            return False
        except Exception as e:
            print("Error fetching data:", e)
            return False

class ProductManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Quản Lý Sản Phẩm")
        self.root.geometry("1000x600")
        self.current_user = None
        self.products_tree = None
        self.avatar_button = None
        self.build_login()

    def build_login(self):
        self.clear_window()
        frame = tk.Frame(self.root)
        frame.pack(expand=True)

        tk.Label(frame, text="Đăng nhập", font=('Arial', 20)).grid(row=0, columnspan=2, pady=10)

        tk.Label(frame, text="Tên đăng nhập").grid(row=1, column=0, sticky='e', padx=10, pady=5)
        self.username_entry = tk.Entry(frame, font=('Arial', 12))
        self.username_entry.grid(row=1, column=1, pady=5)

        tk.Label(frame, text="Mật khẩu").grid(row=2, column=0, sticky='e', padx=10, pady=5)
        self.password_entry = tk.Entry(frame, show='*', font=('Arial', 12))
        self.password_entry.grid(row=2, column=1, pady=5)

        button_frame = tk.Frame(frame)
        button_frame.grid(row=3, columnspan=2, pady=10)

        tk.Button(button_frame, text="Đăng nhập", width=15, command=self.login).pack(side='left', padx=10)
        tk.Button(button_frame, text="Đăng ký", width=15, command=self.build_register).pack(side='right', padx=10)

    def build_register(self):
        self.clear_window()
        frame = tk.Frame(self.root)
        frame.pack(expand=True)

        tk.Label(frame, text="Đăng ký tài khoản", font=('Arial', 20)).grid(row=0, columnspan=2, pady=10)

        tk.Label(frame, text="Tên người dùng").grid(row=1, column=0, sticky='e', padx=10, pady=5)
        self.name_entry = tk.Entry(frame, font=('Arial', 12))
        self.name_entry.grid(row=1, column=1, pady=5)

        tk.Label(frame, text="Tên đăng nhập").grid(row=2, column=0, sticky='e', padx=10, pady=5)
        self.reg_username_entry = tk.Entry(frame, font=('Arial', 12))
        self.reg_username_entry.grid(row=2, column=1, pady=5)

        tk.Label(frame, text="Mật khẩu").grid(row=3, column=0, sticky='e', padx=10, pady=5)
        self.reg_password_entry = tk.Entry(frame, show='*', font=('Arial', 12))
        self.reg_password_entry.grid(row=3, column=1, pady=5)

        tk.Label(frame, text="Nhập lại mật khẩu").grid(row=4, column=0, sticky='e', padx=10, pady=5)
        self.reg_confirm_entry = tk.Entry(frame, show='*', font=('Arial', 12))
        self.reg_confirm_entry.grid(row=4, column=1, pady=5)

        button_frame = tk.Frame(frame)
        button_frame.grid(row=5, columnspan=2, pady=10)

        tk.Button(button_frame, text="Xác nhận", width=15, command=self.register_user).pack(side='left', padx=10)
        tk.Button(button_frame, text="Quay lại", width=15, command=self.build_login).pack(side='right', padx=10)

    def register_user(self):
        name = self.name_entry.get()
        username = self.reg_username_entry.get()
        password = self.reg_password_entry.get()
        confirm = self.reg_confirm_entry.get()

        if password != confirm:
            messagebox.showerror("Lỗi", "Mật khẩu không khớp")
            return

        users = JSONHandler.read(USERS_FILE)
        if any(user['username'] == username for user in users):
            messagebox.showerror("Lỗi", "Tên đăng nhập đã tồn tại")
            return

        users.append({'username': username, 'password': password, 'name': name, 'role': 'user'})
        JSONHandler.write(USERS_FILE, users)
        messagebox.showinfo("Thành công", "Đăng ký thành công")
        self.build_login()

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        users = JSONHandler.read(USERS_FILE)
        for user in users:
            if user['username'] == username and user['password'] == password:
                self.current_user = user
                self.build_main_interface()
                return
        messagebox.showerror("Lỗi", "Sai tên đăng nhập hoặc mật khẩu")

    def build_main_interface(self):
        self.clear_window()

        top_bar = tk.Frame(self.root)
        top_bar.pack(fill='x', pady=5)

        search_entry = tk.Entry(top_bar, font=('Arial', 12))
        search_entry.pack(side='left', padx=10, pady=5)
        tk.Button(top_bar, text="Tìm kiếm", command=lambda: self.search_product(search_entry.get())).pack(side='left')

        avatar_frame = tk.Frame(top_bar)
        avatar_frame.pack(side='right', padx=10)
        avatar_img = Image.open("avatar.png") if os.path.exists("avatar.png") else Image.new('RGB', (40, 40), 'gray')
        avatar_img = avatar_img.resize((40, 40))
        avatar = ImageTk.PhotoImage(avatar_img)

        self.avatar_button = tk.Label(avatar_frame, image=avatar, cursor="hand2")
        self.avatar_button.image = avatar
        self.avatar_button.pack()
        self.avatar_button.bind("<Button-1>", self.show_user_menu)

        self.user_menu = tk.Frame(self.root, relief='raised', bd=1)
        self.user_menu.place(x=900, y=40)
        self.user_menu.lower()
        tk.Label(self.user_menu, text=self.current_user['name'], font=('Arial', 12)).pack(pady=5)
        tk.Button(self.user_menu, text="Thông tin cá nhân", command=self.show_user_info).pack(fill='x')
        tk.Button(self.user_menu, text="Đăng xuất", command=self.build_login).pack(fill='x')

        self.build_product_table()

        if self.current_user['role'] == 'Quản trị viên':
            tk.Button(self.root, text="Thêm", command=self.add_product_popup).pack(pady=5)
            tk.Button(self.root, text="Xóa", command=self.delete_product).pack(pady=5)
            tk.Button(self.root, text="Tạo API", command=self.fetch_api_and_reload).pack(pady=5)
        else:
            tk.Button(self.root, text="Thêm", command=self.add_product_popup).pack(pady=5)

    def show_user_menu(self, event):
        self.user_menu.lift()

    def show_user_info(self):
        messagebox.showinfo("Thông tin cá nhân", f"Tên: {self.current_user['name']}\nVai trò: {self.current_user['role']}")

    def build_product_table(self):
        columns = ("id", "name", "price", "qty")
        self.products_tree = ttk.Treeview(self.root, columns=columns, show="headings")
        for col in columns:
            self.products_tree.heading(col, text=col.capitalize())
            self.products_tree.column(col, anchor='center')
        self.products_tree.pack(expand=True, fill='both')

        self.load_products_to_tree()

    def load_products_to_tree(self):
        for row in self.products_tree.get_children():
            self.products_tree.delete(row)
        products = JSONHandler.read(DATA_FILE)
        for product in products:
            self.products_tree.insert('', 'end', values=(product['id'], product['name'], product['price'], product['qty']))

    def add_product_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("Thêm sản phẩm")
        tk.Label(popup, text="ID").grid(row=0, column=0)
        tk.Label(popup, text="Tên").grid(row=1, column=0)
        tk.Label(popup, text="Giá").grid(row=2, column=0)
        tk.Label(popup, text="Số lượng").grid(row=3, column=0)

        id_entry = tk.Entry(popup)
        name_entry = tk.Entry(popup)
        price_entry = tk.Entry(popup)
        qty_entry = tk.Entry(popup)
        id_entry.grid(row=0, column=1)
        name_entry.grid(row=1, column=1)
        price_entry.grid(row=2, column=1)
        qty_entry.grid(row=3, column=1)

        def add():
            products = JSONHandler.read(DATA_FILE)
            if any(p['name'] == name_entry.get() for p in products):
                messagebox.showwarning("Trùng tên", "Đã có sản phẩm này")
                return
            new_product = {
                "id": id_entry.get(),
                "name": name_entry.get(),
                "price": price_entry.get(),
                "qty": qty_entry.get()
            }
            products.append(new_product)
            JSONHandler.write(DATA_FILE, products)
            self.load_products_to_tree()
            popup.destroy()

        tk.Button(popup, text="Thêm", command=add).grid(row=4, columnspan=2, pady=5)

    def delete_product(self):
        name = simpledialog.askstring("Xóa sản phẩm", "Nhập tên sản phẩm để xoá:")
        if not name:
            return
        confirm = messagebox.askyesno("Xác nhận", f"Bạn có chắc chắn muốn xoá sản phẩm '{name}'?")
        if confirm:
            products = JSONHandler.read(DATA_FILE)
            products = [p for p in products if p['name'] != name]
            JSONHandler.write(DATA_FILE, products)
            self.load_products_to_tree()

    def search_product(self, keyword):
        products = JSONHandler.read(DATA_FILE)
        matched = [p for p in products if keyword.lower() in p['name'].lower()]
        if not matched:
            messagebox.showinfo("Không tìm thấy", "Không có sản phẩm nào phù hợp")
            return
        info = "\n".join([f"ID: {p['id']}\nTên: {p['name']}\nGiá: {p['price']}\nSố lượng: {p['qty']}" for p in matched])
        messagebox.showinfo("Kết quả tìm kiếm", info)

    def fetch_api_and_reload(self):
        if ProductFetcher.fetch_from_api():
            self.load_products_to_tree()
            messagebox.showinfo("Thành công", "Đã cập nhật từ API")
        else:
            messagebox.showerror("Lỗi", "Không thể lấy dữ liệu từ API")

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ProductManagerApp(root)
    root.mainloop()
