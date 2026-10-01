# TypeFlow - Espanso Manager 🚀

![TypeFlow Logo](logo.png)

![Python](https://img.shields.io/badge/Python-3.12-blue?style=for-the-badge&logo=python) ![CustomTkinter](https://img.shields.io/badge/CustomTkinter-Dark_Mode-2ea44f?style=for-the-badge) ![Nuitka](https://img.shields.io/badge/Build-Nuitka_Standalone-orange?style=for-the-badge)

**TypeFlow** é uma interface gráfica moderna desenvolvida para equipes de Customer Experience (CX) gerenciarem macros do [Espanso](https://espanso.org/) em escala, facilitando a edição de arquivos YAML e evitando erros de sintaxe operacionais.

## 🎥 Demonstração Prática

*(Nota: Substitua esta linha pelo link do seu GIF gravado no Loom ou ScreenToGif)*
![Demo do TypeFlow](demo.gif)

## ✨ Funcionalidades
- **Interface Moderna:** Dark Mode nativo (usando CustomTkinter).
- **Segurança (Zero Data Loss):** Utiliza `ruamel.yaml` para preservar 100% dos comentários e a estrutura do seu arquivo original.
- **Gestão Completa e Risco Mitigado:** Crie, Edite e Exclua macros validadas pela interface, eliminando falhas humanas na configuração.
- **Portátil e B2B Ready:** Funciona de forma independente no caminho padrão `%AppData%` do Windows. Compilado via Nuitka para evitar bloqueios de antivírus.

## ⚙️ Arquitetura do Sistema

```mermaid
graph TD;
    A[Interface CustomTkinter] -->|Valida Input do Analista| B(Motor Lógico Python);
    B -->|ruamel.yaml| C{Ficheiro base.yml};
    C -->|Preserva Estrutura| D[Base de Dados YAML Atualizada];
