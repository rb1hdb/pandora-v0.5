FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

# Instala dependências Python (uma vez, no build da imagem).
# Como o código é bind-mounted do host, o site-packages fica na imagem
# e o código vem de fora.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia APENAS o que o container precisa ter baked-in (config.default.json
# para o entrypoint semear o config na primeira execução).
COPY mcp-server/ mcp-server/
COPY entrypoint.sh .

RUN chmod +x entrypoint.sh

EXPOSE 55000

ENTRYPOINT ["./entrypoint.sh"]
