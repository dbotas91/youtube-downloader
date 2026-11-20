import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

import config
import ui
from downloader import YouTubeDownloader
from inventory import ChannelInventory
from youtube_api import YouTubeAPIClient

console = Console()


def main():
    try:
        ui.show_welcome_banner()

        # 1. Escolha do modo de operação
        mode = ui.prompt_download_mode()

        date_range = None
        filter_label = "Nenhum (Todos os vídeos)"
        is_single_video = False
        is_inventory = mode in ["6", "7", "8"]
        export_format = None
        file_suffix = "export"
        start_lbl = ""
        end_lbl = ""

        if mode == "1":
            mode_name = "Canal Completo (Tudo)"
            target_url = ui.prompt_channel_url()
        elif mode == "2":
            mode_name = "Vídeo Individual"
            target_url = ui.prompt_video_url()
            filter_label = "N/A (Vídeo específico)"
            is_single_video = True
        elif mode == "3":
            mode_name = "Filtrar por Ano"
            target_url = ui.prompt_channel_url()
            date_range, filter_label = ui.prompt_filter_year()
        elif mode == "4":
            mode_name = "Filtrar por Mês"
            target_url = ui.prompt_channel_url()
            date_range, filter_label = ui.prompt_filter_month()
        elif mode == "5":
            mode_name = "Filtrar por Dia Específico"
            target_url = ui.prompt_channel_url()
            date_range, filter_label = ui.prompt_filter_day()
        elif mode == "6":
            mode_name = "Listar Mês Específico"
            target_url = ui.prompt_channel_url()
            date_range, filter_label = ui.prompt_filter_month()
            file_suffix = filter_label.replace("Mês ", "").strip()
            export_format = ui.prompt_export_format()
        elif mode == "7":
            mode_name = "Listar Intervalo de Meses"
            target_url = ui.prompt_channel_url()
            date_range, filter_label, start_lbl, end_lbl = ui.prompt_month_range()
            file_suffix = f"{start_lbl}_a_{end_lbl}"
            export_format = ui.prompt_export_format()
        elif mode == "8":
            mode_name = "Listar Todos Agrupados por Mês"
            target_url = ui.prompt_channel_url()
            filter_label = "Todos os vídeos do canal"
            file_suffix = "todos_por_mes"
            export_format = ui.prompt_export_format()
        else:
            console.print("[red]Opção inválida![/red]")
            sys.exit(1)

        # 2. Pasta de destino, autenticação e motor
        dest_dir = ui.prompt_destination_dir()

        api_key = None
        browser_cookies = None
        engine = "scraper"

        if is_single_video:
            browser_cookies = ui.prompt_cookies()
            engine = "cookies" if browser_cookies else "scraper"
        else:
            engine, api_key, browser_cookies = ui.prompt_connection_method(
                is_download=(not is_inventory),
                saved_key=config.get_api_key(),
            )

        # 3. Resumo da Operação e Confirmação
        ui.show_summary(
            mode_name=mode_name,
            target=target_url,
            dest_dir=dest_dir,
            filter_label=filter_label,
            browser_cookies=browser_cookies,
            is_inventory=is_inventory,
            export_format=export_format,
            use_api=(engine == "api"),
        )

        confirm_msg = (
            "[yellow]Iniciar a listagem e exportação do catálogo?[/yellow]"
            if is_inventory
            else "[yellow]Iniciar a transferência agora?[/yellow]"
        )

        if not Confirm.ask(confirm_msg, default=True):
            console.print("[yellow]Operação cancelada pelo utilizador.[/yellow]")
            sys.exit(0)

        # 4. Execução
        if is_inventory:
            if engine == "api":
                console.print(
                    "\n[bold green]⚡ A consultar a YouTube Data API v3 oficial (sem rate-limit)...[/bold green]\n"
                )
            else:
                console.print(
                    "\n[bold green]🔍 A recolher metadados e a indexar vídeos do canal...[/bold green]\n"
                )

            ydl_logger = ui.RichYDLLogger(console)
            inventory = ChannelInventory(
                api_key=api_key,
                cookie_browser=browser_cookies,
                logger=ydl_logger,
            )

            def progress_callback(count: int, total: int, title: str):
                total_str = f"/{total}" if total else ""
                pct_str = (
                    f" ({int((count / total) * 100)}%)"
                    if total and total > 0
                    else ""
                )
                console.print(
                    f"[cyan]A indexar [bold]#{count}{total_str}[/bold]{pct_str}:[/cyan] [dim]{title[:55]}[/dim]",
                    end="\r",
                )

            videos = inventory.load_channel_videos(
                channel_url=target_url,
                date_range=date_range,
                progress_callback=progress_callback,
            )
            console.print()

            # Refinar filtros por garantia de exatidão
            if mode == "6":
                month_target = filter_label.replace("Mês ", "").strip()
                videos = inventory.filter_month(videos, month_target)
            elif mode == "7":
                videos = inventory.filter_range(videos, start_lbl, end_lbl)

            grouped = inventory.group_by_month(videos)

            exported_files = inventory.export_inventory(
                grouped=grouped,
                dest_dir=dest_dir,
                channel_url=target_url,
                filter_desc=filter_label,
                file_suffix=file_suffix,
                export_format=export_format or "md",
            )

            ui.show_inventory_results(grouped, exported_files, filter_label)

        else:
            console.print(
                "\n[bold green]🚀 A iniciar motor de transferência...[/bold green]\n"
            )

            ydl_logger = ui.RichYDLLogger(console)

            downloader = YouTubeDownloader(
                destination_dir=dest_dir,
                progress_callback=ui.print_progress_hook,
                cookie_browser=browser_cookies,
                date_range=date_range,
                logger=ydl_logger,
            )

            if is_single_video:
                downloader.download_single_video(target_url)
            elif engine == "api":
                console.print(
                    "[bold green]⚡ A consultar a YouTube Data API v3 para listar os vídeos do canal (sem rate-limit)...[/bold green]\n"
                )
                client = YouTubeAPIClient(api_key)

                def download_api_progress(count: int, total: Optional[int], title: str):
                    total_str = f"/{total}" if total else ""
                    console.print(
                        f"[cyan]A indexar via API [bold]#{count}{total_str}[/bold]:[/cyan] [dim]{title[:55]}[/dim]",
                        end="\r",
                    )

                videos = client.fetch_videos(
                    channel_input=target_url,
                    date_range=date_range,
                    progress_callback=download_api_progress,
                )
                console.print()

                if not videos:
                    console.print(
                        f"\n[yellow]Nenhum vídeo encontrado para o período selecionado ({filter_label}).[/yellow]"
                    )
                else:
                    console.print(
                        f"\n[green]✔ Encontrados {len(videos)} vídeos via API v3. A iniciar transferência direta de MP4...[/green]\n"
                    )
                    video_urls = [v["url"] for v in videos]
                    downloader.download_videos_list(video_urls)
            else:
                downloader.download_channel(target_url)

            console.print()
            console.print(
                Panel(
                    "[bold green]✔ Processo concluído com sucesso![/bold green]\n"
                    f"Ficheiros organizados em subpastas AAAA-MM dentro de: [cyan]{dest_dir}[/cyan]",
                    border_style="green",
                )
            )

    except KeyboardInterrupt:
        console.print("\n\n[red]Processo interrompido pelo utilizador.[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n\n[red]Ocorreu um erro durante a execução:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
