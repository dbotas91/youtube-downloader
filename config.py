import os
from pathlib import Path

# Diretórios base
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DOWNLOAD_DIR = Path.home() / "Videos" / "YouTube_Backups"
ARCHIVE_FILE = BASE_DIR / "downloaded_archive.txt"

# Estrutura de saída dos ficheiros:
# Cria a pasta AAAA-MM automaticamente com base na data de upload do vídeo
# Exemplo: /pasta_destino/2026-11/Titulo_do_Video [id].mp4
OUTPUT_TEMPLATE = "%(upload_date>%Y-%m)s/%(title)s [%(id)s].%(ext)s"

def normalize_channel_url(channel_input: str) -> str:
    """
    Garante que o link do canal aponta estritamente para a aba de uploads diretos (/videos),
    evitando playlists ou conteúdos de terceiros.
    """
    url = channel_input.strip()
    
    # Se o utilizador apenas digitou o handle (ex: @OSeuCanal)
    if url.startswith("@"):
        url = f"https://www.youtube.com/{url}"
    elif not url.startswith("http://") and not url.startswith("https://"):
        if "/" not in url:
            url = f"https://www.youtube.com/@{url}"
        else:
            url = f"https://www.youtube.com/{url}"

    # Remove barras finais
    url = url.rstrip("/")

    # Se ainda não apontar para /videos, garante que aponta
    if not url.endswith("/videos") and not url.endswith("/shorts") and not url.endswith("/streams"):
        url = f"{url}/videos"

    return url
