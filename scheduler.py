#!/usr/bin/env python
# -*- coding: utf-8 -*-

import schedule
import time
from update_products import update_products
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scheduler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("scheduler")

def job():
    logger.info("Iniciando job de atualização de produtos...")
    try:
        success = update_products()
        if success:
            logger.info("Job de atualização concluído com sucesso")
        else:
            logger.error("Job de atualização falhou")
    except Exception as e:
        logger.error(f"Erro durante execução do job: {str(e)}")

def main():
    logger.info("Iniciando scheduler...")
    
    # Agenda a execução para meia-noite (GMT-03:00)
    schedule.every().day.at("00:00").do(job)
    
    logger.info("Scheduler configurado. Aguardando horário de execução...")
    
    # Executa imediatamente na primeira vez
    job()
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Verifica a cada minuto

if __name__ == "__main__":
    main() 