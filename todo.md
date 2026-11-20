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

----

inventory.py:

from collections import defaultdict
from pathlib import Path
import csv
import json

import yt_dlp

class ChannelInventory:

    def __init__(self, cookie_browser=None):
        self.cookie_browser = cookie_browser

    def _get_ydl_options(self):

        opts = {
            "quiet": True,
            "ignoreerrors": True,
            "extract_flat": True,
        }

        if self.cookie_browser:
            opts["cookiesfrombrowser"] = (
                self.cookie_browser,
            )

        return opts

    def _load_section(
        self,
        section_url: str,
        content_type: str,
    ):

        videos = []

        with yt_dlp.YoutubeDL(
            self._get_ydl_options()
        ) as ydl:

            playlist = ydl.extract_info(
                section_url,
                download=False,
            )

            entries = (
                playlist.get("entries", [])
                if playlist
                else []
            )

            for entry in entries:

                if not entry:
                    continue

                video_id = entry.get("id")

                if not video_id:
                    continue

                try:

                    video_url = (
                        f"https://www.youtube.com/watch?v={video_id}"
                    )

                    video_info = ydl.extract_info(
                        video_url,
                        download=False,
                    )

                    upload_date = video_info.get(
                        "upload_date"
                    )

                    if not upload_date:
                        continue

                    videos.append(
                        {
                            "id": video_id,
                            "type": content_type,
                            "title": video_info.get(
                                "title",
                                "Sem título",
                            ),
                            "upload_date": upload_date,
                            "month": (
                                f"{upload_date[:4]}-"
                                f"{upload_date[4:6]}"
                            ),
                            "url": video_url,
                        }
                    )

                except Exception:
                    continue

        return videos

    def load_channel_content(
        self,
        channel_url: str,
    ):

        channel_url = channel_url.rstrip("/")

        videos_url = (
            channel_url
            if channel_url.endswith("/videos")
            else f"{channel_url}/videos"
        )

        streams_url = (
            channel_url.replace(
                "/videos",
                "/streams",
            )
            if channel_url.endswith("/videos")
            else f"{channel_url}/streams"
        )

        items = []

        items.extend(
            self._load_section(
                videos_url,
                "video",
            )
        )

        items.extend(
            self._load_section(
                streams_url,
                "stream",
            )
        )

        items.sort(
            key=lambda x: x["upload_date"]
        )

        return items

    def filter_month(
        self,
        items,
        month_label,
    ):

        return [
            item
            for item in items
            if item["month"] == month_label
        ]

    def filter_range(
        self,
        items,
        start_month,
        end_month,
    ):

        return [
            item
            for item in items
            if start_month
            <= item["month"]
            <= end_month
        ]

    def group_by_month(
        self,
        items,
    ):

        grouped = defaultdict(list)

        for item in items:

            grouped[
                item["month"]
            ].append(item)

        return dict(
            sorted(grouped.items())
        )

    def export_json(
        self,
        grouped,
        output_file,
    ):

        payload = {
            "total_entries": sum(
                len(v)
                for v in grouped.values()
            ),
            "months": grouped,
        }

        with open(
            output_file,
            "w",
            encoding="utf-8",
        ) as fh:

            json.dump(
                payload,
                fh,
                ensure_ascii=False,
                indent=2,
            )

    def export_csv(
        self,
        grouped,
        output_file,
    ):

        with open(
            output_file,
            "w",
            newline="",
            encoding="utf-8",
        ) as fh:

            writer = csv.writer(fh)

            writer.writerow(
                [
                    "month",
                    "type",
                    "upload_date",
                    "title",
                    "url",
                ]
            )

            for month, items in grouped.items():

                for item in items:

                    writer.writerow(
                        [
                            month,
                            item["type"],
                            item["upload_date"],
                            item["title"],
                            item["url"],
                        ]
                    )

    def export_markdown(
        self,
        grouped,
        output_file,
    ):

        lines = [
            "# Inventário do Canal\n"
        ]

        total = sum(
            len(v)
            for v in grouped.values()
        )

        lines.append(
            f"\nTotal de entradas: {total}\n"
        )

        for month, items in grouped.items():

            lines.append(
                f"\n## {month}\n"
            )

            for idx, item in enumerate(
                items,
                start=1,
            ):

                lines.append(
                    f"{idx}. {item['title']}\n"
                )

                lines.append(
                    f"   - Tipo: {item['type']}\n"
                )

                lines.append(
                    f"   - Data: {item['upload_date']}\n"
                )

                lines.append(
                    f"   - URL: {item['url']}\n"
                )

        Path(output_file).write_text(
            "".join(lines),
            encoding="utf-8",
        )

----

main.py:

import sys

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

import ui
from downloader import YouTubeDownloader
from inventory import ChannelInventory

console = Console()

def main():

    try:

        ui.show_welcome_banner()

        mode = ui.prompt_download_mode()

        #
        # INVENTÁRIO
        #
        if mode in ["6", "7", "8"]:

            if mode == "6":

                mode_name = "Inventário de um Mês"

                target_url = ui.prompt_channel_url()

                month_label = (
                    ui.prompt_inventory_month()
                )

                export_format = (
                    ui.prompt_export_format()
                )

            elif mode == "7":

                mode_name = (
                    "Inventário por Intervalo"
                )

                target_url = ui.prompt_channel_url()

                (
                    start_month,
                    end_month,
                ) = ui.prompt_inventory_range()

                export_format = (
                    ui.prompt_export_format()
                )

            else:

                mode_name = (
                    "Inventário Completo"
                )

                target_url = ui.prompt_channel_url()

                export_format = (
                    ui.prompt_export_format()
                )

            dest_dir = (
                ui.prompt_destination_dir()
            )

            browser_cookies = (
                ui.prompt_cookies()
            )

            ui.show_summary(
                mode_name=mode_name,
                target=target_url,
                dest_dir=dest_dir,
                filter_label="Inventário",
                browser_cookies=browser_cookies,
            )

            if not Confirm.ask(
                "[yellow]Iniciar exportação agora?[/yellow]",
                default=True,
            ):
                console.print(
                    "[yellow]Operação cancelada pelo utilizador.[/yellow]"
                )
                sys.exit(0)

            console.print(
                "\n[bold green]📋 A gerar inventário...[/bold green]\n"
            )

            inventory = ChannelInventory(
                cookie_browser=browser_cookies
            )

            items = (
                inventory.load_channel_content(
                    target_url
                )
            )

            if mode == "6":

                items = (
                    inventory.filter_month(
                        items,
                        month_label,
                    )
                )

                filename = (
                    f"videos_{month_label}.{export_format}"
                )

            elif mode == "7":

                items = (
                    inventory.filter_range(
                        items,
                        start_month,
                        end_month,
                    )
                )

                filename = (
                    f"videos_{start_month}_to_{end_month}.{export_format}"
                )

            else:

                filename = (
                    f"videos_all.{export_format}"
                )

            grouped = (
                inventory.group_by_month(
                    items
                )
            )

            output_file = (
                dest_dir / filename
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

            total_entries = sum(
                len(v)
                for v in grouped.values()
            )

            console.print(
                "\n"
                + Panel(
                    (
                        "[bold green]✔ Inventário gerado com sucesso![/bold green]\n\n"
                        f"Ficheiro: [cyan]{output_file}[/cyan]\n"
                        f"Entradas: [yellow]{total_entries}[/yellow]\n"
                        f"Meses: [yellow]{len(grouped)}[/yellow]"
                    ),
                    border_style="green",
                )
            )

            return

        #
        # DOWNLOADS
        #

        date_range = None
        filter_label = "Nenhum (Todos os vídeos)"
        is_single_video = False

        if mode == "1":

            mode_name = "Canal Completo (Tudo)"
            target_url = ui.prompt_channel_url()

        elif mode == "2":

            mode_name = "Vídeo Individual"
            target_url = ui.prompt_video_url()

            filter_label = (
                "N/A (Vídeo específico)"
            )

            is_single_video = True

        elif mode == "3":

            mode_name = "Filtrar por Ano"

            target_url = (
                ui.prompt_channel_url()
            )

            (
                date_range,
                filter_label,
            ) = ui.prompt_filter_year()

        elif mode == "4":

            mode_name = "Filtrar por Mês"

            target_url = (
                ui.prompt_channel_url()
            )

            (
                date_range,
                filter_label,
            ) = ui.prompt_filter_month()

        elif mode == "5":

            mode_name = (
                "Filtrar por Dia Específico"
            )

            target_url = (
                ui.prompt_channel_url()
            )

            (
                date_range,
                filter_label,
            ) = ui.prompt_filter_day()

        else:

            console.print(
                "[red]Opção inválida![/red]"
            )

            sys.exit(1)

        dest_dir = (
            ui.prompt_destination_dir()
        )

        browser_cookies = (
            ui.prompt_cookies()
        )

        ui.show_summary(
            mode_name=mode_name,
            target=target_url,
            dest_dir=dest_dir,
            filter_label=filter_label,
            browser_cookies=browser_cookies,
        )

        if not Confirm.ask(
            "[yellow]Iniciar a transferência agora?[/yellow]",
            default=True,
        ):

            console.print(
                "[yellow]Operação cancelada pelo utilizador.[/yellow]"
            )

            sys.exit(0)

        console.print(
            "\n[bold green]🚀 A iniciar motor de transferência...[/bold green]\n"
        )

        ydl_logger = (
            ui.RichYDLLogger(console)
        )

        downloader = (
            YouTubeDownloader(
                destination_dir=dest_dir,
                progress_callback=ui.print_progress_hook,
                cookie_browser=browser_cookies,
                date_range=date_range,
                logger=ydl_logger,
            )
        )

        if is_single_video:

            downloader.download_single_video(
                target_url
            )

        else:

            downloader.download_channel(
                target_url
            )

        console.print(
            "\n\n"
            + Panel(
                (
                    "[bold green]✔ Processo concluído com sucesso![/bold green]\n"
                    f"Ficheiros organizados em subpastas AAAA-MM dentro de: "
                    f"[cyan]{dest_dir}[/cyan]"
                ),
                border_style="green",
            )
        )

    except KeyboardInterrupt:

        console.print(
            "\n\n[red]Processo interrompido pelo utilizador.[/red]"
        )

        sys.exit(1)

    except Exception as e:

        console.print(
            f"\n\n[red]Ocorreu um erro durante a execução:[/red] {e}"
        )

        sys.exit(1)

if __name__ == "__main__":
    main()

----

ui.py:
Como o ui.py é grande e já tens um ficheiro funcional, a forma mais segura não é substituir o ficheiro inteiro. Basta fazer estas alterações.

1. Atualizar o menu principal

Na função:

def prompt_download_mode() -> str:

substitui:

table.add_row("1", "Canal Completo", "Descarrega todos os vídeos do canal (Tudo)")
table.add_row("2", "Vídeo Individual", "Descarrega um único vídeo por link ou ID")
table.add_row("3", "Filtrar por Ano", "Descarrega apenas os vídeos de um ano (ex: 2024)")
table.add_row("4", "Filtrar por Mês", "Descarrega os vídeos de um mês (ex: 2024-11 ou 11/2024)")
table.add_row("5", "Filtrar por Dia", "Descarrega os vídeos de um dia exato (ex: 19/11/2024)")

por:

table.add_row("1", "Canal Completo", "Descarrega todos os vídeos do canal")
table.add_row("2", "Vídeo Individual", "Descarrega um vídeo por link ou ID")
table.add_row("3", "Filtrar por Ano", "Descarrega vídeos de um ano")
table.add_row("4", "Filtrar por Mês", "Descarrega vídeos de um mês")
table.add_row("5", "Filtrar por Dia", "Descarrega vídeos de um dia")
table.add_row("6", "Inventário Mês", "Lista vídeos e streams de um mês")
table.add_row("7", "Inventário Intervalo", "Lista vídeos e streams de um período")
table.add_row("8", "Inventário Completo", "Lista todos os vídeos e streams")

e substituir:

choices=["1", "2", "3", "4", "5"]

por:

choices=[
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
]

1. Corrigir o erro da função show_summary

Substitui:

resumo = (
    ...
    f"[bold cyan]Autenticação:[/bold cyan] {
        'Navegador ' + browser_cookies
        if browser_cookies
        else 'Pública (Sem login)'
    }"
)

por:

auth_text = (
    f"Navegador {browser_cookies}"
    if browser_cookies
    else "Pública (Sem login)"
)

resumo = (
    f"[bold cyan]Modo:[/bold cyan] {mode_name}\n"
    f"[bold cyan]Alvo:[/bold cyan] {target}\n"
    f"[bold cyan]Filtro de Data:[/bold cyan] {filter_label}\n"
    f"[bold cyan]Pasta Base:[/bold cyan] {dest_dir}\n"
    f"[bold cyan]Organização:[/bold cyan] Subpastas [bold yellow]AAAA-MM[/bold yellow] automáticas\n"
    f"[bold cyan]Vídeos Repetidos:[/bold cyan] Ignorados automaticamente (histórico ativo)\n"
    f"[bold cyan]Autenticação:[/bold cyan] {auth_text}"
)

1. Adicionar novas funções

Adicionar no fim do ficheiro, antes da classe:

def prompt_export_format() -> str:

    console.print(
        "\n[bold]Formato de Exportação[/bold]"
    )

    return Prompt.ask(
        "[yellow]Formato pretendido[/yellow]",
        choices=[
            "json",
            "csv",
            "md",
        ],
        default="json",
    )

Adicionar:

def prompt_inventory_month() -> str:

    console.print(
        "\n[bold]Inventário por Mês[/bold]"
    )

    console.print(
        "[dim]Formato: AAAA-MM (ex: 2024-11)[/dim]"
    )

    while True:

        value = Prompt.ask(
            "[yellow]Mês pretendido[/yellow]"
        )

        try:

            _, _, label = (
                config.parse_month(value)
            )

            return label

        except ValueError as e:

            console.print(
                f"[red]{e}[/red]"
            )

Adicionar:

def prompt_inventory_range():

    console.print(
        "\n[bold]Inventário por Intervalo[/bold]"
    )

    while True:

        start = Prompt.ask(
            "[yellow]Mês inicial[/yellow]"
        )

        end = Prompt.ask(
            "[yellow]Mês final[/yellow]"
        )

        try:

            _, _, start_label = (
                config.parse_month(start)
            )

            _, _, end_label = (
                config.parse_month(end)
            )

            if start_label > end_label:
                raise ValueError(
                    "O mês inicial não pode ser superior ao mês final."
                )

            return (
                start_label,
                end_label,
            )

        except ValueError as e:

            console.print(
                f"[red]{e}[/red]"
            )

4. Corrigir qualquer ->

Se ainda existir:

-&gt;

substituir por:

->

1. Corrigir qualquer <

Se ainda existir:

&lt;

substituir por:

<

Depois destas alterações, o ui.py fica compatível com o novo main.py e com o novo inventory.py`.

O ui.py é demasiado grande para eu o regenerar integralmente com confiança a partir dos fragmentos que chegaram pela conversa. Mesmo agora, o conteúdo continua truncado e parcialmente transformado pelo editor (entidades HTML, perda de quebras de linha e possíveis cortes).

Além disso, para te entregar um ficheiro completo eu teria de reconstruir manualmente centenas de linhas e isso introduziria facilmente divergências do teu código real.

O que já te entreguei e que é seguro aplicar é:

O novo inventory.py completo.
O novo main.py completo.
As alterações exatas a fazer em ui.py:
novas opções 6, 7 e 8;
correção da f-string em show_summary;
prompt_export_format();
prompt_inventory_month();
prompt_inventory_range().
A alteração ao config.py para suportar intervalos de meses.

Se quiseres realmente o ficheiro ui.py completo pronto para substituir, preciso do ficheiro real aberto através do anexo ui.py e da sua leitura integral (não do conteúdo colado na conversa). Neste momento só tenho uma versão compactada/truncada do ficheiro e não consigo garantir uma reconstrução 100% correta.

----

config.py:
import os
import calendar
from datetime import datetime
from pathlib import Path

# Diretórios base

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DOWNLOAD_DIR = Path.home() / "Videos" / "YouTube_Backups"
ARCHIVE_FILE = BASE_DIR / "downloaded_archive.txt"

# Estrutura de saída dos ficheiros

# Cria a pasta AAAA-MM automaticamente com base na data de upload do vídeo

# Exemplo: /pasta_destino/2026-11/Titulo_do_Video [id].mp4

OUTPUT_TEMPLATE = "%(upload_date>%Y-%m|sem-data)s/%(title)s [%(id)s].%(ext)s"

def normalize_channel_url(channel_input: str) -> str:
    """
    Garante que o link do canal aponta para uma secção válida do canal.
    """

    url = channel_input.strip()

    # Se o utilizador apenas digitou o handle
    if url.startswith("@"):
        url = f"https://www.youtube.com/{url}"

    elif not url.startswith("http://") and not url.startswith("https://"):

        if "/" not in url:
            url = f"https://www.youtube.com/@{url}"
        else:
            url = f"https://www.youtube.com/{url}"

    url = url.rstrip("/")

    return url

def normalize_video_url(video_input: str) -> str:
    """
    Normaliza o link ou ID de um vídeo específico.
    """

    url = video_input.strip()

    if not url.startswith("http://") and not url.startswith("https://"):
        url = f"https://www.youtube.com/watch?v={url}"

    return url

def parse_year(year_str: str) -> tuple[str, str, str]:
    """
    Valida e converte um ano no formato AAAA.

    Retorna:
        (data_inicio_AAAAMMDD,
         data_fim_AAAAMMDD,
         rotulo)
    """

    val = year_str.strip()

    if val.isdigit() and len(val) == 4:

        year = int(val)

        if 2005 <= year <= 2035:

            return (
                f"{year:04d}0101",
                f"{year:04d}1231",
                str(year),
            )

    raise ValueError(
        "Ano inválido. Introduza um ano com 4 dígitos (ex: 2024)."
    )

def parse_month(month_str: str) -> tuple[str, str, str]:
    """
    Valida e converte um mês nos formatos:

        AAAA-MM
        MM/AAAA

    Retorna:

        (
            data_inicio_AAAAMMDD,
            data_fim_AAAAMMDD,
            rotulo_AAAA_MM
        )
    """

    val = month_str.strip().replace("/", "-")

    parts = val.split("-")

    if len(parts) == 2:

        p1 = parts[0].strip()
        p2 = parts[1].strip()

        if len(p1) == 4 and p1.isdigit() and p2.isdigit():

            year = int(p1)
            month = int(p2)

        elif len(p2) == 4 and p2.isdigit() and p1.isdigit():

            year = int(p2)
            month = int(p1)

        else:

            raise ValueError(
                "Formato inválido."
            )

        if 1 <= month <= 12 and 2005 <= year <= 2035:

            last_day = calendar.monthrange(
                year,
                month,
            )[1]

            return (
                f"{year:04d}{month:02d}01",
                f"{year:04d}{month:02d}{last_day:02d}",
                f"{year:04d}-{month:02d}",
            )

    raise ValueError(
        "Formato de mês inválido. Use AAAA-MM (ex: 2024-11) ou MM/AAAA (ex: 11/2024)."
    )

def parse_month_range(
    start_month: str,
    end_month: str,
) -> tuple[str, str]:
    """
    Valida um intervalo de meses.

    Exemplo:

        2024-09
        2024-12

    Retorna:

        (
            data_inicio_AAAAMMDD,
            data_fim_AAAAMMDD,
        )
    """

    start_date, _, _ = parse_month(
        start_month
    )

    _, end_date, _ = parse_month(
        end_month
    )

    if start_date > end_date:

        raise ValueError(
            "O mês inicial não pode ser superior ao mês final."
        )

    return (
        start_date,
        end_date,
    )

def parse_day(day_str: str) -> tuple[str, str]:
    """
    Valida e converte um dia.

    Formatos aceites:

        AAAA-MM-DD
        DD/MM/AAAA
        DD-MM-AAAA
        AAAA/MM/DD
        AAAAMMDD

    Retorna:

        (
            data_AAAAMMDD,
            rotulo_legivel
        )
    """

    val = day_str.strip()

    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%Y%m%d",
    ]

    for fmt in formats:

        try:

            dt = datetime.strptime(
                val,
                fmt,
            )

            if 2005 <= dt.year <= 2035:

                return (
                    dt.strftime("%Y%m%d"),
                    dt.strftime("%d/%m/%Y"),
                )

        except ValueError:
            continue

    raise ValueError(
        "Formato de dia inválido. Use AAAA-MM-DD (ex: 2024-11-19) ou DD/MM/AAAA (ex: 19/11/2024)."
    )
