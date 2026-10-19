import customtkinter as ctk
from tkinter import messagebox
from typing import Any

import config
from backend import MacroManager

class App(ctk.CTk):
    """Interface gráfica (Frontend) do TypeFlow."""

    def __init__(self) -> None:
        super().__init__()

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.title("TypeFlow")
        self.geometry("700x550")
        
        icon_path = config.get_asset_path("logo.ico")
        if icon_path.exists():
            self.iconbitmap(icon_path)
        
        self.manager = MacroManager()
        self.macros_cache: list[dict[str, Any]] = []
        self.selected_index: int | None = None
        self._status_after_id: str | None = None
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(self, width=650)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.status_label = ctk.CTkLabel(self, text="", anchor="w")
        self.status_label.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        self.tab_criar = self.tabview.add("Criar Nova")
        self.tab_gerenciar = self.tabview.add("Gerenciar Macros")
        
        self.setup_aba_criar()
        self.setup_aba_gerenciar()
        
        try:
            self.atualizar_lista_macros()
        except Exception as e:
            messagebox.showerror("Erro Inicial", f"Falha ao carregar macros: {e}")

    def setup_aba_criar(self) -> None:
        frame = ctk.CTkFrame(self.tab_criar, fg_color="transparent")
        frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        ctk.CTkLabel(frame, text="Gatilho (ex: :ola)", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 5))
        self.entry_trigger_new = ctk.CTkEntry(frame, placeholder_text=":exemplo")
        self.entry_trigger_new.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(frame, text="Texto de Substituição", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(0, 5))
        self.text_replace_new = ctk.CTkTextbox(frame, height=150)
        self.text_replace_new.pack(fill="x", pady=(0, 20))
        
        self.btn_salvar = ctk.CTkButton(frame, text="Salvar Nova Macro", command=self.acao_salvar_nova, fg_color="#2ecc71", hover_color="#27ae60")
        self.btn_salvar.pack(fill="x", pady=10)

    def setup_aba_gerenciar(self) -> None:
        self.tab_gerenciar.grid_columnconfigure(0, weight=1)
        self.tab_gerenciar.grid_columnconfigure(1, weight=2)
        self.tab_gerenciar.grid_rowconfigure(0, weight=1)
        
        frame_lista = ctk.CTkFrame(self.tab_gerenciar)
        frame_lista.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="nsew")
        ctk.CTkLabel(frame_lista, text="Lista de Macros", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        self.scroll_lista = ctk.CTkScrollableFrame(frame_lista)
        self.scroll_lista.pack(expand=True, fill="both", padx=5, pady=5)
        ctk.CTkButton(frame_lista, text="Recarregar Lista", command=self.atualizar_lista_macros).pack(pady=5, padx=5)

        frame_editor = ctk.CTkFrame(self.tab_gerenciar)
        frame_editor.grid(row=0, column=1, padx=0, pady=0, sticky="nsew")
        ctk.CTkLabel(frame_editor, text="Editor", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        self.edit_trigger = ctk.CTkEntry(frame_editor, placeholder_text="Gatilho")
        self.edit_trigger.pack(fill="x", padx=10, pady=(0, 10))
        self.edit_replace = ctk.CTkTextbox(frame_editor, height=200)
        self.edit_replace.pack(fill="x", padx=10, pady=(0, 10))
        
        row_btns = ctk.CTkFrame(frame_editor, fg_color="transparent")
        row_btns.pack(fill="x", padx=10, pady=10)
        self.btn_update = ctk.CTkButton(row_btns, text="Atualizar", command=self.acao_atualizar, state="disabled")
        self.btn_update.pack(side="left", expand=True, padx=(0, 5))
        self.btn_delete = ctk.CTkButton(row_btns, text="Excluir", command=self.acao_excluir, fg_color="#e74c3c", hover_color="#c0392b", state="disabled")
        self.btn_delete.pack(side="right", expand=True, padx=(5, 0))

    def atualizar_lista_macros(self) -> None:
        for widget in self.scroll_lista.winfo_children():
            widget.destroy()
            
        dados = self.manager.carregar_dados()
        self.macros_cache = dados.get('matches', [])
        
        for i, macro in enumerate(self.macros_cache):
            trigger = macro.get('trigger', '???')
            btn = ctk.CTkButton(
                self.scroll_lista, 
                text=trigger, 
                anchor="w",
                fg_color="transparent", 
                text_color=("gray10", "gray90"),
                hover_color=("gray70", "gray30"),
                command=lambda idx=i: self.selecionar_macro(idx)
            )
            btn.pack(fill="x", pady=1)

    def selecionar_macro(self, index: int) -> None:
        self.selected_index = index
        macro = self.macros_cache[index]
        
        self.edit_trigger.delete(0, "end")
        self.edit_trigger.insert(0, macro.get('trigger', ''))
        self.edit_replace.delete("0.0", "end")
        self.edit_replace.insert("0.0", str(macro.get('replace', '')))
        
        self.btn_update.configure(state="normal")
        self.btn_delete.configure(state="normal")

    def acao_salvar_nova(self) -> None:
        trigger = self.entry_trigger_new.get().strip()
        replace = self.text_replace_new.get("0.0", "end").strip()
        
        if not trigger or not replace:
            messagebox.showwarning("Atenção", "Preencha todos os campos!")
            return
            
        try:
            self.manager.adicionar_macro(trigger, replace)
            self.entry_trigger_new.delete(0, "end")
            self.text_replace_new.delete("0.0", "end")
            self.atualizar_lista_macros()
            self.exibir_status("Status: Macro injetada com sucesso")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar: {e}")

    def acao_atualizar(self) -> None:
        if self.selected_index is None: return
        trigger = self.edit_trigger.get().strip()
        replace = self.edit_replace.get("0.0", "end").strip()
        
        if not trigger or not replace:
            messagebox.showwarning("Atenção", "Campos não podem ficar vazios!")
            return

        try:
            if self.manager.atualizar_macro(self.selected_index, trigger, replace):
                self.atualizar_lista_macros()
                self.exibir_status("Status: Macro atualizada com sucesso")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao atualizar: {e}")

    def acao_excluir(self) -> None:
        if self.selected_index is None: return
        if messagebox.askyesno("Confirmar Exclusão", "Tem certeza que deseja excluir esta macro?"):
            try:
                if self.manager.excluir_macro(self.selected_index):
                    self.selected_index = None
                    self.edit_trigger.delete(0, "end")
                    self.edit_replace.delete("0.0", "end")
                    self.btn_update.configure(state="disabled")
                    self.btn_delete.configure(state="disabled")
                    self.atualizar_lista_macros()
                    self.exibir_status("Status: Macro excluída com sucesso")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao excluir: {e}")

    def exibir_status(self, mensagem: str) -> None:
        if self._status_after_id is not None:
            self.after_cancel(self._status_after_id)
        self.status_label.configure(text=mensagem, text_color="#2ecc71")
        self._status_after_id = self.after(3000, lambda: self.status_label.configure(text=""))

if __name__ == "__main__":
    app = App()
    app.mainloop()