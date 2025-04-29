from flask_cors import CORS

def configure_cors(app):
    """
    Configura CORS para la aplicación Flask con opciones avanzadas
    que permiten el acceso desde cualquier origen.
    """
    cors_options = {
        'origins': '*',
        'methods': ['GET', 'POST', 'OPTIONS'],
        'allow_headers': [
            'Content-Type', 
            'Authorization', 
            'X-Requested-With',
            'Access-Control-Allow-Origin',
            'Origin'
        ],
        'expose_headers': [
            'Content-Type',
            'Content-Length',
            'Access-Control-Allow-Origin'
        ],
        'supports_credentials': True,
        'max_age': 3600
    }
    
    CORS(app, **cors_options)
    
    # Configuración adicional para asegurar que CORS funcione correctamente
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        return response
    
    return app
