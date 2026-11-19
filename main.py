import sys
from pathlib import Path

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

        # 2. Pasta de destino e autenticação
        dest_dir = ui.prompt_destination_dir()
        browser_cookies = ui.prompt_cookies()

        # 3. Resumo da Operação e Confirmação
        ui.show_summary(
            mode_name=mode_name,
            target=target_url,
            dest_dir=dest_dir,
            filter_label=filter_label,
            browser_cookies=browser_cookies,
            is_inventory=is_inventory,
            export_format=export_format,
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
            console.print(
                "\n[bold green]🔍 A recolher metadados e a indexar vídeos do canal...[/bold green]\n"
            )

            ydl_logger = ui.RichYDLLogger(console)
            inventory = ChannelInventory(
                cookie_browser=browser_cookies,
                logger=ydl_logger,
            )

            def progress_callback(count: int, title: str):
                console.print(
                    f"[cyan]A processar (#{count}):[/cyan] [dim]{title[:60]}[/dim]",
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
            else:
                downloader.download_channel(target_url)

            console.print(
                "\n\n"
                + Panel(
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
