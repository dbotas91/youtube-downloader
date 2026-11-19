# 📺 YouTube Channel Backup — Downloader

Aplicação em Python para descarregar vídeos do teu canal do YouTube, organizando-os automaticamente em subpastas por ano e mês de publicação (`AAAA-MM`).

---

## ✨ Funcionalidades

### 📥 Transferência de Vídeos (MP4)

| Opção | Modo | Descrição |
|:---:|------|-----------|
| **1** | **Canal Completo** | Descarrega todos os uploads do canal |
| **2** | **Vídeo Individual** | Descarrega um vídeo específico por link ou ID |
| **3** | **Filtrar por Ano** | Apenas vídeos de um ano (ex: `2024`) |
| **4** | **Filtrar por Mês** | Apenas vídeos de um mês (ex: `2024-11` ou `11-2024`) |
| **5** | **Filtrar por Dia** | Apenas vídeos de um dia exato (ex: `19/11/2024`) |

**Sempre que um vídeo é descarregado**, é automaticamente guardado na subpasta correspondente à data de publicação:

```
<pasta destino>/
  2024-03/
    Título do Vídeo [abc123].mp4
  2024-11/
    Outro Vídeo [xyz789].mp4
```

### 📋 Listagem e Catálogo de Vídeos (Sem Download)

Permite indexar e catalogar os vídeos do canal organizados em ordem cronológica crescente, exportando para o formato que preferires:

| Opção | Modo | Descrição |
|:---:|------|-----------|
| **6** | **Listar Mês Específico** | Exporta a lista de vídeos de um mês (ex: `11-2024`) |
| **7** | **Listar Intervalo de Meses** | Exporta os vídeos de um intervalo (ex: `09-2024` a `12-2024`) |
| **8** | **Listar Todos Agrupados** | Exporta todos os vídeos do canal separados e agrupados por mês |

**Formatos de exportação suportados:**
- **Markdown (`.md`)** — Ideal para visualização direta, leitura humana, GitHub e notas (Obsidian) com índice por mês e links diretos.
- **JSON (`.json`)** — Ideal para integrações, scripts de automação, APIs e preservação completa de metadados estruturados.
- **CSV (`.csv`)** — Ideal para abrir diretamente no Excel ou Google Sheets (com codificação UTF-8-BOM) para filtros e ordenação manual.
- **Todos (`md, json, csv`)** — Exporta os 3 ficheiros em simultâneo com nomes descritivos (ex: `catalogo_OSeuCanal_09-2024_a_12-2024.md`).

Outras características:
- **Sem duplicados** — registo permanente em `downloaded_archive.txt`; vídeos já descarregados são ignorados automaticamente em execuções futuras
- **Máxima qualidade (MP4)** — combina o melhor fluxo de vídeo e áudio via FFmpeg
- **Apenas uploads próprios** — foca-se na aba `/videos` do canal, ignorando playlists de terceiros
- **Vídeos privados / não listados** — suporte a importação de cookies de sessão do browser (Chrome, Firefox, Edge, etc.)
- **Anti rate-limit** — pausa automática entre pedidos para não ser bloqueado pelo YouTube
- **Suporte a WSL / Windows / Linux** — deteta automaticamente a pasta `Vídeos` do utilizador Windows em ambientes WSL

---

## 🛠 Pré-requisitos

| Ferramenta | Versão mínima | Notas |
|-----------|--------------|-------|
| Python | 3.12+ | Incluído no Ubuntu 24.04 |
| FFmpeg | qualquer | Necessário para juntar vídeo + áudio |
| pip | qualquer | Para instalar dependências Python |

> [!NOTE]
> Instalar o Node.js (`sudo apt install nodejs`) é opcional mas recomendado: elimina o aviso de *JS runtime* e garante acesso a todos os formatos de qualidade.

---

## 🚀 Instalação e Primeira Execução

```bash
# 1. Clonar o repositório
git clone git@github.com:<utilizador>/youtube-downloader.git
cd youtube-downloader

# 2. Criar o ambiente virtual e instalar dependências
python3 -m venv .venv --without-pip
curl -sSL https://bootstrap.pypa.io/get-pip.py | .venv/bin/python3
.venv/bin/pip install -r requirements.txt

# 3. Executar
./run.sh
```

---

## ▶️ Utilização do Dia-a-Dia

```bash
cd ~/Projetos/youtube-downloader
./run.sh
```

Ou manualmente:
```bash
source .venv/bin/activate
python3 main.py
```

**Para interromper a qualquer momento:** `Ctrl + C`

> [!TIP]
> Para executar em segundo plano e poder fechar o terminal, usa o Tmux:
> ```bash
> tmux new -s yt
> ./run.sh
> # Para largar sem parar: Ctrl+a d
> # Para voltar: tmux attach -t yt
> ```

---

## 🗂 Exemplos de Entradas Aceites

| Campo | Exemplos válidos |
|-------|----------------|
| Canal | `@MeuCanal`, `https://www.youtube.com/@MeuCanal`, `MeuCanal` |
| Vídeo individual | `https://www.youtube.com/watch?v=abc123`, `abc123` |
| Ano | `2024` |
| Mês | `2024-11`, `11/2024` |
| Dia | `2024-11-19`, `19/11/2024`, `19-11-2024` |

---

## ⚠️ Resolução de Problemas Comuns

### Rate-limit do YouTube
```
ERROR: Video unavailable. The current session has been rate-limited...
```
O YouTube bloqueou temporariamente a tua sessão por excesso de pedidos. **Aguarda 1 hora** e volta a executar. Os vídeos já registados no histórico não serão repetidos.

### Aviso de JS runtime
```
No supported JavaScript runtime could be found...
```
Instala o Node.js para eliminar definitivamente este aviso:
```bash
sudo apt update && sudo apt install -y nodejs
```

### Ambiente virtual sem o ficheiro `activate`
```bash
# Recriar o venv (preserva os pacotes instalados)
python3 -m venv .venv --without-pip
```

### Vídeos privados não descarregados
Ao executar `./run.sh`, na etapa de cookies escolhe **Sim** e indica o teu browser. Garante que tens sessão ativa no YouTube nesse browser.

---

## 📄 Licença

Uso pessoal. Consulta os [Termos de Serviço do YouTube](https://www.youtube.com/t/terms) antes de distribuir conteúdo descarregado.
