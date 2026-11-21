# Petit serveur pour fabriquer les vidéos d'intro des projets.
# 1) Lancer depuis le dossier outils-atelier :  python3 portfolio/assets/projets/serveur-rendu.py
# 2) Ouvrir http://localhost:8795/portfolio/assets/projets/motion.html?p=tif&render (ajouter &f=v pour le téléphone)
#    et lancer window.render() dans la console : chaque image arrive dans le dossier « frames ».
# 3) ffmpeg -framerate 30 -i frames/%04d.jpg -c:v libx264 -crf 24 -preset slow -pix_fmt yuv420p -movflags +faststart tif.mp4
import http.server, os, sys
from urllib.parse import urlparse, parse_qs

OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else 'frames')
os.makedirs(OUT, exist_ok=True)

class H(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        qs = parse_qs(urlparse(self.path).query)
        n, d = int(qs['n'][0]), os.path.basename(qs.get('d', [''])[0])  # d = sous-dossier (un par vidéo)
        os.makedirs(os.path.join(OUT, d), exist_ok=True)
        with open(os.path.join(OUT, d, f'{n:04d}.jpg'), 'wb') as f:
            f.write(self.rfile.read(int(self.headers['Content-Length'])))
        self.send_response(204); self.end_headers()
    def log_message(self, *a): pass

http.server.ThreadingHTTPServer(('127.0.0.1', 8795), H).serve_forever()
