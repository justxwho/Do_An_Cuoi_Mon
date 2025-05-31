import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, ttk, simpledialog, filedialog
from PIL import Image, ImageTk
import json, os, io, shutil
import requests, random, string
import urllib3
import hashlib

DATA_FILE = 'products.json'
USERS_FILE = 'users.json'
AVATAR_FOLDER = "avatars"
IMAGE_FOLDER = "image_products"
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
            "password": hash_password("admin123"),
            "name": "Quản trị viên",
            "role": "Quản trị viên"
        },
        {
            "username": "user1",
            "password": hash_password("user123"),
            "name": "Người dùng",
            "role": "Người dùng"
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
    def generate_random_id(existing_ids):
        while True:
            letters = ''.join(random.choices(string.ascii_uppercase, k=2))
            digits = ''.join(random.choices(string.digits, k=3))
            new_id = letters + digits
            if new_id not in existing_ids:
                return new_id

    @staticmethod
    def fetch_from_api():
        try:
            response = requests.get("https://fakestoreapi.com/products", verify=False)
            if response.status_code == 200:
                api_products = response.json()
                existing_products = JSONHandler.read(DATA_FILE)
                existing_ids = {p['id'] for p in existing_products}

                for p in api_products:
                    new_id = ProductFetcher.generate_random_id(existing_ids)
                    existing_ids.add(new_id)

                    new_product = {
                        "id": new_id,
                        "name": p['title'],
                        "price": str(p['price']),
                        "qty": str(random.randint(1, 999)),
                        "description": p.get('description', ''),
                        "image": p.get('image', ''),
                        "rate": str(p.get('rating', {}).get('rate', '')),
                        "count": str(p.get('rating', {}).get('count', ''))
                    }
                    existing_products.append(new_product)

                JSONHandler.write(DATA_FILE, existing_products)
                return True
            return False
        except Exception as e:
            print("Error fetching from API:", e)
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
        if not name or not username or not password or not confirm:
            messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ thông tin !")
            return

        if password != confirm:
            messagebox.showerror("Lỗi", "Mật khẩu không khớp")
            return

        users = JSONHandler.read(USERS_FILE)
        if any(user['username'] == username for user in users):
            messagebox.showerror("Lỗi", "Tên đăng nhập đã tồn tại !")
            return

        users.append({'username': username, 'password': password, 'name': name, 'role': 'Người dùng'})
        JSONHandler.write(USERS_FILE, users)
        messagebox.showinfo("Thành công", "Đăng ký thành công")
        self.build_login()

    def login(self):
        username = self.username_entry.get()
        password = hash_password(self.password_entry.get())
        if not username or not password:
            messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ thông tin !")
            return
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
                        command=self.fetch_api_and_reload).pack(side='left', padx=100)
            ctk.CTkButton(api_button_frame, text="Xem chi tiết", width=10, corner_radius=32, font=font_settings,
                        command=self.view_product_info).pack(side='right')
        else:
            bottom_button = tk.Frame(self.root)
            bottom_button.pack(side='bottom', anchor="e", fill='x', pady=5, padx=10)
            ctk.CTkButton(bottom_button, text="Xem Thông Tin Sản Phẩm", width=10, corner_radius=32, font=font_settings,
                        command=self.view_product_info).pack(side='right')
            
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
            "qty": "Số lượng tồn kho"
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

    def view_product_info(self):
        selected = self.products_tree.focus()
        if not selected:
            messagebox.showwarning("Chú ý", "Vui lòng chọn một sản phẩm để xem thông tin.")
            return

        item = self.products_tree.item(selected)
        product_id = item['values'][0]

        products = JSONHandler.read(DATA_FILE)
        product = next((p for p in products if p['id'] == product_id), None)
        if not product:
            messagebox.showerror("Lỗi", "Không tìm thấy sản phẩm.")
            return

        # Tạo cửa sổ xem/chỉnh sửa thông tin
        info_win = tk.Toplevel(self.root)
        info_win.title(f"Thông tin sản phẩm {product['id']}")
        info_win.geometry("600x500")

        # Các trường thông tin:
        fields = [
            ("Mã sản phẩm", "id"),
            ("Tên sản phẩm", "name"),
            ("Giá", "price"),
            ("Số lượng tồn kho", "qty"),
            ("Số lượng mua", "count"),
            ("Đánh giá", "rate"),
            ("Mô tả", "description"),
            ("Hình ảnh", "image"),
        ]

        entries = {}
        row = 0
        for label_text, key in fields:
            tk.Label(info_win, text=label_text).grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
            if key == 'image':
                img_path = product.get('image', '')
                if img_path:
                    try:
                        if img_path.startswith('http://') or img_path.startswith('https://'):
                            # Tải ảnh từ URL
                            response = requests.get(img_path)
                            img_data = response.content
                            pil_img = Image.open(io.BytesIO(img_data))
                        else:
                            # Ảnh local: mở file trực tiếp
                            if not os.path.isfile(img_path):
                                raise FileNotFoundError(f"File ảnh không tồn tại: {img_path}")
                            pil_img = Image.open(img_path)
                        pil_img.thumbnail((200, 200))
                        img = ImageTk.PhotoImage(pil_img)
                        img_label = tk.Label(info_win, image=img)
                        img_label.image = img  # Giữ tham chiếu ảnh
                        img_label.grid(row=row, column=1, padx=5, pady=5)
                    except Exception as e:
                        tk.Label(info_win, text=f"Không tải được hình ảnh:\n{str(e)}").grid(row=row, column=1, padx=5, pady=5)
                else:
                    tk.Label(info_win, text="Không có hình ảnh").grid(row=row, column=1, padx=5, pady=5)
            elif key == "description":
                txt = tk.Text(info_win, width=50, height=5)
                txt.insert('1.0', product.get(key, ''))
                txt.grid(row=row, column=1, padx=5, pady=5)
                txt.config(state='normal' if self.current_user['role'] == 'Quản trị viên' else 'disabled')
                entries[key] = txt
            else:
                ent = tk.Entry(info_win, width=50)
                ent.insert(0, product.get(key, ''))
                ent.grid(row=row, column=1, padx=5, pady=5)
                if key == 'id':  # Không cho sửa mã sản phẩm
                    ent.config(state='disabled')
                else:
                    ent.config(state='normal' if self.current_user['role'] == 'Quản trị viên' else 'disabled')
                entries[key] = ent
            row += 1


    def add_product_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("Thêm sản phẩm mới")
        popup.geometry("500x400")

        labels = ["Mã sản phẩm", "Tên sản phẩm", "Giá", "Số lượng tồn", "Mô tả", "Hình ảnh", "Đánh giá (số)", "Số lượng mua"]
        entries = {}

        for i, label_text in enumerate(labels):
            tk.Label(popup, text=label_text).grid(row=i, column=0, sticky='w', pady=5, padx=5)
            entry = tk.Entry(popup, width=40)
            entry.grid(row=i, column=1, sticky='w', pady=5)
            entries[label_text] = entry

            # Nếu là trường Hình ảnh thì thêm nút chọn ảnh bên cạnh
            if label_text == "Hình ảnh":
                def choose_image():
                    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif")])
                    if file_path:
                        entries["Hình ảnh"].delete(0, tk.END)
                        entries["Hình ảnh"].insert(0, file_path)

                ctk.CTkButton(popup, text="Chọn ảnh", corner_radius=32, command=choose_image).grid(row=i, column=2, padx=10)

        def save_new_product():
            new_product = {
                'id': entries["Mã sản phẩm"].get().strip(),
                'name': entries["Tên sản phẩm"].get().strip(),
                'price': entries["Giá"].get().strip(),
                'qty': entries["Số lượng tồn"].get().strip(),
                'description': entries["Mô tả"].get().strip(),
                'image': entries["Hình ảnh"].get().strip(),
                'rate': entries["Đánh giá (số)"].get().strip(),
                'count': entries["Số lượng mua"].get().strip()
            }

            # Kiểm tra và chuyển đổi kiểu dữ liệu
            try:
                new_product['price'] = float(new_product['price'])
                new_product['qty'] = int(new_product['qty'])
                new_product['rate'] = float(new_product['rate'])
                new_product['count'] = int(new_product['count'])
            except ValueError:
                messagebox.showerror("Lỗi dữ liệu", "Giá, số lượng tồn, đánh giá và số lượng mua phải là số hợp lệ.")
                return

            if not new_product['id'] or not new_product['name']:
                messagebox.showerror("Lỗi dữ liệu", "Mã sản phẩm và Tên sản phẩm không được để trống.")
                return

            # Kiểm tra trùng ID
            products = JSONHandler.read(DATA_FILE)
            if any(p['id'] == new_product['id'] for p in products):
                messagebox.showerror("Lỗi", "Mã sản phẩm đã tồn tại.")
                return

            # Xử lý ảnh
            image_input = new_product['image']
            if image_input and os.path.isfile(image_input):
                ext = os.path.splitext(image_input)[-1]
                safe_name = new_product['name'].replace(" ", "_")
                image_filename = f"image-{safe_name}{ext}"
                image_dir = "image_products"
                if not os.path.exists(image_dir):
                    os.makedirs(image_dir)
                image_path = os.path.join("image_products", image_filename)
                shutil.copy(image_input, image_path)
                new_product['image'] = image_path  # Ghi lại đường dẫn mới
            else:
                messagebox.showerror("Lỗi ảnh", "Vui lòng chọn một ảnh hợp lệ từ máy.")
                return

            products.append(new_product)
            JSONHandler.write(DATA_FILE, products)
            self.load_products_to_tree()
            messagebox.showinfo("Thành công", "Thêm sản phẩm thành công!")
            popup.destroy()

        ctk.CTkButton(popup, text="Lưu", command=save_new_product, corner_radius=32).grid(row=len(labels), column=0, columnspan=3, pady=15)

    def edit_product(self):
        selected = self.products_tree.selection()
        if not selected:
            messagebox.showwarning("Chọn sản phẩm", "Vui lòng chọn sản phẩm để sửa")
            return

        values = self.products_tree.item(selected[0], 'values')
        product_id = values[0]

        # Tìm sản phẩm trong JSON
        products = JSONHandler.read(DATA_FILE)
        for product in products:
            if product['id'] == product_id:
                current_product = product
                break
        else:
            messagebox.showerror("Lỗi", "Không tìm thấy sản phẩm trong dữ liệu.")
            return

        popup = tk.Toplevel(self.root)
        popup.title("Sửa sản phẩm")
        popup.geometry("600x400")

        labels = [
            "Mã sản phẩm", "Tên sản phẩm", "Giá", "Số lượng tồn kho",
            "Mô tả", "Link ảnh", "Đánh giá", "Số lượng mua"
        ]

        keys = ['id', 'title', 'price', 'qty', 'description', 'image', 'rate', 'count']
        entries = {}

        for i, label in enumerate(labels):
            tk.Label(popup, text=label + ":").grid(row=i, column=0, padx=10, pady=5, sticky='e')
            entry = tk.Entry(popup, width=45)
            key = keys[i]
            value = current_product.get(key, '')
            if isinstance(value, (int, float)):
                value = str(value)
            entry.insert(0, value)
            if key == 'id':
                entry.configure(state='disabled')
            entry.grid(row=i, column=1, padx=10, pady=5, sticky='w')
            entries[key] = entry

        # Nút chọn ảnh
        def select_image():
            file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif")])
            if file_path:
                entries['image'].delete(0, tk.END)
                entries['image'].insert(0, file_path)

        ctk.CTkButton(popup, text="Chọn ảnh", corner_radius=32, command=select_image).grid(row=5, column=2, padx=5)

        # Hàm lưu
        def save_edit():
            try:
                title = entries['title'].get()
                price = float(entries['price'].get())
                qty = int(entries['qty'].get())
                description = entries['description'].get()
                image_input_path = entries['image'].get()
                rate = float(entries['rate'].get())
                count = int(entries['count'].get())

                old_image_path = current_product.get('image', '')
                if image_input_path != old_image_path:
                    if not (image_input_path.startswith('http://') or image_input_path.startswith('https://')):
                        ext = os.path.splitext(image_input_path)[1]
                        safe_name = title.replace(' ', '_')
                        dest_dir = 'image_products'
                        os.makedirs(dest_dir, exist_ok=True)
                        new_filename = f"image-{safe_name}{ext}"
                        dest_path = os.path.join(dest_dir, new_filename)
                        try:
                            shutil.copy(image_input_path, dest_path)
                            image_input_path = dest_path
                        except Exception as e:
                            messagebox.showerror("Lỗi", f"Lỗi khi sao chép ảnh: {str(e)}")
                            return

                for product in products:
                    if product['id'] == product_id:
                        product['title'] = title
                        product['price'] = price
                        product['qty'] = qty
                        product['description'] = description
                        product['image'] = image_input_path
                        product['rate'] = rate
                        product['count'] = count
                        break

                JSONHandler.write(DATA_FILE, products)
                self.load_products_to_tree()
                messagebox.showinfo("Thành công", "Đã cập nhật sản phẩm.")
                popup.destroy()

            except ValueError:
                messagebox.showerror("Lỗi", "Vui lòng nhập đúng định dạng cho giá, số lượng, đánh giá và số lượng mua.")

        ctk.CTkButton(popup, text="Lưu", corner_radius=32, command=save_edit).grid(row=8, columnspan=3, pady=20)


    def delete_product(self):
        selected = self.products_tree.selection()
        if not selected:
            messagebox.showwarning("Chọn sản phẩm", "Vui lòng chọn sản phẩm để xóa")
            return
        confirm = messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn xóa sản phẩm này?")
        if confirm:
            values = self.products_tree.item(selected[0], 'values')
            product_id = values[0]

            products = JSONHandler.read(DATA_FILE)

            # Tìm sản phẩm cần xóa để lấy thông tin ảnh
            product_to_delete = None
            for p in products:
                if p['id'] == product_id:
                    product_to_delete = p
                    break

            if product_to_delete:
                # Xóa file ảnh nếu nằm trong folder image_products
                image_path = product_to_delete.get('image', '')
                if image_path and os.path.isfile(image_path):
                    # Kiểm tra xem file ảnh có nằm trong thư mục image_products hay không
                    abs_image_path = os.path.abspath(image_path)
                    abs_image_dir = os.path.abspath('image_products')
                    if abs_image_path.startswith(abs_image_dir):
                        try:
                            os.remove(image_path)
                        except Exception as e:
                            messagebox.showwarning("Cảnh báo", f"Không thể xóa ảnh sản phẩm: {str(e)}")

                # Loại bỏ sản phẩm khỏi danh sách
                products = [p for p in products if p['id'] != product_id]

                JSONHandler.write(DATA_FILE, products)
                self.load_products_to_tree()
                messagebox.showinfo("Thông báo", "Xóa sản phẩm thành công!")
            else:
                messagebox.showerror("Lỗi", "Không tìm thấy sản phẩm cần xóa.")

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
