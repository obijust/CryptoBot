import logging
import threading

import dash_core_components as dcc
import dash_html_components as html
import dash_table_experiments as dt
from flask import request

from config.cst import CONFIG_CRYPTO_CURRENCIES
from interfaces.web import app_instance, load_callbacks, get_bot, load_routes


class WebApp(threading.Thread):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        self.app = None

    def run(self):

        # Define the WSGI application object
        self.app = app_instance
        self.app.config['suppress_callback_exceptions']=True

        self.app.layout = html.Div([
                dcc.Tabs(
                    tabs=[
                        {'label': 'Portfolio', 'value': 1},
                        {'label': 'Trading', 'value': 2}
                    ],
                    value=1,
                    id='tabs',
                    vertical=False
                ),
                html.Div(id='tab-output'),

            ], style={
                'width': '80%',
                'fontFamily': 'Sans-Serif',
                'margin-left': 'auto',
                'margin-right': 'auto'
            })
        load_callbacks()
        load_routes()
        self.app.run_server(host='0.0.0.0',
                            port=5000,
                            debug=False,
                            threaded=True)

    def stop(self):
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            self.logger.warning("Not running with the Werkzeug Server")
        func()
