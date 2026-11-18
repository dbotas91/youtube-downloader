# 📺 YouTube Channel Backup - Downloader

Aplicação em Python para descarregar todos os vídeos do teu canal do YouTube, organizando-os automaticamente em subpastas por data de publicação (**AAAA-MM**).

---

## ✨ Características

* **Apenas Vídeos do Canal:** Foca-se estritamente na lista de uploads diretos (`/videos`), ignorando playlists de terceiros e evitando qualquer duplicação.
* **Organização Automática por Data:** Cria subpastas no formato `AAAA-MM` (ex: `2026-11/Nome_do_Video [id].mp4`) com base na data real de envio do vídeo.
* **Prevenção de Duplicados:** Utiliza um ficheiro de registo permanente (`downloaded_archive.txt`). Ao executar novamente no futuro, **descarrega apenas os vídeos novos**.
* **Máxima Qualidade (MP4):** Seleciona automaticamente o melhor stream de vídeo e áudio, unindo-os num ficheiro `.mp4` com o `FFmpeg`.
* **Suporte a WSL e Windows:** Permite escolher facilmente entre guardar na pasta de Vídeos do Windows (`/mnt/c/Users/dapb/Videos`) ou no Linux.
* **Vídeos Privados:** Suporte para ler cookies de sessão do navegador (Chrome, Firefox, Edge, etc.) para vídeos não públicos.

---

## 🚀 Como Executar

Entra na pasta do projeto e executa:

```bash
cd ~/Projetos/youtube-downloader
./run.sh
```

*(Ou manualmente com `source .venv/bin/activate && python3 main.py`).*
