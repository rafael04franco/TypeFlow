import os
import sys
import json
from pathlib import Path

APP_NAME = "TypeFlow"

def get_asset_path(filename: str) -> Path:
    """Garante que assets (como logo.ico) sejam encontrados mesmo dentro do .exe gerado."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / filename
    return Path(__file__).parent / filename

def get_user_data_path() -> Path:
    """Garante permissão de escrita salvando logs e config no %LOCALAPPDATA%."""
    if os.name == 'nt':
        base_dir = Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")))
    else:
        base_dir = Path(os.path.expanduser("~")) / ".config"
    app_dir = base_dir / APP_NAME
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir

USER_DATA_DIR = get_user_data_path()
CONFIG_FILE = USER_DATA_DIR / "config.json"
LOG_FILE = USER_DATA_DIR / "typeflow.log"
DEFAULT_ESPANSO_DIR = Path(os.environ.get("APPDATA", os.path.expanduser("~"))) / "espanso" / "match"

def carregar_configuracao_segura() -> Path:
    """Carrega o caminho do Espanso e aplica a correção de troca de PC."""
    def _salvar_padrao() -> Path:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"espanso_match_dir": str(DEFAULT_ESPANSO_DIR)}, f, indent=2, ensure_ascii=False)
        return DEFAULT_ESPANSO_DIR

    if not CONFIG_FILE.exists():
        return _salvar_padrao()

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)
        
        diretorio = dados.get("espanso_match_dir")
        if not diretorio:
            return _salvar_padrao()
            
        caminho_expandido = Path(os.path.expandvars(str(diretorio).strip()))
        
        # A correção vital: verifica se a pasta do PC anterior existe neste PC
        if not caminho_expandido.parent.exists():
            return _salvar_padrao()
            
        return caminho_expandido
    except Exception:
        return _salvar_padrao()
        