# OTUI Editor — Editor Visual para OTUI/OTMD

O **OTUI Editor** é um editor visual desenvolvido em **Python + PySide6 (Qt)**, projetado para criação e modificação de arquivos **OTUI** e **OTMD** — formatos amplamente utilizados em projetos como **OpenTibia**, **OTClient** e sistemas de modding derivados.

Ele oferece um ambiente completo para edição visual, gerenciamento de recursos, manipulação de propriedades e organização de módulos.

---

## 🎨 Visão Geral

A classe principal, **OTUIEditor** (`QMainWindow`), monta toda a interface do editor, incluindo:

- **Barra de ferramentas de widgets**  
  Para adicionar elementos OTUI à cena.

- **Canvas (Área de Edição)**  
  Com grade, zoom, pan e suporte a seleção.

- **Painel lateral direito**, dividido em:  
  - **PropertiesEditor** (propriedades do widget selecionado)  
  - **Navegador de arquivos** para `.otui`, `.otmd` e `.lua`.

---

# 🛠️ Componentes e Funcionalidades

## 1. 📂 ModuleProject — Gerenciamento de Projeto

Responsável por toda a estrutura do módulo OTClient.

### Funções Principais

- **Root do projeto:** diretório base do módulo.  
- **Leitura do `.otmod`:** identifica diretórios de imagens (`images-dir`), dependências etc.  
- **Indexação automática:** localiza arquivos `.otui`, `.otmd`, `.lua` e pastas de imagem.  
- **ResourceResolver:** resolve caminhos relativos OTUI para caminhos absolutos no sistema.  
- **Gerenciamento de estado:** armazena último arquivo editado em  
  `.otui_editor_state.json`.

---

## 2. 🎛️ Canvas e WidgetItem — Edição Visual

### Canvas
Baseado em `QGraphicsView`, inclui:

- Grade de alinhamento  
- Zoom (scroll)  
- Pan (middle mouse)  
- Histórico de ações (undo/redo)  
- Serialização completa do estado da cena

### WidgetItem

Cada widget OTUI do arquivo é representado por um `QGraphicsObject` com:

#### Interação
- Movimentação com snapping (grid 10px)  
- Redimensionamento com 8 handles  
- Desativação automática se houver layout ou anchors  
- Menu de contexto:  
  - trazer para frente  
  - enviar para trás  
  - duplicar  
  - excluir  
  - definir layout (vertical / horizontal)

#### Renderização
- Suporte a **image-source**, **icon-source**, tinting e clipping  
- Suporte completo a **nine-slice scaling** via `image-border`  
- Cores personalizadas por tipo (AppConstants.WIDGET_TYPE_COLORS)

#### Hierarquia & Layouts
- Widgets filhos organizados automaticamente com  
  `layout: vertical` ou `layout: horizontal`  
- Respeita âncoras e regras de alinhamento OTUI

---

## 3. ⚙️ PropertiesEditor — Editor de Propriedades

Gerencia todas as propriedades do widget selecionado.

### Funções
- Atualização **em tempo real** (size/pos refletem movimentos no Canvas)  
- Campos dinâmicos para propriedades padrão e customizadas  
- Suporte nativo para:  
  - **Seleção de imagem** (ImageSourceBrowser)  
  - **Seleção de cor** (QColorDialog)  
  - **Booleanos** (QComboBox)  
- Botão **Adicionar Propriedade**, usando a lista AppConstants.KNOWN_PROPERTIES

---

## 4. 🖼️ ImageSourceBrowser — Navegador de Imagens

Interface dedicada para escolher imagens do módulo.

- Exibe pastas definidas em `images-dir`  
- Mostra thumbnails em grade  
- Retorna o caminho relativo OTUI adequado para o arquivo

---

## 5. 🧩 OTUIParser e save_otui — Parser e Serialização

### OTUIParser
Converte texto OTUI/OTMD em estrutura visual:

- Analisa indentação para determinar hierarquia  
- Cria widgets, propriedades, estados e eventos  
- Popula o Canvas com base no arquivo

### save_otui
Gera o arquivo OTUI final:

- Percorre toda a árvore de WidgetItems  
- Aplica indentação correta  
- Copia imagens externas para o diretório do módulo (se necessário)  
- Converte paths para caminhos relativos OTUI limpos

---

# 🚀 Fluxo de Trabalho

1. **Carregar módulo** (`load_client_module`)  
2. **Abrir arquivo OTUI/OTMD** pelo navegador  
3. **Editar no Canvas**  
   - adicionar widgets  
   - mover, redimensionar, aplicar layouts  
4. **Configurar propriedades** no PropertiesEditor  
5. **Salvar arquivo**, gerando OTUI organizado e válido para o jogo

---

## 📌 Recursos Futuros (opcional)

- Suporte avançado para estados OTUI (`$state`)  
- Editor de eventos (`@event`)  
- Validação automática de hierarquia OTUI  
- Temas customizáveis para o editor  
- Exportação em JSON ou XML

---

## 📄 Licença

*(Adicione aqui a licença do projeto, se existir.)*

---

Se quiser, posso gerar:

✅ uma versão mais curta  
✅ uma versão com imagens e diagramas  
✅ badges (Python, Qt, PySide6, etc.)  
✅ um README completo com instalação, screenshots e passo a passo  

Só pedir!  



## Instalação

Clone o repositório

```bash
 git clone [https://github.com/lehnox/otui-editor.git](https://github.com/lehnox/otui-editor.git)
```
Instale as dependências:
O projeto utiliza a biblioteca PySide6. Instale-a com pip:

  ```bash
 pip install PySide6
```
Execute o Editor:

  ```bash
 python Otui.py
```

Contribuição
Contribuições são muito bem-vindas! Se você encontrar um bug ou tiver uma ideia de melhoria, sinta-se à vontade para abrir uma issue ou enviar um pull request.

