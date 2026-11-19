import re
from pathlib import Path
from typing import Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from yt_dlp.utils import DateRange

import config

console = Console()


def show_welcome_banner():
    banner_text = (
        "[bold cyan]YouTube Channel Backup - Downloader[/bold cyan]\n"
        "[dim]Descarrega vídeos do teu canal (tudo, vídeo único, ou por dia/mês/ano)\n"
        "Organização automática em subpastas: [bold yellow]AAAA-MM[/bold yellow][/dim]"
    )
    console.print(Panel(banner_text, border_style="cyan", expand=False))


def prompt_download_mode() -> str:
    """
    Permite escolher o modo de descarregamento.
    """
    console.print("\n[bold]1. O que pretendes descarregar?[/bold]")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Opção", style="cyan", width=6)
    table.add_column("Modo", style="bold white", width=22)
    table.add_column("Descrição", style="dim")

    table.add_row("1", "Canal Completo", "Descarrega todos os vídeos do canal (Tudo)")
    table.add_row("2", "Vídeo Individual", "Descarrega um único vídeo por link ou ID")
    table.add_row("3", "Filtrar por Ano", "Descarrega apenas os vídeos de um ano (ex: 2024)")
    table.add_row("4", "Filtrar por Mês", "Descarrega os vídeos de um mês (ex: 2024-11 ou 11/2024)")
    table.add_row("5", "Filtrar por Dia", "Descarrega os vídeos de um dia exato (ex: 19/11/2024)")

    console.print(table)

    escolha = Prompt.ask(
        "[yellow]Escolhe o modo desejado[/yellow]",
        choices=["1", "2", "3", "4", "5"],
        default="1",
    )
    return escolha


def prompt_channel_url() -> str:
    console.print("\n[bold]2. Canal do YouTube[/bold]")
    console.print(
        "[dim]Exemplo: [cyan]@OSeuCanal[/cyan] ou [cyan]https://www.youtube.com/@OSeuCanal[/cyan][/dim]"
    )

    while True:
        canal = Prompt.ask("[yellow]Indica o identificador ou link do canal[/yellow]")
        if canal.strip():
            return canal.strip()
        console.print("[red]O canal não pode estar vazio![/red]")


def prompt_video_url() -> str:
    console.print("\n[bold]2. Vídeo do YouTube[/bold]")
    console.print(
        "[dim]Exemplo: [cyan]https://www.youtube.com/watch?v=XXXXX[/cyan] ou apenas o ID [cyan]XXXXX[/cyan][/dim]"
    )

    while True:
        video = Prompt.ask("[yellow]Indica o link ou ID do vídeo[/yellow]")
        if video.strip():
            return video.strip()
        console.print("[red]O vídeo não pode estar vazio![/red]")


def prompt_filter_year() -> Tuple[DateRange, str]:
    console.print("\n[bold]Filtro de Data: Ano[/bold]")
    while True:
        ano_input = Prompt.ask("[yellow]Indica o ano pretendido (ex: 2024)[/yellow]")
        try:
            start_date, end_date, label = config.parse_year(ano_input)
            dr = DateRange(start_date, end_date)
            return dr, f"Ano de {label}"
        except ValueError as e:
            console.print(f"[red]{e}[/red]")


def prompt_filter_month() -> Tuple[DateRange, str]:
    console.print("\n[bold]Filtro de Data: Mês[/bold]")
    console.print("[dim]Formatos aceites: AAAA-MM (ex: 2024-11) ou MM/AAAA (ex: 11/2024)[/dim]")
    while True:
        mes_input = Prompt.ask("[yellow]Indica o mês pretendido[/yellow]")
        try:
            start_date, end_date, label = config.parse_month(mes_input)
            dr = DateRange(start_date, end_date)
            return dr, f"Mês {label}"
        except ValueError as e:
            console.print(f"[red]{e}[/red]")


def prompt_filter_day() -> Tuple[DateRange, str]:
    console.print("\n[bold]Filtro de Data: Dia Específico[/bold]")
    console.print("[dim]Formatos aceites: AAAA-MM-DD (ex: 2024-11-19) ou DD/MM/AAAA (ex: 19/11/2024)[/dim]")
    while True:
        dia_input = Prompt.ask("[yellow]Indica o dia pretendido[/yellow]")
        try:
            day_str, label = config.parse_day(dia_input)
            dr = DateRange.day(day_str)
            return dr, f"Dia {label}"
        except ValueError as e:
            console.print(f"[red]{e}[/red]")


def prompt_destination_dir() -> Path:
    console.print("\n[bold]3. Pasta Base de Destino[/bold]")

    opcoes = []

    # Opção Windows (WSL)
    windows_videos = Path("/mnt/c/Users/dapb/Videos/YouTube_Backups")
    if Path("/mnt/c/Users/dapb/Videos").exists():
        opcoes.append(("Windows: Pasta 'Vídeos' do utilizador", windows_videos))

    # Opção Linux interna
    linux_videos = Path.home() / "Videos" / "YouTube_Backups"
    opcoes.append(("Linux/WSL: ~/Videos/YouTube_Backups", linux_videos))

    table = Table(
        title="Opções de Pasta Base",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Opção", style="cyan", width=6)
    table.add_column("Descrição", style="white")
    table.add_column("Caminho", style="dim")

    for i, (desc, path) in enumerate(opcoes, start=1):
        table.add_row(str(i), desc, str(path))
    table.add_row(
        str(len(opcoes) + 1), "Outro caminho personalizado", "Escrever manualmente..."
    )

    console.print(table)

    escolha = Prompt.ask(
        "[yellow]Escolhe o número da pasta desejada[/yellow]",
        choices=[str(i) for i in range(1, len(opcoes) + 2)],
        default="1",
    )

    escolha_idx = int(escolha) - 1
    if escolha_idx < len(opcoes):
        destino = opcoes[escolha_idx][1]
    else:
        caminho_custom = Prompt.ask(
            "[yellow]Introduz o caminho absoluto da pasta[/yellow]"
        )
        destino = Path(caminho_custom).expanduser().resolve()

    destino.mkdir(parents=True, exist_ok=True)
    console.print(f"[green]✓ Destino configurado:[/green] [bold]{destino}[/bold]")
    console.print(
        "[dim]Os vídeos serão organizados nesta pasta em subpastas com o formato AAAA-MM (ex: 2024-11/)[/dim]"
    )
    return destino


def prompt_cookies() -> Optional[str]:
    console.print("\n[bold]4. Vídeos Privados ou Restritos[/bold]")
    tem_privados = Confirm.ask(
        "O canal/vídeo contém itens [bold]privados[/bold] que necessitam de login?",
        default=False,
    )

    if not tem_privados:
        return None

    browsers = ["chrome", "firefox", "edge", "brave", "chromium"]
    console.print(
        "[dim]A aplicação pode importar a tua sessão diretamente de um navegador:[/dim]"
    )
    browser = Prompt.ask(
        "[yellow]De qual navegador queres usar a sessão?[/yellow]",
        choices=browsers,
        default="chrome",
    )
    return browser


def show_summary(
    mode_name: str,
    target: str,
    dest_dir: Path,
    filter_label: str,
    browser_cookies: Optional[str],
):
    console.print("\n[bold]5. Resumo da Operação[/bold]")
    resumo = (
        f"[bold cyan]Modo:[/bold cyan] {mode_name}\n"
        f"[bold cyan]Alvo:[/bold cyan] {target}\n"
        f"[bold cyan]Filtro de Data:[/bold cyan] {filter_label}\n"
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


def print_progress_hook(d: dict):
    """
    Hook chamado pelo yt-dlp em cada evento de transferência.
    """
    status = d.get("status")

    if status == "downloading":
        filename = Path(d.get("filename", "")).name
        percent = d.get("_percent_str", "0.0%").strip()
        speed = d.get("_speed_str", "N/A").strip()
        eta = d.get("_eta_str", "N/A").strip()

        console.print(
            f"[cyan]A descarregar:[/cyan] [bold]{filename[:40]}[/bold] | "
            f"[green]{percent}[/green] a [yellow]{speed}[/yellow] (Restam: {eta})",
            end="\r",
        )
    elif status == "finished":
        console.print(
            "\n[green]✓ Download concluído! A verificar e converter formato com FFmpeg...[/green]"
        )


class RichYDLLogger:
    """
    Logger personalizado para fornecer feedback limpo e elegante no terminal
    quando vídeos forem ignorados por filtros de data ou histórico.
    """

    def __init__(self, console_instance: Console):
        self.console = console_instance

    def debug(self, msg: str):
        if "upload date is not in range" in msg:
            self.console.print(
                "[dim yellow]⏭ Vídeo ignorado (data fora do período selecionado)[/dim yellow]"
            )
        elif "has already been recorded in the archive" in msg:
            match = re.search(r":\s*(.*?)\s*has already been recorded", msg)
            title = match.group(1) if match else "Vídeo"
            self.console.print(
                f"[dim]⏭ Já descarregado anteriormente: [italic]{title[:45]}[/italic][/dim]"
            )
        elif msg.startswith("[download] Destination:"):
            dest = Path(msg.replace("[download] Destination:", "").strip()).name
            self.console.print(f"\n[cyan]A preparar:[/cyan] [bold]{dest}[/bold]")

    def info(self, msg: str):
        pass

    def warning(self, msg: str):
        if "upload date is not in range" in msg:
            return
        if "No supported JavaScript runtime could be found" in msg:
            self.console.print(
                "[dim yellow]ℹ Nota: Nenhum motor JavaScript detetado (Node.js/Deno). A utilizar clientes alternativos.[/dim yellow]"
            )
            return
        self.console.print(f"[yellow]Aviso:[/yellow] {msg}")

    def error(self, msg: str):
        if "rate-limited by YouTube" in msg:
            self.console.print(
                "\n[bold red]⚠ Rate-limit do YouTube:[/bold red] [yellow]A tua sessão foi temporariamente limitada pelo YouTube (pode durar até 1 hora).[/yellow]\n"
                "[dim]A aplicação continuará automaticamente para o próximo vídeo com uma pausa.[/dim]\n"
            )
        elif "Video unavailable" in msg or "content isn't available" in msg:
            vid_id = msg.split(":")[0].strip() if ":" in msg else "desconhecido"
            self.console.print(
                f"[dim red]✗ Vídeo indisponível[/dim red] [dim]({vid_id})[/dim]"
            )
        else:
            self.console.print(f"[red]Erro:[/red] {msg}")
