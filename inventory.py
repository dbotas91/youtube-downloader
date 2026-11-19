import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import yt_dlp
from yt_dlp.utils import DateRange

import config


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


class ChannelInventory:
    """
    Responsável por obter os metadados dos vídeos do canal sem efetuar o download dos ficheiros multimédia,
    filtrar por data ou intervalo, ordenar em ordem cronológica crescente e exportar para Markdown (.md),
    JSON (.json) e CSV (.csv).
    """

    def __init__(
        self,
        cookie_browser: Optional[str] = None,
        logger: Optional[Any] = None,
    ):
        self.cookie_browser = cookie_browser
        self.logger = logger

    def _get_ydl_options(self, date_range: Optional[DateRange] = None) -> dict:
        opts: Dict[str, Any] = {
            "skip_download": True,
            "noplaylist": True,
            "ignoreerrors": True,
            "quiet": True,
            "no_warnings": True,
            "js_runtimes": (
                {"node": {"path": "/home/linuxbrew/.linuxbrew/bin/node"}}
                if Path("/home/linuxbrew/.linuxbrew/bin/node").exists()
                else {"deno": {}, "node": {}, "quickjs": {}, "bun": {}}
            ),
            "remote_components": ["ejs:github"],
            "sleep_interval_requests": 1,
        }

        if self.cookie_browser:
            opts["cookiesfrombrowser"] = (self.cookie_browser,)

        if date_range is not None:
            opts["daterange"] = date_range

        if self.logger:
            opts["logger"] = self.logger

        return opts

    def load_channel_videos(
        self,
        channel_url: str,
        date_range: Optional[DateRange] = None,
        progress_callback: Optional[Callable[[int, Optional[int], str], None]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Extrai a lista de vídeos do canal através do yt-dlp sem descarregar os fluxos de vídeo.
        Retorna a lista de vídeos já ordenada em ordem cronológica crescente.
        """
        normalized_url = config.normalize_channel_url(channel_url)
        opts = self._get_ydl_options(date_range=date_range)

        videos: List[Dict[str, Any]] = []

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(normalized_url, download=False)
            if not info:
                return []

            raw_entries = info.get("entries") or []
            entries_list = list(raw_entries)
            total = len(entries_list)
            count = 0

            for entry in entries_list:
                count += 1
                if not entry:
                    continue

                upload_date = entry.get("upload_date")
                if not upload_date and entry.get("timestamp"):
                    upload_date = datetime.fromtimestamp(entry["timestamp"]).strftime(
                        "%Y%m%d"
                    )

                if not upload_date:
                    continue

                video_id = entry.get("id") or ""
                title = entry.get("title") or "Sem título"
                duration = entry.get("duration")
                url = entry.get("webpage_url") or f"https://www.youtube.com/watch?v={video_id}"

                month = f"{upload_date[:4]}-{upload_date[4:6]}"
                upload_date_formatted = (
                    f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
                )

                videos.append(
                    {
                        "id": video_id,
                        "title": title,
                        "upload_date": upload_date,
                        "upload_date_formatted": upload_date_formatted,
                        "month": month,
                        "url": url,
                        "duration": duration,
                        "duration_formatted": format_duration(duration),
                        "view_count": entry.get("view_count"),
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
            lines.append("| # | Data | Título | Duração | Link |\n")
            lines.append("|:---:|:---:|---|:---:|---|\n")

            for v in vids:
                clean_title = v["title"].replace("|", "\\|")
                lines.append(
                    f"| {global_idx} | {v['upload_date_formatted']} | {clean_title} | "
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
