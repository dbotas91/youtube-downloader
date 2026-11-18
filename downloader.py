import os
from pathlib import Path
from typing import Callable, Optional

import yt_dlp

import config


class YouTubeChannelDownloader:
    def __init__(
        self,
        destination_dir: Path,
        progress_callback: Optional[Callable[[dict], None]] = None,
        cookie_browser: Optional[str] = None,
    ):
        self.destination_dir = Path(destination_dir)
        self.destination_dir.mkdir(parents=True, exist_ok=True)
        self.progress_callback = progress_callback
        self.cookie_browser = cookie_browser

    def _get_ydl_options(self) -> dict:
        out_template = str(self.destination_dir / config.OUTPUT_TEMPLATE)

        opts = {
            # Seleciona a melhor qualidade de vídeo e áudio e converte para MP4
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
            "merge_output_format": "mp4",
            "outtmpl": out_template,
            # Registo de vídeos já descarregados (evita duplicados)
            "download_archive": str(config.ARCHIVE_FILE),
            # Garantir que processa apenas os uploads e ignora playlists aninhadas
            "noplaylist": True,
            "ignoreerrors": True,
            # Configuração do ffmpeg para pós-processamento
            "postprocessors": [
                {
                    "key": "FFmpegVideoRemuxer",
                    "preferedformat": "mp4",
                }
            ],
            # Manter a data de modificação original do ficheiro igual à data de upload
            "updatetime": True,
            # Silenciar logs desnecessários para a nossa barra de progresso brilhar
            "quiet": True,
            "no_warnings": False,
        }

        # Se o utilizador tiver vídeos privados/não listados e quiser usar cookies do browser
        if self.cookie_browser:
            opts["cookiesfrombrowser"] = (self.cookie_browser,)

        if self.progress_callback:
            opts["progress_hooks"] = [self.progress_callback]

        return opts

    def download_channel(self, channel_url: str):
        """
        Executa a transferência de todos os vídeos novos do canal.
        """
        normalized_url = config.normalize_channel_url(channel_url)
        opts = self._get_ydl_options()

        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([normalized_url])
