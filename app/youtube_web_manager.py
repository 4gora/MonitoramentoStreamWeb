"""
youtube_web_manager.py - Gerenciador YouTube para versão web (sem OBS)
Adapta a lógica do YouTubeOBSManager para retornar dados via JSON/WebSocket
"""

import json
import http.client as client
from datetime import datetime as dt, timezone
from config_loader import config
from canal_web import CanalWeb
from log_config import log_terminal
import os


class YouTubeWebManager:
    """Gerencia integração YouTube para interface web"""
    
    def __init__(self):
        """Inicializa o gerenciador com configurações do config.yaml"""
        self.youtube_key = config.get("youtube_api_key")
        self.intervalo_execucao = config.get("intervalo_execucao", 120)
        self.intervalo_busca = config.get("intervalo_busca", 180)
        self.intervalo_atualizacao = config.get("intervalo_atualizacao", 300)
        
        # Criação dos canais
        self.canais = [
            CanalWeb(c["channel_id"], c["nome"])
            for c in config["canais"]
        ]
        
        self.ultima_atualizacao_status = 0
        
        log_terminal(f"YouTubeWebManager inicializado com {len(self.canais)} canais", cor='green')
    
    def filter_eventos_validos(self, eventos):
        """
        Filtra eventos que não estão encerrados (actualEndTime vazio) 
        e agendados para hoje ou futuro.
        """
        agora = dt.now(timezone.utc)
        eventos_filtrados = []
        
        for evento in eventos:
            if evento.get("actualEndTime"):
                continue
            
            sched = evento.get("scheduledStartTime")
            if sched:
                try:
                    sched_dt = dt.fromisoformat(sched.replace("Z", "+00:00"))
                    if sched_dt.date() < agora.date():
                        continue
                except Exception:
                    pass
            
            eventos_filtrados.append(evento)
        
        return eventos_filtrados
    
    def buscar_eventos_api(self, canal):
        """
        Busca eventos ao vivo e agendados do canal no YouTube.
        Retorna lista de eventos com detalhes de horário.
        """
        if not canal.channel_id:
            return []
        
        eventos = []
        try:
            # Buscar eventos ao vivo
            endpoint_live = f"/youtube/v3/search?part=snippet&channelId={canal.channel_id}&key={self.youtube_key}&eventType=live&type=video&maxResults=10"
            eventos += self._eventos_da_api(endpoint_live)
            
            # Buscar eventos agendados
            endpoint_upcoming = f"/youtube/v3/search?part=snippet&channelId={canal.channel_id}&key={self.youtube_key}&eventType=upcoming&type=video&maxResults=10"
            eventos += self._eventos_da_api(endpoint_upcoming)
            
            # Buscar detalhes dos vídeos para pegar horários
            video_ids = [ev['videoId'] for ev in eventos]
            if video_ids:
                detalhes = self._detalhes_videos(video_ids)
                for ev in eventos:
                    det = detalhes.get(ev['videoId'], {})
                    ev['actualStartTime'] = det.get('actualStartTime')
                    ev['scheduledStartTime'] = det.get('scheduledStartTime')
                    ev['actualEndTime'] = det.get('actualEndTime')
            
            eventos = self.filter_eventos_validos(eventos)
            
        except Exception as e:
            log_terminal(f"[buscar_eventos_api] Erro para canal {canal.nome}: {e}", 
                        level='error', cor='red')
        
        return eventos
    
    def _eventos_da_api(self, endpoint):
        """Busca eventos de um endpoint da API YouTube"""
        try:
            conn = client.HTTPSConnection("www.googleapis.com", timeout=10)
            conn.request("GET", endpoint)
            res = conn.getresponse()
            
            if res.status != 200:
                log_terminal(f"[_eventos_da_api] HTTP status: {res.status}", 
                            level='warning', cor='yellow')
                return []
            
            data = json.loads(res.read().decode("utf-8"))
            items = data.get("items", [])
            eventos = []
            
            for item in items:
                try:
                    video_id = item["id"]["videoId"]
                    title = item["snippet"]["title"]
                    url = f"https://www.youtube.com/watch?v={video_id}"
                    live_details = item.get("liveStreamingDetails", {})
                    
                    eventos.append({
                        "videoId": video_id,
                        "title": title,
                        "url": url,
                        "actualStartTime": live_details.get("actualStartTime"),
                        "scheduledStartTime": live_details.get("scheduledStartTime"),
                        "actualEndTime": live_details.get("actualEndTime"),
                    })
                except Exception as e:
                    log_terminal(f"[_eventos_da_api] Erro ao processar item: {e}", 
                                level='warning', cor='yellow')
                    continue
            
            return eventos
            
        except Exception as e:
            log_terminal(f"[_eventos_da_api] Erro: {e}", level='error', cor='red')
            return []
    
    def _detalhes_videos(self, video_ids):
        """Busca detalhes de vídeos (horários de início/fim)"""
        detalhes = {}
        try:
            endpoint = f"/youtube/v3/videos?part=liveStreamingDetails&id={','.join(video_ids)}&key={self.youtube_key}"
            conn = client.HTTPSConnection("www.googleapis.com", timeout=10)
            conn.request("GET", endpoint)
            res = conn.getresponse()
            
            if res.status != 200:
                log_terminal(f"[_detalhes_videos] HTTP status: {res.status}", 
                            level='warning', cor='yellow')
                return detalhes
            
            data = json.loads(res.read().decode("utf-8"))
            for item in data.get("items", []):
                vid = item["id"]
                live_details = item.get("liveStreamingDetails", {})
                detalhes[vid] = live_details
            
        except Exception as e:
            log_terminal(f"[_detalhes_videos] Erro: {e}", level='error', cor='red')
        
        return detalhes
    
    def atualizar_status_videos(self, canal):
        """
        Atualiza o status de todos os vídeos monitorados do canal.
        Carrega pesquisa anterior e atualiza horários.
        """
        eventos = canal.carregar_ultima_pesquisa()
        video_ids = [ev['videoId'] for ev in eventos if 'videoId' in ev]
        
        if not video_ids:
            return
        
        # Dividir em lotes de até 50
        for i in range(0, len(video_ids), 50):
            lote = video_ids[i:i+50]
            detalhes = self._detalhes_videos(lote)
            
            for ev in eventos:
                if ev['videoId'] in detalhes:
                    det = detalhes.get(ev['videoId'], {})
                    ev['actualStartTime'] = det.get('actualStartTime')
                    ev['scheduledStartTime'] = det.get('scheduledStartTime')
                    ev['actualEndTime'] = det.get('actualEndTime')
        
        eventos_filtrados = self.filter_eventos_validos(eventos)
        canal.salvar_pesquisa(eventos_filtrados)
    
    def selecionar_stream(self, eventos, canal):
        """
        Seleciona a melhor stream para o canal, priorizando:
        1. Lives ao vivo (actualStartTime preenchido)
        2. Agendadas mais próximas
        """
        agora = dt.now(timezone.utc)
        
        # Filtrar eventos válidos
        eventos_filtrados = []
        for evento in eventos:
            if evento.get("actualEndTime"):
                continue
            
            sched = evento.get("scheduledStartTime")
            if sched:
                try:
                    sched_dt = dt.fromisoformat(sched.replace("Z", "+00:00"))
                    if sched_dt.date() < agora.date():
                        continue
                except Exception:
                    pass
            
            eventos_filtrados.append(evento)
        
        eventos = eventos_filtrados
        melhor_evento = None
        menor_delta = None
        
        # 1. Priorizar ao vivo
        for evento in eventos:
            is_live = False
            
            if evento.get("actualStartTime") and not evento.get("actualEndTime"):
                is_live = True
                try:
                    inicio = dt.fromisoformat(evento["actualStartTime"].replace("Z", "+00:00"))
                except Exception:
                    inicio = agora
            
            elif evento.get("scheduledStartTime") and not evento.get("actualEndTime"):
                try:
                    sched_dt = dt.fromisoformat(evento["scheduledStartTime"].replace("Z", "+00:00"))
                    if sched_dt <= agora:
                        is_live = True
                        inicio = sched_dt
                except Exception:
                    pass
            
            if is_live:
                delta = abs((agora - inicio).total_seconds())
                if menor_delta is None or delta < menor_delta:
                    melhor_evento = evento
                    menor_delta = delta
        
        # 2. Se não há ao vivo, pegar agendado mais próximo
        if not melhor_evento:
            menor_delta = None
            for evento in eventos:
                sched = evento.get("scheduledStartTime")
                if sched:
                    try:
                        inicio = dt.fromisoformat(sched.replace("Z", "+00:00"))
                        if inicio > agora:
                            delta = (inicio - agora).total_seconds()
                            if menor_delta is None or delta < menor_delta:
                                melhor_evento = evento
                                menor_delta = delta
                    except Exception:
                        continue
        
        if melhor_evento:
            return melhor_evento
        
        return None
    
    def run_cycle(self):
        """
        Executa um ciclo completo de monitoramento:
        - Carrega pesquisas anteriores
        - Atualiza status se necessário
        - Seleciona melhor stream para cada canal
        """
        import time
        
        agora = time.time()
        
        for canal in self.canais:
            try:
                # Carregar pesquisa anterior
                eventos = canal.carregar_ultima_pesquisa()
                
                # Se não há pesquisa ou passou intervalo de atualização, buscar nova
                if not eventos or (agora - self.ultima_atualizacao_status) >= self.intervalo_atualizacao:
                    log_terminal(f"[{canal.nome}] Atualizando pesquisa na API...", cor='magenta')
                    eventos = self.buscar_eventos_api(canal)
                    if eventos:
                        canal.salvar_pesquisa(eventos)
                else:
                    # Atualizar status dos vídeos existentes
                    self.atualizar_status_videos(canal)
                    eventos = canal.carregar_ultima_pesquisa()
                
                # Selecionar melhor stream
                melhor = self.selecionar_stream(eventos, canal)
                
                if melhor:
                    canal.selected_stream = melhor
                    canal.proxima_stream_url = melhor.get('url')
                    log_terminal(f"[{canal.nome}] Stream selecionada: {melhor.get('title')}", cor='green')
                else:
                    canal.selected_stream = None
                    canal.proxima_stream_url = None
                    log_terminal(f"[{canal.nome}] Nenhuma stream disponível", level='warning', cor='yellow')
                
            except Exception as e:
                log_terminal(f"[{canal.nome}] Erro no ciclo: {e}", level='error', cor='red')
                canal.selected_stream = None
                canal.proxima_stream_url = None
        
        self.ultima_atualizacao_status = agora
    
    def get_streams_data(self):
        """
        Retorna dicionário com dados de todos os canais para enviar ao frontend.
        Formato: {channel_id: {channel_id, nome, selected_stream}}
        """
        streams_data = {}
        
        for canal in self.canais:
            streams_data[canal.channel_id or canal.nome] = {
                "channel_id": canal.channel_id or canal.nome,
                "nome": canal.nome,
                "selected_stream": canal.selected_stream if hasattr(canal, 'selected_stream') else None,
            }
        
        return streams_data
