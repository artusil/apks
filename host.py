"""Start the self-hosted hubsoc application (not the GitHub Pages edition)."""
import argparse
import os

from waitress import serve


def main():
    parser = argparse.ArgumentParser(description='HTTP-сервер hubsoc')
    parser.add_argument('--host', default='0.0.0.0')
    parser.add_argument('--port', type=int, default=os.getenv('PORT', '8000'))
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error('порт должен быть от 1 до 65535')
    from app import app
    serve(app, host=args.host, port=args.port, max_request_body_size=app.config['MAX_CONTENT_LENGTH'])


if __name__ == '__main__':
    main()
