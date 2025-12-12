# 📡 Monitor de Lives YouTube - Versão Web

Uma aplicação Python moderna que monitora canais do YouTube e exibe streams em tempo real através de uma **interface web responsiva**, eliminando a necessidade do OBS.

## 🎯 Características

✅ **Sem OBS** - Grid HTML/CSS responsivo em vez de múltiplas instâncias do OBS  
✅ **Tempo real** - Atualização via WebSocket  
✅ **Multiplataforma** - Acesse de qualquer navegador na rede  
✅ **Leve** - Menor consumo de CPU/RAM  
✅ **Pesquisa inteligente** - Busca periódica + cache de pesquisas  
✅ **Dark theme** - Interface otimizada para monitoramento 24/7  

## 📋 Requisitos

- Python 3.7+
- Chave API do YouTube (gratuita)
- Navegador moderno (Chrome, Firefox, Edge, Safari)

## 🚀 Instalação Rápida

### 1. Clonar/Preparar o projeto

```bash
# Se você já tem o projeto original, copie apenas os novos arquivos
# Você precisará de:
# - youtube_web_manager.py (novo)
# - server_web.py (novo)
# - requirements_web.txt (novo)
# - config.yaml (usar o existente, sem alterações)
# - config_loader.py (usar o existente)
# - canal_obs.py (usar o existente)
# - utils.py (usar o existente)
# - log_config.py (usar o existente)
```

### 2. Instalar dependências

```bash
pip install -r requirements_web.txt
```

### 3. Configurar o `config.yaml`

Seu arquivo `config.yaml` existente funciona **sem alterações**. As configurações essenciais:

```yaml
youtube_api_key: "SUA_CHAVE_API_AQUI"  # Obtenha em https://console.cloud.google.com

canais:
  - nome: "FonteIguacu"
    channel_id: "UCX0P-o4zRG7vkGl226MfRYg"
  - nome: "FonteGuara"
    channel_id: "UC3Pc4GMGuJ7MrtusvlAfzUA"
  # ... adicione seus canais

intervalo_execucao: 120          # Segundos entre ciclos
intervalo_busca: 180              # Segundos antes de evento agendado
intervalo_atualizacao: 300        # Segundos para atualizar status
```

**Nota:** As configurações de OBS (`obs_host`, `obs_port`, `obs_password`, `obs_servers`) são ignoradas em modo web.

### 4. Executar o servidor

```bash
python server_web.py
```

Saída esperada:
```
[12:30:45] Servidor iniciando em http://0.0.0.0:5000
[12:30:45] Acesse em: http://localhost:5000 ou http://<SEU_IP>:5000
[12:30:46] YouTubeWebManager iniciado com 6 canais
```

### 5. Acessar a interface

- **Local:** `http://localhost:5000`
- **Rede:** `http://<IP_DA_MAQUINA>:5000`

Exemplo: `http://192.168.1.100:5000`

## 📊 Arquitetura

```
┌─────────────────┐
│  YouTube API    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│  YouTubeWebManager          │
│  - Busca eventos            │
│  - Seleciona melhor stream  │
│  - Atualiza status          │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│  Server Web (Flask)         │
│  - HTTP: /health            │
│  - WebSocket: /socket.io    │
└────────┬────────────────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌──────────┐
│Browser │ │Browser 2 │
│Grid    │ │Grid      │
└────────┘ └──────────┘
```

## 🔧 Funcionamento

### Ciclo de Monitoramento (a cada 120 segundos por padrão)

1. **Carrega pesquisa anterior** do cache local (`pesquisa_api/`)
2. **Atualiza status** dos vídeos se passou intervalo de atualização
3. **Busca nova pesquisa** na API se:
   - Não há pesquisa em cache, OU
   - Passou o intervalo de atualização (300s)
4. **Seleciona melhor stream** com prioridade:
   - 🔴 Ao vivo (com `actualStartTime`)
   - ⏰ Agendada mais próxima
   - ⚫ Offline (nenhuma disponível)
5. **Envia dados via WebSocket** para todos os clientes conectados

### Lógica de Seleção de Stream

Para cada canal, o sistema escolhe a melhor stream nesta ordem:

1. **Lives ao vivo** (aquelas que já começaram)
2. **Streams agendadas mais próximas** (se nenhuma ao vivo)
3. **Offline** (se nenhuma válida)

## 🎨 Interface Web

### Layout

- **Header:** Status de conexão + Horário da última atualização
- **Grid:** Cartões responsivos (1-3 colunas conforme tela)
- **Cada cartão:**
  - Iframe do YouTube (player nativo)
  - Título da stream
  - Nome do canal
  - Badge de status (🔴 Ao Vivo / ⏰ Agendada / ⚫ Offline)
  - Countdown ou status

### Responsividade

- **Desktop (1600px+):** 3 colunas
- **Tablet (768-1024px):** 2 colunas
- **Mobile (<768px):** 1 coluna

### Cores

```
Tema escuro otimizado para ambientes 24/7:
- Fundo: #0f0f0f (preto profundo)
- Texto: #ffffff (branco)
- Live: Verde (#0ccf0c)
- Agendada: Laranja (#ff9800)
- Offline: Vermelho (#ff4444)
```

## 📁 Estrutura de Pastas

```
projeto/
├── server_web.py                 # Servidor Flask + WebSocket
├── youtube_web_manager.py        # Gerenciador YouTube (novo)
├── config.yaml                   # Configuração (usar existente)
├── config_loader.py              # Loader config (usar existente)
├── canal_obs.py                  # Classe Canal (usar existente)
├── utils.py                      # Utilidades (usar existente)
├── log_config.py                 # Logging (usar existente)
├── requirements_web.txt          # Dependências web
├── pesquisa_api/                 # Cache de pesquisas (criado automaticamente)
│   ├── channel_id_1/
│   └── channel_id_2/
└── logs/
    ├── main.log
    └── connection.log
```

## 🔍 Debug e Logs

Logs são salvos automaticamente em:
- `logs/main.log` - Log geral
- `logs/connection.log` - Log de conexões WebSocket

### Verbosidade no terminal

Mensagens codificadas por cor:
- 🟢 Verde = Sucesso
- 🟡 Amarelo = Aviso
- 🔴 Vermelho = Erro
- ⚪ Branco = Info

## 🐛 Troubleshooting

### "Módulo não encontrado: flask"

```bash
pip install -r requirements_web.txt
```

### "Porta 5000 já em uso"

Mude a porta em `server_web.py`:
```python
socketio.run(app, host='0.0.0.0', port=5001, ...)
```

### "YouTube API retorna 403"

- Verifique a chave API em `config.yaml`
- Certifique-se que YouTube Data API v3 está habilitada no Console Google Cloud
- Verifique quota de requisições

### "Nenhuma stream aparece"

1. Verifique se os `channel_id` estão corretos em `config.yaml`
2. Verifique conexão com YouTube API: acesse `http://localhost:5000/health`
3. Verifique logs em `logs/main.log`

### "WebSocket desconecta constantemente"

- Aumente `ping_timeout` em `server_web.py` se conexão for lenta
- Verifique firewall/proxy bloqueando WebSocket

## 📡 API/Endpoints

### HTTP

```
GET /
  └─ Retorna a página HTML da interface

GET /health
  └─ JSON com status do servidor
  └─ Exemplo:
     {
       "status": "healthy",
       "timestamp": "2025-12-12T15:30:00+00:00",
       "connected_clients": 3,
       "manager_running": true
     }
```

### WebSocket (`socket.io`)

```javascript
// Evento: Servidor envia atualização
socket.on('streams_update', (data) => {
  // data = {
  //   channel_id_1: {
  //     channel_id: "UCX0P-o4zRG7vkGl226MfRYg",
  //     nome: "FonteIguacu",
  //     selected_stream: {
  //       videoId: "dQw4w9WgXcQ",
  //       title: "Live Title",
  //       url: "https://youtube.com/watch?v=...",
  //       actualStartTime: "2025-12-12T15:00:00Z",
  //       scheduledStartTime: null,
  //       actualEndTime: null
  //     }
  //   },
  //   ...
  // }
});
```

## 🚀 Performance

### Antes (com OBS)
- CPU: ~25-40% (múltiplas instâncias OBS)
- RAM: ~800MB - 1.2GB
- Rede: Streaming local + WebSocket OBS

### Depois (com web)
- CPU: ~2-5% (apenas Python + Flask)
- RAM: ~50-100MB
- Rede: API YouTube + WebSocket leve

## 📝 Diferencas do Sistema Original

| Aspecto | Original (OBS) | Web |
|---------|---|---|
| Saída | Múltiplas janelas OBS | Um único navegador web |
| Processamento | Alto (várias instâncias OBS) | Baixo (Flask) |
| Acesso | Apenas máquina local | Qualquer máquina da rede |
| Lógica YouTube | ✅ Mesma | ✅ Mesma |
| Pesquisa inteligente | ✅ Sim | ✅ Sim |
| Cache pesquisas | ✅ Sim | ✅ Sim |
| Logs | ✅ Sim | ✅ Sim |

## 📞 Suporte

Se encontrar problemas:

1. Verifique `logs/main.log` e `logs/connection.log`
2. Teste `/health` endpoint
3. Abra console do navegador (F12) para erros JavaScript
4. Verifique config.yaml

## 📄 Licença

Mesmo do projeto original.

---

**Versão:** 1.0  
**Última atualização:** Dezembro 2025
