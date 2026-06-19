"""Mini server estático para previsualizar la PoC (evita os.getcwd, bloqueado por el sandbox)."""
import functools
from http.server import HTTPServer, SimpleHTTPRequestHandler

DIRECTORY = "/Users/kevinkovacs/Downloads/moav-hr 2/poc"
Handler = functools.partial(SimpleHTTPRequestHandler, directory=DIRECTORY)
HTTPServer(("127.0.0.1", 8731), Handler).serve_forever()
