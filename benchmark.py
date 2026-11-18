import time
import requests
import pandas as pd

URL = "http://localhost:11434/api/generate"
MODELS = ["qwen2.5:1.5b-instruct-q4_K_M", "qwen2.5:1.5b-instruct-q8_0"]
PROMPTS = [
    {"tipo": "Corto (Definición)",
     "texto": "Explica en exactamente 3 viñetas qué es la cuantización de modelos de lenguaje."},
    {"tipo": "Medio (Razonamiento)",
     "texto": "Tengo un servidor con 16 GB de RAM y sin GPU. Quiero desplegar un asistente interno con un LLM. Explica qué arquitectura y qué nivel de cuantización recomiendas, y por qué."},
    {"tipo": "Largo (Generación de Código)",
     "texto": "Escribe una función en Python bien documentada que lea un archivo CSV, calcule el promedio de cada columna numérica y devuelva un diccionario. Incluye manejo de errores y un ejemplo de uso."},
]
OPTIONS = {"num_ctx": 2048, "temperature": 0}


def generar(model, prompt, options=OPTIONS):
    r = requests.post(URL, json={"model": model, "prompt": prompt, "stream": False,
                                 "options": options}, timeout=600)
    r.raise_for_status()
    return r.json()


rows, respuestas = [], []
for model in MODELS:
    print(f"Calentando {model}...")
    generar(model, "Hola", {**OPTIONS, "num_predict": 8})
    for p in PROMPTS:
        print(f"  {p['tipo']}")
        t0 = time.time()
        d = generar(model, p["texto"])
        total = time.time() - t0
        ttft = d["prompt_eval_duration"] / 1e6
        tps = d["eval_count"] / (d["eval_duration"] / 1e9)
        rows.append({"modelo": model, "prompt": p["tipo"],
                     "ttft_ms": round(ttft, 1), "tps": round(tps, 2),
                     "tokens_prompt": d["prompt_eval_count"],
                     "tokens_generados": d["eval_count"],
                     "total_s": round(total, 2)})
        respuestas.append((model, p["tipo"], d["response"]))

df = pd.DataFrame(rows)
df.to_csv("resultados_benchmark.csv", index=False)

with open("resultados_benchmark.md", "w", encoding="utf-8") as f:
    f.write("# Resultados Benchmark\n\n")
    f.write(df.to_markdown(index=False) + "\n\n")
    for model, tipo, texto in respuestas:
        f.write(f"## {model} - {tipo}\n\n{texto}\n\n")

print(df.to_markdown(index=False))