import binascii
import copy
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, simpledialog, ttk

from nacl.exceptions import CryptoError

from accounts import (
    add_account,
    delete_account,
    get_account_by_id,
    get_accounts,
    search_accounts,
    update_account,
)

from generator import generate_password
from password_policy import validate_master_password

from backup import (
    create_backup,
    list_backups,
    restore_backup,
)

from vault import (
    create_vault,
    get_vault_kdf_profile,
    migrate_vault_kdf,
    needs_kdf_upgrade,
    save_vault_with_session,
    unlock_vault,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VAULT_PATH = PROJECT_ROOT / "data" / "vault.vault"
BACKUP_DIR = PROJECT_ROOT / "data" / "backups"


class VaultGitGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("VaultGit")
        self.geometry("1000x620")
        self.minsize(900, 560)
        self.configure(bg="#111318")

        # Datos sensibles disponibles solamente
        # mientras la bóveda permanece desbloqueada.
        self.vault_data = None
        self.session = None

        # Elementos de interfaz.
        self.search_var = None
        self.accounts_table = None
        self.count_label = None

        # Bloqueo automático.
        self.auto_lock_after_id = None
        self.auto_lock_minutes = 5

        # Portapapeles temporal.
        self.clipboard_after_id = None
        self.clipboard_secret = None
        self.clipboard_timeout_seconds = 30

        self.setup_styles()

        self.protocol(
            "WM_DELETE_WINDOW",
            self.on_close,
        )

        if VAULT_PATH.exists():
            self.show_unlock_screen()
        else:
            self.show_create_vault_screen()

    # =========================================================
    # ESTILOS
    # =========================================================

    def setup_styles(self):
        style = ttk.Style(self)

        style.theme_use("clam")

        style.configure(
            "Vault.Treeview",
            background="#1b1f27",
            foreground="white",
            fieldbackground="#1b1f27",
            rowheight=36,
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
            foreground=[
                ("selected", "white")
            ],
        )

    # =========================================================
    # BLOQUEO AUTOMÁTICO
    # =========================================================

    def start_inactivity_monitor(self):
        """
        Empieza a observar actividad de teclado y ratón.
        """

        self.bind_all(
            "<Any-KeyPress>",
            self.register_activity,
        )

        self.bind_all(
            "<Any-Button>",
            self.register_activity,
        )

        self.reset_auto_lock_timer()

    def register_activity(self, event=None):
        """
        Cada interacción reinicia el contador.
        """

        if (
            self.vault_data is not None
            and self.session is not None
        ):
            self.reset_auto_lock_timer()

    def reset_auto_lock_timer(self):
        """
        Reinicia el temporizador de bloqueo.
        """

        if self.auto_lock_after_id is not None:
            try:
                self.after_cancel(
                    self.auto_lock_after_id
                )
            except tk.TclError:
                pass

        milliseconds = int(
            self.auto_lock_minutes
            * 60
            * 1000
        )

        self.auto_lock_after_id = self.after(
            milliseconds,
            self.auto_lock_due_to_inactivity,
        )

    def auto_lock_due_to_inactivity(self):
        """
        Bloquea VaultGit cuando se alcanza
        el tiempo máximo sin actividad.
        """

        self.auto_lock_after_id = None

        if (
            self.vault_data is None
            or self.session is None
        ):
            return

        self.lock_vault()

        messagebox.showinfo(
            "VaultGit",
            (
                "La bóveda se bloqueó "
                "automáticamente por inactividad."
            ),
        )

    # =========================================================
    # PORTAPAPELES TEMPORAL
    # =========================================================

    def cancel_clipboard_timer(self):
        """
        Cancela el temporizador pendiente del portapapeles.
        """

        if self.clipboard_after_id is not None:
            try:
                self.after_cancel(
                    self.clipboard_after_id
                )
            except tk.TclError:
                pass

            self.clipboard_after_id = None

    def copy_sensitive_to_clipboard(self, value):
        """
        Copia un secreto al portapapeles y programa
        su limpieza automática.
        """

        if not value:
            messagebox.showwarning(
                "VaultGit",
                "No hay una contraseña para copiar.",
            )
            return

        self.cancel_clipboard_timer()

        try:
            self.clipboard_clear()
            self.clipboard_append(value)

            # Fuerza a Windows/Tk a publicar el contenido.
            self.update()

        except tk.TclError:
            messagebox.showerror(
                "VaultGit",
                "No se pudo acceder al portapapeles.",
            )
            return

        self.clipboard_secret = value

        self.clipboard_after_id = self.after(
            self.clipboard_timeout_seconds * 1000,
            self.clear_clipboard_due_to_timeout,
        )

        messagebox.showinfo(
            "VaultGit",
            (
                "Contraseña copiada.\n\n"
                "VaultGit intentará retirarla del "
                "portapapeles en 30 segundos."
            ),
        )

    def clear_clipboard_due_to_timeout(self):
        """
        Intenta limpiar el secreto al vencer el tiempo.
        """

        self.clipboard_after_id = None

        self.clear_sensitive_clipboard(
            cancel_timer=False
        )

    def clear_sensitive_clipboard(
        self,
        cancel_timer=True,
    ):
        """
        Limpia el portapapeles únicamente si todavía
        contiene exactamente el secreto que VaultGit copió.

        Si el usuario copió otra cosa después, VaultGit
        no modifica ese nuevo contenido.
        """

        if cancel_timer:
            self.cancel_clipboard_timer()

        tracked_secret = self.clipboard_secret

        # Dejamos de conservar nuestra referencia al secreto
        # independientemente del estado actual del portapapeles.
        self.clipboard_secret = None

        if tracked_secret is None:
            return False

        try:
            current_value = self.clipboard_get()
        except tk.TclError:
            return False

        if current_value != tracked_secret:
            return False

        try:
            self.clipboard_clear()
            self.update()
        except tk.TclError:
            return False

        return True

    # =========================================================
    # UTILIDADES GENERALES
    # =========================================================

    def clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()

    def create_primary_button(
        self,
        parent,
        text,
        command,
        width=None,
    ):
        return tk.Button(
            parent,
            text=text,
            command=command,
            width=width,
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
            padx=18,
            pady=8,
        )

    def create_secondary_button(
        self,
        parent,
        text,
        command,
    ):
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=(
                "Segoe UI",
                9,
                "bold",
            ),
            bg="#292e38",
            fg="white",
            activebackground="#3a404c",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=7,
        )

    # =========================================================
    # CREAR BÓVEDA
    # =========================================================

    def show_create_vault_screen(self):
        self.clear_window()

        container = tk.Frame(
            self,
            bg="#111318",
        )

        container.place(
            relx=0.5,
            rely=0.5,
            anchor="center",
        )

        tk.Label(
            container,
            text="VaultGit",
            font=(
                "Segoe UI",
                30,
                "bold",
            ),
            bg="#111318",
            fg="white",
        ).pack(
            pady=(0, 5)
        )

        tk.Label(
            container,
            text="Crear nueva bóveda cifrada",
            font=(
                "Segoe UI",
                11,
            ),
            bg="#111318",
            fg="#9ca3af",
        ).pack(
            pady=(0, 25)
        )

        card = tk.Frame(
            container,
            bg="#1b1f27",
            padx=35,
            pady=30,
        )

        card.pack()

        tk.Label(
            card,
            text="Contraseña maestra",
            bg="#1b1f27",
            fg="white",
            font=(
                "Segoe UI",
                10,
                "bold",
            ),
        ).pack(
            anchor="w",
            pady=(0, 7),
        )

        password_var = tk.StringVar()

        password_entry = tk.Entry(
            card,
            textvariable=password_var,
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

        password_entry.pack(
            ipady=8,
            pady=(0, 15),
        )

        tk.Label(
            card,
            text="Confirmar contraseña",
            bg="#1b1f27",
            fg="white",
            font=(
                "Segoe UI",
                10,
                "bold",
            ),
        ).pack(
            anchor="w",
            pady=(0, 7),
        )

        confirmation_var = tk.StringVar()

        confirmation_entry = tk.Entry(
            card,
            textvariable=confirmation_var,
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

        confirmation_entry.pack(
            ipady=8,
            pady=(0, 10),
        )

        show_var = tk.BooleanVar(
            value=False
        )

        def toggle_passwords():
            show_value = (
                ""
                if show_var.get()
                else "●"
            )

            password_entry.config(
                show=show_value
            )

            confirmation_entry.config(
                show=show_value
            )

        tk.Checkbutton(
            card,
            text="Mostrar contraseñas",
            variable=show_var,
            command=toggle_passwords,
            bg="#1b1f27",
            fg="#c7cbd4",
            activebackground="#1b1f27",
            activeforeground="white",
            selectcolor="#252a34",
            font=(
                "Segoe UI",
                9,
            ),
        ).pack(
            anchor="w",
            pady=(0, 15),
        )

        tk.Label(
            card,
            text=(
                "Utiliza una frase maestra "
                "larga, única y difícil de adivinar."
            ),
            bg="#1b1f27",
            fg="#9ca3af",
            font=(
                "Segoe UI",
                8,
            ),
        ).pack(
            pady=(0, 15),
        )

        def create_new_vault():
            password = password_var.get()
            confirmation = confirmation_var.get()

            if not password:
                messagebox.showwarning(
                    "VaultGit",
                    "Introduce una contraseña maestra.",
                )
                return

            password_is_valid, password_error = (
                validate_master_password(password)
            )

            if not password_is_valid:
                messagebox.showwarning(
                    "VaultGit",
                    password_error,
                )
                return

            if password != confirmation:
                messagebox.showwarning(
                    "VaultGit",
                    "Las contraseñas no coinciden.",
                )
                return

            initial_data = {
                "accounts": []
            }

            try:
                create_vault(
                    VAULT_PATH,
                    password,
                    initial_data,
                )

                vault_data, session = (
                    unlock_vault(
                        VAULT_PATH,
                        password,
                    )
                )

            except (
                OSError,
                ValueError,
                KeyError,
                TypeError,
                binascii.Error,
            ):
                messagebox.showerror(
                    "VaultGit",
                    "No se pudo crear la bóveda.",
                )
                return

            password_var.set("")
            confirmation_var.set("")

            self.vault_data = vault_data
            self.session = session

            password = None
            confirmation = None

            self.show_dashboard()

        self.create_primary_button(
            card,
            "Crear bóveda",
            create_new_vault,
            width=28,
        ).pack()

        password_entry.focus_set()

    # =========================================================
    # DESBLOQUEO
    # =========================================================

    def show_unlock_screen(self):
        self.clear_window()

        self.vault_data = None
        self.session = None

        container = tk.Frame(
            self,
            bg="#111318",
        )

        container.place(
            relx=0.5,
            rely=0.5,
            anchor="center",
        )

        tk.Label(
            container,
            text="VaultGit",
            font=(
                "Segoe UI",
                30,
                "bold",
            ),
            bg="#111318",
            fg="white",
        ).pack(
            pady=(0, 5)
        )

        tk.Label(
            container,
            text="Bóveda personal cifrada",
            font=(
                "Segoe UI",
                11,
            ),
            bg="#111318",
            fg="#9ca3af",
        ).pack(
            pady=(0, 30)
        )

        card = tk.Frame(
            container,
            bg="#1b1f27",
            padx=35,
            pady=30,
        )

        card.pack()

        tk.Label(
            card,
            text="Contraseña maestra",
            font=(
                "Segoe UI",
                10,
                "bold",
            ),
            bg="#1b1f27",
            fg="white",
        ).pack(
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
            lambda event: self.unlock_vault_gui(),
        )

        self.show_password_var = tk.BooleanVar(
            value=False
        )

        tk.Checkbutton(
            card,
            text="Mostrar contraseña",
            variable=self.show_password_var,
            command=self.toggle_master_password,
            bg="#1b1f27",
            fg="#c7cbd4",
            activebackground="#1b1f27",
            activeforeground="white",
            selectcolor="#252a34",
            font=(
                "Segoe UI",
                9,
            ),
        ).pack(
            anchor="w",
            pady=(0, 20),
        )

        self.create_primary_button(
            card,
            "Desbloquear bóveda",
            self.unlock_vault_gui,
            width=28,
        ).pack()

        self.password_entry.focus_set()

    def toggle_master_password(self):
        self.password_entry.config(
            show=(
                ""
                if self.show_password_var.get()
                else "●"
            )
        )

    def unlock_vault_gui(self):
        password = self.password_var.get()

        if not password:
            messagebox.showwarning(
                "VaultGit",
                "Introduce tu contraseña maestra.",
            )
            return

        try:
            vault_data, session = unlock_vault(
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
            TypeError,
            binascii.Error,
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
        self.session = session

        password = None

        self.show_dashboard()

    # =========================================================
    # DASHBOARD
    # =========================================================

    def show_dashboard(self):
        self.clear_window()

        self.start_inactivity_monitor()

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

        tk.Label(
            top_bar,
            text="🔐 VaultGit",
            font=(
                "Segoe UI",
                20,
                "bold",
            ),
            bg="#181b21",
            fg="white",
        ).pack(
            side="left",
            padx=25,
        )

        self.create_secondary_button(
            top_bar,
            "Bloquear",
            self.lock_vault,
        ).pack(
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

        tk.Label(
            header,
            text="Mis cuentas",
            font=(
                "Segoe UI",
                18,
                "bold",
            ),
            bg="#111318",
            fg="white",
        ).pack(
            side="left"
        )

        self.count_label = tk.Label(
            header,
            text="",
            font=(
                "Segoe UI",
                10,
            ),
            bg="#111318",
            fg="#9ca3af",
        )

        self.count_label.pack(
            side="left",
            padx=12,
        )

        self.create_primary_button(
            header,
            "+ Añadir cuenta",
            self.open_add_account,
        ).pack(
            side="right",
            padx=(10, 0),
        )

        self.create_secondary_button(
            header,
            "Generar contraseña",
            self.open_password_generator,
        ).pack(
            side="right",
        )

        self.create_secondary_button(
            header,
            "Backups",
            self.open_backups_window,
        ).pack(
            side="right",
            padx=(0, 10),
        )

        self.create_secondary_button(
            header,
            "Seguridad",
            self.open_security_window,
        ).pack(
            side="right",
            padx=(0, 10),
        )

        search_frame = tk.Frame(
            body,
            bg="#111318",
        )

        search_frame.pack(
            fill="x",
            pady=(0, 15),
        )

        tk.Label(
            search_frame,
            text="Buscar:",
            bg="#111318",
            fg="#c7cbd4",
            font=(
                "Segoe UI",
                10,
            ),
        ).pack(
            side="left",
            padx=(0, 8),
        )

        self.search_var = tk.StringVar()

        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=(
                "Segoe UI",
                10,
            ),
            bg="#252a34",
            fg="white",
            insertbackground="white",
            relief="flat",
        )

        search_entry.pack(
            side="left",
            fill="x",
            expand=True,
            ipady=7,
        )

        self.search_var.trace_add(
            "write",
            lambda *_: self.refresh_accounts(),
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
            selectmode="browse",
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
            width=300,
            anchor="w",
        )

        self.accounts_table.column(
            "username",
            width=520,
            anchor="w",
        )

        self.accounts_table.bind(
            "<Double-1>",
            lambda event: self.open_account_details(),
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

        actions = tk.Frame(
            body,
            bg="#111318",
        )

        actions.pack(
            fill="x",
            pady=(15, 0),
        )

        self.create_secondary_button(
            actions,
            "Ver detalles",
            self.open_account_details,
        ).pack(
            side="left"
        )

        self.create_secondary_button(
            actions,
            "Editar",
            self.open_edit_account,
        ).pack(
            side="left",
            padx=8,
        )

        delete_button = tk.Button(
            actions,
            text="Eliminar",
            command=self.delete_selected_account,
            font=(
                "Segoe UI",
                9,
                "bold",
            ),
            bg="#3a2226",
            fg="#ffb4b4",
            activebackground="#512b31",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=7,
        )

        delete_button.pack(
            side="left"
        )

        self.refresh_accounts()

    # =========================================================
    # LISTADO Y BÚSQUEDA
    # =========================================================

    def refresh_accounts(self):
        if self.accounts_table is None:
            return

        for item in self.accounts_table.get_children():
            self.accounts_table.delete(
                item
            )

        query = ""

        if self.search_var is not None:
            query = self.search_var.get().strip()

        if query:
            accounts = search_accounts(
                self.vault_data,
                query,
            )
        else:
            accounts = get_accounts(
                self.vault_data
            )

        for account in accounts:
            account_id = account.get(
                "id"
            )

            if not account_id:
                continue

            self.accounts_table.insert(
                "",
                "end",
                iid=account_id,
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

        total = len(
            get_accounts(
                self.vault_data
            )
        )

        if self.count_label is not None:
            self.count_label.config(
                text=f"{total} almacenadas"
            )

    def get_selected_account(self):
        selection = (
            self.accounts_table.selection()
        )

        if not selection:
            messagebox.showinfo(
                "VaultGit",
                "Selecciona una cuenta primero.",
            )
            return None

        account_id = selection[0]

        account = get_account_by_id(
            self.vault_data,
            account_id,
        )

        if account is None:
            messagebox.showerror(
                "VaultGit",
                "No se encontró la cuenta.",
            )
            return None

        return account

    # =========================================================
    # DETALLES
    # =========================================================

    def open_account_details(self):
        account = self.get_selected_account()

        if account is None:
            return

        window = tk.Toplevel(
            self
        )

        window.title(
            "Detalles de cuenta"
        )

        window.geometry(
            "560x480"
        )

        window.resizable(
            False,
            False,
        )

        window.configure(
            bg="#181b21"
        )

        tk.Label(
            window,
            text=account.get(
                "service",
                "Cuenta",
            ),
            font=(
                "Segoe UI",
                20,
                "bold",
            ),
            bg="#181b21",
            fg="white",
        ).pack(
            pady=(25, 20)
        )

        card = tk.Frame(
            window,
            bg="#22262f",
            padx=25,
            pady=20,
        )

        card.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=(0, 25),
        )

        self.detail_row(
            card,
            "Usuario / correo",
            account.get(
                "username",
                "",
            ),
        )

        password_frame = tk.Frame(
            card,
            bg="#22262f",
        )

        password_frame.pack(
            fill="x",
            pady=10,
        )

        tk.Label(
            password_frame,
            text="Contraseña",
            width=18,
            anchor="w",
            bg="#22262f",
            fg="#9ca3af",
            font=(
                "Segoe UI",
                9,
                "bold",
            ),
        ).pack(
            side="left"
        )

        hidden_password = tk.StringVar(
            value="●●●●●●●●●●●●"
        )

        tk.Label(
            password_frame,
            textvariable=hidden_password,
            anchor="w",
            bg="#22262f",
            fg="white",
            font=(
                "Consolas",
                10,
            ),
        ).pack(
            side="left",
            fill="x",
            expand=True,
        )

        is_visible = {
            "value": False
        }

        def toggle_account_password():
            is_visible["value"] = (
                not is_visible["value"]
            )

            if is_visible["value"]:
                hidden_password.set(
                    account.get(
                        "password",
                        "",
                    )
                )

                show_button.config(
                    text="Ocultar"
                )

            else:
                hidden_password.set(
                    "●●●●●●●●●●●●"
                )

                show_button.config(
                    text="Mostrar"
                )

        show_button = tk.Button(
            password_frame,
            text="Mostrar",
            command=toggle_account_password,
            font=(
                "Segoe UI",
                8,
                "bold",
            ),
            bg="#303641",
            fg="white",
            activebackground="#414956",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=4,
        )

        show_button.pack(
            side="right"
        )

        copy_button = tk.Button(
            password_frame,
            text="Copiar",
            command=lambda: self.copy_sensitive_to_clipboard(
                account.get(
                    "password",
                    "",
                )
            ),
            font=(
                "Segoe UI",
                8,
                "bold",
            ),
            bg="#303641",
            fg="white",
            activebackground="#414956",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=4,
        )

        copy_button.pack(
            side="right",
            padx=(0, 6),
        )

        self.detail_row(
            card,
            "URL",
            account.get(
                "url",
                "",
            )
            or "Sin URL",
        )

        self.detail_row(
            card,
            "Notas",
            account.get(
                "notes",
                "",
            )
            or "Sin notas",
        )

    def detail_row(
        self,
        parent,
        title,
        value,
    ):
        row = tk.Frame(
            parent,
            bg="#22262f",
        )

        row.pack(
            fill="x",
            pady=10,
        )

        tk.Label(
            row,
            text=title,
            width=18,
            anchor="w",
            bg="#22262f",
            fg="#9ca3af",
            font=(
                "Segoe UI",
                9,
                "bold",
            ),
        ).pack(
            side="left"
        )

        tk.Label(
            row,
            text=value,
            anchor="w",
            bg="#22262f",
            fg="white",
            wraplength=280,
            justify="left",
            font=(
                "Segoe UI",
                10,
            ),
        ).pack(
            side="left",
            fill="x",
            expand=True,
        )

    # =========================================================
    # AÑADIR / EDITAR
    # =========================================================

    def open_add_account(self):
        self.open_account_form(
            account=None
        )

    def open_edit_account(self):
        account = self.get_selected_account()

        if account is None:
            return

        self.open_account_form(
            account=account
        )

    def open_account_form(
        self,
        account=None,
    ):
        editing = (
            account is not None
        )

        window = tk.Toplevel(
            self
        )

        window.title(
            (
                "Editar cuenta"
                if editing
                else "Nueva cuenta"
            )
        )

        window.geometry(
            "560x610"
        )

        window.resizable(
            False,
            False,
        )

        window.configure(
            bg="#181b21"
        )

        tk.Label(
            window,
            text=(
                "Editar cuenta"
                if editing
                else "Nueva cuenta"
            ),
            font=(
                "Segoe UI",
                20,
                "bold",
            ),
            bg="#181b21",
            fg="white",
        ).pack(
            pady=(25, 20)
        )

        form = tk.Frame(
            window,
            bg="#181b21",
        )

        form.pack(
            fill="both",
            expand=True,
            padx=40,
        )

        service_var = tk.StringVar(
            value=(
                account.get(
                    "service",
                    "",
                )
                if editing
                else ""
            )
        )

        username_var = tk.StringVar(
            value=(
                account.get(
                    "username",
                    "",
                )
                if editing
                else ""
            )
        )

        password_var = tk.StringVar()

        url_var = tk.StringVar(
            value=(
                account.get(
                    "url",
                    "",
                )
                if editing
                else ""
            )
        )

        self.form_label(
            form,
            "Servicio",
        )

        service_entry = self.form_entry(
            form,
            service_var,
        )

        self.form_label(
            form,
            "Usuario / correo",
        )

        self.form_entry(
            form,
            username_var,
        )

        password_title = (
            "Nueva contraseña "
            "(vacía = conservar)"
            if editing
            else "Contraseña"
        )

        self.form_label(
            form,
            password_title,
        )

        password_row = tk.Frame(
            form,
            bg="#181b21",
        )

        password_row.pack(
            fill="x",
            pady=(0, 12),
        )

        password_entry = tk.Entry(
            password_row,
            textvariable=password_var,
            show="●",
            font=(
                "Segoe UI",
                10,
            ),
            bg="#252a34",
            fg="white",
            insertbackground="white",
            relief="flat",
        )

        password_entry.pack(
            side="left",
            fill="x",
            expand=True,
            ipady=7,
        )

        show_password_state = {
            "visible": False
        }

        def toggle_password():
            show_password_state[
                "visible"
            ] = not show_password_state[
                "visible"
            ]

            password_entry.config(
                show=(
                    ""
                    if show_password_state[
                        "visible"
                    ]
                    else "●"
                )
            )

            show_button.config(
                text=(
                    "Ocultar"
                    if show_password_state[
                        "visible"
                    ]
                    else "Mostrar"
                )
            )

        show_button = tk.Button(
            password_row,
            text="Mostrar",
            command=toggle_password,
            bg="#303641",
            fg="white",
            activebackground="#414956",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=6,
        )

        show_button.pack(
            side="left",
            padx=(8, 0),
        )

        def generate_into_field():
            generated = generate_password(
                length=20
            )

            password_var.set(
                generated
            )

        self.create_secondary_button(
            form,
            "Generar contraseña",
            generate_into_field,
        ).pack(
            anchor="w",
            pady=(0, 12),
        )

        self.form_label(
            form,
            "URL",
        )

        self.form_entry(
            form,
            url_var,
        )

        self.form_label(
            form,
            "Notas",
        )

        notes_text = tk.Text(
            form,
            height=5,
            font=(
                "Segoe UI",
                10,
            ),
            bg="#252a34",
            fg="white",
            insertbackground="white",
            relief="flat",
            wrap="word",
        )

        notes_text.pack(
            fill="x",
            pady=(0, 18),
        )

        if editing:
            notes_text.insert(
                "1.0",
                account.get(
                    "notes",
                    "",
                ),
            )

        buttons = tk.Frame(
            form,
            bg="#181b21",
        )

        buttons.pack(
            fill="x"
        )

        self.create_secondary_button(
            buttons,
            "Cancelar",
            window.destroy,
        ).pack(
            side="right"
        )

        def save_account():
            service = (
                service_var.get().strip()
            )

            username = (
                username_var.get().strip()
            )

            password = (
                password_var.get()
            )

            url = (
                url_var.get().strip()
            )

            notes = (
                notes_text.get(
                    "1.0",
                    "end-1c",
                ).strip()
            )

            if not service:
                messagebox.showwarning(
                    "VaultGit",
                    (
                        "El servicio no puede "
                        "estar vacío."
                    ),
                    parent=window,
                )
                return

            if (
                not editing
                and not password
            ):
                messagebox.showwarning(
                    "VaultGit",
                    (
                        "Introduce una contraseña "
                        "para la cuenta."
                    ),
                    parent=window,
                )
                return

            candidate_data = copy.deepcopy(
                self.vault_data
            )

            if editing:
                updated = update_account(
                    candidate_data,
                    account["id"],
                    service=service,
                    username=username,
                    password=(
                        password
                        if password
                        else None
                    ),
                    url=url,
                    notes=notes,
                )

                if not updated:
                    messagebox.showerror(
                        "VaultGit",
                        (
                            "No se pudo encontrar "
                            "la cuenta."
                        ),
                        parent=window,
                    )
                    return

            else:
                add_account(
                    candidate_data,
                    service,
                    username,
                    password,
                    url,
                    notes,
                )

            try:
                # Creamos una copia cifrada del estado actual
                # antes de modificar la bóveda.
                create_backup(
                    VAULT_PATH,
                    BACKUP_DIR,
                    keep=10,
                )

                save_vault_with_session(
                    VAULT_PATH,
                    self.session,
                    candidate_data,
                )

            except (
                OSError,
                ValueError,
                KeyError,
                TypeError,
            ):
                messagebox.showerror(
                    "VaultGit",
                    (
                        "No se pudieron guardar "
                        "los cambios."
                    ),
                    parent=window,
                )
                return

            self.vault_data = candidate_data

            password_var.set("")

            self.refresh_accounts()

            window.destroy()

        self.create_primary_button(
            buttons,
            (
                "Guardar cambios"
                if editing
                else "Guardar cuenta"
            ),
            save_account,
        ).pack(
            side="right",
            padx=(0, 10),
        )

        service_entry.focus_set()

    def form_label(
        self,
        parent,
        text,
    ):
        tk.Label(
            parent,
            text=text,
            bg="#181b21",
            fg="#c7cbd4",
            font=(
                "Segoe UI",
                9,
                "bold",
            ),
        ).pack(
            anchor="w",
            pady=(0, 5),
        )

    def form_entry(
        self,
        parent,
        variable,
    ):
        entry = tk.Entry(
            parent,
            textvariable=variable,
            font=(
                "Segoe UI",
                10,
            ),
            bg="#252a34",
            fg="white",
            insertbackground="white",
            relief="flat",
        )

        entry.pack(
            fill="x",
            ipady=7,
            pady=(0, 12),
        )

        return entry

    # =========================================================
    # ELIMINAR
    # =========================================================

    def delete_selected_account(self):
        account = self.get_selected_account()

        if account is None:
            return

        confirmed = messagebox.askyesno(
            "Eliminar cuenta",
            (
                "¿Seguro que quieres eliminar "
                f"'{account.get('service', '')}'?\n\n"
                "Esta acción no se puede deshacer."
            ),
        )

        if not confirmed:
            return

        candidate_data = copy.deepcopy(
            self.vault_data
        )

        deleted = delete_account(
            candidate_data,
            account["id"],
        )

        if not deleted:
            messagebox.showerror(
                "VaultGit",
                "No se pudo eliminar la cuenta.",
            )
            return

        try:
            # Creamos una copia cifrada del estado actual
            # antes de eliminar la cuenta.
            create_backup(
                VAULT_PATH,
                BACKUP_DIR,
                keep=10,
            )

            save_vault_with_session(
                VAULT_PATH,
                self.session,
                candidate_data,
            )

        except (
            OSError,
            ValueError,
            KeyError,
            TypeError,
        ):
            messagebox.showerror(
                "VaultGit",
                (
                    "No se pudieron guardar "
                    "los cambios."
                ),
            )
            return

        self.vault_data = candidate_data

        self.refresh_accounts()


    # =========================================================
    # SEGURIDAD / MIGRACION KDF
    # =========================================================

    def open_security_window(self):
        window = tk.Toplevel(
            self
        )

        window.title(
            "Seguridad de la bóveda"
        )

        window.geometry(
            "660x500"
        )

        window.resizable(
            False,
            False,
        )

        window.configure(
            bg="#181b21"
        )

        tk.Label(
            window,
            text="Seguridad de la bóveda",
            font=(
                "Segoe UI",
                19,
                "bold",
            ),
            bg="#181b21",
            fg="white",
        ).pack(
            pady=(26, 6)
        )

        tk.Label(
            window,
            text=(
                "VaultGit puede actualizar el coste de Argon2id "
                "sin cambiar tus credenciales."
            ),
            font=(
                "Segoe UI",
                9,
            ),
            bg="#181b21",
            fg="#9ca3af",
        ).pack(
            pady=(0, 20)
        )

        card = tk.Frame(
            window,
            bg="#22262f",
            padx=26,
            pady=22,
        )

        card.pack(
            fill="x",
            padx=34,
        )

        current_title = tk.Label(
            card,
            text="Perfil Argon2id actual",
            font=(
                "Segoe UI",
                10,
                "bold",
            ),
            bg="#22262f",
            fg="#9ca3af",
        )

        current_title.pack(
            anchor="w"
        )

        current_profile_label = tk.Label(
            card,
            text="",
            font=(
                "Consolas",
                11,
            ),
            bg="#22262f",
            fg="white",
            justify="left",
        )

        current_profile_label.pack(
            anchor="w",
            pady=(6, 18),
        )

        recommended_title = tk.Label(
            card,
            text="Perfil recomendado VaultGit V1",
            font=(
                "Segoe UI",
                10,
                "bold",
            ),
            bg="#22262f",
            fg="#9ca3af",
        )

        recommended_title.pack(
            anchor="w"
        )

        recommended_profile_label = tk.Label(
            card,
            text=(
                "4 operaciones / 512 MiB"
            ),
            font=(
                "Consolas",
                11,
            ),
            bg="#22262f",
            fg="white",
        )

        recommended_profile_label.pack(
            anchor="w",
            pady=(6, 18),
        )

        status_label = tk.Label(
            card,
            text="",
            font=(
                "Segoe UI",
                10,
                "bold",
            ),
            bg="#22262f",
            fg="#9ca3af",
        )

        status_label.pack(
            anchor="w"
        )

        tk.Label(
            window,
            text=(
                "Antes de una actualización VaultGit verifica "
                "la contraseña maestra y crea un backup cifrado "
                "del estado actual."
            ),
            font=(
                "Segoe UI",
                9,
            ),
            bg="#181b21",
            fg="#9ca3af",
            wraplength=560,
            justify="left",
        ).pack(
            pady=(20, 14)
        )

        button_row = tk.Frame(
            window,
            bg="#181b21",
        )

        button_row.pack(
            fill="x",
            padx=34,
            pady=(4, 0),
        )

        upgrade_button = self.create_primary_button(
            button_row,
            "Actualizar protección",
            lambda: None,
        )

        upgrade_button.pack(
            side="right"
        )

        self.create_secondary_button(
            button_row,
            "Cerrar",
            window.destroy,
        ).pack(
            side="right",
            padx=(0, 10),
        )

        def refresh_security_status():
            try:
                profile = get_vault_kdf_profile(
                    VAULT_PATH
                )

                requires_upgrade = needs_kdf_upgrade(
                    VAULT_PATH
                )

            except (
                OSError,
                ValueError,
                KeyError,
                TypeError,
                binascii.Error,
            ):
                current_profile_label.config(
                    text="No disponible"
                )

                status_label.config(
                    text="No se pudo leer el perfil de seguridad.",
                    fg="#ffb4b4",
                )

                upgrade_button.config(
                    state="disabled"
                )
                return

            memory_mib = (
                profile["memlimit"]
                // (1024 * 1024)
            )

            current_profile_label.config(
                text=(
                    f"{profile['opslimit']} operaciones / "
                    f"{memory_mib} MiB"
                )
            )

            if requires_upgrade:
                status_label.config(
                    text=(
                        "Actualización recomendada: "
                        "la bóveda usa un perfil anterior."
                    ),
                    fg="#f5c26b",
                )

                upgrade_button.config(
                    state="normal"
                )

            else:
                status_label.config(
                    text=(
                        "Protección actualizada: "
                        "la bóveda ya usa el perfil recomendado."
                    ),
                    fg="#75d69c",
                )

                upgrade_button.config(
                    state="disabled"
                )

        def perform_kdf_upgrade():
            password = simpledialog.askstring(
                "Actualizar protección",
                (
                    "Introduce tu contraseña maestra para "
                    "autorizar la actualización:"
                ),
                show="●",
                parent=window,
            )

            if password is None:
                return

            if not password:
                messagebox.showwarning(
                    "VaultGit",
                    "Introduce tu contraseña maestra.",
                    parent=window,
                )
                return

            # Primero verificamos la contraseña SIN modificar
            # el archivo actual.
            try:
                unlock_vault(
                    VAULT_PATH,
                    password,
                )

            except CryptoError:
                messagebox.showerror(
                    "VaultGit",
                    "Contraseña maestra incorrecta.",
                    parent=window,
                )
                return

            except (
                OSError,
                ValueError,
                KeyError,
                TypeError,
                binascii.Error,
            ):
                messagebox.showerror(
                    "VaultGit",
                    (
                        "No se pudo verificar la bóveda "
                        "antes de la actualización."
                    ),
                    parent=window,
                )
                return

            try:
                safety_backup = create_backup(
                    VAULT_PATH,
                    BACKUP_DIR,
                    prefix="pre-kdf-upgrade",
                    keep=None,
                )

                (
                    migrated_data,
                    migrated_session,
                ) = migrate_vault_kdf(
                    VAULT_PATH,
                    password,
                )

            except CryptoError:
                messagebox.showerror(
                    "VaultGit",
                    (
                        "La contraseña dejó de ser válida "
                        "durante la migración."
                    ),
                    parent=window,
                )
                return

            except (
                OSError,
                ValueError,
                KeyError,
                TypeError,
                binascii.Error,
            ):
                messagebox.showerror(
                    "VaultGit",
                    (
                        "No se pudo completar la actualización. "
                        "La bóveda no debería quedar modificada."
                    ),
                    parent=window,
                )
                return

            finally:
                password = None

            self.vault_data = migrated_data
            self.session = migrated_session

            self.reset_auto_lock_timer()

            refresh_security_status()

            messagebox.showinfo(
                "VaultGit",
                (
                    "Protección Argon2id actualizada "
                    "correctamente.\n\n"
                    "Se creó un backup cifrado previo:\n"
                    f"{safety_backup.name}"
                ),
                parent=window,
            )

        upgrade_button.config(
            command=perform_kdf_upgrade
        )

        refresh_security_status()

    # =========================================================
    # BACKUPS CIFRADOS
    # =========================================================

    def open_backups_window(self):
        window = tk.Toplevel(
            self
        )

        window.title(
            "Backups cifrados"
        )

        window.geometry(
            "700x480"
        )

        window.minsize(
            620,
            420,
        )

        window.configure(
            bg="#181b21"
        )

        tk.Label(
            window,
            text="Backups cifrados",
            font=(
                "Segoe UI",
                18,
                "bold",
            ),
            bg="#181b21",
            fg="white",
        ).pack(
            pady=(24, 5)
        )

        tk.Label(
            window,
            text=(
                "Cada backup es una copia de la bóveda "
                "que permanece cifrada."
            ),
            font=(
                "Segoe UI",
                9,
            ),
            bg="#181b21",
            fg="#9ca3af",
        ).pack(
            pady=(0, 18)
        )

        list_frame = tk.Frame(
            window,
            bg="#181b21",
        )

        list_frame.pack(
            fill="both",
            expand=True,
            padx=28,
        )

        backups_list = tk.Listbox(
            list_frame,
            bg="#22262f",
            fg="white",
            selectbackground="#315efb",
            selectforeground="white",
            relief="flat",
            font=(
                "Consolas",
                10,
            ),
            activestyle="none",
        )

        scrollbar = ttk.Scrollbar(
            list_frame,
            orient="vertical",
            command=backups_list.yview,
        )

        backups_list.configure(
            yscrollcommand=scrollbar.set
        )

        backups_list.pack(
            side="left",
            fill="both",
            expand=True,
        )

        scrollbar.pack(
            side="right",
            fill="y",
        )

        backup_paths = []

        def refresh_backup_list():
            nonlocal backup_paths

            backups_list.delete(
                0,
                tk.END,
            )

            backup_paths = list_backups(
                BACKUP_DIR
            )

            for backup_path in backup_paths:
                backups_list.insert(
                    tk.END,
                    backup_path.name,
                )

            if not backup_paths:
                backups_list.insert(
                    tk.END,
                    "No hay backups disponibles.",
                )

        def create_manual_backup():
            try:
                backup_path = create_backup(
                    VAULT_PATH,
                    BACKUP_DIR,
                    prefix="manual-backup",
                    keep=None,
                )

            except (
                OSError,
                ValueError,
                FileNotFoundError,
            ):
                messagebox.showerror(
                    "VaultGit",
                    "No se pudo crear el backup.",
                    parent=window,
                )
                return

            refresh_backup_list()

            messagebox.showinfo(
                "VaultGit",
                (
                    "Backup cifrado creado:\n\n"
                    f"{backup_path.name}"
                ),
                parent=window,
            )

        def restore_selected_backup():
            selection = backups_list.curselection()

            if not selection:
                messagebox.showinfo(
                    "VaultGit",
                    "Selecciona un backup primero.",
                    parent=window,
                )
                return

            index = selection[0]

            if index >= len(backup_paths):
                return

            backup_path = backup_paths[index]

            confirmed = messagebox.askyesno(
                "Restaurar backup",
                (
                    "VaultGit reemplazará la bóveda actual "
                    "por el backup seleccionado.\n\n"
                    "Antes de hacerlo creará una copia "
                    "pre-restauración del estado actual.\n\n"
                    "¿Quieres continuar?"
                ),
                parent=window,
            )

            if not confirmed:
                return

            password = simpledialog.askstring(
                "Contraseña maestra",
                (
                    "Introduce la contraseña maestra "
                    "correspondiente a este backup:"
                ),
                show="●",
                parent=window,
            )

            if password is None:
                return

            if not password:
                messagebox.showwarning(
                    "VaultGit",
                    "Introduce una contraseña maestra.",
                    parent=window,
                )
                return

            try:
                (
                    restored_data,
                    restored_session,
                    safety_backup,
                ) = restore_backup(
                    backup_path,
                    VAULT_PATH,
                    password,
                    BACKUP_DIR,
                )

            except CryptoError:
                messagebox.showerror(
                    "VaultGit",
                    (
                        "Contraseña incorrecta "
                        "o backup manipulado."
                    ),
                    parent=window,
                )
                return

            except (
                OSError,
                ValueError,
                KeyError,
                TypeError,
                binascii.Error,
            ):
                messagebox.showerror(
                    "VaultGit",
                    (
                        "No se pudo restaurar "
                        "el backup seleccionado."
                    ),
                    parent=window,
                )
                return

            password = None

            self.vault_data = restored_data
            self.session = restored_session

            window.destroy()

            self.show_dashboard()

            if safety_backup is not None:
                messagebox.showinfo(
                    "VaultGit",
                    (
                        "Backup restaurado correctamente.\n\n"
                        "También se creó una copia "
                        "pre-restauración:\n"
                        f"{safety_backup.name}"
                    ),
                )
            else:
                messagebox.showinfo(
                    "VaultGit",
                    "Backup restaurado correctamente.",
                )

        buttons = tk.Frame(
            window,
            bg="#181b21",
        )

        buttons.pack(
            fill="x",
            padx=28,
            pady=20,
        )

        self.create_primary_button(
            buttons,
            "Crear backup ahora",
            create_manual_backup,
        ).pack(
            side="left",
        )

        self.create_secondary_button(
            buttons,
            "Restaurar seleccionado",
            restore_selected_backup,
        ).pack(
            side="left",
            padx=10,
        )

        self.create_secondary_button(
            buttons,
            "Cerrar",
            window.destroy,
        ).pack(
            side="right",
        )

        refresh_backup_list()

    # =========================================================
    # GENERADOR
    # =========================================================

    def open_password_generator(self):
        window = tk.Toplevel(
            self
        )

        window.title(
            "Generador de contraseñas"
        )

        window.geometry(
            "480x330"
        )

        window.resizable(
            False,
            False,
        )

        window.configure(
            bg="#181b21"
        )

        tk.Label(
            window,
            text="Generador seguro",
            font=(
                "Segoe UI",
                18,
                "bold",
            ),
            bg="#181b21",
            fg="white",
        ).pack(
            pady=(25, 18)
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
        ).pack(
            side="left",
            padx=(0, 8),
        )

        length_var = tk.StringVar(
            value="20"
        )

        tk.Entry(
            length_frame,
            textvariable=length_var,
            width=6,
            justify="center",
        ).pack(
            side="left"
        )

        password_var = tk.StringVar()

        password_entry = tk.Entry(
            window,
            textvariable=password_var,
            width=40,
            justify="center",
            font=(
                "Consolas",
                11,
            ),
            state="readonly",
        )

        password_entry.pack(
            pady=22,
            ipady=7,
        )

        def generate():
            value = (
                length_var.get().strip()
            )

            if not value.isdigit():
                messagebox.showwarning(
                    "VaultGit",
                    (
                        "Introduce una longitud "
                        "válida."
                    ),
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

        button_row = tk.Frame(
            window,
            bg="#181b21",
        )

        button_row.pack()

        self.create_primary_button(
            button_row,
            "Generar",
            generate,
        ).pack(
            side="left",
            padx=5,
        )

        self.create_secondary_button(
            button_row,
            "Copiar",
            lambda: self.copy_sensitive_to_clipboard(
                password_var.get()
            ),
        ).pack(
            side="left",
            padx=5,
        )

        tk.Label(
            window,
            text=(
                "Las contraseñas copiadas se intentan "
                "retirar del portapapeles tras 30 segundos."
            ),
            bg="#181b21",
            fg="#9ca3af",
            font=(
                "Segoe UI",
                8,
            ),
        ).pack(
            pady=(18, 0)
        )

    # =========================================================
    # BLOQUEO Y CIERRE
    # =========================================================

    def lock_vault(self):
        if self.auto_lock_after_id is not None:
            try:
                self.after_cancel(
                    self.auto_lock_after_id
                )
            except tk.TclError:
                pass

            self.auto_lock_after_id = None

        # Si el portapapeles todavía contiene una contraseña
        # copiada por VaultGit, la retiramos al bloquear.
        self.clear_sensitive_clipboard()

        self.vault_data = None
        self.session = None
        self.search_var = None
        self.accounts_table = None
        self.count_label = None

        self.show_unlock_screen()

    def on_close(self):
        if self.auto_lock_after_id is not None:
            try:
                self.after_cancel(
                    self.auto_lock_after_id
                )
            except tk.TclError:
                pass

            self.auto_lock_after_id = None

        # Misma protección al cerrar completamente la app.
        self.clear_sensitive_clipboard()

        self.vault_data = None
        self.session = None

        self.destroy()


def main():
    app = VaultGitGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
