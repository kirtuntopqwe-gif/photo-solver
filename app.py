import os
from flask import Flask, request, jsonify, render_template_string
from google import genai
from PIL import Image

app = Flask(__name__)

# Ключ теперь безопасно берётся из настроек сервера
client = genai.Client(api_key=os.environ.get("AQ.Ab8RN6K8_f1k7JK13mocHkbM4K6xIrVF5_zxfjOqgCzpsqzDvg"))

HTML_PAGE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Решатель задач</title>
    <script>window.MathJax = { tex: { inlineMath: [['$', '$'], ['\\\\(', '\\\\)']] } };</script>
    <script async src="https://jsdelivr.net"></script>
    <script src="https://jsdelivr.net"></script>
    <style>
        body { font-family: sans-serif; max-width: 600px; margin: 20px auto; padding: 15px; background: #f0f2f5; }
        .card { background: white; padding: 20px; border-radius: 16px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); text-align: center; }
        .btn { display: block; background: #2563eb; color: white; padding: 15px; border-radius: 12px; font-size: 16px; font-weight: bold; cursor: pointer; border: none; width: 100%; box-sizing: border-box; margin-top: 10px; }
        input[type="file"] { display: none; }
        #preview { max-width: 100%; max-height: 300px; border-radius: 10px; margin-top: 15px; display: none; }
        #result { text-align: left; margin-top: 20px; line-height: 1.6; display: none; }
    </style>
</head>
<body>
    <div class="card">
        <h2>📸 Решить задачу по фото</h2>
        <label class="btn">
            📷 Сфоткать / Выбрать фото
            <input type="file" id="photoInput" accept="image/*" capture="environment">
        </label>
        <img id="preview">
        <button id="solveBtn" class="btn" style="background: #16a34a; display: none;">✨ Решить</button>
        <p id="status" style="display:none; color: #555;">Думаю над задачей...</p>
        <div id="result"></div>
    </div>

    <script>
        const photoInput = document.getElementById('photoInput');
        const preview = document.getElementById('preview');
        const solveBtn = document.getElementById('solveBtn');
        const statusText = document.getElementById('status');
        const resultDiv = document.getElementById('result');

        photoInput.addEventListener('change', (e) => {
            const file = e.target.files.item(0);
            if (file) {
                preview.src = URL.createObjectURL(file);
                preview.style.display = 'inline-block';
                solveBtn.style.display = 'block';
                resultDiv.style.display = 'none';
            }
        });

        solveBtn.addEventListener('click', async () => {
            const file = photoInput.files.item(0);
            if (!file) return;

            const formData = new FormData();
            formData.append('photo', file);

            solveBtn.disabled = true;
            statusText.style.display = 'block';
            resultDiv.style.display = 'none';

            try {
                const res = await fetch('/solve', { method: 'POST', body: formData });
                const data = await res.json();
                resultDiv.innerHTML = data.error ? `<b style="color:red">Ошибка: ${data.error}</b>` : marked.parse(data.solution);
                if (!data.error && window.MathJax) MathJax.typesetPromise([resultDiv]);
                resultDiv.style.display = 'block';
            } catch (err) {
                resultDiv.innerHTML = `<b style="color:red">Ошибка сети: ${err.message}</b>`;
                resultDiv.style.display = 'block';
            } finally {
                solveBtn.disabled = false;
                statusText.style.display = 'none';
            }
        });
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_PAGE)

@app.route("/solve", methods=["POST"])
def solve():
    file = request.files.get("photo")
    if not file:
        return jsonify({"error": "Фото не выбрано"}), 400
    try:
        image = Image.open(file.stream)
        prompt = "Реши задачу на фото подробно по шагам. Формулы пиши в LaTeX ($...$). В конце выдели ответ."
        response = client.models.generate_content(
            model="gemini-4-hydrogen",
            contents=(image, prompt),
        )
        return jsonify({"solution": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
