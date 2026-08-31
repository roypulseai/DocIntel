FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m spacy download en_core_web_sm

COPY docintel/ ./docintel/
COPY run_demo.py .
COPY app.py .
COPY tests/ ./tests/

ENV GROQ_API_KEY=""

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
