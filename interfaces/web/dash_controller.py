from dash.dependencies import Output, Event, Input

import dash_core_components as dcc
import dash_html_components as html
import dash_table_experiments as dt

from config.cst import EvaluatorMatrixTypes, CONFIG_CRYPTO_CURRENCIES, CONFIG_CRYPTO_PAIRS, CONFIG_TIME_FRAME
from interfaces.web import app_instance, global_config
from interfaces.web.bot_data_model import *


@app_instance.callback(Output('tab-output', 'children'),
              [Input('tabs', 'value')])
def display_content(value):
    print(value)
    if value == 1:
        return html.Div([
                    html.Div([
                        dcc.Graph(id='portfolio-value-graph', animate=True),
                        dcc.Interval(
                            id='portfolio-update',
                            interval=1 * 1000
                        ),
                        # dt.DataTable(
                        #     rows=[{}],
                        #     row_selectable=False,
                        #     filterable=True,
                        #     sortable=True,
                        #     editable=False,
                        #     selected_row_indices=[],
                        #     id='datatable-portfolio'
                        # ),
                    ],
                    style={'columnCount': 1, 'marginLeft': 25, 'marginRight': 25, 'marginTop': 25, 'marginBottom': 25}
                    )
                ]
            )
    elif value == 2:
        return html.Div([
                    html.Div([
                        html.Label('Exchange'),
                        dcc.Dropdown(id='exchange-name',
                                     options=[{'label': s, 'value': s}
                                              for s in get_bot().get_exchanges_list().keys()],
                                     value=next(iter(get_bot().get_exchanges_list().keys())),
                                     multi=False,
                                     ),
                        html.Label('Currency'),
                        dcc.Dropdown(id='cryptocurrency-name',
                                     options=[{'label': s, 'value': s}
                                              for s in global_config[CONFIG_CRYPTO_CURRENCIES].keys()],
                                     value=next(iter(global_config[CONFIG_CRYPTO_CURRENCIES].keys())),
                                     multi=False,
                                     ),
                        html.Label('Symbol'),
                        dcc.Dropdown(id='symbol',
                                     options=[],
                                     value="BTC/USDT",
                                     multi=False,
                                     ),
                        html.Label('TimeFrame'),
                        dcc.Dropdown(id='time-frame',
                                     options=[],
                                     value=None,
                                     multi=False,
                                     ),
                        html.Label('Evaluator'),
                        dcc.Dropdown(id='evaluator-name',
                                     options=[],
                                     value="TempFullMixedStrategiesEvaluator",
                                     multi=False,
                                     ),
                        ],
                        style={'columnCount': 1, 'marginLeft': 25, 'marginRight': 25, 'marginTop': 25, 'marginBottom': 25}
                    ),
                    dcc.Graph(id='live-graph', animate=True),
                    dcc.Interval(
                        id='strategy-graph-update',
                        interval=1 * 1000
                    ),
                    dcc.Graph(id='strategy-live-graph', animate=True),
                    dcc.Interval(
                        id='graph-update',
                        interval=60 * 1000
                    )
                ]
            )


@app_instance.callback(Output('live-graph', 'figure'),
                       [Input('exchange-name', 'value'),
                        Input('cryptocurrency-name', 'value'),
                        Input('symbol', 'value'),
                        Input('time-frame', 'value')],
                       events=[Event('graph-update', 'interval')])
def update_values(exchange_name, cryptocurrency_name, symbol, time_frame):
    if exchange_name:
        return get_currency_graph_update(exchange_name,
                                         get_value_from_dict_or_string(symbol),
                                         get_value_from_dict_or_string(time_frame, True),
                                         cryptocurrency_name)
    return []


@app_instance.callback(Output('strategy-live-graph', 'figure'),
                       [Input('exchange-name', 'value'),
                        Input('cryptocurrency-name', 'value'),
                        Input('symbol', 'value'),
                        Input('time-frame', 'value'),
                        Input('evaluator-name', 'value')],
                       events=[Event('strategy-graph-update', 'interval')])
def update_strategy_values(exchange_name, cryptocurrency_name, symbol, time_frame, evaluator_name):
    if exchange_name:
        return get_evaluator_graph_in_matrix_history(get_value_from_dict_or_string(symbol),
                                                     exchange_name,
                                                     EvaluatorMatrixTypes.STRATEGIES,
                                                     evaluator_name,
                                                     get_value_from_dict_or_string(time_frame, True),
                                                     cryptocurrency_name)
    return []


@app_instance.callback(Output('portfolio-value-graph', 'figure'),
                       events=[Event('portfolio-update', 'interval')])
def update_portfolio_value():
    print("update_portfolio_value")
    return get_portfolio_value_in_history()


@app_instance.callback(Output('datatable-portfolio', 'rows'),
                       [Input('portfolio-value-graph', 'figure')])
def update_currencies_amounts():
    print("update_currencies_amounts")
    return get_portfolio_currencies_update()


@app_instance.callback(Output('symbol', 'options'),
                       [Input('exchange-name', 'value'),
                        Input('cryptocurrency-name', 'value')])
def update_symbol_dropdown_options(exchange_name, cryptocurrency_name):
    if exchange_name:
        exchange = get_bot().get_exchanges_list()[exchange_name]
        symbol_list = []

        for symbol in global_config[CONFIG_CRYPTO_CURRENCIES][cryptocurrency_name][CONFIG_CRYPTO_PAIRS]:
            if exchange.symbol_exists(symbol):
                symbol_list.append({
                    "label": symbol,
                    "value": symbol
                })

        return symbol_list
    return None


@app_instance.callback(Output('symbol', 'value'),
                       [Input('exchange-name', 'value'),
                        Input('cryptocurrency-name', 'value')])
def update_symbol_dropdown_value(exchange_name, cryptocurrency_name):
    if exchange_name:
        exchange = get_bot().get_exchanges_list()[exchange_name]

        for symbol in global_config[CONFIG_CRYPTO_CURRENCIES][cryptocurrency_name][CONFIG_CRYPTO_PAIRS]:
            if exchange.symbol_exists(symbol):
                return {
                    "label": symbol,
                    "value": symbol
                }

    return None


@app_instance.callback(Output('time-frame', 'options'),
                       [Input('exchange-name', 'value'),
                        Input('symbol', 'value')])
def update_time_frame_dropdown_options(exchange_name, symbol):
    if exchange_name:
        exchange = get_bot().get_exchanges_list()[exchange_name]

        time_frame_list = []
        for time_frame in global_config[CONFIG_TIME_FRAME]:
            if exchange.time_frame_exists(TimeFrames(time_frame).value):
                time_frame_list.append({
                    "label": time_frame,
                    "value": time_frame
                })
        return time_frame_list
    return []


@app_instance.callback(Output('time-frame', 'value'),
                       [Input('exchange-name', 'value'),
                        Input('symbol', 'value')])
def update_time_frame_dropdown_options(exchange_name, symbol):
    if exchange_name:
        exchange = get_bot().get_exchanges_list()[exchange_name]

        for time_frame in global_config[CONFIG_TIME_FRAME]:
            if exchange.time_frame_exists(TimeFrames(time_frame).value):
                return {
                    "label": time_frame,
                    "value": time_frame
                }
    return None


@app_instance.callback(Output('evaluator-name', 'options'),
                       [Input('cryptocurrency-name', 'value'),
                        Input('exchange-name', 'value'),
                        Input('symbol', 'value'),
                        Input('time-frame', 'value')])
def update_evaluator_dropdown(cryptocurrency_name, exchange_name, symbol, time_frame):
    if symbol:
        symbol_evaluator = get_bot().get_symbol_evaluator_list()[get_value_from_dict_or_string(symbol)]
        exchange = get_bot().get_exchanges_list()[exchange_name]

        evaluator_list = []
        evaluator_name_list = []
        for strategies in symbol_evaluator.get_strategies_eval_list(exchange):
            if strategies.get_name() not in evaluator_name_list:
                evaluator_name_list.append(strategies.get_name())
                evaluator_list.append({
                    "label": strategies.get_name(),
                    "value": strategies.get_name()
                })

        return evaluator_list
    return []
