import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

import ui
from downloader import YouTubeDownloader

console = Console()


def main():
    try:
        ui.show_welcome_banner()

        # 1. Escolha do modo de descarregamento
        mode = ui.prompt_download_mode()

        date_range = None
        filter_label = "Nenhum (Todos os vídeos)"
        is_single_video = False

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
        )

        if not Confirm.ask(
            "[yellow]Iniciar a transferência agora?[/yellow]", default=True
        ):
            console.print("[yellow]Operação cancelada pelo utilizador.[/yellow]")
            sys.exit(0)

        # 4. Execução
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
