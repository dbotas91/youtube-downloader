# 📺 YouTube Channel Backup — Downloader

Aplicação em Python para descarregar vídeos do teu canal do YouTube, organizando-os automaticamente em subpastas por ano e mês de publicação (`AAAA-MM`).

---

## ✨ Funcionalidades

### 📥 Transferência de Vídeos (MP4)

| Opção | Modo | Descrição |
|:---:|------|-----------|
| **1** | **Canal ou Playlist** | Descarrega todos os uploads do canal ou todos os vídeos de uma playlist |
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

### 🛡️ Proteção Anti Rate-Limit (Disponível para Download e Catálogo)

Tanto ao **descarregar vídeos (MP4)** como ao **gerar catálogos**, podes escolher entre três motores:
1. **YouTube Data API v3 (Oficial Google):**
   - Usa a API oficial do Google Cloud (10.000 requisições/dia gratuitas para sempre).
   - Instantânea, fiável e com **0% de risco de rate-limit**.
   - No descarregamento: descobre a lista de vídeos via API sem tocar na página do canal e transfere apenas os ficheiros encontrados.
   - Podes definir a chave no ficheiro `.env` (`YOUTUBE_API_KEY=sua_chave`) ou inseri-la diretamente na primeira execução quando solicitada no terminal.
2. **yt-dlp com Cookies do Navegador:**
   - Importa a tua sessão do Chrome, Firefox, Edge, Brave ou Chromium para o YouTube reconhecer a tua conta de proprietário do canal.
   - Ativação automática de `break_on_reject: True`: para transferências e listagens por mês ou intervalo, interrompe a leitura assim que sai das datas selecionadas, poupando centenas de pedidos.
3. **yt-dlp Anónimo (Padrão):**
   - Ligação direta sem login nem chaves de API.

#### 🔑 Como obter a Chave de API Gratuita (Opção B)
1. Acede a [console.cloud.google.com](https://console.cloud.google.com/) com a tua conta Google.
2. Cria um novo projeto (ex: `YouTube Backup`).
3. Em **APIs e Serviços ➔ Biblioteca**, pesquisa por **YouTube Data API v3** e clica em **Ativar**.
4. Em **Credenciais ➔ Criar Credenciais ➔ Chave de API** (*API Key*).
5. Copia a chave gerada e cola-a quando a aplicação perguntar (podes optar por guardá-la automaticamente no ficheiro `.env`).

Outras características:
- **Suporte a Playlists** — permite processar playlists inteiras (perfeito para descarregar ou catalogar transmissões ao vivo não listadas ou privadas reunidas no YouTube Studio)
- **Suporte a Vídeos e Lives** — escolha flexível entre apenas vídeos normais, apenas transmissões ao vivo gravadas (`/streams`) ou ambos (Shorts excluídos por padrão)
- **Sem duplicados** — registo permanente em `downloaded_archive.txt`; vídeos já descarregados são ignorados automaticamente em execuções futuras
- **Máxima qualidade (MP4)** — combina o melhor fluxo de vídeo e áudio via FFmpeg
- **Apenas uploads próprios** — foca-se nas abas `/videos` e `/streams` do canal, ignorando playlists de terceiros
- **Vídeos privados / não listados** — suporte a importação de cookies de sessão do browser (Chrome, Firefox, Edge, etc.)
- **Anti rate-limit** — pausa automática entre pedidos para não ser bloqueado pelo YouTube
- **Suporte Multiplataforma (Windows Nativo, WSL e Linux)** — funciona diretamente no Windows (`run.bat` / `run.ps1`) e no Linux/WSL (`run.sh`)
- **Deteção Automática de Discos Externos / USB** — lista unidades e partições com o espaço em disco disponível em tempo real
- **Nomes de ficheiros seguros** — sanitização automática de caracteres para compatibilidade total entre NTFS, FAT32 e ext4

---

## 🛠 Pré-requisitos

| Ferramenta | Windows Nativo | Linux / WSL | Notas |
|-----------|----------------|-------------|-------|
| Python | 3.10+ (adicionar ao PATH) | 3.10+ | [python.org/downloads](https://www.python.org/downloads/) |
| FFmpeg | `winget install Gyan.FFmpeg` | `sudo apt install ffmpeg` | Necessário para juntar vídeo + áudio em MP4 |
| Node.js *(opcional)* | `winget install OpenJS.NodeJS` | `sudo apt install nodejs` | Resolve desafios JavaScript (n challenge) sem avisos |

---

## 🚀 Como Executar

### 🪟 No Windows (Nativo)

1. Dá duplo clique no ficheiro **`run.bat`** (ou executa `.\run.ps1` no PowerShell).
2. O script configura automaticamente o ambiente virtual Python (`.venv`), instala as dependências e inicia o programa!

### 🐧 No Linux ou WSL

```bash
cd youtube-downloader
./run.sh
```
*(O script `run.sh` ativa o ambiente virtual ou cria-o automaticamente na primeira execução).*

---

## 💾 Seleção de Destino e Discos Externos

Na etapa **3. Pasta Base de Destino e Armazenamento**, a aplicação lista automaticamente:
1. A pasta padrão **Vídeos** do teu utilizador (`~/Videos` ou `C:\Users\<utilizador>\Videos`).
2. **Discos externos / pens USB** e unidades secundárias detetadas (ex: `D:`, `E:`, ou `/mnt/d`), com indicação clara do **espaço livre**.
3. Opção manual para colar qualquer caminho ou letra de unidade (se estiveres em WSL e colares um caminho do Windows como `D:\Backups`, a ferramenta converte automaticamente para `/mnt/d/Backups`!).

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
| Canal ou Playlist | `@MeuCanal`, `https://www.youtube.com/@MeuCanal`, `https://www.youtube.com/playlist?list=PL...`, `PLrAXtmErZg...` |
| Vídeo individual | `https://www.youtube.com/watch?v=abc123`, `abc123` |
| Ano | `2024` |
| Mês | `2024-11`, `11-2024`, `11/2024`, `11.2024` |
| Intervalo de Meses | Inicial: `09-2024`, Final: `12-2024` |
| Dia | `2024-11-19`, `19/11/2024`, `19-11-2024` |

---

## ⚠️ Resolução de Problemas Comuns

### Rate-limit do YouTube
```
ERROR: Video unavailable. The current session has been rate-limited...
```
O YouTube bloqueou temporariamente o teu IP por excesso de scraping anónimo.
- **Para gerar catálogos:** Usa a **Opção B (YouTube Data API v3)** — é instantânea e imune a rate-limits.
- **Para transferências:** Seleciona a **Opção C (Cookies do navegador)** para usar a tua sessão autenticada do canal e ativação de paragem antecipada.
- Se já foste bloqueado pelo YouTube, aguarda cerca de 30 a 60 minutos para o IP ser libertado.

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
