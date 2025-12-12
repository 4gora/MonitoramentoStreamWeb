import logging
from colorama import Fore, Style
import datetime
from config_loader import config

intervalo_apagar_log = config.get("intervalo_apagar_log", 3600)
qtd_linhas_log = config.get("qtd_linhas_log", 1000)

# Logger de conexões OBS (separado)
connection_logger = None

def setup_connection_logger():
    """
    Configura o logger de conexões OBS, salvando em logs/connection.log separadamente.
    """
    global connection_logger
    import os
    os.makedirs('logs', exist_ok=True)
    log_path = os.path.join('logs', "connection.log")
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler = logging.FileHandler(log_path, encoding='utf-8')
    handler.setFormatter(formatter)
    connection_logger = logging.getLogger('obs_connections')
    connection_logger.setLevel(logging.INFO)
    if connection_logger.hasHandlers():
        connection_logger.handlers.clear()
    connection_logger.addHandler(handler)
    connection_logger.propagate = False  # Não propagar para o logger raiz
    return connection_logger

def log_connection_terminal(msg, level='info', cor=None):
    """
    Exibe mensagem de conexão colorida no terminal e registra em logs/connection.log.
    """
    global connection_logger
    if connection_logger is None:
        setup_connection_logger()
    
    hora_str = datetime.datetime.now().strftime("%H:%M:%S")
    cor_map = {
        'green': Fore.LIGHTGREEN_EX,
        'red': Fore.LIGHTRED_EX,
        'magenta': Fore.LIGHTMAGENTA_EX,
        'yellow': Fore.LIGHTYELLOW_EX,
        'black': Fore.LIGHTBLACK_EX,
        'cyan': Fore.LIGHTCYAN_EX,
        'white': Fore.LIGHTWHITE_EX,
    }
    cor_prefix = cor_map.get(cor, '')
    print(f"{cor_prefix}[{hora_str}] {msg}" + Style.RESET_ALL)
    
    if level == 'info':
        connection_logger.info(msg)
    elif level == 'warning':
        connection_logger.warning(msg)
    elif level == 'error':
        connection_logger.error(msg)
    else:
        connection_logger.info(msg)

def setup_logger(): 
    """
    Configura o logger principal do sistema, salvando logs em um único arquivo.
    A cada 1 hora, mantém apenas as últimas 1000 linhas do arquivo de log.
    """
    import os
    import threading
    os.makedirs('logs', exist_ok=True)
    log_path = os.path.join('logs', "main.log")
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler = logging.FileHandler(log_path, encoding='utf-8')
    handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.addHandler(handler)

    def trim_log_file():
        while True:
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                if len(lines) > qtd_linhas_log:
                    with open(log_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines[-qtd_linhas_log:])
            except Exception:
                pass
            # Espera 1 hora
            threading.Event().wait(intervalo_apagar_log)

    t = threading.Thread(target=trim_log_file, daemon=True)
    t.start()
    return logger

def log_blank_line(logger):
    """
    Adiciona uma linha em branco ao arquivo de log principal.
    """
    if logger.handlers:
        logger.handlers[0].stream.write("\n");
        logger.handlers[0].flush()

def log_terminal(msg, level='info', cor=None, log=True):
    """
    Exibe mensagem colorida no terminal e registra no log, se desejado.
    """
    hora_str = datetime.datetime.now().strftime("%H:%M:%S")
    cor_map = {
        'green': Fore.LIGHTGREEN_EX,
        'red': Fore.LIGHTRED_EX,
        'magenta': Fore.LIGHTMAGENTA_EX,
        'yellow': Fore.LIGHTYELLOW_EX,
        'black': Fore.LIGHTBLACK_EX,
        'cyan': Fore.LIGHTCYAN_EX,
        'white': Fore.LIGHTWHITE_EX,
    }
    cor_prefix = cor_map.get(cor, '')
    print(f"{cor_prefix}[{hora_str}] {msg}" + Style.RESET_ALL)
    if log:
        logger = logging.getLogger()
        if level == 'info':
            logger.info(msg)
        elif level == 'warning':
            logger.warning(msg)
        elif level == 'error':
            logger.error(msg)
        else:
            logger.info(msg)
