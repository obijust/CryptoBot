import copy
import logging
import numpy
import time

import dash
import flask
import pandas

server_instance = flask.Flask(__name__)
app_instance = dash.Dash(__name__, sharing=True, server=server_instance, url_base_pathname='/dashboard')

# disable Flask logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

matrix_history = []
symbol_data_history = {}
portfolio_value_history = {
    "real_value": [],
    "simulated_value": [],
    "timestamp": []
}

TIME_AXIS_TITLE = "Time"


def add_to_matrix_history(matrix):
    matrix_history.append({
        "matrix": copy.deepcopy(matrix.get_matrix()),
        "timestamp": time.time()
    })


def add_to_portfolio_value_history(real_value, simulated_value):
    portfolio_value_history["real_value"].append(real_value)
    portfolio_value_history["simulated_value"].append(simulated_value)
    portfolio_value_history["timestamp"].append(time.time())


def add_to_symbol_data_history(symbol, data, time_frame):
    if symbol not in symbol_data_history:
        symbol_data_history[symbol] = {}

    if time_frame not in symbol_data_history[symbol]:
        symbol_data_history[symbol][time_frame] = data

    symbol_data_history[symbol][time_frame] = pandas.concat([symbol_data_history[symbol][time_frame], data])
    symbol_data_history[symbol][time_frame] = symbol_data_history[symbol][time_frame].reset_index(drop=True)


def get_matrix_history():
    return matrix_history


def get_portfolio_value_history():
    return portfolio_value_history


def get_symbol_data_history(symbol, time_frame):
    return symbol_data_history[symbol][time_frame]


def load_callbacks():
    from .dash_controller import update_values, \
        update_strategy_values, \
        update_time_frame_dropdown_options, \
        update_symbol_dropdown_options, \
        update_symbol_dropdown_value, \
        update_evaluator_dropdown_options, \
        update_evaluator_dropdown_values, \
        update_currencies_amounts, \
        update_portfolio_value


def load_routes():
    from .flask_controller import index
