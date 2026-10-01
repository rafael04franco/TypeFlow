import json
import logging
import os
import sys
from typing import Any
from tkinter import messagebox

import customtkinter as ctk
from ruamel.yaml import YAML, CommentedMap
from ruamel.yaml.scalarstring import PreservedScalarString

# --- CONFIGURAÇÃO E CONSTANTES ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

def obter_diretorio_aplicacao() -> str:
    """Retorna o diretório do executável ou do código-fonte.

    Returns:
        Diretório base usado para os arquivos de configuração, log e recursos.
    """
    if getattr(sys, "frozen", False) or "__compiled__" in globals():
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


DIRETORIO_APLICACAO: str = obter_diretorio_aplicacao()
CAMINHO_CONFIGURACAO: str = os.path.join(DIRETORIO_APLICACAO, "config.json")
CAMINHO_LOG: str = os.path.join(DIRETORIO_APLICACAO, "typeflow.log")
CAMINHO_ESPANSO_PADRAO: str = os.path.join(
    os.environ.get("APPDATA", os.path.expanduser("~")), "espanso", "match"
)

logging.basicConfig(
    filename=CAMINHO_LOG,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    encoding="utf-8",
)
logger: logging.Logger = logging.getLogger("typeflow")


def carregar_configuracao() -> dict[str, str]:
    """Carrega ou cria a configuração do diretório de destino.

    Returns:
        Configuração contendo o diretório de macros do Espanso.

    Raises:
        ValueError: Se o arquivo existir, mas não contiver um caminho válido.
        OSError: Se não for possível criar ou ler o arquivo de configuração.
    """
    if not os.path.exists(CAMINHO_CONFIGURACAO):
        configuracao = {"espanso_match_dir": CAMINHO_ESPANSO_PADRAO}
        with open(CAMINHO_CONFIGURACAO, "w", encoding="utf-8") as arquivo:
            json.dump(configuracao, arquivo, indent=2, ensure_ascii=False)
        logger.info("Arquivo de configuração criado: %s", CAMINHO_CONFIGURACAO)
        return configuracao

    with open(CAMINHO_CONFIGURACAO, "r", encoding="utf-8") as arquivo:
        configuracao = json.load(arquivo)

    diretorio = configuracao.get("espanso_match_dir")
    if not isinstance(diretorio, str) or not diretorio.strip():
        raise ValueError(
            "A configuração 'espanso_match_dir' deve conter um caminho válido."
        )
    return {"espanso_match_dir": os.path.expandvars(diretorio.strip())}

# --- GERENCIADOR DE DADOS (BACKEND) ---
class MacroManager:
    """Gerencia a leitura, edição e persistência das macros do Espanso."""

    def __init__(self) -> None:
        """Inicializa o parser YAML e carrega o diretório configurado."""
        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        self.yaml.indent(mapping=2, sequence=4, offset=2)
        self.dados_carregados: CommentedMap | None = None
        self.diretorio_espanso = carregar_configuracao()["espanso_match_dir"]
        self.caminho_base_yml = os.path.join(self.diretorio_espanso, "base.yml")

    def carregar_dados(self) -> CommentedMap:
        """Carrega o YAML preservando comentários e estrutura.

        Returns:
            Mapa YAML com a coleção ``matches``.
        """
        if not os.path.exists(self.caminho_base_yml):
            self.dados_carregados = CommentedMap({'matches': []})
            return self.dados_carregados

        try:
            with open(self.caminho_base_yml, 'r', encoding='utf-8') as arquivo:
                dados = self.yaml.load(arquivo)
                if not dados:
                    dados = CommentedMap({'matches': []})
                if 'matches' not in dados:
                    dados['matches'] = []
                self.dados_carregados = dados
                return dados
        except Exception as erro:
            logger.exception("Falha ao ler arquivo YAML: %s", self.caminho_base_yml)
            raise RuntimeError(f"Erro ao ler arquivo: {erro}") from erro

    def salvar_dados(self) -> None:
        """Persiste as alterações no arquivo YAML configurado."""
        if self.dados_carregados is None:
            return

        try:
            os.makedirs(self.diretorio_espanso, exist_ok=True)
            with open(self.caminho_base_yml, 'w', encoding='utf-8') as arquivo:
                self.yaml.dump(self.dados_carregados, arquivo)
        except Exception:
            logger.exception("Falha ao escrever arquivo YAML: %s", self.caminho_base_yml)
            raise

    def adicionar_macro(self, trigger: str, replace: str) -> None:
        """Adiciona e registra uma macro após salvar o YAML.

        Args:
            trigger: Atalho que aciona a macro.
            replace: Texto inserido pelo Espanso.
        """
        if self.dados_carregados is None:
            self.carregar_dados()

        nova_macro = {
            'trigger': trigger,
            'replace': self._formatar_replace(replace)
        }
        self.dados_carregados['matches'].append(nova_macro)
        self.salvar_dados()
        logger.info("Macro adicionada: trigger=%s", trigger)

    def atualizar_macro(
        self, index: int, novo_trigger: str, novo_replace: str
    ) -> bool:
        """Atualiza uma macro existente pelo índice.

        Args:
            index: Posição da macro na coleção.
            novo_trigger: Novo atalho da macro.
            novo_replace: Novo texto de substituição.

        Returns:
            ``True`` se a macro foi atualizada; caso contrário, ``False``.
        """
        if self.dados_carregados is None:
            self.carregar_dados()

        if 0 <= index < len(self.dados_carregados['matches']):
            self.dados_carregados['matches'][index]['trigger'] = novo_trigger
            self.dados_carregados['matches'][index]['replace'] = self._formatar_replace(novo_replace)
            self.salvar_dados()
            logger.info("Macro editada: trigger=%s", novo_trigger)
            return True
        return False

    def excluir_macro(self, index: int) -> bool:
        """Remove uma macro pelo índice.

        Args:
            index: Posição da macro na coleção.

        Returns:
            ``True`` se a macro foi removida; caso contrário, ``False``.
        """
        if self.dados_carregados is None:
            self.carregar_dados()

        if 0 <= index < len(self.dados_carregados['matches']):
            trigger = self.dados_carregados['matches'][index].get('trigger', '???')
            del self.dados_carregados['matches'][index]
            self.salvar_dados()
            logger.info("Macro excluída: trigger=%s", trigger)
            return True
        return False

    def _formatar_replace(self, text: str) -> str:
        """Preserva substituições multilinha como escalares YAML literais.

        Args:
            text: Texto de substituição da macro.

        Returns:
            Texto preparado para serialização YAML.
        """
        if '\n' in text:
            return PreservedScalarString(text)
        return text

# --- INTERFACE GRÁFICA (FRONTEND) ---
class App(ctk.CTk):
    """Interface gráfica para gerenciar as macros do Espanso."""

    def __init__(self) -> None:
        """Cria a janela principal e inicializa as abas da aplicação."""
        super().__init__()

        self.title("TypeFlow")
        self.geometry("700x550")
        
        icon_path = os.path.join(DIRETORIO_APLICACAO, "logo.ico")
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)
        
        self.manager = MacroManager()
        self.macros_cache: list[dict[str, Any]] = []
        self.selected_index: int | None = None
        self._status_after_id: str | None = None
        
        # Grid layout 1x1
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Abas
        self.tabview = ctk.CTkTabview(self, width=650)
        self.tabview.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.status_label = ctk.CTkLabel(self, text="", anchor="w")
        self.status_label.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")
        
        self.tab_criar = self.tabview.add("Criar Nova")
        self.tab_gerenciar = self.tabview.add("Gerenciar Macros")
        
        self.setup_aba_criar()
        self.setup_aba_gerenciar()
        
        # Carrega dados iniciais
        try:
            self.atualizar_lista_macros()
        except Exception as e:
            logger.exception("Falha ao carregar macros na inicialização")
            messagebox.showerror("Erro Inicial", str(e))

    def setup_aba_criar(self) -> None:
        """Monta os campos para cadastrar uma nova macro."""
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

    def setup_aba_gerenciar(self) -> None:
        """Monta a lista de macros e o editor da aba de gerenciamento."""
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

    def atualizar_lista_macros(self) -> None:
        """Atualiza a lista visual a partir do arquivo YAML configurado."""
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

    def selecionar_macro(self, index: int) -> None:
        """Carrega no editor os dados da macro selecionada.

        Args:
            index: Posição da macro na lista em memória.
        """
        self.selected_index = index
        macro = self.macros_cache[index]
        
        self.edit_trigger.delete(0, "end")
        self.edit_trigger.insert(0, macro.get('trigger', ''))
        
        self.edit_replace.delete("0.0", "end")
        self.edit_replace.insert("0.0", str(macro.get('replace', '')))
        
        self.btn_update.configure(state="normal")
        self.btn_delete.configure(state="normal")

    def acao_salvar_nova(self) -> None:
        """Valida e salva uma nova macro informada na interface."""
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
            logger.exception("Falha na ação de criação de macro")
            messagebox.showerror("Erro", f"Falha ao salvar: {e}")

    def acao_atualizar(self) -> None:
        """Valida e persiste as alterações da macro selecionada."""
        if self.selected_index is None: return
        
        trigger = self.edit_trigger.get().strip()
        replace = self.edit_replace.get("0.0", "end").strip()
        
        if not trigger or not replace:
            messagebox.showwarning("Atenção", "Campos não podem ficar vazios!")
            return

        try:
            atualizada = self.manager.atualizar_macro(
                self.selected_index, trigger, replace
            )
            self.atualizar_lista_macros()
            if atualizada:
                self.exibir_status("Status: Macro atualizada com sucesso")
        except Exception as e:
            logger.exception("Falha na ação de edição de macro")
            messagebox.showerror("Erro", f"Falha ao atualizar: {e}")

    def acao_excluir(self) -> None:
        """Confirma e exclui a macro selecionada."""
        if self.selected_index is None: return
        
        confirm = messagebox.askyesno("Confirmar Exclusão", "Tem certeza que deseja excluir esta macro?")
        if confirm:
            try:
                excluida = self.manager.excluir_macro(self.selected_index)
                # Limpa editor
                self.selected_index = None
                self.edit_trigger.delete(0, "end")
                self.edit_replace.delete("0.0", "end")
                self.btn_update.configure(state="disabled")
                self.btn_delete.configure(state="disabled")
                
                self.atualizar_lista_macros()
                if excluida:
                    self.exibir_status("Status: Macro excluída com sucesso")
            except Exception as e:
                logger.exception("Falha na ação de exclusão de macro")
                messagebox.showerror("Erro", f"Falha ao excluir: {e}")

    def exibir_status(self, mensagem: str) -> None:
        """Exibe feedback temporário no rodapé da janela.

        Args:
            mensagem: Texto de status a ser exibido por três segundos.
        """
        if self._status_after_id is not None:
            self.after_cancel(self._status_after_id)
        self.status_label.configure(text=mensagem, text_color="#2ecc71")
        self._status_after_id = self.after(
            3000, lambda: self.status_label.configure(text="")
        )

if __name__ == "__main__":
    app: App = App()
    app.mainloop()
