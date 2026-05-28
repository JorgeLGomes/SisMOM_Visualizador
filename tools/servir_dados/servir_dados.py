#!/usr/bin/env python3
"""
SisMOM - Servidor HTTP local de dados.

Serve uma pasta local em http://localhost:PORTA/ com headers CORS abertos
e MIME types corretos para os formatos do SisMOM (PNG, GIF, TIF, GeoJSON).

Uso:
  python servir_dados.py --dir /caminho/da/pasta --port 8765

Args:
  --dir, -d   pasta a servir (default: diretório atual)
  --port, -p  porta TCP (default: 8765)
  --bind, -b  interface (default: 127.0.0.1, só localhost)

Funciona em Safari, Firefox, Chrome, Edge — qualquer browser. Use no
template do modelo do SisMOM:
  http://localhost:8765/Eta3km/{yyyy}/{mm}/{dd}{hh}/
"""
import argparse
import http.server
import mimetypes
import os
import socketserver
import sys

# Mime types específicos do SisMOM (Python 3 às vezes não conhece .tif)
mimetypes.add_type('image/tiff', '.tif')
mimetypes.add_type('image/tiff', '.tiff')
mimetypes.add_type('application/json', '.geojson')


class CORSHandler(http.server.SimpleHTTPRequestHandler):
    """SimpleHTTPRequestHandler com headers CORS abertos."""

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    # Log mais limpo
    def log_message(self, fmt, *args):
        sys.stdout.write("  %s - %s\n" % (self.address_string(), fmt % args))
        sys.stdout.flush()


class ThreadingHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """TCPServer multi-thread + reuso de endereço (evita 'Address in use' após Ctrl+C)."""
    allow_reuse_address = True
    daemon_threads = True


def main():
    ap = argparse.ArgumentParser(
        description='GISELE - servidor HTTP local de dados',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument('--dir', '-d', default='.', help='Diretório raiz (default: atual)')
    ap.add_argument('--port', '-p', type=int, default=8765, help='Porta TCP (default: 8765)')
    ap.add_argument('--bind', '-b', default='127.0.0.1',
                    help='Interface (default: 127.0.0.1 = só localhost; "0.0.0.0" expõe na rede)')
    args = ap.parse_args()

    root = os.path.abspath(args.dir)
    if not os.path.isdir(root):
        print(f'ERRO: "{root}" não é um diretório.', file=sys.stderr)
        sys.exit(1)

    os.chdir(root)

    bar = '=' * 62
    print(bar)
    print(' GISELE — Servidor local de dados')
    print(bar)
    print(f' Diretório:  {root}')
    print(f' URL base:   http://localhost:{args.port}/')
    print(f' Interface:  {args.bind}  (127.0.0.1 = só esta máquina)')
    print(' CORS:       habilitado para qualquer origem')
    print('')
    print(' Use no template do modelo (Configurar > Editar):')
    print(f'   http://localhost:{args.port}/Eta3km/{{yyyy}}/{{mm}}/{{dd}}{{hh}}/')
    print('')
    print(' Ctrl+C para parar.')
    print(bar)

    try:
        with ThreadingHTTPServer((args.bind, args.port), CORSHandler) as srv:
            srv.serve_forever()
    except KeyboardInterrupt:
        print('\nServidor parado.')
    except OSError as e:
        msg = str(e).lower()
        if 'in use' in msg or getattr(e, 'errno', None) in (48, 98, 10048):
            print(f'\nERRO: porta {args.port} já está em uso. Use --port para outra.', file=sys.stderr)
            sys.exit(2)
        raise


if __name__ == '__main__':
    main()
