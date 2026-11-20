import os
import re
import sys
import shutil
import string
import calendar
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

# ---------------------------------------------------------------------------
# Deteção de plataforma
# ---------------------------------------------------------------------------

IS_WINDOWS: bool = sys.platform == "win32"


def _detect_wsl() -> bool:
    """Verifica se está a correr dentro do WSL (Windows Subsystem for Linux)."""
    try:
        return "microsoft" in Path("/proc/version").read_text(encoding="utf-8").lower()
    except Exception:
        return False


IS_WSL: bool = not IS_WINDOWS and _detect_wsl()

# Diretórios base
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DOWNLOAD_DIR = Path.home() / "Videos" / "YouTube_Backups"
ARCHIVE_FILE = BASE_DIR / "downloaded_archive.txt"
ENV_FILE = BASE_DIR / ".env"


def format_bytes(bytes_val: int) -> str:
    """Formata bytes para representação legível (ex: 500.2 GB)."""
    val = float(bytes_val)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if val < 1024:
            return f"{val:.1f} {unit}"
        val /= 1024
    return f"{val:.1f} PB"


def get_free_space_str(path: Path | str) -> str:
    """Devolve string com espaço livre num dado caminho ou unidade."""
    try:
        p = Path(path)
        while not p.exists() and p.parent != p:
            p = p.parent
        _, _, free = shutil.disk_usage(str(p))
        return f"{format_bytes(free)} livres"
    except Exception:
        return "N/D"


def is_ffmpeg_installed() -> bool:
    """Verifica se o FFmpeg está instalado e acessível no PATH."""
    return shutil.which("ffmpeg") is not None


def get_js_runtimes() -> dict:
    """
    Deteta runtimes JavaScript disponíveis no sistema (Node.js, Deno, Bun)
    para o yt-dlp resolver desafios JS (n challenge). Suporta Linux, WSL e Windows.
    """
    # 1. Linuxbrew Node.js (se presente em Linux/WSL)
    node_brew = Path("/home/linuxbrew/.linuxbrew/bin/node")
    if node_brew.exists():
        return {"node": {"path": str(node_brew)}}

    # 2. Node.js no PATH do sistema
    node_path = shutil.which("node")
    if node_path:
        return {"node": {"path": node_path}}

    # 3. Deno no PATH
    deno_path = shutil.which("deno")
    if deno_path:
        return {"deno": {"path": deno_path}}

    # 4. Bun no PATH
    bun_path = shutil.which("bun")
    if bun_path:
        return {"bun": {"path": bun_path}}

    # 5. Localizações padrão no Windows (se não estiver no PATH)
    if IS_WINDOWS:
        common_win_node = [
            Path(os.environ.get("ProgramFiles", "C:\\Program Files")) / "nodejs" / "node.exe",
            Path(os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")) / "nodejs" / "node.exe",
            Path(os.environ.get("LocalAppData", "")) / "Programs" / "node" / "node.exe",
        ]
        for p in common_win_node:
            if p.exists():
                return {"node": {"path": str(p)}}

    # 6. Fallback padrão yt-dlp
    return {"deno": {}, "node": {}, "quickjs": {}, "bun": {}}


def get_available_storage_locations() -> List[Dict[str, Any]]:
    """
    Deteta unidades e pastas disponíveis para download de vídeos:
    - Pastas predefinidas de vídeos (Linux/Windows)
    - Discos externos (USB / discos rígidos externos)
    - Unidades e partições montadas
    """
    locations: List[Dict[str, Any]] = []
    seen_paths = set()

    def _add_loc(label: str, path: Path, is_external: bool, loc_type: str = "default"):
        canonical = str(path.resolve()) if path.exists() else str(path)
        if canonical in seen_paths:
            return
        seen_paths.add(canonical)
        locations.append({
            "label": label,
            "path": path,
            "free_space": get_free_space_str(path),
            "is_external": is_external,
            "type": loc_type,
        })

    # Caso 1: Windows Nativo
    if IS_WINDOWS:
        user_name = os.environ.get("USERNAME", "Utilizador")
        user_videos = Path.home() / "Videos" / "YouTube_Backups"
        _add_loc(f"Windows: Pasta 'Vídeos' ({user_name})", user_videos, False, "default")

        # Inspecionar unidades lógicas (A: a Z:)
        try:
            import ctypes
            bitmask = ctypes.windll.kernel32.GetLogicalDrives()
            for letter in string.ascii_uppercase:
                if bitmask & 1:
                    drive_root = f"{letter}:\\"
                    drive_type = ctypes.windll.kernel32.GetDriveTypeW(drive_root)
                    is_c = (letter == "C")

                    # DRIVE_REMOVABLE = 2, DRIVE_FIXED = 3, DRIVE_REMOTE = 4
                    if drive_type == 2:
                        _add_loc(
                            f"Disco Removível / USB ({letter}:)",
                            Path(f"{letter}:\\YouTube_Backups"),
                            True,
                            "external",
                        )
                    elif drive_type == 4:
                        _add_loc(
                            f"Unidade de Rede ({letter}:)",
                            Path(f"{letter}:\\YouTube_Backups"),
                            True,
                            "network",
                        )
                    elif drive_type == 3 and not is_c:
                        _add_loc(
                            f"Disco Secundário / Externo ({letter}:)",
                            Path(f"{letter}:\\YouTube_Backups"),
                            True,
                            "external",
                        )
                bitmask >>= 1
        except Exception:
            # Fallback se ctypes falhar
            for letter in string.ascii_uppercase:
                root = Path(f"{letter}:\\")
                if root.exists() and letter != "C":
                    _add_loc(
                        f"Disco Secundário / Externo ({letter}:)",
                        root / "YouTube_Backups",
                        True,
                        "external",
                    )

    # Caso 2: WSL (Windows Subsystem for Linux)
    elif IS_WSL:
        # Detectar utilizadores Windows reais
        c_users = Path("/mnt/c/Users")
        if c_users.exists():
            try:
                for u in c_users.iterdir():
                    if (
                        u.is_dir()
                        and u.name.lower() not in ("default", "default user", "public", "all users", "defaultuser0")
                        and not u.name.startswith("$")
                    ):
                        vid = u / "Videos"
                        if vid.exists():
                            _add_loc(
                                f"Windows: Pasta 'Vídeos' ({u.name})",
                                vid / "YouTube_Backups",
                                False,
                                "default",
                            )
            except Exception:
                pass

        # Pasta de vídeos interna do Linux/WSL
        linux_videos = Path.home() / "Videos" / "YouTube_Backups"
        _add_loc("Linux/WSL: ~/Videos/YouTube_Backups", linux_videos, False, "default")

        # Unidades Windows montadas em /mnt (ex: /mnt/d, /mnt/e, etc.)
        mnt = Path("/mnt")
        if mnt.exists():
            try:
                for item in sorted(mnt.iterdir()):
                    if item.is_dir() and len(item.name) == 1 and item.name.isalpha():
                        letter = item.name.upper()
                        if letter != "C":
                            _add_loc(
                                f"Disco Externo / Unidade Windows ({letter}:) [WSL]",
                                item / "YouTube_Backups",
                                True,
                                "external",
                            )
            except Exception:
                pass

    # Caso 3: Linux Nativo
    else:
        linux_videos = Path.home() / "Videos" / "YouTube_Backups"
        _add_loc("Linux: ~/Videos/YouTube_Backups", linux_videos, False, "default")

    # Deteção de pens USB e discos externos montados em /media ou /run/media (Linux e WSL)
    for media_root in [Path("/media"), Path("/run/media")]:
        if media_root.exists():
            try:
                for user_dir in media_root.iterdir():
                    if user_dir.is_dir():
                        for mount_dir in user_dir.iterdir():
                            if mount_dir.is_dir():
                                _add_loc(
                                    f"Disco Externo USB: {mount_dir.name}",
                                    mount_dir / "YouTube_Backups",
                                    True,
                                    "external",
                                )
            except Exception:
                pass

    # Se nenhuma opção foi encontrada, garantir a pasta padrão
    if not locations:
        locations.append({
            "label": "Pasta Padrão (~/Videos/YouTube_Backups)",
            "path": DEFAULT_DOWNLOAD_DIR,
            "free_space": get_free_space_str(DEFAULT_DOWNLOAD_DIR),
            "is_external": False,
            "type": "default",
        })

    return locations


def normalize_destination_path(raw_input: str) -> Path:
    """
    Normaliza caminhos introduzidos pelo utilizador, suportando:
    - Letras de unidade no Windows (ex: D:, D:\\Backups)
    - Caminhos estilo Windows introduzidos no WSL (ex: D:\\Filmes -> /mnt/d/Filmes)
    - Caminhos com expansão de utilizador (~/...)
    """
    raw = raw_input.strip().strip("\"'")
    if not raw:
        return DEFAULT_DOWNLOAD_DIR

    # Se estiver no WSL e o utilizador colar uma unidade Windows (ex: D: ou D:\Pasta)
    if IS_WSL:
        m = re.match(r"^([a-zA-Z]):[\\/]?(.*)$", raw)
        if m:
            letter = m.group(1).lower()
            rest = m.group(2).replace("\\", "/").strip("/")
            if not rest:
                return Path(f"/mnt/{letter}/YouTube_Backups")
            return Path(f"/mnt/{letter}/{rest}")

    # No Windows nativo, se o utilizador escrever apenas "D:" ou "D:\"
    if IS_WINDOWS:
        m = re.match(r"^([a-zA-Z]):[\\/]?$", raw)
        if m:
            letter = m.group(1).upper()
            return Path(f"{letter}:\\YouTube_Backups")

    path = Path(raw).expanduser()
    return path


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
