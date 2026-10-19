import logging
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML, CommentedMap
from ruamel.yaml.scalarstring import PreservedScalarString

import config

logging.basicConfig(
    filename=config.LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    encoding="utf-8",
)
logger = logging.getLogger("typeflow_backend")

class MacroManager:
    """Camada de dados isolada para gerenciar os arquivos YAML do Espanso."""

    def __init__(self) -> None:
        self.yaml = YAML()
        self.yaml.preserve_quotes = True
        self.yaml.indent(mapping=2, sequence=4, offset=2)
        self.dados_carregados: CommentedMap | None = None
        
        self.diretorio_espanso: Path = config.carregar_configuracao_segura()
        self.caminho_base_yml: Path = self.diretorio_espanso / "base.yml"

    def carregar_dados(self) -> CommentedMap:
        if not self.caminho_base_yml.exists():
            self.dados_carregados = CommentedMap({'matches': []})
            return self.dados_carregados

        try:
            with open(self.caminho_base_yml, 'r', encoding='utf-8') as arquivo:
                dados = self.yaml.load(arquivo)
                if not dados or 'matches' not in dados:
                    dados = CommentedMap({'matches': []})
                self.dados_carregados = dados
                return dados
        except Exception as erro:
            logger.exception("Falha ao ler arquivo YAML")
            raise RuntimeError(f"Erro ao ler arquivo YAML: {erro}") from erro

    def salvar_dados(self) -> None:
        if self.dados_carregados is None:
            return
        try:
            self.diretorio_espanso.mkdir(parents=True, exist_ok=True)
            with open(self.caminho_base_yml, 'w', encoding='utf-8') as arquivo:
                self.yaml.dump(self.dados_carregados, arquivo)
        except Exception as erro:
            logger.exception("Falha ao escrever arquivo YAML")
            raise RuntimeError(f"Erro ao salvar arquivo YAML: {erro}")

    def _formatar_replace(self, text: str) -> str:
        # Previne erros de quebra de linha do Windows no YAML
        texto_limpo = text.replace('\r\n', '\n')
        if '\n' in texto_limpo:
            return PreservedScalarString(texto_limpo)
        return texto_limpo

    def adicionar_macro(self, trigger: str, replace: str) -> None:
        self.carregar_dados()
        nova_macro = {
            'trigger': trigger,
            'replace': self._formatar_replace(replace)
        }
        self.dados_carregados['matches'].append(nova_macro)
        self.salvar_dados()
        logger.info("Macro adicionada: trigger=%s", trigger)

    def atualizar_macro(self, index: int, novo_trigger: str, novo_replace: str) -> bool:
        self.carregar_dados()
        if 0 <= index < len(self.dados_carregados['matches']):
            self.dados_carregados['matches'][index]['trigger'] = novo_trigger
            self.dados_carregados['matches'][index]['replace'] = self._formatar_replace(novo_replace)
            self.salvar_dados()
            logger.info("Macro editada: trigger=%s", novo_trigger)
            return True
        return False

    def excluir_macro(self, index: int) -> bool:
        self.carregar_dados()
        if 0 <= index < len(self.dados_carregados['matches']):
            trigger = self.dados_carregados['matches'][index].get('trigger', '???')
            del self.dados_carregados['matches'][index]
            self.salvar_dados()
            logger.info("Macro excluída: trigger=%s", trigger)
            return True
        return False