import sys
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

import ui
from downloader import YouTubeChannelDownloader

console = Console()


def main():
    try:
        ui.show_welcome_banner()

        # 1. Recolha das informações
        channel_input = ui.prompt_channel_url()
        dest_dir = ui.prompt_destination_dir()
        browser_cookies = ui.prompt_cookies()

        # 2. Confirmação do utilizador
        console.print("\n[bold]4. Resumo da Operação[/bold]")
        resumo = (
            f"[bold cyan]Canal:[/bold cyan] {channel_input}\n"
            f"[bold cyan]Pasta Base:[/bold cyan] {dest_dir}\n"
            f"[bold cyan]Organização:[/bold cyan] Subpastas [bold yellow]AAAA-MM[/bold yellow] automáticas\n"
            f"[bold cyan]Vídeos Repetidos:[/bold cyan] Ignorados automaticamente (histórico ativo)\n"
            f"[bold cyan]Autenticação:[/bold cyan] {
                'Navegador ' + browser_cookies
                if browser_cookies
                else 'Pública (Sem login)'
            }"
        )
        console.print(Panel(resumo, title="Configuração Final", border_style="green"))

        if not Confirm.ask(
            "[yellow]Iniciar a transferência agora?[/yellow]", default=True
        ):
            console.print("[yellow]Operação cancelada pelo utilizador.[/yellow]")
            sys.exit(0)

        # 3. Execução
        console.print(
            "\n[bold green]🚀 A iniciar motor de transferência...[/bold green]\n"
        )

        downloader = YouTubeChannelDownloader(
            destination_dir=dest_dir,
            progress_callback=ui.print_progress_hook,
            cookie_browser=browser_cookies,
        )

        downloader.download_channel(channel_input)

        console.print(
            "\n\n"
            + Panel(
                "[bold green]✔ Todos os novos vídeos do canal foram processados com sucesso![/bold green]\n"
                f"Ficheiros organizados em: [cyan]{dest_dir}[/cyan]",
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
