import os
import re
import calendar
from datetime import datetime
from pathlib import Path
from typing import Optional

# Diretórios base
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DOWNLOAD_DIR = Path.home() / "Videos" / "YouTube_Backups"
ARCHIVE_FILE = BASE_DIR / "downloaded_archive.txt"
ENV_FILE = BASE_DIR / ".env"


def _load_env_file():
    """Carrega variáveis do ficheiro .env se presente."""
    if ENV_FILE.exists():
        try:
            for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("\"'")
                    if k and k not in os.environ:
                        os.environ[k] = v
        except Exception:
            pass


_load_env_file()


def get_api_key() -> Optional[str]:
    """Devolve a chave da YouTube Data API v3 se configurada."""
    return os.environ.get("YOUTUBE_API_KEY", "").strip() or None


def save_api_key(key: str):
    """Guarda a chave da YouTube Data API v3 no ficheiro .env local."""
    key = key.strip()
    os.environ["YOUTUBE_API_KEY"] = key
    lines = []
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if not line.strip().startswith("YOUTUBE_API_KEY="):
                lines.append(line)
    lines.append(f"YOUTUBE_API_KEY={key}")
    ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")

# Estrutura de saída dos ficheiros:
# Cria a pasta AAAA-MM automaticamente com base na data de upload do vídeo
# Exemplo: /pasta_destino/2026-11/Titulo_do_Video [id].mp4
OUTPUT_TEMPLATE = "%(upload_date>%Y-%m|sem-data)s/%(title)s [%(id)s].%(ext)s"


def format_duration(seconds: Optional[int]) -> str:
    """
    Formata segundos para o formato legível HH:MM:SS ou MM:SS.
    """
    if seconds is None:
        return "N/D"
    try:
        s = int(seconds)
        m, sec = divmod(s, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h:d}:{m:02d}:{sec:02d}"
        return f"{m:02d}:{sec:02d}"
    except (ValueError, TypeError):
        return "N/D"


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
    if (
        not url.endswith("/videos")
        and not url.endswith("/shorts")
        and not url.endswith("/streams")
    ):
        url = f"{url}/videos"

    return url


def normalize_video_url(video_input: str) -> str:
    """
    Normaliza o link ou ID de um vídeo específico.
    Suporta links diretos, shorts, youtu.be ou ID direto de 11 caracteres.
    """
    url = video_input.strip()
    if not url.startswith("http://") and not url.startswith("https://"):
        url = f"https://www.youtube.com/watch?v={url}"
    return url


def parse_year(year_str: str) -> tuple[str, str, str]:
    """
    Valida e converte um ano no formato AAAA.
    Retorna: (data_inicio_AAAAMMDD, data_fim_AAAAMMDD, rotulo)
    """
    val = year_str.strip()
    if val.isdigit() and len(val) == 4:
        year = int(val)
        if 2005 <= year <= 2035:
            return f"{year:04d}0101", f"{year:04d}1231", str(year)
    raise ValueError("Ano inválido. Introduza um ano com 4 dígitos (ex: 2024).")


def parse_month(month_str: str) -> tuple[str, str, str]:
    """
    Valida e converte um mês nos formatos AAAA-MM, MM-AAAA, MM/AAAA ou MM.AAAA.
    Retorna: (data_inicio_AAAAMMDD, data_fim_AAAAMMDD, rotulo_AAAA-MM)
    """
    val = month_str.strip().replace("/", "-").replace(".", "-")
    parts = val.split("-")
    if len(parts) == 2:
        p1, p2 = parts[0].strip(), parts[1].strip()
        if len(p1) == 4 and p1.isdigit() and p2.isdigit():
            year, month = int(p1), int(p2)
        elif len(p2) == 4 and p2.isdigit() and p1.isdigit():
            year, month = int(p2), int(p1)
        else:
            raise ValueError("Formato inválido.")

        if 1 <= month <= 12 and 2005 <= year <= 2035:
            last_day = calendar.monthrange(year, month)[1]
            return (
                f"{year:04d}{month:02d}01",
                f"{year:04d}{month:02d}{last_day:02d}",
                f"{year:04d}-{month:02d}",
            )
    raise ValueError(
        "Formato de mês inválido. Use AAAA-MM (ex: 2024-11) ou MM-AAAA (ex: 11-2024)."
    )


def parse_month_range(start_str: str, end_str: str) -> tuple[str, str, str, str]:
    """
    Valida e converte dois meses para um intervalo (início e fim).
    Retorna: (start_date_YYYYMMDD, end_date_YYYYMMDD, label_start_YYYY-MM, label_end_YYYY-MM)
    """
    start_date, _, label_start = parse_month(start_str)
    _, end_date, label_end = parse_month(end_str)

    if start_date > end_date:
        raise ValueError(
            f"O mês inicial ({label_start}) não pode ser posterior ao mês final ({label_end})."
        )

    return start_date, end_date, label_start, label_end


def get_channel_slug(channel_input: str) -> str:
    """
    Extrai um nome/identificador seguro para nomes de ficheiros a partir do link ou handle do canal.
    Exemplo: '@MeuCanal' -> 'MeuCanal'
             'https://www.youtube.com/@CanalX/videos' -> 'CanalX'
    """
    import re

    clean = channel_input.strip().rstrip("/")
    if "/videos" in clean:
        clean = clean.rsplit("/videos", 1)[0]
    if "@" in clean:
        slug = clean.split("@")[-1].split("/")[0]
    else:
        slug = clean.split("/")[-1]
    slug = re.sub(r"[^\w\-]", "_", slug).strip("_")
    return slug or "canal"


def parse_day(day_str: str) -> tuple[str, str]:
    """
    Valida e converte um dia nos formatos AAAA-MM-DD ou DD/MM/AAAA.
    Retorna: (data_AAAAMMDD, rotulo_legivel)
    """
    val = day_str.strip()
    formats = ["%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d", "%Y%m%d"]
    for fmt in formats:
        try:
            dt = datetime.strptime(val, fmt)
            if 2005 <= dt.year <= 2035:
                return dt.strftime("%Y%m%d"), dt.strftime("%d/%m/%Y")
        except ValueError:
            continue
    raise ValueError(
        "Formato de dia inválido. Use AAAA-MM-DD (ex: 2024-11-19) ou DD/MM/AAAA (ex: 19/11/2024)."
    )
