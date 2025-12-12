"""
canal_web.py - Classe adaptada para monitoramento web
(Pode usar a existente canal_obs.py como base, sem OBS)

Se você quiser, pode renomear seu canal_obs.py para canal_web.py
ou simplesmente importar CanalOBS como está (ambas funcionam).
"""

import json
import os
from datetime import datetime


class CanalWeb:
    """
    Representa um canal YouTube a ser monitorado.
    Armazena informações do canal e cache de pesquisas.
    """
    
    def __init__(self, channel_id, nome):
        """
        Inicializa o canal.
        
        Args:
            channel_id: ID do canal YouTube (ou None para canais especiais)
            nome: Nome exibição do canal
        """
        self.channel_id = channel_id
        self.nome = nome
        self.browser_source_name = nome  # Mantém compatibilidade com código antigo
        self.proxima_stream_url = None
        self.selected_stream = None
        
        # Criar pasta de cache se não existir
        self.pasta_pesquisa = f"pesquisa_api/{channel_id}" if channel_id else f"pesquisa_api/{nome}"
        os.makedirs(self.pasta_pesquisa, exist_ok=True)
    
    def carregar_ultima_pesquisa(self):
        """
        Carrega o arquivo de pesquisa mais recente do canal.
        Retorna lista de eventos ou lista vazia se não houver.
        """
        try:
            arquivos = sorted([f for f in os.listdir(self.pasta_pesquisa) if f.endswith('.json')])
            if not arquivos:
                return []
            
            arquivo_mais_recente = os.path.join(self.pasta_pesquisa, arquivos[-1])
            with open(arquivo_mais_recente, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    
    def salvar_pesquisa(self, eventos):
        """
        Salva pesquisa de eventos em arquivo JSON timestamped.
        
        Args:
            eventos: Lista de eventos (dicts)
        """
        try:
            timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
            arquivo = os.path.join(self.pasta_pesquisa, f"{timestamp}.json")
            
            with open(arquivo, 'w', encoding='utf-8') as f:
                json.dump(eventos, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Erro] Não foi possível salvar pesquisa: {e}")
    
    def __repr__(self):
        return f"Canal({self.nome}, {self.channel_id})"


# Para manter compatibilidade, exporte como CanalOBS também
CanalOBS = CanalWeb
