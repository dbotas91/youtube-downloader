import json
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from yt_dlp.utils import DateRange

import config
from config import format_duration


def parse_iso8601_duration(duration_str: str) -> Optional[int]:
    """
    Converte durações ISO 8601 devolvidas pela YouTube Data API v3
    (ex: 'PT1H2M34S', 'PT15M33S', 'PT45S') para segundos inteiros.
    """
    if not duration_str or not duration_str.startswith("P"):
        return None

    pattern = re.compile(
        r"P(?:(?P<days>\d+)D)?T?(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?"
    )
    match = pattern.match(duration_str)
    if not match:
        return None

    parts = match.groupdict()
    days = int(parts.get("days") or 0)
    hours = int(parts.get("hours") or 0)
    minutes = int(parts.get("minutes") or 0)
    seconds = int(parts.get("seconds") or 0)
    return days * 86400 + hours * 3600 + minutes * 60 + seconds


class YouTubeAPIClient:
    """
    Cliente para a YouTube Data API v3 oficial do Google.
    Permite listar e catalogar vídeos de qualquer canal de forma instantânea,
    sem scraping e sem risco de rate-limit.
    """

    BASE_URL = "https://www.googleapis.com/youtube/v3"

    def __init__(self, api_key: str):
        self.api_key = api_key.strip()
        if not self.api_key:
            raise ValueError("A chave de API do YouTube não pode estar vazia.")

    def _get(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa um pedido GET seguro à YouTube Data API v3 usando apenas a biblioteca padrão.
        """
        query_params = dict(params)
        query_params["key"] = self.api_key
        url = f"{self.BASE_URL}/{endpoint}?{urllib.parse.urlencode(query_params)}"

        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "YouTubeBackupTool/1.0",
                "Accept": "application/json",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            try:
                error_body = json.loads(e.read().decode("utf-8"))
                error_msg = (
                    error_body.get("error", {}).get("message")
                    or f"HTTP Error {e.code}"
                )
            except Exception:
                error_msg = f"HTTP Error {e.code}: {e.reason}"

            if e.code == 400:
                raise ValueError(
                    f"Erro de pedido na API do YouTube (400): {error_msg}"
                )
            elif e.code == 403:
                raise PermissionError(
                    f"Acesso recusado pela API do YouTube (403). Verifica se a chave é válida e se a 'YouTube Data API v3' está ativada no Google Cloud. Detalhe: {error_msg}"
                )
            elif e.code == 404:
                raise FileNotFoundError(
                    f"Recurso não encontrado na API do YouTube (404): {error_msg}"
                )
            else:
                raise RuntimeError(
                    f"Erro na comunicação com a API do YouTube ({e.code}): {error_msg}"
                )
        except urllib.error.URLError as e:
            raise ConnectionError(
                f"Falha de ligação à API do YouTube: {e.reason}"
            )

    def resolve_channel_uploads_playlist(
        self, channel_input: str
    ) -> tuple[str, str, str]:
        """
        Resolve o identificador ou link do canal para:
        (channel_id, channel_title, uploads_playlist_id)
        """
        clean = channel_input.strip().rstrip("/")
        if "/videos" in clean:
            clean = clean.rsplit("/videos", 1)[0]

        channel_id: Optional[str] = None
        handle: Optional[str] = None
        username: Optional[str] = None

        if "/channel/" in clean:
            channel_id = clean.split("/channel/")[-1].split("/")[0]
        elif clean.startswith("UC") and len(clean) == 24:
            channel_id = clean
        elif "/c/" in clean or "/user/" in clean:
            username = clean.split("/")[-1]
        elif "@" in clean:
            handle = "@" + clean.split("@")[-1].split("/")[0]
        else:
            if clean.startswith("@"):
                handle = clean
            else:
                # Pode ser um handle sem @ ou username
                handle = f"@{clean}"

        # 1. Tentar por handle se disponível
        if handle:
            data = self._get(
                "channels",
                {
                    "part": "snippet,contentDetails",
                    "forHandle": handle,
                },
            )
            items = data.get("items", [])
            if items:
                ch = items[0]
                ch_id = ch["id"]
                title = ch["snippet"]["title"]
                uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
                return ch_id, title, uploads

        # 2. Tentar por channel_id direto se disponível
        if channel_id:
            data = self._get(
                "channels",
                {
                    "part": "snippet,contentDetails",
                    "id": channel_id,
                },
            )
            items = data.get("items", [])
            if items:
                ch = items[0]
                ch_id = ch["id"]
                title = ch["snippet"]["title"]
                uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
                return ch_id, title, uploads

        # 3. Tentar por forUsername se aplicável
        if username or handle:
            uname = username or (handle[1:] if handle else clean)
            try:
                data = self._get(
                    "channels",
                    {
                        "part": "snippet,contentDetails",
                        "forUsername": uname,
                    },
                )
                items = data.get("items", [])
                if items:
                    ch = items[0]
                    ch_id = ch["id"]
                    title = ch["snippet"]["title"]
                    uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
                    return ch_id, title, uploads
            except Exception:
                pass

        # 4. Fallback: procurar via search de canais
        search_query = handle or channel_input
        data = self._get(
            "search",
            {
                "part": "snippet",
                "type": "channel",
                "q": search_query,
                "maxResults": 1,
            },
        )
        items = data.get("items", [])
        if items:
            ch_id = items[0]["id"]["channelId"]
            title = items[0]["snippet"]["title"]
            # Na convenção do YouTube, a playlist de uploads é 'UU' substituindo 'UC'
            uploads = "UU" + ch_id[2:] if ch_id.startswith("UC") else ch_id
            return ch_id, title, uploads

        raise ValueError(
            f"Não foi possível encontrar o canal correspondente a '{channel_input}'. "
            "Verifica se o @handle ou o link do canal estão corretos."
        )

    def fetch_videos(
        self,
        channel_input: str,
        date_range: Optional[DateRange] = None,
        progress_callback: Optional[Callable[[int, Optional[int], str], None]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Recolhe todos os vídeos do canal via YouTube Data API v3.
        Aplica interrupção antecipada inteligente se houver date_range e devolve a lista
        ordenada cronologicamente em ordem crescente.
        """
        ch_id, ch_title, uploads_playlist_id = (
            self.resolve_channel_uploads_playlist(channel_input)
        )

        videos: List[Dict[str, Any]] = []
        page_token: Optional[str] = None
        count = 0
        stop_pagination = False

        # DateRange.start e .end são objetos datetime.date — converter para string YYYYMMDD
        # para poder comparar diretamente com upload_date (que também é string YYYYMMDD)
        start_bound = (
            date_range.start.strftime("%Y%m%d")
            if date_range and date_range.start
            else None
        )
        end_bound = (
            date_range.end.strftime("%Y%m%d")
            if date_range and date_range.end
            else None
        )

        # 1. Paginação através da playlist de uploads do canal (50 itens por página = 1 unidade de quota)
        while True:
            params: Dict[str, Any] = {
                "part": "snippet,contentDetails",
                "playlistId": uploads_playlist_id,
                "maxResults": 50,
            }
            if page_token:
                params["pageToken"] = page_token

            data = self._get("playlistItems", params)
            items = data.get("items", [])
            if not items:
                break

            total_estimate = data.get("pageInfo", {}).get("totalResults")

            for item in items:
                video_id = item["contentDetails"]["videoId"]
                title = item["snippet"]["title"]
                published_at = item["snippet"]["publishedAt"]  # Ex: 2024-11-19T10:00:00Z

                upload_date = published_at[:10].replace("-", "")  # Ex: 20241119
                upload_date_formatted = published_at[:10]  # Ex: 2024-11-19
                month = published_at[:7]  # Ex: 2024-11
                url = f"https://www.youtube.com/watch?v={video_id}"

                # Interrupção antecipada: se já estamos antes da data de início selecionada
                if start_bound and upload_date < start_bound:
                    stop_pagination = True
                    break

                # Se está dentro do intervalo (ou não há intervalo)
                if (not start_bound or upload_date >= start_bound) and (
                    not end_bound or upload_date <= end_bound
                ):
                    count += 1
                    videos.append(
                        {
                            "id": video_id,
                            "title": title,
                            "upload_date": upload_date,
                            "upload_date_formatted": upload_date_formatted,
                            "month": month,
                            "url": url,
                            "duration": None,
                            "duration_formatted": "N/D",
                            "view_count": None,
                        }
                    )

                    if progress_callback:
                        progress_callback(count, total_estimate, title)

            if stop_pagination:
                break

            page_token = data.get("nextPageToken")
            if not page_token:
                break

        # 2. Obter as durações dos vídeos em lotes de 50 (apenas 1 unidade de quota por lote de 50)
        if videos:
            self._enrich_video_durations(videos)

        # 3. Ordenação crescente estrita por data de publicação
        videos.sort(key=lambda v: (v["upload_date"], v["title"].lower()))
        return videos

    def _enrich_video_durations(self, videos: List[Dict[str, Any]]):
        """
        Enriquece a lista de vídeos com as respetivas durações fazendo pedidos em lote de até 50 vídeos.
        """
        batch_size = 50
        for i in range(0, len(videos), batch_size):
            batch = videos[i : i + batch_size]
            ids_str = ",".join(v["id"] for v in batch)

            try:
                data = self._get(
                    "videos",
                    {
                        "part": "contentDetails",
                        "id": ids_str,
                    },
                )
                duration_map = {}
                for item in data.get("items", []):
                    vid_id = item["id"]
                    dur_iso = item["contentDetails"].get("duration")
                    seconds = parse_iso8601_duration(dur_iso)
                    duration_map[vid_id] = seconds

                for v in batch:
                    secs = duration_map.get(v["id"])
                    v["duration"] = secs
                    v["duration_formatted"] = format_duration(secs)
            except Exception:
                # Se falhar a obtenção de duração, mantém 'N/D' sem quebrar a listagem
                pass
