"""
GUMP/app.py
-------------
Interface gráfica do GUMP — General Unstructured Material Parser (LOCAL)
Roda com: python app.py

Modo LOCAL:
- Sem Gemini / sem API
- Lê PDF/DOCX/TXT/HTML/EML/RTF/ODT
- Gera JSONL: <output>/documento.jsonl
"""

import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from datetime import datetime

# Tenta carregar .env se existir (opcional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Licença (mantive porque teu app depende disso)
from license import (
    validate_license, validate_license_code, save_license_from_code,
    get_machine_id_display, days_until_expiry,
)

# ---------------------------------------------------------------------------
# Paleta de cores
# ---------------------------------------------------------------------------
BG_DARK    = "#0f1117"
BG_CARD    = "#1a1d27"
BG_INPUT   = "#23273a"
ACCENT     = "#4f8ef7"
ACCENT_DIM = "#2d5cb8"
SUCCESS    = "#3ecf8e"
WARNING    = "#f5a623"
ERROR      = "#e05c5c"
TEXT_MAIN  = "#ffffff"
TEXT_DIM   = "#e3e6ec"
BORDER     = "#2e3347"


# ---------------------------------------------------------------------------
# Componente: campo de pasta com botão Browse
# ---------------------------------------------------------------------------
class FolderField(tk.Frame):
    def __init__(self, parent, label, placeholder="", **kwargs):
        super().__init__(parent, bg=BG_DARK, **kwargs)

        tk.Label(
            self, text=label, bg=BG_DARK, fg=TEXT_DIM,
            font=("Courier New", 9), anchor="w"
        ).pack(fill="x", pady=(0, 4))

        row = tk.Frame(self, bg=BG_DARK)
        row.pack(fill="x")

        self.var = tk.StringVar()
        self.entry = tk.Entry(
            row, textvariable=self.var,
            bg=BG_INPUT, fg=TEXT_MAIN, insertbackground=TEXT_MAIN,
            relief="flat", font=("Courier New", 10),
            bd=0, highlightthickness=1,
            highlightbackground=BORDER, highlightcolor=ACCENT,
        )
        self.entry.pack(side="left", fill="x", expand=True, ipady=8, ipadx=10)

        tk.Button(
            row, text="  BROWSE  ",
            bg=BG_CARD, fg=ACCENT, activebackground=ACCENT, activeforeground=BG_DARK,
            relief="flat", font=("Courier New", 9, "bold"),
            cursor="hand2", bd=0,
            command=self._browse,
        ).pack(side="left", padx=(6, 0), ipady=8, ipadx=4)

        if placeholder:
            self.var.set(placeholder)

    def _browse(self):
        path = filedialog.askdirectory(title="Selecione uma pasta")
        if path:
            self.var.set(path)

    def get(self):
        return self.var.get().strip()


# ---------------------------------------------------------------------------
# Componente: log de saída
# ---------------------------------------------------------------------------
class LogBox(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG_DARK, **kwargs)

        tk.Label(
            self, text="OUTPUT", bg=BG_DARK, fg=TEXT_DIM,
            font=("Courier New", 9), anchor="w"
        ).pack(fill="x", pady=(0, 4))

        box_frame = tk.Frame(self, bg=BORDER, pady=1, padx=1)
        box_frame.pack(fill="both", expand=True)

        self.text = tk.Text(
            box_frame,
            bg=BG_INPUT, fg=TEXT_MAIN,
            font=("Courier New", 9),
            relief="flat", bd=0,
            state="disabled",
            wrap="word",
            padx=12, pady=10,
        )
        self.text.pack(fill="both", expand=True)

        # Tags de cor
        self.text.tag_config("ok",      foreground=SUCCESS)
        self.text.tag_config("error",   foreground=ERROR)
        self.text.tag_config("warning", foreground=WARNING)
        self.text.tag_config("accent",  foreground=ACCENT)
        self.text.tag_config("dim",     foreground=TEXT_DIM)

    def write(self, msg: str, tag: str = ""):
        self.text.config(state="normal")
        self.text.insert("end", msg + "\n", tag)
        self.text.see("end")
        self.text.config(state="disabled")

    def clear(self):
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.config(state="disabled")


# ---------------------------------------------------------------------------
# App principal
# ---------------------------------------------------------------------------
class GumpApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("GUMP — Local")
        self.geometry("820x620")
        self.minsize(700, 560)
        self.configure(bg=BG_DARK)
        self.resizable(True, True)
        
        # Carrega o ícone
        try:
            icon_path = Path(__file__).parent / "gump.ico"
            if icon_path.exists():
                self.iconbitmap(str(icon_path))
        except Exception:
            pass  # Se falhar, usa o ícone padrão

        self._running = False
        self._build_ui()

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=BG_DARK)
        header.pack(fill="x", padx=32, pady=(28, 0))

        tk.Label(
            header, text="GUMP", bg=BG_DARK, fg=TEXT_MAIN,
            font=("Courier New", 28, "bold"),
        ).pack(side="left")

        tk.Label(
            header,
            text="GENERAL UNSTRUCTURED MATERIAL PARSER — Local version",
            bg=BG_DARK, fg=TEXT_DIM,
            font=("Courier New", 10),
        ).pack(side="left", padx=(14, 0), pady=(10, 0))

        tk.Label(
            header, text="vLOCAL", bg=BG_DARK, fg=BORDER,
            font=("Courier New", 9),
        ).pack(side="right", pady=(10, 0))

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=32, pady=(16, 24))

        # Form
        form = tk.Frame(self, bg=BG_DARK)
        form.pack(fill="x", padx=32)

        self.input_field = FolderField(
            form,
            label="PASTA DE ENTRADA — documentos misturados (pdf/docx/txt/html/eml/rtf/odt)"
        )
        self.input_field.pack(fill="x", pady=(0, 14))

        self.output_field = FolderField(
            form,
            label="PASTA DE SAÍDA — vai gerar documento.jsonl"
        )
        self.output_field.pack(fill="x", pady=(0, 14))

        # Botões
        btn_frame = tk.Frame(self, bg=BG_DARK)
        btn_frame.pack(fill="x", padx=32, pady=(18, 0))

        self.run_btn = tk.Button(
            btn_frame,
            text="▶   RUN (LOCAL)",
            bg=ACCENT, fg=BG_DARK,
            activebackground=ACCENT_DIM, activeforeground=BG_DARK,
            font=("Courier New", 11, "bold"),
            relief="flat", cursor="hand2", bd=0,
            command=self._start,
        )
        self.run_btn.pack(side="left", ipady=12, ipadx=28)

        self.stop_btn = tk.Button(
            btn_frame,
            text="■   STOP",
            bg=BG_CARD, fg=ERROR,
            activebackground=ERROR, activeforeground=BG_DARK,
            font=("Courier New", 11, "bold"),
            relief="flat", cursor="hand2", bd=0,
            state="disabled",
            command=self._stop,
        )
        self.stop_btn.pack(side="left", padx=(10, 0), ipady=12, ipadx=20)

        self.status_dot = tk.Label(
            btn_frame, text="●", bg=BG_DARK, fg=TEXT_DIM,
            font=("Courier New", 14),
        )
        self.status_dot.pack(side="right")
        self.status_text = tk.Label(
            btn_frame, text="idle", bg=BG_DARK, fg=TEXT_DIM,
            font=("Courier New", 9),
        )
        self.status_text.pack(side="right", padx=(0, 6))

        # Log
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=32, pady=(20, 16))

        self.log = LogBox(self)
        self.log.pack(fill="both", expand=True, padx=32, pady=(0, 24))

        self.log.write("GUMP LOCAL READY. Selecione as pastas e roda.", "dim")

    def _set_status(self, text, color):
        self.status_dot.config(fg=color)
        self.status_text.config(text=text, fg=color)

    def _start(self):
        input_dir = self.input_field.get()
        output_dir = self.output_field.get()

        if not input_dir:
            messagebox.showerror("Erro", "Select Input Folder.")
            return
        if not output_dir:
            messagebox.showerror("Erro", "Select Output Folder.")
            return
        if not Path(input_dir).exists():
            messagebox.showerror("Erro", f"Input folder not found:\n{input_dir}")
            return

        self._running = True
        self.run_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self._set_status("rodando...", ACCENT)
        self.log.clear()
        self.log.write("=" * 56, "dim")
        self.log.write(f"  GUMP LOCAL iniciado — {datetime.now().strftime('%H:%M:%S')}", "accent")
        self.log.write("=" * 56, "dim")

        thread = threading.Thread(
            target=self._run_pipeline,
            args=(input_dir, output_dir),
            daemon=True,
        )
        thread.start()

    def _stop(self):
        # Importante: nesse modo local, não dá pra cancelar “no meio” facilmente
        # sem reescrever o runner pra checar flag por arquivo.
        # Aqui a gente só atualiza UI.
        self._running = False
        self._set_status("stop (não cancela no meio)", WARNING)
        self.log.write("\n⚠  STOP clicado. Vai terminar o arquivo atual e seguir.", "warning")
        self.run_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

    def _log(self, msg, tag=""):
        self.after(0, lambda: self.log.write(msg, tag))

    def _run_pipeline(self, input_dir, output_dir):
        try:
            # IMPORTANTE: isso chama o main.py do GUMP LOCAL LIGHT
            from main import run as run_local

            self._log("\n📄  Extraindo texto local + limpando caracteres...", "accent")
            out_path = run_local(input_dir=input_dir, output_dir=output_dir)

            self._log("\n✅  Concluído.", "ok")
            self._log(f"Saída: {out_path}", "ok")

            self._finish(error=False)

        except Exception as e:
            self._log(f"\n❌  Erro inesperado: {e}", "error")
            self._finish(error=True)

    def _finish(self, error=False):
        self._running = False
        self.after(0, lambda: self.run_btn.config(state="normal"))
        self.after(0, lambda: self.stop_btn.config(state="disabled"))
        if error:
            self.after(0, lambda: self._set_status("erro", ERROR))
        else:
            self.after(0, lambda: self._set_status("concluído", SUCCESS))


# ---------------------------------------------------------------------------
# Tela de ativação (mantive do teu app)
# ---------------------------------------------------------------------------
class ActivationScreen(tk.Tk):
    REASONS = {
        "arquivo_nao_encontrado": "Licença não encontrada.",
        "arquivo_corrompido":     "Arquivo de licença corrompido.",
        "campos_faltando":        "Arquivo de licença inválido.",
        "assinatura_invalida":    "Licença inválida ou adulterada.",
        "maquina_diferente":      "Esta licença pertence a outra máquina.",
        "expirada":               "Sua licença expirou.\nEntre em contato para renovação.",
        "data_invalida":          "Data de expiração inválida.",
        "codigo_invalido":        "Código de licença inválido.",
        "codigo_vazio":           "Insira um código de licença.",
    }

    def __init__(self, reason: str, client: str = "", expiry: str = ""):
        super().__init__()
        self.title("GUMP — Ativação")
        self.geometry("560x500")
        self.resizable(False, False)
        self.configure(bg=BG_DARK)
        self._activated = False
        
        # Carrega o ícone
        try:
            icon_path = Path(__file__).parent / "gump.ico"
            if icon_path.exists():
                self.iconbitmap(str(icon_path))
        except Exception:
            pass  # Se falhar, usa o ícone padrão
        
        self._build(reason, client, expiry)

    def _build(self, reason, client, expiry):
        tk.Label(self, text="GUMP", bg=BG_DARK, fg=TEXT_MAIN,
                 font=("Courier New", 24, "bold")).pack(pady=(28, 0))
        tk.Label(self, text="General Unstructured Material Parser (LOCAL)",
                 bg=BG_DARK, fg=TEXT_DIM, font=("Courier New", 9)).pack()

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=32, pady=(16, 12))

        msg = self.REASONS.get(reason, "Licença inválida.")
        tk.Label(self, text=msg, bg=BG_DARK, fg=WARNING,
                 font=("Courier New", 10), justify="center", wraplength=460).pack(pady=(8, 4))

        tk.Label(self, text="SEU MACHINE ID:",
                 bg=BG_DARK, fg=TEXT_DIM, font=("Courier New", 8)).pack(pady=(12, 3))

        mid_frame = tk.Frame(self, bg=BG_INPUT, pady=6, padx=12)
        mid_frame.pack(padx=32)

        tk.Label(mid_frame, text=get_machine_id_display(), bg=BG_INPUT, fg=ACCENT,
                 font=("Courier New", 11, "bold")).pack(side="left")

        def copy_mid():
            self.clipboard_clear()
            self.clipboard_append(get_machine_id_display())

        copy_btn = tk.Label(mid_frame, text="copiar", bg=BG_INPUT, fg=TEXT_DIM,
                            font=("Courier New", 8), cursor="hand2")
        copy_btn.pack(side="left", padx=(10, 0))
        copy_btn.bind("<Button-1>", lambda _: copy_mid())

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=32, pady=(16, 12))

        tk.Label(self, text="INSIRA SEU CÓDIGO DE LICENÇA:",
                 bg=BG_DARK, fg=TEXT_DIM, font=("Courier New", 8)).pack(padx=32, anchor="w")

        self.code_var = tk.StringVar()
        code_entry = tk.Entry(self, textvariable=self.code_var,
                              bg=BG_INPUT, fg=TEXT_MAIN, insertbackground=TEXT_MAIN,
                              relief="flat", font=("Courier New", 9),
                              bd=0, highlightthickness=1,
                              highlightbackground=BORDER, highlightcolor=ACCENT)
        code_entry.pack(fill="x", padx=32, ipady=8, ipadx=10, pady=(4, 0))
        code_entry.bind("<Return>", lambda _: self._activate_code())

        self.code_status = tk.Label(self, text="", bg=BG_DARK, font=("Courier New", 8))
        self.code_status.pack(padx=32, anchor="w", pady=(3, 0))

        tk.Button(self, text="  ATIVAR  ",
                  bg=ACCENT, fg=BG_DARK,
                  activebackground=ACCENT_DIM, activeforeground=BG_DARK,
                  font=("Courier New", 10, "bold"), relief="flat",
                  cursor="hand2", bd=0, command=self._activate_code
                  ).pack(pady=(10, 0), ipady=10, ipadx=16)

    def _activate_code(self):
        code = self.code_var.get().strip()
        result = validate_license_code(code)
        if result.valid:
            save_license_from_code(code)
            self.code_status.config(text=f"✅  Ativado — {result.client}", fg=SUCCESS)
            self._activated = True
            self.after(800, self.destroy)
        else:
            msg = self.REASONS.get(result.reason, "Código inválido.")
            self.code_status.config(text=f"❌  {msg}", fg=ERROR)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    result = validate_license()

    if not result.valid:
        screen = ActivationScreen(reason=result.reason, client=result.client, expiry=result.expiry)
        screen.mainloop()
        if not screen._activated:
            sys.exit(0)

        result = validate_license()
        if not result.valid:
            sys.exit(0)

    app = GumpApp()

    days = days_until_expiry(result.expiry)
    if days is not None and days <= 30:
        app.after(500, lambda: messagebox.showwarning(
            "Licença expirando",
            f"Sua licença expira em {days} dia(s).\nEntre em contato para renovação."
        ))

    app.mainloop()
