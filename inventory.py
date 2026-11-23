import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import yt_dlp
from yt_dlp.utils import DateRange

import config
from config import format_duration
from youtube_api import YouTubeAPIClient


class ChannelInventory:
    """
    Responsável por obter os metadados dos vídeos do canal sem efetuar o download dos ficheiros multimédia,
    filtrar por data ou intervalo, ordenar em ordem cronológica crescente e exportar para Markdown (.md),
    JSON (.json) e CSV (.csv).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        cookie_browser: Optional[str] = None,
        logger: Optional[Any] = None,
    ):
        self.api_key = api_key
        self.cookie_browser = cookie_browser
        self.logger = logger

    def _get_ydl_options(
        self, date_range: Optional[DateRange] = None, is_playlist: bool = False
    ) -> dict:
        opts: Dict[str, Any] = {
            "skip_download": True,
            "noplaylist": not is_playlist,
            "ignoreerrors": True,
            "quiet": True,
            "no_warnings": True,
            "js_runtimes": config.get_js_runtimes(),
            "remote_components": ["ejs:github"],
            "sleep_interval_requests": 1,
        }

        if self.cookie_browser:
            opts["cookiesfrombrowser"] = (self.cookie_browser,)

        if date_range is not None:
            opts["daterange"] = date_range
            # Interrompe a extração assim que encontrar vídeos anteriores à data mínima,
            # poupando centenas de pedidos desnecessários e evitando rate-limit
            opts["break_on_reject"] = True

        if self.logger:
            opts["logger"] = self.logger

        return opts

    def load_channel_videos(
        self,
        channel_url: str,
        date_range: Optional[DateRange] = None,
        progress_callback: Optional[Callable[[int, Optional[int], str], None]] = None,
        content_type: str = "videos",
    ) -> List[Dict[str, Any]]:
        """
        Extrai a lista de vídeos do canal ou playlist (via YouTube Data API v3 se configurada, ou yt-dlp).
        Suporta filtrar por 'videos' (uploads regulares), 'streams' (lives) ou 'both'.
        Retorna a lista de vídeos já ordenada em ordem cronológica crescente.
        """
        is_playlist = config.is_playlist_url(channel_url)

        # Se foi fornecida uma chave de API, utilizar a YouTube Data API v3 oficial (Opção B)
        if self.api_key:
            client = YouTubeAPIClient(self.api_key)
            return client.fetch_videos(
                channel_input=channel_url,
                date_range=date_range,
                progress_callback=progress_callback,
                content_type=content_type,
            )

        # Caso contrário, recorrer ao yt-dlp (com cookies e break_on_reject se configurados)
        target_urls = config.get_channel_target_urls(channel_url, content_type)
        opts = self._get_ydl_options(date_range=date_range, is_playlist=is_playlist)

        videos: List[Dict[str, Any]] = []
        seen_ids = set()

        with yt_dlp.YoutubeDL(opts) as ydl:
            count = 0
            for url in target_urls:
                is_stream_url = url.endswith("/streams")
                info = ydl.extract_info(url, download=False)
                if not info:
                    continue

                raw_entries = info.get("entries") or []
                entries_list = list(raw_entries)
                total = len(entries_list)

                for entry in entries_list:
                    if not entry:
                        continue

                    video_id = entry.get("id") or ""
                    if not video_id or video_id in seen_ids:
                        continue
                    seen_ids.add(video_id)

                    upload_date = entry.get("upload_date")
                    if not upload_date and entry.get("timestamp"):
                        upload_date = datetime.fromtimestamp(entry["timestamp"]).strftime(
                            "%Y%m%d"
                        )

                    if not upload_date:
                        continue

                    count += 1
                    title = entry.get("title") or "Sem título"
                    duration = entry.get("duration")
                    webpage_url = entry.get("webpage_url") or f"https://www.youtube.com/watch?v={video_id}"

                    month = f"{upload_date[:4]}-{upload_date[4:6]}"
                    upload_date_formatted = (
                        f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
                    )

                    is_live = (
                        is_stream_url
                        or entry.get("is_live")
                        or entry.get("was_live")
                        or entry.get("live_status") in ("is_live", "was_live", "post_live")
                    )
                    video_type = "Live" if is_live else "Vídeo"

                    videos.append(
                        {
                            "id": video_id,
                            "title": title,
                            "upload_date": upload_date,
                            "upload_date_formatted": upload_date_formatted,
                            "month": month,
                            "url": webpage_url,
                            "duration": duration,
                            "duration_formatted": format_duration(duration),
                            "view_count": entry.get("view_count"),
                            "is_live": is_live,
                            "video_type": video_type,
                        }
                    )

                    if progress_callback:
                        progress_callback(count, total, title)

        # Ordenação estritamente em ordem crescente por data de publicação
        videos.sort(key=lambda v: (v["upload_date"], v["title"].lower()))
        return videos

    def filter_month(
        self, videos: List[Dict[str, Any]], month_label: str
    ) -> List[Dict[str, Any]]:
        """
        Filtra os vídeos correspondentes a um mês específico no formato AAAA-MM.
        """
        return [v for v in videos if v["month"] == month_label]

    def filter_range(
        self,
        videos: List[Dict[str, Any]],
        start_month: str,
        end_month: str,
    ) -> List[Dict[str, Any]]:
        """
        Filtra vídeos dentro de um intervalo de meses [start_month, end_month] (ambos AAAA-MM).
        """
        return [v for v in videos if start_month <= v["month"] <= end_month]

    def group_by_month(
        self, videos: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Agrupa os vídeos por mês (AAAA-MM), garantindo meses e vídeos em ordem crescente.
        """
        grouped = defaultdict(list)
        for video in videos:
            grouped[video["month"]].append(video)

        # Meses ordenados de forma crescente (ex: 2024-09, 2024-10, 2024-11...)
        return dict(sorted(grouped.items(), key=lambda item: item[0]))

    def export_json(
        self,
        grouped: Dict[str, List[Dict[str, Any]]],
        output_file: Path,
        channel_name: str,
        filter_desc: str,
    ) -> Path:
        """
        Exporta a listagem para formato JSON com metadados detalhados.
        """
        total_videos = sum(len(vids) for vids in grouped.values())
        payload = {
            "channel": channel_name,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "filter": filter_desc,
            "total_videos": total_videos,
            "total_months": len(grouped),
            "months": grouped,
        }

        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

        return output_file

    def export_csv(
        self,
        grouped: Dict[str, List[Dict[str, Any]]],
        output_file: Path,
    ) -> Path:
        """
        Exporta a listagem para CSV codificado com UTF-8-SIG para compatibilidade perfeita com Excel.
        """
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "Mês",
                    "Data de Publicação",
                    "Tipo",
                    "Título",
                    "Duração",
                    "ID do Vídeo",
                    "URL",
                ]
            )

            for month, vids in grouped.items():
                for v in vids:
                    writer.writerow(
                        [
                            month,
                            v["upload_date_formatted"],
                            v.get("video_type", "Vídeo"),
                            v["title"],
                            v["duration_formatted"],
                            v["id"],
                            v["url"],
                        ]
                    )

        return output_file

    def export_markdown(
        self,
        grouped: Dict[str, List[Dict[str, Any]]],
        output_file: Path,
        channel_name: str,
        filter_desc: str,
    ) -> Path:
        """
        Exporta a listagem para Markdown (.md) estruturado e legível em leitores e GitHub/Obsidian.
        """
        total_videos = sum(len(vids) for vids in grouped.values())
        total_months = len(grouped)
        now_str = datetime.now().strftime("%d/%m/%Y %H:%M")

        lines = [
            f"# 📺 Catálogo de Vídeos — {channel_name}\n\n",
            f"> **Gerado em:** {now_str}  \n",
            f"> **Filtro:** {filter_desc}  \n",
            f"> **Total de vídeos:** {total_videos} | **Meses abrangidos:** {total_months}\n\n",
            "---\n\n",
        ]

        if total_months > 1:
            lines.append("## 📑 Índice por Mês\n\n")
            for month, vids in grouped.items():
                s = "s" if len(vids) != 1 else ""
                lines.append(f"- [{month}](#mes-{month.replace('-', '')}) ({len(vids)} vídeo{s})\n")
            lines.append("\n---\n\n")

        global_idx = 1
        for month, vids in grouped.items():
            s = "s" if len(vids) != 1 else ""
            anchor = f"mes-{month.replace('-', '')}"
            lines.append(f'## <a id="{anchor}"></a>📅 {month} ({len(vids)} vídeo{s})\n\n')
            lines.append("| # | Data | Tipo | Título | Duração | Link |\n")
            lines.append("|:---:|:---:|:---:|---|:---:|---|\n")

            for v in vids:
                clean_title = v["title"].replace("|", "\\|")
                vtype = v.get("video_type", "Vídeo")
                lines.append(
                    f"| {global_idx} | {v['upload_date_formatted']} | {vtype} | {clean_title} | "
                    f"{v['duration_formatted']} | [Ver no YouTube]({v['url']}) |\n"
                )
                global_idx += 1

            lines.append("\n")

        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text("".join(lines), encoding="utf-8")
        return output_file

    def export_inventory(
        self,
        grouped: Dict[str, List[Dict[str, Any]]],
        dest_dir: Path,
        channel_url: str,
        filter_desc: str,
        file_suffix: str,
        export_format: str,
    ) -> List[Path]:
        """
        Exporta nos formatos escolhidos ('md', 'json', 'csv' ou 'all').
        Devolve a lista dos ficheiros gerados.
        """
        dest_dir = Path(dest_dir)
        dest_dir.mkdir(parents=True, exist_ok=True)

        slug = config.get_channel_slug(channel_url)
        base_name = f"catalogo_{slug}_{file_suffix}"
        exported_paths: List[Path] = []

        if export_format in ["md", "all"]:
            p = dest_dir / f"{base_name}.md"
            self.export_markdown(grouped, p, channel_name=slug, filter_desc=filter_desc)
            exported_paths.append(p)

        if export_format in ["json", "all"]:
            p = dest_dir / f"{base_name}.json"
            self.export_json(grouped, p, channel_name=slug, filter_desc=filter_desc)
            exported_paths.append(p)

        if export_format in ["csv", "all"]:
            p = dest_dir / f"{base_name}.csv"
            self.export_csv(grouped, p)
            exported_paths.append(p)

        return exported_paths
