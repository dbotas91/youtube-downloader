   youtube-downloader
 ├╴  README.md
 ├╴  TECHNICAL.md
 ├╴  config.py
 ├╴  downloader.py
 ├╴  main.py
 ├╴  requirements.txt
 ├╴  run.sh
 └╴  ui.py

Depois de ver o conteúdo de config.py, ui.py, downloader.py e main.py, eu implementaria isto de forma relativamente simples sem mexer demasiado na arquitetura existente.

1. Alterações ao config.py

Adicionar no final:

def parse_month_range(start_month: str, end_month: str) -> tuple[str, str]:
    """
    Converte dois meses para uma data inicial e final.

    Ex:
        2024-09 -> 20240901
        2024-12 -> 20241231
    """

    start_date, _, _ = parse_month(start_month)
    _, end_date, _ = parse_month(end_month)

    if start_date > end_date:
        raise ValueError(
            "A data inicial não pode ser superior à data final."
        )

    return start_date, end_date

2. Criar novo ficheiro inventory.py

Novo ficheiro completo:

import csv
import json
from collections import defaultdict
from pathlib import Path

import yt_dlp

class ChannelInventory:

    def __init__(self, cookie_browser=None):
        self.cookie_browser = cookie_browser

    def load_channel_videos(self, channel_url: str):

        opts = {
            "extract_flat": True,
            "quiet": True,
            "ignoreerrors": True,
        }

        if self.cookie_browser:
            opts["cookiesfrombrowser"] = (self.cookie_browser,)

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(
                channel_url,
                download=False,
            )

        videos = []

        for entry in info.get("entries", []):

            upload_date = entry.get("upload_date")
            if not upload_date:
                continue

            videos.append(
                {
                    "id": entry.get("id"),
                    "title": entry.get("title"),
                    "upload_date": upload_date,
                    "month": f"{upload_date[:4]}-{upload_date[4:6]}",
                    "url": f"https://www.youtube.com/watch?v={entry.get('id')}",
                }
            )

        videos.sort(key=lambda v: v["upload_date"])

        return videos

    def filter_month(self, videos, month_label):

        return [
            v
            for v in videos
            if v["month"] == month_label
        ]

    def filter_range(
        self,
        videos,
        start_month,
        end_month,
    ):

        return [
            v
            for v in videos
            if start_month <= v["month"] <= end_month
        ]

    def group_by_month(self, videos):

        grouped = defaultdict(list)

        for video in videos:
            grouped[video["month"]].append(video)

        return dict(sorted(grouped.items()))

    def export_json(self, grouped, output_file):

        with open(
            output_file,
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                grouped,
                f,
                ensure_ascii=False,
                indent=2,
            )

    def export_csv(self, grouped, output_file):

        with open(
            output_file,
            "w",
            newline="",
            encoding="utf-8",
        ) as f:

            writer = csv.writer(f)

            writer.writerow(
                [
                    "month",
                    "upload_date",
                    "title",
                    "url",
                ]
            )

            for month in grouped:
                for video in groupedwriter.writerow(
                        [
                            month,
                            video["upload_date"],
                            video["title"],
                            video["url"],
                        ]
                    )

    def export_markdown(self, grouped, output_file):

        lines = ["# Inventário do Canal\n"]

        for month in grouped:

            lines.append(f"\n## {month}\n")

            for idx, video in enumerate(
                grouped[month],
                start=1,
            ):

                lines.append(
                    f"{idx}. {video['title']}\n"
                )

                lines.append(
                    f"   - Data: {video['upload_date']}\n"
                )

                lines.append(
                    f"   - URL: {video['url']}\n"
                )

        Path(output_file).write_text(
            "".join(lines),
            encoding="utf-8",
        )

3. Alterações ao ui.py

Adicionar ao menu:

table.add_row(
    "6",
    "Listar Mês",
    "Exportar vídeos de um mês específico"
)

table.add_row(
    "7",
    "Listar Intervalo",
    "Exportar vídeos entre dois meses"
)

table.add_row(
    "8",
    "Listar Todos",
    "Exportar todos os vídeos agrupados"
)

e:

choices=[
    "1","2","3","4","5",
    "6","7","8"
]

Adicionar:

def prompt_export_format():

    return Prompt.ask(
        "[yellow]Formato de exportação[/yellow]",
        choices=["json", "csv", "md"],
        default="json",
    )

Adicionar:

def prompt_month_range():

    console.print(
        "\n[bold]Intervalo de Meses[/bold]"
    )

    start_month = Prompt.ask(
        "[yellow]Mês inicial[/yellow]"
    )

    end_month = Prompt.ask(
        "[yellow]Mês final[/yellow]"
    )

    return (
        start_month,
        end_month,
    )

4. Alterações ao main.py

Adicionar import:

from inventory import ChannelInventory

Depois dos modos atuais:

elif mode == "6":

    mode_name = "Listagem por Mês"

    target_url = ui.prompt_channel_url()

    month_input = Prompt.ask(
        "Mês (AAAA-MM)"
    )

    export_format = ui.prompt_export_format()

    inventory_mode = "month"

elif mode == "7":

    mode_name = "Listagem por Intervalo"

    target_url = ui.prompt_channel_url()

    start_month, end_month = (
        ui.prompt_month_range()
    )

    export_format = ui.prompt_export_format()

    inventory_mode = "range"

elif mode == "8":

    mode_name = "Listagem Completa"

    target_url = ui.prompt_channel_url()

    export_format = ui.prompt_export_format()

    inventory_mode = "all"

Antes da criação do downloader:

is_inventory = mode in ["6", "7", "8"]

Depois da confirmação:

if is_inventory:

    inventory = ChannelInventory(
        cookie_browser=browser_cookies
    )

    videos = inventory.load_channel_videos(
        target_url
    )

    if mode == "6":

        videos = inventory.filter_month(
            videos,
            month_input,
        )

    elif mode == "7":

        videos = inventory.filter_range(
            videos,
            start_month,
            end_month,
        )

    grouped = inventory.group_by_month(
        videos
    )

    output_file = (
        dest_dir
        / f"videos_export.{export_format}"
    )

    if export_format == "json":
        inventory.export_json(
            grouped,
            output_file,
        )

    elif export_format == "csv":
        inventory.export_csv(
            grouped,
            output_file,
        )

    else:
        inventory.export_markdown(
            grouped,
            output_file,
        )

    console.print(
        f"\n[green]✓ Exportado:[/green] "
        f"{output_file}"
    )

    return

Uma melhoria que recomendo

Em vez de exportar sempre:

videos_export.json

gera automaticamente:

videos_2024-11.json

ou

videos_2024-09_to_2024-12.json

ou

videos_all.json

Fica muito mais limpo para manter histórico de exportações.

Além disso, para canais grandes (500+ vídeos), eu adicionaria também no JSON:

{
  "generated_at": "...",
  "total_videos": 534,
  "months": {
    ...
  }
}

porque vais agradecer essa informação quando exportares novamente daqui a alguns anos.
