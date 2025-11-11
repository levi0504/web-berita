from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

berita_data = [
    {"judul": "Pemerintah Umumkan Kebijakan Baru", "isi": "Kebijakan terbaru diumumkan untuk meningkatkan ekonomi nasional."},
    {"judul": "Timnas Indonesia Menang Lagi!", "isi": "Timnas Indonesia berhasil menang melawan Malaysia dengan skor 3-1."},
    {"judul": "Teknologi AI Makin Canggih", "isi": "Perkembangan AI membuat banyak industri berubah secara signifikan."},
]

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "berita": berita_data})
