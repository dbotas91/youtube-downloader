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
        "[bold cyan]YouTube Channel Backup & Catalog Tool[/bold cyan]\n"
        "[dim]Descarrega vídeos ou gera catálogos (.md / .json / .csv) por mês/ano em ordem crescente\n"
        "Organização automática de downloads em subpastas: [bold yellow]AAAA-MM[/bold yellow][/dim]"
    )
    console.print(Panel(banner_text, border_style="cyan", expand=False))

    if not config.is_ffmpeg_installed():
        if config.IS_WINDOWS:
            msg = "[bold yellow]⚠ Aviso: FFmpeg não foi detetado no PATH do Windows.[/bold yellow] [dim]Instalação rápida: winget install Gyan.FFmpeg[/dim]"
        else:
            msg = "[bold yellow]⚠ Aviso: FFmpeg não foi detetado no PATH.[/bold yellow] [dim]Instalação rápida: sudo apt install ffmpeg[/dim]"
        console.print(msg)


def prompt_download_mode() -> str:
    """
    Permite escolher o modo de operação (transferência ou listagem/catálogo).
    """
    console.print("\n[bold]1. O que pretendes fazer?[/bold]")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Opção", style="cyan", width=6)
    table.add_column("Tipo", style="yellow", width=12)
    table.add_column("Modo", style="bold white", width=24)
    table.add_column("Descrição", style="dim")

    # Modos de download
    table.add_row("1", "Download", "Canal Completo", "Descarrega todos os vídeos do canal (Tudo)")
    table.add_row("2", "Download", "Vídeo Individual", "Descarrega um único vídeo por link ou ID")
    table.add_row("3", "Download", "Filtrar por Ano", "Descarrega apenas os vídeos de um ano (ex: 2024)")
    table.add_row("4", "Download", "Filtrar por Mês", "Descarrega os vídeos de um mês (ex: 2024-11 ou 11-2024)")
    table.add_row("5", "Download", "Filtrar por Dia", "Descarrega os vídeos de um dia exato (ex: 19/11/2024)")

    # Modos de listagem / catálogo
    table.add_row("6", "Listar", "Listar Mês Específico", "Exporta lista de vídeos de um mês (.md, .json ou .csv)")
    table.add_row("7", "Listar", "Listar Intervalo de Meses", "Exporta vídeos de um intervalo (ex: 09-2024 a 12-2024)")
    table.add_row("8", "Listar", "Listar Todos Agrupados", "Exporta todos os vídeos do canal agrupados por mês")

    console.print(table)

    escolha = Prompt.ask(
        "[yellow]Escolhe a opção desejada[/yellow]",
        choices=["1", "2", "3", "4", "5", "6", "7", "8"],
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
    console.print(
        "[dim]Formatos aceites: AAAA-MM (ex: 2024-11), MM-AAAA (ex: 11-2024) ou MM/AAAA[/dim]"
    )
    while True:
        mes_input = Prompt.ask("[yellow]Indica o mês pretendido[/yellow]")
        try:
            start_date, end_date, label = config.parse_month(mes_input)
            dr = DateRange(start_date, end_date)
            return dr, f"Mês {label}"
        except ValueError as e:
            console.print(f"[red]{e}[/red]")


def prompt_month_range() -> Tuple[DateRange, str, str, str]:
    """
    Pergunta ao utilizador o mês de início e o mês de fim para exportar por intervalo.
    Retorna: (DateRange, label_filtro, label_inicio, label_fim)
    """
    console.print("\n[bold]Intervalo de Meses[/bold]")
    console.print(
        "[dim]Formatos aceites: AAAA-MM (ex: 2024-09) ou MM-AAAA (ex: 09-2024)[/dim]"
    )
    while True:
        inicio = Prompt.ask("[yellow]Mês inicial (ex: 09-2024)[/yellow]")
        fim = Prompt.ask("[yellow]Mês final (ex: 12-2024)[/yellow]")
        try:
            start_date, end_date, lbl_start, lbl_end = config.parse_month_range(
                inicio, fim
            )
            dr = DateRange(start_date, end_date)
            label = f"Intervalo de {lbl_start} a {lbl_end}"
            return dr, label, lbl_start, lbl_end
        except ValueError as e:
            console.print(f"[red]{e}[/red]")


def prompt_export_format() -> str:
    """
    Pergunta ao utilizador qual o formato de ficheiro preferido para o catálogo (.md, .json, .csv).
    Apresenta claramente os pontos fortes de cada opção para ajudar na decisão.
    """
    console.print("\n[bold]Formato de Exportação do Catálogo[/bold]")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Opção", style="cyan", width=6)
    table.add_column("Formato", style="bold white", width=14)
    table.add_column("Melhor opção para...", style="dim")

    table.add_row(
        "1",
        "Markdown (.md)",
        "Melhor para leitura direta, GitHub, notas Obsidian e relatórios formatados",
    )
    table.add_row(
        "2",
        "JSON (.json)",
        "Melhor para integrações técnicas, scripts, automação e preservação de metadados",
    )
    table.add_row(
        "3",
        "CSV (.csv)",
        "Melhor para tabelas no Excel, Google Sheets, filtros e ordenações manuais",
    )
    table.add_row(
        "4",
        "Todos (md, json, csv)",
        "Gera em simultâneo os três formatos (recomendado para inventário completo)",
    )

    console.print(table)

    escolha = Prompt.ask(
        "[yellow]Escolhe o formato pretendido[/yellow]",
        choices=["1", "2", "3", "4", "md", "json", "csv", "todos"],
        default="1",
    )
    mapping = {
        "1": "md",
        "2": "json",
        "3": "csv",
        "4": "all",
        "md": "md",
        "json": "json",
        "csv": "csv",
        "todos": "all",
        "all": "all",
    }
    return mapping[escolha.lower()]


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
    console.print("\n[bold]3. Pasta Base de Destino e Armazenamento[/bold]")

    storage_locations = config.get_available_storage_locations()

    table = Table(
        title="Unidades e Pastas de Destino Detetadas",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Opção", style="cyan", width=6)
    table.add_column("Descrição / Tipo", style="white", width=36)
    table.add_column("Caminho Sugerido", style="dim")
    table.add_column("Espaço Livre", style="green", justify="right")

    for i, loc in enumerate(storage_locations, start=1):
        table.add_row(
            str(i),
            loc["label"],
            str(loc["path"]),
            loc["free_space"],
        )

    custom_opt_num = len(storage_locations) + 1
    table.add_row(
        str(custom_opt_num),
        "[yellow]Outro caminho ou disco personalizado[/yellow]",
        "Escrever ou colar caminho manual...",
        "-",
    )

    console.print(table)

    escolha = Prompt.ask(
        "[yellow]Escolhe o número da pasta/disco desejado[/yellow]",
        choices=[str(i) for i in range(1, custom_opt_num + 1)],
        default="1",
    )

    escolha_idx = int(escolha) - 1
    if escolha_idx < len(storage_locations):
        selected_loc = storage_locations[escolha_idx]
        destino = selected_loc["path"]

        # Se for um disco externo ou partição, dar a opção de personalizar o nome da subpasta
        if selected_loc.get("is_external"):
            console.print(f"\n[cyan]Selecionaste:[/cyan] [bold]{selected_loc['label']}[/bold]")
            usar_padrao = Confirm.ask(
                f"Gravar na subpasta [bold yellow]{destino}[/bold yellow]?",
                default=True,
            )
            if not usar_padrao:
                sub = Prompt.ask(
                    "[yellow]Nome da subpasta neste disco[/yellow]",
                    default="YouTube_Backups",
                )
                destino = destino.parent / sub if destino.name == "YouTube_Backups" else destino / sub
    else:
        caminho_custom = Prompt.ask(
            "[yellow]Introduz o caminho ou letra da unidade (ex: D:, D:\\Backups, /mnt/d, ~/Videos)[/yellow]"
        )
        destino = config.normalize_destination_path(caminho_custom)

    try:
        destino.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        console.print(f"[red]Erro ao criar pasta no destino ({destino}): {e}[/red]")
        console.print("[yellow]A usar pasta de recurso em ~/Videos/YouTube_Backups[/yellow]")
        destino = config.DEFAULT_DOWNLOAD_DIR
        destino.mkdir(parents=True, exist_ok=True)

    free_info = config.get_free_space_str(destino)
    console.print(f"[green]✓ Destino configurado:[/green] [bold]{destino}[/bold] [dim]({free_info})[/dim]")
    console.print(
        "[dim]Os vídeos serão organizados nesta pasta em subpastas com o formato AAAA-MM (ex: 2024-11/)[/dim]"
    )
    return destino


def prompt_connection_method(
    is_download: bool = False,
    saved_key: Optional[str] = None,
) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Pergunta ao utilizador qual o motor que pretende usar (tanto para descarregar como para catalogar).
    1. YouTube Data API v3 (Oficial Google, sem scraping do canal nem rate-limit)
    2. yt-dlp com Cookies do Navegador (Sessão do canal)
    3. yt-dlp Anónimo (Padrão)
    Retorna: (motor: 'api' | 'cookies' | 'scraper', api_key, cookie_browser)
    """
    tipo_acao = "Transferência" if is_download else "Indexação do Catálogo"
    console.print(f"\n[bold]4. Método de {tipo_acao} (Anti Rate-Limit)[/bold]")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Opção", style="cyan", width=6)
    table.add_column("Método", style="bold white", width=30)
    table.add_column("Vantagens", style="dim")

    api_extra = " (Chave guardada no .env ✔)" if saved_key else " (Requer chave API do Google Cloud)"
    desc_api = (
        f"Oficial Google: lista os vídeos via API sem scraping e descarrega direto{api_extra}"
        if is_download
        else f"Oficial Google: ultra rápida, sem scraping, sem rate-limit{api_extra}"
    )
    table.add_row(
        "1",
        "YouTube Data API v3" + ("[green]*[/green]" if saved_key else ""),
        desc_api,
    )
    table.add_row(
        "2",
        "yt-dlp com Cookies do Browser",
        "Usa a tua sessão do canal (Chrome, Firefox, etc.) para evitar bloqueios de scraping",
    )
    table.add_row(
        "3",
        "yt-dlp Anónimo (Padrão)",
        "Sem autenticação (pode ser limitado pelo YouTube se o canal tiver muitos vídeos)",
    )

    console.print(table)

    escolha = Prompt.ask(
        "[yellow]Escolhe o método pretendido[/yellow]",
        choices=["1", "2", "3"],
        default="1" if saved_key else "2",
    )

    if escolha == "1":
        api_key = saved_key
        if not api_key:
            api_key = prompt_api_key_input()
        return "api", api_key, None

    elif escolha == "2":
        browser = prompt_browser_selection()
        return "cookies", None, browser

    else:
        return "scraper", None, None


# Alias para retrocompatibilidade
prompt_inventory_method = prompt_connection_method


def prompt_api_key_input() -> str:
    """
    Solicita a chave da YouTube Data API v3 ao utilizador e oferece a possibilidade de a guardar no .env.
    """
    console.print("\n[bold cyan]Configuração da YouTube Data API v3 (Opção B)[/bold cyan]")
    console.print(
        "[dim]Para obter uma chave gratuita (10.000 unidades/dia grátis para sempre):\n"
        "1. Acede a https://console.cloud.google.com/ e cria um projeto\n"
        "2. Ativa a 'YouTube Data API v3'\n"
        "3. Em 'Credenciais', cria uma 'Chave de API'[/dim]\n"
    )

    while True:
        key = Prompt.ask("[yellow]Introduz a tua chave de API do YouTube (Google Cloud)[/yellow]")
        if key.strip():
            api_key = key.strip()
            if Confirm.ask("[yellow]Guardar esta chave no ficheiro .env para não teres de repetir?[/yellow]", default=True):
                config.save_api_key(api_key)
                console.print("[green]✔ Chave guardada no .env com sucesso![/green]")
            return api_key
        console.print("[red]A chave de API não pode estar vazia![/red]")


def prompt_browser_selection() -> str:
    """
    Permite escolher o navegador de onde importar os cookies de sessão.
    """
    browsers = ["chrome", "firefox", "edge", "brave", "chromium"]
    console.print("\n[bold]Sessão do Navegador (Opção C)[/bold]")
    console.print(
        "[dim]A aplicação importará a tua sessão ativa para o YouTube não tratar os pedidos como bots anónimos.[/dim]"
    )
    browser = Prompt.ask(
        "[yellow]De qual navegador pretendes importar a sessão?[/yellow]",
        choices=browsers,
        default="chrome",
    )
    return browser


def prompt_cookies() -> Optional[str]:
    console.print("\n[bold]4. Autenticação e Sessão do Navegador (Opção C)[/bold]")
    console.print(
        "[dim]Importar a tua sessão do navegador evita rate-limits do YouTube e permite aceder a vídeos privados do teu canal.[/dim]"
    )
    usar_cookies = Confirm.ask(
        "Desejas autenticar usando a sessão do teu navegador (Chrome, Firefox, etc.)?",
        default=True,
    )

    if not usar_cookies:
        return None

    return prompt_browser_selection()


def show_summary(
    mode_name: str,
    target: str,
    dest_dir: Path,
    filter_label: str,
    browser_cookies: Optional[str],
    is_inventory: bool = False,
    export_format: Optional[str] = None,
    use_api: bool = False,
):
    console.print("\n[bold]5. Resumo da Operação[/bold]")

    format_labels = {
        "md": "Markdown (.md)",
        "json": "JSON (.json)",
        "csv": "CSV (.csv)",
        "all": "Todos (.md, .json, .csv)",
    }
    fmt_text = format_labels.get(export_format, export_format or "N/A")

    if is_inventory:
        motor_desc = (
            "YouTube Data API v3 Oficial (Google Cloud — Sem Rate-Limit)"
            if use_api
            else f"yt-dlp ({'Cookies de ' + browser_cookies if browser_cookies else 'Anónimo'})"
        )
        resumo = (
            f"[bold cyan]Ação:[/bold cyan] Listar e Exportar Catálogo\n"
            f"[bold cyan]Modo:[/bold cyan] {mode_name}\n"
            f"[bold cyan]Canal:[/bold cyan] {target}\n"
            f"[bold cyan]Motor:[/bold cyan] {motor_desc}\n"
            f"[bold cyan]Filtro:[/bold cyan] {filter_label}\n"
            f"[bold cyan]Ordenação:[/bold cyan] Cronológica crescente (antigo ➔ recente)\n"
            f"[bold cyan]Formato de Exportação:[/bold cyan] {fmt_text}\n"
            f"[bold cyan]Pasta de Destino:[/bold cyan] {dest_dir}\n"
        )
    else:
        motor_desc = (
            "YouTube Data API v3 (Descoberta oficial sem rate-limit) + Download MP4"
            if use_api
            else f"yt-dlp ({'Cookies de ' + browser_cookies if browser_cookies else 'Anónimo'})"
        )
        resumo = (
            f"[bold cyan]Ação:[/bold cyan] Descarregar Vídeos (MP4)\n"
            f"[bold cyan]Modo:[/bold cyan] {mode_name}\n"
            f"[bold cyan]Alvo:[/bold cyan] {target}\n"
            f"[bold cyan]Motor:[/bold cyan] {motor_desc}\n"
            f"[bold cyan]Filtro de Data:[/bold cyan] {filter_label}\n"
            f"[bold cyan]Pasta Base:[/bold cyan] {dest_dir}\n"
            f"[bold cyan]Organização:[/bold cyan] Subpastas [bold yellow]AAAA-MM[/bold yellow] automáticas\n"
            f"[bold cyan]Vídeos Repetidos:[/bold cyan] Ignorados automaticamente (histórico ativo)\n"
            f"[bold cyan]Autenticação:[/bold cyan] {
                'Chave de API Google Cloud'
                if use_api
                else ('Navegador ' + browser_cookies if browser_cookies else 'Pública (Sem login)')
            }"
        )
    console.print(Panel(resumo, title="Configuração Final", border_style="green"))


def show_inventory_results(
    grouped: dict,
    exported_files: list[Path],
    filter_label: str,
):
    """
    Apresenta um relatório visual elegante dos vídeos catalogados e dos ficheiros exportados.
    """
    total_videos = sum(len(vids) for vids in grouped.values())
    total_months = len(grouped)

    console.print(
        f"\n[bold green]✔ Catálogo concluído com sucesso![/bold green] "
        f"[dim]Total: {total_videos} vídeo{'s' if total_videos != 1 else ''} em {total_months} mês{'es' if total_months != 1 else ''} ({filter_label})[/dim]\n"
    )

    if total_videos > 0:
        table = Table(
            title="Distribuição por Mês (Ordem Crescente)",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Mês", style="bold cyan", width=10)
        table.add_column("Vídeos", style="green", justify="right", width=8)
        table.add_column("Primeiro Vídeo", style="dim", no_wrap=True)
        table.add_column("Último Vídeo", style="dim", no_wrap=True)

        for month, vids in grouped.items():
            first_vid = vids[0]["title"][:35] if vids else "-"
            last_vid = vids[-1]["title"][:35] if vids else "-"
            table.add_row(month, str(len(vids)), first_vid, last_vid)

        console.print(table)

    console.print("\n[bold]📁 Ficheiro(s) Gerado(s):[/bold]")
    for p in exported_files:
        ext = p.suffix.lower()
        icon = "📄" if ext == ".md" else "📊" if ext == ".csv" else "📦"
        console.print(f"  {icon} [cyan]{p}[/cyan]")


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

        idx = d.get("playlist_index")
        total = d.get("playlist_count") or d.get("n_entries")
        item_prefix = f" [bold yellow]({idx}/{total})[/bold yellow]" if idx and total else ""

        console.print(
            f"[cyan]A descarregar{item_prefix}:[/cyan] [bold]{filename[:35]}[/bold] | "
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
        if "Remote component challenge solver script" in msg:
            return
        if "n challenge solving failed" in msg:
            return
        if "No supported JavaScript runtime could be found" in msg:
            self.console.print(
                "[dim yellow]ℹ Nota: Nenhum motor JavaScript detetado (Node.js/Deno). A utilizar clientes alternativos.[/dim yellow]"
            )
            return
        if "Incomplete data received. Retrying" in msg:
            match = re.search(r"Retrying \((\d+/\d+)\)", msg)
            tentativa = match.group(1) if match else "..."
            self.console.print(
                f"[dim yellow]ℹ Pacote incompleto recebido; nova tentativa ({tentativa})...[/dim yellow]"
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
