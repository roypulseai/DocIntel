FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

# Install CPU-only PyTorch first: the default `torch` wheel on Linux bundles
# ~2.5GB of CUDA libraries, but DocIntel only runs CPU embeddings. Installing
# the CPU variant here satisfies `torch>=2.2` (pulled by sentence-transformers)
# so the subsequent `pip install -r requirements.txt` skips the CUDA build.
RUN pip install --no-cache-dir --retries 10 --timeout 60 --index-url https://download.pytorch.org/whl/cpu torch

RUN pip install --no-cache-dir --retries 10 --timeout 60 -r requirements.txt

# Download the spaCy name-detection model. Retried a few times because the
# download is large and can be truncated by flaky networks.
RUN for i in 1 2 3 4 5; do \
        python -m spacy download en_core_web_sm && break; \
        echo "spacy model download attempt $i failed, retrying..."; \
        sleep 5; \
    done

COPY docintel/ ./docintel/
COPY run_demo.py .
COPY app.py .
COPY tests/ ./tests/

# No API key is baked into the image. Provide it at runtime (e.g. via
# docker-compose `GROQ_API_KEY`) or enter it in the app's sidebar — the app
# falls back to in-app entry if the variable is unset.

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
