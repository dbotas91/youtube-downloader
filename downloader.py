import os
from pathlib import Path
from typing import Callable, Optional, Any

import yt_dlp
from yt_dlp.utils import DateRange

import config


class YouTubeDownloader:
    def __init__(
        self,
        destination_dir: Path,
        progress_callback: Optional[Callable[[dict], None]] = None,
        cookie_browser: Optional[str] = None,
        date_range: Optional[DateRange] = None,
        logger: Optional[Any] = None,
    ):
        self.destination_dir = Path(destination_dir)
        self.destination_dir.mkdir(parents=True, exist_ok=True)
        self.progress_callback = progress_callback
        self.cookie_browser = cookie_browser
        self.date_range = date_range
        self.logger = logger

    def _get_ydl_options(self, apply_date_filter: bool = True) -> dict:
        out_template = str(self.destination_dir / config.OUTPUT_TEMPLATE)

        opts = {
            # Seleciona a melhor qualidade de vídeo e áudio e converte para MP4
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "outtmpl": out_template,
            # Registo de vídeos já descarregados (evita duplicados)
            "download_archive": str(config.ARCHIVE_FILE),
            # Processar estritamente o vídeo/uploads e ignorar playlists aninhadas
            "noplaylist": True,
            "ignoreerrors": True,
            # Configuração do ffmpeg para remux em MP4
            "postprocessors": [
                {
                    "key": "FFmpegVideoRemuxer",
                    "preferedformat": "mp4",
                }
            ],
            # Manter a data de modificação original do ficheiro igual à data de upload
            "updatetime": True,
            "quiet": True,
            "no_warnings": False,
            # Suportar qualquer motor JavaScript disponível no sistema
            "js_runtimes": {"deno": {}, "node": {}, "quickjs": {}, "bun": {}},
        }

        # Filtro de data (se fornecido e aplicável)
        if apply_date_filter and self.date_range is not None:
            opts["daterange"] = self.date_range

        # Se o utilizador tiver vídeos privados/não listados e quiser usar cookies do browser
        if self.cookie_browser:
            opts["cookiesfrombrowser"] = (self.cookie_browser,)

        if self.progress_callback:
            opts["progress_hooks"] = [self.progress_callback]

        if self.logger:
            opts["logger"] = self.logger

        return opts

    def download_channel(self, channel_url: str):
        """
        Executa a transferência dos vídeos do canal (com ou sem filtro de data).
        """
        normalized_url = config.normalize_channel_url(channel_url)
        opts = self._get_ydl_options(apply_date_filter=True)

        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([normalized_url])

    def download_single_video(self, video_input: str):
        """
        Executa a transferência de um vídeo específico.
        Não aplica filtro de data para garantir a descarga do vídeo solicitado,
        mas organiza-o automaticamente na subpasta AAAA-MM correspondente.
        """
        normalized_url = config.normalize_video_url(video_input)
        opts = self._get_ydl_options(apply_date_filter=False)

        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([normalized_url])


# Compatibilidade retroativa
YouTubeChannelDownloader = YouTubeDownloader
