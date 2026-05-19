FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN mkdir -p web_ui/saves/rooms

ENV PORT=7860

EXPOSE 7860

CMD ["python", "web_ui/server.py"]