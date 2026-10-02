import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from nacl.exceptions import CryptoError

from accounts import get_accounts
from generator import generate_password
from vault import load_vault


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VAULT_PATH = PROJECT_ROOT / "data" / "vault.vault"


class VaultGitGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("VaultGit")
        self.geometry("920x560")
        self.minsize(820, 500)

        self.vault_data = None

        self.configure(
            bg="#111318"
        )

        self.setup_styles()
        self.show_unlock_screen()

    def setup_styles(self):
        style = ttk.Style(self)

        style.theme_use("clam")

        style.configure(
            "Vault.Treeview",
            background="#1b1f27",
            foreground="white",
            fieldbackground="#1b1f27",
            rowheight=34,
            borderwidth=0,
            font=("Segoe UI", 10),
        )

        style.configure(
            "Vault.Treeview.Heading",
            background="#262b35",
            foreground="white",
            borderwidth=0,
            font=("Segoe UI", 10, "bold"),
        )

        style.map(
            "Vault.Treeview",
            background=[
                ("selected", "#315efb")
            ],
        )

    def clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()

    def show_unlock_screen(self):
        self.clear_window()

        self.vault_data = None

        container = tk.Frame(
            self,
            bg="#111318",
        )

        container.place(
            relx=0.5,
            rely=0.5,
            anchor="center",
        )

        title = tk.Label(
            container,
            text="VaultGit",
            font=(
                "Segoe UI",
                30,
                "bold",
            ),
            bg="#111318",
            fg="white",
        )

        title.pack(
            pady=(0, 5)
        )

        subtitle = tk.Label(
            container,
            text="Bóveda personal cifrada",
            font=(
                "Segoe UI",
                11,
            ),
            bg="#111318",
            fg="#9ca3af",
        )

        subtitle.pack(
            pady=(0, 30)
        )

        card = tk.Frame(
            container,
            bg="#1b1f27",
            padx=35,
            pady=30,
        )

        card.pack()

        password_label = tk.Label(
            card,
            text="Contraseña maestra",
            font=(
                "Segoe UI",
                10,
                "bold",
            ),
            bg="#1b1f27",
            fg="white",
        )

        password_label.pack(
            anchor="w",
            pady=(0, 8),
        )

        self.password_var = tk.StringVar()

        self.password_entry = tk.Entry(
            card,
            textvariable=self.password_var,
            show="●",
            width=34,
            font=(
                "Segoe UI",
                12,
            ),
            bg="#252a34",
            fg="white",
            insertbackground="white",
            relief="flat",
        )

        self.password_entry.pack(
            ipady=9,
            pady=(0, 12),
        )

        self.password_entry.bind(
            "<Return>",
            lambda event: self.unlock_vault(),
        )

        self.show_password_var = tk.BooleanVar(
            value=False
        )

        show_password = tk.Checkbutton(
            card,
            text="Mostrar contraseña",
            variable=self.show_password_var,
            command=self.toggle_password,
            bg="#1b1f27",
            fg="#c7cbd4",
            activebackground="#1b1f27",
            activeforeground="white",
            selectcolor="#252a34",
            font=(
                "Segoe UI",
                9,
            ),
        )

        show_password.pack(
            anchor="w",
            pady=(0, 20),
        )

        unlock_button = tk.Button(
            card,
            text="Desbloquear bóveda",
            command=self.unlock_vault,
            width=28,
            font=(
                "Segoe UI",
                10,
                "bold",
            ),
            bg="#315efb",
            fg="white",
            activebackground="#2448c7",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            pady=8,
        )

        unlock_button.pack()

        if not VAULT_PATH.exists():
            warning = tk.Label(
                container,
                text=(
                    "No se encontró una bóveda. "
                    "Créala primero desde la versión de terminal."
                ),
                bg="#111318",
                fg="#f59e0b",
                font=(
                    "Segoe UI",
                    9,
                ),
            )

            warning.pack(
                pady=(20, 0)
            )

        self.password_entry.focus_set()

    def toggle_password(self):
        if self.show_password_var.get():
            self.password_entry.config(
                show=""
            )
        else:
            self.password_entry.config(
                show="●"
            )

    def unlock_vault(self):
        if not VAULT_PATH.exists():
            messagebox.showerror(
                "VaultGit",
                "No existe una bóveda todavía.",
            )
            return

        password = self.password_var.get()

        if not password:
            messagebox.showwarning(
                "VaultGit",
                "Introduce tu contraseña maestra.",
            )
            return

        try:
            vault_data = load_vault(
                VAULT_PATH,
                password,
            )

        except CryptoError:
            self.password_var.set("")

            messagebox.showerror(
                "VaultGit",
                (
                    "Contraseña incorrecta o "
                    "bóveda manipulada."
                ),
            )

            self.password_entry.focus_set()
            return

        except (
            OSError,
            ValueError,
            KeyError,
        ):
            self.password_var.set("")

            messagebox.showerror(
                "VaultGit",
                (
                    "La bóveda está dañada "
                    "o tiene un formato incompatible."
                ),
            )
            return

        self.password_var.set("")

        self.vault_data = vault_data

        password = None

        self.show_dashboard()

    def show_dashboard(self):
        self.clear_window()

        top_bar = tk.Frame(
            self,
            bg="#181b21",
            height=70,
        )

        top_bar.pack(
            fill="x"
        )

        top_bar.pack_propagate(
            False
        )

        title = tk.Label(
            top_bar,
            text="🔐 VaultGit",
            font=(
                "Segoe UI",
                20,
                "bold",
            ),
            bg="#181b21",
            fg="white",
        )

        title.pack(
            side="left",
            padx=25,
        )

        lock_button = tk.Button(
            top_bar,
            text="Bloquear",
            command=self.lock_vault,
            font=(
                "Segoe UI",
                10,
                "bold",
            ),
            bg="#2b303a",
            fg="white",
            activebackground="#3b414d",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=18,
            pady=7,
        )

        lock_button.pack(
            side="right",
            padx=25,
        )

        body = tk.Frame(
            self,
            bg="#111318",
        )

        body.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=25,
        )

        header = tk.Frame(
            body,
            bg="#111318",
        )

        header.pack(
            fill="x",
            pady=(0, 15),
        )

        accounts = get_accounts(
            self.vault_data
        )

        accounts_title = tk.Label(
            header,
            text="Mis cuentas",
            font=(
                "Segoe UI",
                18,
                "bold",
            ),
            bg="#111318",
            fg="white",
        )

        accounts_title.pack(
            side="left"
        )

        count_label = tk.Label(
            header,
            text=f"{len(accounts)} almacenadas",
            font=(
                "Segoe UI",
                10,
            ),
            bg="#111318",
            fg="#9ca3af",
        )

        count_label.pack(
            side="left",
            padx=12,
        )

        generator_button = tk.Button(
            header,
            text="Generar contraseña",
            command=self.open_password_generator,
            font=(
                "Segoe UI",
                9,
                "bold",
            ),
            bg="#252a34",
            fg="white",
            activebackground="#343a46",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=7,
        )

        generator_button.pack(
            side="right"
        )

        table_frame = tk.Frame(
            body,
            bg="#111318",
        )

        table_frame.pack(
            fill="both",
            expand=True,
        )

        columns = (
            "service",
            "username",
        )

        self.accounts_table = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            style="Vault.Treeview",
        )

        self.accounts_table.heading(
            "service",
            text="Servicio",
        )

        self.accounts_table.heading(
            "username",
            text="Usuario / Correo",
        )

        self.accounts_table.column(
            "service",
            width=260,
            anchor="w",
        )

        self.accounts_table.column(
            "username",
            width=500,
            anchor="w",
        )

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.accounts_table.yview,
        )

        self.accounts_table.configure(
            yscrollcommand=scrollbar.set
        )

        self.accounts_table.pack(
            side="left",
            fill="both",
            expand=True,
        )

        scrollbar.pack(
            side="right",
            fill="y",
        )

        self.refresh_accounts()

    def refresh_accounts(self):
        for item in self.accounts_table.get_children():
            self.accounts_table.delete(
                item
            )

        for account in get_accounts(
            self.vault_data
        ):
            self.accounts_table.insert(
                "",
                "end",
                values=(
                    account.get(
                        "service",
                        "",
                    ),
                    account.get(
                        "username",
                        "",
                    ),
                ),
            )

    def open_password_generator(self):
        window = tk.Toplevel(
            self
        )

        window.title(
            "Generador de contraseñas"
        )

        window.geometry(
            "440x260"
        )

        window.resizable(
            False,
            False,
        )

        window.configure(
            bg="#181b21"
        )

        title = tk.Label(
            window,
            text="Generador seguro",
            font=(
                "Segoe UI",
                17,
                "bold",
            ),
            bg="#181b21",
            fg="white",
        )

        title.pack(
            pady=(25, 15)
        )

        length_frame = tk.Frame(
            window,
            bg="#181b21",
        )

        length_frame.pack()

        tk.Label(
            length_frame,
            text="Longitud:",
            bg="#181b21",
            fg="white",
            font=(
                "Segoe UI",
                10,
            ),
        ).pack(
            side="left",
            padx=(0, 8),
        )

        length_var = tk.StringVar(
            value="20"
        )

        length_entry = tk.Entry(
            length_frame,
            textvariable=length_var,
            width=6,
            justify="center",
            font=(
                "Segoe UI",
                10,
            ),
        )

        length_entry.pack(
            side="left"
        )

        password_var = tk.StringVar()

        password_entry = tk.Entry(
            window,
            textvariable=password_var,
            width=38,
            justify="center",
            font=(
                "Consolas",
                11,
            ),
            state="readonly",
        )

        password_entry.pack(
            pady=20,
            ipady=7,
        )

        def generate():
            value = length_var.get().strip()

            if not value.isdigit():
                messagebox.showwarning(
                    "VaultGit",
                    "Introduce una longitud válida.",
                    parent=window,
                )
                return

            length = int(value)

            try:
                password = generate_password(
                    length=length
                )

            except ValueError as error:
                messagebox.showwarning(
                    "VaultGit",
                    str(error),
                    parent=window,
                )
                return

            password_var.set(
                password
            )

        generate_button = tk.Button(
            window,
            text="Generar",
            command=generate,
            font=(
                "Segoe UI",
                10,
                "bold",
            ),
            bg="#315efb",
            fg="white",
            activebackground="#2448c7",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=30,
            pady=7,
        )

        generate_button.pack()

    def lock_vault(self):
        self.vault_data = None
        self.show_unlock_screen()


def main():
    app = VaultGitGUI()
    app.mainloop()


if __name__ == "__main__":
    main()