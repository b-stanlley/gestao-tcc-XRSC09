import logging

def criar_logger(nome_servico: str):
    logger = logging.getLogger(nome_servico)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        h = logging.StreamHandler()
        h.setFormatter(logging.Formatter(
            '%(asctime)s [%(name)s] %(levelname)s: %(message)s', datefmt='%H:%M:%S'))
        logger.addHandler(h)
    return logger
