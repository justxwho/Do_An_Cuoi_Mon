import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, ttk, simpledialog, filedialog
from PIL import Image, ImageTk
import json, os
import requests
import urllib3
import hashlib

DATA_FILE = 'products.json'
USERS_FILE = 'users.json'
AVATAR_FOLDER = "avatars"
os.makedirs(AVATAR_FOLDER, exist_ok=True)

# Hash mật khẩu
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_image(path, size):
    try:
        img = Image.open(path).resize(size)
    except:
        img = Image.new('RGB', size, 'gray')
    return ImageTk.PhotoImage(img)

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
        self.account_popup = None
        self.root.bind("<Button-1>", self.handle_click_outside)
        self.background_image = ImageTk.PhotoImage(Image.open("background.jpg").resize((1000, 600)))
        self.build_login()

    def toggle_account_info(self):
        if self.account_popup and self.account_popup.winfo_exists():
            self.account_popup.destroy()
        else:
            self.account_popup = tk.Toplevel(self.root)
            self.account_popup.geometry("200x100")
            self.account_popup.overrideredirect(True)
            x = self.avatar_button.winfo_rootx()
            y = self.avatar_button.winfo_rooty() + self.avatar_button.winfo_height()
            self.account_popup.geometry(f"200x130+{x}+{y}")
            ctk.CTkLabel(self.account_popup, text=f"👤 {self.current_user['name']}\nVai trò: {self.current_user['role']}", font=('Arial', 12, 'bold'), 
                        anchor="center").pack(fill='x', padx=10, pady=5)
            ctk.CTkButton(self.account_popup, text="Chọn ảnh", corner_radius=32, font=('Arial', 12, 'bold'), command=self.choose_avatar).pack(pady=10)
            ctk.CTkButton(self.account_popup, text="Đăng xuất", corner_radius=32, font=('Arial', 12, 'bold'), command=self.logout).pack(pady=2)


    def handle_click_outside(self, event):
        if self.account_popup and self.account_popup.winfo_exists():
            if not (self.account_popup.winfo_rootx() <= event.x_root <= self.account_popup.winfo_rootx() + self.account_popup.winfo_width() and
                    self.account_popup.winfo_rooty() <= event.y_root <= self.account_popup.winfo_rooty() + self.account_popup.winfo_height()):
                if not (self.avatar_button.winfo_rootx() <= event.x_root <= self.avatar_button.winfo_rootx() + self.avatar_button.winfo_width() and
                        self.avatar_button.winfo_rooty() <= event.y_root <= self.avatar_button.winfo_rooty() + self.avatar_button.winfo_height()):
                    self.account_popup.destroy()

    def logout(self):
        self.current_user = None
        if self.account_popup:
            self.account_popup.destroy()
        self.build_login()

    def build_login(self):
        self.clear_window()
        bg_label = tk.Label(self.root, image=self.background_image)
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        frame = tk.Frame(self.root, bg='white')
        frame.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(frame, text="Đăng nhập", font=('Arial', 20), bg='white').grid(row=0, columnspan=2, pady=10)

        tk.Label(frame, text="Tên đăng nhập", bg='white').grid(row=1, column=0, sticky='e', padx=10, pady=5)
        self.username_entry = tk.Entry(frame, font=('Arial', 12))
        self.username_entry.grid(row=1, column=1, pady=5)

        tk.Label(frame, text="Mật khẩu", bg='white').grid(row=2, column=0, sticky='e', padx=10, pady=5)
        self.password_entry = tk.Entry(frame, show='*', font=('Arial', 12))
        self.password_entry.grid(row=2, column=1, pady=5)

        button_frame = tk.Frame(frame, bg='white')
        button_frame.grid(row=3, columnspan=2, pady=10)
        ctk.CTkButton(master=button_frame, text="Đăng nhập", width=15, corner_radius=32, font=("Arial", 12, "bold"), 
                    command=self.login).pack(side='left', padx=10)
        ctk.CTkButton(master=button_frame, text="Đăng ký", width=15, corner_radius=32, font=("Arial", 12, "bold"), 
                    command=self.build_register).pack(side='right', padx=10)

    def build_register(self):
        self.clear_window()
        bg_label = tk.Label(self.root, image=self.background_image)
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        frame = tk.Frame(self.root, bg='white')
        frame.place(relx=0.5, rely=0.5, anchor='center')

        tk.Label(frame, text="Đăng ký tài khoản", font=('Arial', 20), bg='white').grid(row=0, columnspan=2, pady=10)

        tk.Label(frame, text="Tên người dùng", bg='white').grid(row=1, column=0, sticky='e', padx=10, pady=5)
        self.name_entry = tk.Entry(frame, font=('Arial', 12))
        self.name_entry.grid(row=1, column=1, pady=5)

        tk.Label(frame, text="Tên đăng nhập", bg='white').grid(row=2, column=0, sticky='e', padx=10, pady=5)
        self.reg_username_entry = tk.Entry(frame, font=('Arial', 12))
        self.reg_username_entry.grid(row=2, column=1, pady=5)

        tk.Label(frame, text="Mật khẩu", bg='white').grid(row=3, column=0, sticky='e', padx=10, pady=5)
        self.reg_password_entry = tk.Entry(frame, show='*', font=('Arial', 12))
        self.reg_password_entry.grid(row=3, column=1, pady=5)

        tk.Label(frame, text="Nhập lại mật khẩu", bg='white').grid(row=4, column=0, sticky='e', padx=10, pady=5)
        self.reg_confirm_entry = tk.Entry(frame, show='*', font=('Arial', 12))
        self.reg_confirm_entry.grid(row=4, column=1, pady=5)

        button_frame = tk.Frame(frame, bg='white')
        button_frame.grid(row=5, columnspan=2, pady=10)

        ctk.CTkButton(button_frame, text="Xác nhận", width=15, corner_radius=32, font=("Arial", 12, "bold"), 
                    command=self.register_user).pack(side='left', padx=10)
        ctk.CTkButton(button_frame, text="Quay lại", width=15, corner_radius=32, font=("Arial", 12, "bold"),
                    command=self.build_login).pack(side='right', padx=10)

    def register_user(self):
        name = self.name_entry.get()
        username = self.reg_username_entry.get()
        password = hash_password(self.reg_password_entry.get())
        confirm = hash_password(self.reg_confirm_entry.get())

        if password != confirm:
            messagebox.showerror("Lỗi", "Mật khẩu không khớp")
            return

        users = JSONHandler.read(USERS_FILE)
        if any(user['username'] == username for user in users):
            messagebox.showerror("Lỗi", "Tên đăng nhập đã tồn tại")
            return

        users.append({'username': username, 'password': password, 'name': name, 'role': 'Người dùng'})
        JSONHandler.write(USERS_FILE, users)
        messagebox.showinfo("Thành công", "Đăng ký thành công")
        self.build_login()

    def login(self):
        username = self.username_entry.get()
        password = hash_password(self.password_entry.get())
        users = JSONHandler.read(USERS_FILE)
        user = next((u for u in users if u['username'] == username and u['password'] == password), None)
        if user:
            self.current_user = user
            self.build_main_interface()
        else:
            messagebox.showerror("Lỗi", "Sai thông tin đăng nhập")

    def build_main_interface(self):
        self.clear_window()

        top_bar = tk.Frame(self.root)
        top_bar.pack(fill='x', pady=5)

        font_setting_search = ("Arial", 12, "bold")
        search_entry = tk.Entry(top_bar, font=('Arial', 12))
        search_entry.pack(side='left', padx=10, pady=5)
        ctk.CTkButton(top_bar, text="Tìm kiếm", corner_radius=10, text_color="black", fg_color="white", border_color="black", 
                border_width=2, hover_color="#498EFD", font=font_setting_search,
                command=lambda: self.search_product(search_entry.get())).pack(side='left')

        avatar_path = os.path.join(AVATAR_FOLDER, f"{self.current_user['username']}.png")
        avatar_img = load_image(avatar_path, (50, 50))
        avatar_label = tk.Label(top_bar, image=avatar_img)
        avatar_label.image = avatar_img
        avatar_label.pack(side="right", padx=10, pady=5)
        
        self.build_product_table()

        font_settings = ("Arial", 12, "bold")

        if self.current_user['role'] == 'Quản trị viên':
            ctk.CTkButton(self.root, text="Thêm", width=10, corner_radius=32, font=font_settings, 
                        command=self.add_product_popup).pack(side='left', padx=10)
            ctk.CTkButton(self.root, text="Sửa", width=10, corner_radius=32, font=font_settings, 
                        command=self.edit_product).pack(side='left', padx=10)
            ctk.CTkButton(self.root, text="Xóa", width=10, corner_radius=32, font=font_settings, 
                        fg_color="#ff0000", hover_color="#CD0202", command=self.delete_product).pack(side='left', padx=10)
            api_button_frame = tk.Frame(self.root)
            api_button_frame.pack(pady=5)
            ctk.CTkButton(api_button_frame, text="Tạo dữ liệu từ API", width=20, corner_radius=32, font=font_settings, 
                        command=self.fetch_api_and_reload).pack()
        else:
            ctk.CTkButton(self.root, text="Thêm", width=10, corner_radius=32, font=font_settings, 
                        command=self.add_product_popup).pack(side='left', padx=100)
            api_button_frame = tk.Frame(self.root)
            api_button_frame.pack(pady=5)
            ctk.CTkButton(api_button_frame, text="Tạo dữ liệu từ API", width=20, corner_radius=32, font=font_settings, 
                        command=self.fetch_api_and_reload).pack()
            
    def show_user_menu(self, event):
        self.user_menu.lift()

    def show_user_info(self):
        messagebox.showinfo("Thông tin cá nhân", f"Tên: {self.current_user['name']}\nVai trò: {self.current_user['role']}")

    def build_product_table(self):
        avatar_frame = tk.Frame(self.root)
        avatar_frame.pack(anchor='ne', padx=10, pady=5)
        self.avatar_button = tk.Button(avatar_frame, text="👤", command=self.toggle_account_info)
        self.avatar_button.pack()
        columns = ("id", "name", "price", "qty")
        self.products_tree = ttk.Treeview(self.root, columns=columns, show="headings")
        column_names = {
            "id": "Mã sản phẩm",
            "name": "Tên sản phẩm",
            "price": "Giá",
            "qty": "Số lượng"
        }
        column_widths = {
            "id": 50,
            "name": 500,
            "price": 50,
            "qty": 50
        }
        for col in columns:
            self.products_tree.heading(col, text=column_names[col])
            align = 'w' if col == 'name' else 'center'
            self.products_tree.column(col, anchor=align, width=column_widths[col])
        self.products_tree.pack(expand=True, fill='both')
        scrollbar = ttk.Scrollbar(self.products_tree, orient="vertical", command=self.products_tree.yview)
        self.products_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.load_products_to_tree()

    def load_products_to_tree(self):
        self.products_tree.delete(*self.products_tree.get_children())
        for p in JSONHandler.read(DATA_FILE):
            price_str = f"{p['price']} USD"
            self.products_tree.insert('', 'end', values=(p['id'], p['name'], price_str, p['qty']))

    def add_product_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("Thêm sản phẩm")
        tk.Label(popup, text="Mã sản phẩm").grid(row=0, column=0)
        tk.Label(popup, text="Tên sản phẩm").grid(row=1, column=0)
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

    def edit_product(self):
        selected = self.products_tree.selection()
        if not selected:
            messagebox.showwarning("Chọn sản phẩm", "Vui lòng chọn sản phẩm để sửa")
            return
        values = self.products_tree.item(selected[0], 'values')
        popup = tk.Toplevel(self.root)
        popup.title("Sửa sản phẩm")
        tk.Label(popup, text="Mã sản phẩm").grid(row=0, column=0)
        tk.Label(popup, text="Tên sản phẩm").grid(row=1, column=0)
        tk.Label(popup, text="Giá").grid(row=2, column=0)
        tk.Label(popup, text="Số lượng").grid(row=3, column=0)

        id_entry = tk.Entry(popup)
        id_entry.insert(0, values[0])
        id_entry.grid(row=0, column=1)

        name_entry = tk.Entry(popup)
        name_entry.insert(0, values[1])
        name_entry.grid(row=1, column=1)

        price_entry = tk.Entry(popup)
        price_entry.insert(0, values[2])
        price_entry.grid(row=2, column=1)

        qty_entry = tk.Entry(popup)
        qty_entry.insert(0, values[3])
        qty_entry.grid(row=3, column=1)

        def save_edit():
            products = JSONHandler.read(DATA_FILE)
            for product in products:
                if product['id'] == values[0]:
                    product['name'] = name_entry.get()
                    product['price'] = price_entry.get()
                    product['qty'] = qty_entry.get()
                    break
            JSONHandler.write(DATA_FILE, products)
            self.load_products_to_tree()
            popup.destroy()

        tk.Button(popup, text="Lưu", command=save_edit).grid(row=4, columnspan=2)

    def delete_product(self):
        selected = self.products_tree.selection()
        if not selected:
            messagebox.showwarning("Chọn sản phẩm", "Vui lòng chọn sản phẩm để xóa")
            return
        confirm = messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa sản phẩm này?")
        if confirm:
            values = self.products_tree.item(selected[0], 'values')
            products = JSONHandler.read(DATA_FILE)
            products = [p for p in products if p['id'] != values[0]]
            JSONHandler.write(DATA_FILE, products)
            self.load_products_to_tree()

    def search_product(self, keyword):
        keyword = keyword.lower()
        products = JSONHandler.read(DATA_FILE)
        filtered = [p for p in products if keyword in p['name'].lower()]
        self.products_tree.delete(*self.products_tree.get_children())
        for p in filtered:
            price_str = f"{p['price']} USD"
            self.products_tree.insert('', 'end', values=(p['id'], p['name'], price_str, p['qty']))

    def choose_avatar(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif")])
        if file_path:
            try:
                img = Image.open(file_path).resize((50, 50))
                avatar_path = os.path.join(AVATAR_FOLDER, f"{self.current_user['username']}.png")
                img.save(avatar_path)
                self.build_main_interface()
                if self.account_popup:
                    self.account_popup.destroy()
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể đặt ảnh avatar: {e}")

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
