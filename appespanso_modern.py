import os
import sys
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from ruamel.yaml import YAML, CommentedMap
from ruamel.yaml.scalarstring import PreservedScalarString

# --- CONFIGURAÇÃO E CONSTANTES ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

CAMINHO_DIRETORIO_ESPANSO = os.path.expandvars(r"%AppData%\espanso\match")
CAMINHO_ARQUIVO_BASE_YML = os.path.join(CAMINHO_DIRETORIO_ESPANSO, "base.yml")

# --- GERENCIADOR DE DADOS (BACKEND) ---
class MacroManager:
    def __init__(self):
        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        self.yaml.indent(mapping=2, sequence=4, offset=2)
        self.dados_carregados = None

    def carregar_dados(self):
        """Carrega o arquivo YAML preservando comentários e estrutura."""
        if not os.path.exists(CAMINHO_ARQUIVO_BASE_YML):
            # Cria estrutura básica se não existir
            self.dados_carregados = CommentedMap({'matches': []})
            return self.dados_carregados

        try:
            with open(CAMINHO_ARQUIVO_BASE_YML, 'r', encoding='utf-8') as f:
                dados = self.yaml.load(f)
                if not dados:
                    dados = CommentedMap({'matches': []})
                if 'matches' not in dados:
                    dados['matches'] = []
                self.dados_carregados = dados
                return dados
        except Exception as e:
            raise Exception(f"Erro ao ler arquivo: {e}")

    def salvar_dados(self):
        """Salva as alterações no arquivo."""
        if self.dados_carregados is None:
            return
        
        os.makedirs(CAMINHO_DIRETORIO_ESPANSO, exist_ok=True)
        with open(CAMINHO_ARQUIVO_BASE_YML, 'w', encoding='utf-8') as f:
            self.yaml.dump(self.dados_carregados, f)

    def adicionar_macro(self, trigger, replace):
        """Adiciona uma nova macro à lista."""
        if self.dados_carregados is None:
            self.carregar_dados()
        
        nova_macro = {
            'trigger': trigger,
            'replace': self._formatar_replace(replace)
        }
        self.dados_carregados['matches'].append(nova_macro)
        self.salvar_dados()

    def atualizar_macro(self, index, novo_trigger, novo_replace):
        """Atualiza uma macro existente pelo índice."""
        if self.dados_carregados is None:
            self.carregar_dados()
            
        if 0 <= index < len(self.dados_carregados['matches']):
            self.dados_carregados['matches'][index]['trigger'] = novo_trigger
            self.dados_carregados['matches'][index]['replace'] = self._formatar_replace(novo_replace)
            self.salvar_dados()
            return True
        return False

    def excluir_macro(self, index):
        """Remove uma macro pelo índice."""
        if self.dados_carregados is None:
            self.carregar_dados()

        if 0 <= index < len(self.dados_carregados['matches']):
            del self.dados_carregados['matches'][index]
            self.salvar_dados()
            return True
        return False

    def _formatar_replace(self, text):
        """Formata o texto para bloco (|) se tiver quebras de linha."""
        if '\n' in text:
            return PreservedScalarString(text)
        return text

# --- HELPER FUNÇÕES ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)

# --- INTERFACE GRÁFICA (FRONTEND) ---
class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("TypeFlow")
        self.geometry("700x550")
        
        # Define ícone da janela se existir
        icon_path = resource_path("logo.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)
        
        self.manager = MacroManager()
        self.macros_cache = [] # Lista local para indexação
        
        # Grid layout 1x1
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Abas
        self.tabview = ctk.CTkTabview(self, width=650)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        self.tab_criar = self.tabview.add("Criar Nova")
        self.tab_gerenciar = self.tabview.add("Gerenciar Macros")
        
        self.setup_aba_criar()
        self.setup_aba_gerenciar()
        
        # Carrega dados iniciais
        try:
            self.atualizar_lista_macros()
        except Exception as e:
            messagebox.showerror("Erro Inicial", str(e))

    def setup_aba_criar(self):
        # Frame centralizado
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

    def setup_aba_gerenciar(self):
        # Layout: Esquerda (Lista), Direita (Edição)
        self.tab_gerenciar.grid_columnconfigure(0, weight=1) # Lista
        self.tab_gerenciar.grid_columnconfigure(1, weight=2) # Edição
        self.tab_gerenciar.grid_rowconfigure(0, weight=1)
        
        # Coluna Esquerda: Lista
        frame_lista = ctk.CTkFrame(self.tab_gerenciar)
        frame_lista.grid(row=0, column=0, padx=(0, 10), pady=0, sticky="nsew")
        
        ctk.CTkLabel(frame_lista, text="Lista de Macros", font=ctk.CTkFont(weight="bold")).pack(pady=5)
        
        # Scrollable Frame para simular Listbox com widgets modernos
        self.scroll_lista = ctk.CTkScrollableFrame(frame_lista)
        self.scroll_lista.pack(expand=True, fill="both", padx=5, pady=5)
        
        # Botão Atualizar Lista
        ctk.CTkButton(frame_lista, text="Recarregar Lista", command=self.atualizar_lista_macros).pack(pady=5, padx=5)

        # Coluna Direita: Editor
        frame_editor = ctk.CTkFrame(self.tab_gerenciar)
        frame_editor.grid(row=0, column=1, padx=0, pady=0, sticky="nsew")
        
        ctk.CTkLabel(frame_editor, text="Editor", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        self.edit_trigger = ctk.CTkEntry(frame_editor, placeholder_text="Gatilho")
        self.edit_trigger.pack(fill="x", padx=10, pady=(0, 10))
        
        self.edit_replace = ctk.CTkTextbox(frame_editor, height=200)
        self.edit_replace.pack(fill="x", padx=10, pady=(0, 10))
        
        # Botões de Ação
        row_btns = ctk.CTkFrame(frame_editor, fg_color="transparent")
        row_btns.pack(fill="x", padx=10, pady=10)
        
        self.btn_update = ctk.CTkButton(row_btns, text="Atualizar", command=self.acao_atualizar, state="disabled")
        self.btn_update.pack(side="left", expand=True, padx=(0, 5))
        
        self.btn_delete = ctk.CTkButton(row_btns, text="Excluir", command=self.acao_excluir, fg_color="#e74c3c", hover_color="#c0392b", state="disabled")
        self.btn_delete.pack(side="right", expand=True, padx=(5, 0))

        self.selected_index = None

    def atualizar_lista_macros(self):
        # Limpa lista visual
        for widget in self.scroll_lista.winfo_children():
            widget.destroy()
            
        # Carrega dados
        dados = self.manager.carregar_dados()
        self.macros_cache = dados.get('matches', [])
        
        # Popula lista
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

    def selecionar_macro(self, index):
        self.selected_index = index
        macro = self.macros_cache[index]
        
        self.edit_trigger.delete(0, "end")
        self.edit_trigger.insert(0, macro.get('trigger', ''))
        
        self.edit_replace.delete("0.0", "end")
        self.edit_replace.insert("0.0", str(macro.get('replace', '')))
        
        self.btn_update.configure(state="normal")
        self.btn_delete.configure(state="normal")

    def acao_salvar_nova(self):
        trigger = self.entry_trigger_new.get().strip()
        replace = self.text_replace_new.get("0.0", "end").strip()
        
        if not trigger or not replace:
            messagebox.showwarning("Atenção", "Preencha todos os campos!")
            return
            
        try:
            self.manager.adicionar_macro(trigger, replace)
            messagebox.showinfo("Sucesso", "Macro criada com sucesso!")
            self.entry_trigger_new.delete(0, "end")
            self.text_replace_new.delete("0.0", "end")
            self.atualizar_lista_macros()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar: {e}")

    def acao_atualizar(self):
        if self.selected_index is None: return
        
        trigger = self.edit_trigger.get().strip()
        replace = self.edit_replace.get("0.0", "end").strip()
        
        if not trigger or not replace:
            messagebox.showwarning("Atenção", "Campos não podem ficar vazios!")
            return

        try:
            self.manager.atualizar_macro(self.selected_index, trigger, replace)
            messagebox.showinfo("Sucesso", "Macro atualizada!")
            self.atualizar_lista_macros()
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao atualizar: {e}")

    def acao_excluir(self):
        if self.selected_index is None: return
        
        confirm = messagebox.askyesno("Confirmar Exclusão", "Tem certeza que deseja excluir esta macro?")
        if confirm:
            try:
                self.manager.excluir_macro(self.selected_index)
                messagebox.showinfo("Sucesso", "Macro excluída!")
                # Limpa editor
                self.selected_index = None
                self.edit_trigger.delete(0, "end")
                self.edit_replace.delete("0.0", "end")
                self.btn_update.configure(state="disabled")
                self.btn_delete.configure(state="disabled")
                
                self.atualizar_lista_macros()
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao excluir: {e}")

if __name__ == "__main__":
    app = App()
    app.mainloop()
