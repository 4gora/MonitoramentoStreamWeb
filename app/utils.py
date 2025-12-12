def force_browser_source_refresh(ws, source_name, input_settings):
    """
    Força o refresh visual da fonte browser do OBS.
    Atualiza a URL com parâmetro fictício alternado e alterna visibilidade (hide/show).
    """
    url = input_settings.get("url", "")
    if "_mainrefresh=1" in url:
        url_refresh = url.replace("_mainrefresh=1", "_mainrefresh=2")
    elif "_mainrefresh=2" in url:
        url_refresh = url.replace("_mainrefresh=2", "_mainrefresh=1")
    elif "?" in url:
        url_refresh = url + "&_mainrefresh=1"
    else:
        url_refresh = url + "?_mainrefresh=1"
    input_settings["url"] = url_refresh
    ws.set_input_settings(source_name, input_settings, overlay=True)
    # Alterna visibilidade para garantir refresh visual
    try:
        ws.set_input_settings(source_name, {**input_settings, "visible": False}, overlay=True)
        ws.set_input_settings(source_name, {**input_settings, "visible": True}, overlay=True)
    except Exception:
        pass

def clear_terminal():
    """
    Limpa o terminal de acordo com o sistema operacional.
    """
    import os
    os.system('cls' if os.name == 'nt' else 'clear')

def limpar_pesquisa_api(mensagem=None):
    """
    Remove todos os arquivos de pesquisa das subpastas de pesquisa_api.
    """
    import os
    import glob
    pastas = glob.glob('pesquisa_api/*')
    for pasta in pastas:
        arquivos = glob.glob(os.path.join(pasta, '*.json'))
        for arquivo in arquivos:
            try:
                os.remove(arquivo)
                print(f"[INFO] Removido arquivo de pesquisa: {arquivo}")
            except Exception as e:
                print(f"[WARN] Não foi possível remover {arquivo}: {e}")
    if mensagem:
        print(mensagem)


def precisa_limpar_pesquisa_api():
    """
    Verifica se é necessário limpar a pasta de pesquisas (se não há pesquisa do dia).
    """
    import glob
    from datetime import datetime, timezone
    hoje_str = datetime.now(timezone.utc).strftime("%d-%m-%Y")
    arquivos_hoje = glob.glob(f"pesquisa_api/*/{hoje_str}_*.json")
    return len(arquivos_hoje) == 0

def manter_apenas_ultimas_pesquisas_pastas(pastas, max_arquivos=5):
    """
    Para cada pasta em pesquisa_api, mantém apenas os últimos max_arquivos arquivos .json, removendo os mais antigos.
    """
    import os
    import glob
    for pasta in pastas:
        if not os.path.isdir(pasta):
            continue
        arquivos = sorted(glob.glob(os.path.join(pasta, '*.json')), key=os.path.getmtime, reverse=True)
        for arquivo in arquivos[max_arquivos:]:
            try:
                os.remove(arquivo)
                print(f"[INFO] Removido arquivo antigo de pesquisa: {arquivo}")
            except Exception as e:
                print(f"[WARN] Não foi possível remover {arquivo}: {e}")