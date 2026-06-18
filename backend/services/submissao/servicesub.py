import zmq
import json
import time
from common.eventos import Evento, TipoEvento
from common.config import get_zmq_address
from common.logger import criar_logger

logger = criar_logger("Submissão")

context = zmq.Context()

# Socket PUB para publicar eventos de submissão
publisher = context.socket(zmq.PUB)
publisher.bind(get_zmq_address("submissao", "bind"))

logger.info("🚀 Serviço de Submissão iniciado na porta 5560")

def publicar_proposta(aluno_id: int, titulo: str, descricao: str):
    """Publica um evento de proposta submetida"""
    evento = Evento(
        TipoEvento.PROPOSTA_SUBMETIDA,
        aluno_id=aluno_id,
        payload={
            "titulo": titulo,
            "descricao": descricao,
            "status": "pendente_avaliacao"
        }
    )
    
    publisher.send_string(f"{evento.evento} {evento.to_json_str()}")
    logger.info(f"✓ {evento}")

# Simular submissões de propostas
if __name__ == "__main__":
    try:
        alunos = [
            (1, "Análise de Desempenho em Sistemas Distribuídos", "Um estudo comparativo..."),
            (2, "Machine Learning para Otimização de Redes", "Aplicação de IA em infraestrutura..."),
            (3, "Segurança em Computação em Nuvem", "Investigação de vulnerabilidades..."),
        ]
        
        for aluno_id, titulo, descricao in alunos:
            publicar_proposta(aluno_id, titulo, descricao)
            time.sleep(2)
        
        # Manter serviço rodando para novas submissões
        logger.info("Aguardando novas submissões...")
        while True:
            time.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("Serviço finalizado")
    finally:
        publisher.close()
        context.term()
