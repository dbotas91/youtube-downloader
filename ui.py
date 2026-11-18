from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
import config

console = Console()

def show_welcome_banner():
    banner_text = (
        "[bold cyan]YouTube Channel Backup - Downloader[/bold cyan]\n"
        "[dim]Descarrega todos os vídeos do teu canal organizados por [bold yellow]AAAA-MM[/bold yellow][/dim]"
    )
    console.print(Panel(banner_text, border_style="cyan", expand=False))

def prompt_channel_url() -> str:
    console.print("\n[bold]1. Canal do YouTube[/bold]")
    console.print("[dim]Exemplo: [cyan]@OSeuCanal[/cyan] ou [cyan]https://www.youtube.com/@OSeuCanal[/cyan][/dim]")
    
    while True:
        canal = Prompt.ask("[yellow]Indica o identificador ou link do teu canal[/yellow]")
        if canal.strip():
            return canal.strip()
        console.print("[red]O canal não pode estar vazio![/red]")

def prompt_destination_dir() -> Path:
    console.print("\n[bold]2. Pasta de Destino[/bold]")
    
    # Deteta opções convenientes
    opcoes = []
    
    # Opção Windows (WSL)
    windows_videos = Path("/mnt/c/Users/dapb/Videos/YouTube_Backups")
    if Path("/mnt/c/Users/dapb/Videos").exists():
        opcoes.append(("Windows: Pasta 'Vídeos' do utilizador", windows_videos))
        
    # Opção Linux interna
    linux_videos = Path.home() / "Videos" / "YouTube_Backups"
    opcoes.append(("Linux/WSL: ~/Videos/YouTube_Backups", linux_videos))

    table = Table(title="Opções de Pasta Base", show_header=True, header_style="bold magenta")
    table.add_column("Opção", style="cyan", width=6)
    table.add_column("Descrição", style="white")
    table.add_column("Caminho", style="dim")

    for i, (desc, path) in enumerate(opcoes, start=1):
        table.add_row(str(i), desc, str(path))
    table.add_row(str(len(opcoes) + 1), "Outro caminho personalizado", "Escrever manualmente...")

    console.print(table)

    escolha = Prompt.ask(
        "[yellow]Escolhe o número da pasta desejada[/yellow]",
        choices=[str(i) for i in range(1, len(opcoes) + 2)],
        default="1"
    )

    escolha_idx = int(escolha) - 1
    if escolha_idx < len(opcoes):
        destino = opcoes[escolha_idx][1]
    else:
        caminho_custom = Prompt.ask("[yellow]Introduz o caminho absoluto da pasta[/yellow]")
        destino = Path(caminho_custom).expanduser().resolve()

    destino.mkdir(parents=True, exist_ok=True)
    console.print(f"[green]✓ Destino configurado:[/green] [bold]{destino}[/bold]")
    console.print("[dim]Dentro desta pasta serão criadas as subpastas no formato AAAA-MM (ex: 2026-11/)[/dim]")
    return destino

def prompt_cookies() -> Optional[str]:
    console.print("\n[bold]3. Vídeos Privados ou Restritos[/bold]")
    tem_privados = Confirm.ask(
        "O canal contém vídeos [bold]privados[/bold] que necessitam de login?",
        default=False
    )
    
    if not tem_privados:
        return None
        
    browsers = ["chrome", "firefox", "edge", "brave", "chromium"]
    console.print("[dim]A aplicação pode importar a tua sessão diretamente de um navegador:[/dim]")
    browser = Prompt.ask(
        "[yellow]De qual navegador queres usar a sessão?[/yellow]",
        choices=browsers,
        default="chrome"
    )
    return browser

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
        
        # Exibe progresso limpo em tempo real
        console.print(
            f"[cyan]A descarregar:[/cyan] [bold]{filename[:45]}[/bold] | "
            f"[green]{percent}[/green] a [yellow]{speed}[/yellow] (Restam: {eta})",
            end="\r"
        )
    elif status == "finished":
        console.print("\n[green]✓ Download concluído! A verificar e converter formato com FFmpeg...[/green]")
