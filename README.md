# 📺 YouTube Channel Backup - Downloader

Aplicação em Python para descarregar vídeos do teu canal do YouTube, organizando-os automaticamente em subpastas por data de publicação (**AAAA-MM**).

---

## ✨ Características

* **Modos Flexíveis de Transferência:**
  * **Canal Completo (Tudo):** Descarrega todos os uploads do canal.
  * **Vídeo Individual:** Descarrega um vídeo específico a partir do link ou ID.
  * **Filtro por Ano:** Descarrega apenas os vídeos publicados num determinado ano (ex: `2024`).
  * **Filtro por Mês:** Descarrega os vídeos publicados num determinado mês (ex: `2024-11` ou `11/2024`).
  * **Filtro por Dia Específico:** Descarrega os vídeos de um dia exato (ex: `2024-11-19` ou `19/11/2024`).
* **Organização Automática por Data (AAAA-MM):** Qualquer vídeo descarregado é automaticamente arrumado na respetiva subpasta com base na data de upload (ex: `2024-11/Titulo_do_Video [id].mp4`).
* **Apenas Uploads Próprios:** Foca-se na aba `/videos` do canal, ignorando playlists de terceiros e evitando duplicações.
* **Prevenção de Duplicados:** Utiliza um ficheiro de registo permanente (`downloaded_archive.txt`). Em execuções futuras, **ignora vídeos já descarregados**.
* **Máxima Qualidade (MP4):** Seleciona o melhor fluxo de vídeo e áudio, convertendo/unindo em formato `.mp4` com FFmpeg.
* **Suporte a WSL e Windows:** Deteta e permite gravar diretamente na pasta `Vídeos` do utilizador Windows (`/mnt/c/Users/dapb/Videos/YouTube_Backups`) ou no WSL/Linux.
* **Vídeos Privados / Restritos:** Opção de carregar cookies de sessão do teu navegador (Chrome, Firefox, Edge, etc.) para transferir vídeos privados ou não listados.

---

## 🚀 Como Executar

Entra na pasta do projeto e executa o script de inicialização:

```bash
cd ~/Projetos/youtube-downloader
./run.sh
```

*(Em alternativa, pode ativar o ambiente virtual manualmente com `source .venv/bin/activate && python3 main.py`).*
