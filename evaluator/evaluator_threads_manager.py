import logging

from config.cst import *
from evaluator.evaluator import Evaluator


class EvaluatorThreadsManager:
    def __init__(self, config,
                 symbol,
                 time_frame,
                 symbol_time_frame_updater_thread,
                 symbol_evaluator,
                 exchange,
                 real_time_ta_eval_list):
        self.config = config
        self.exchange = exchange
        self.symbol = symbol
        self.time_frame = time_frame
        self.symbol_time_frame_updater_thread = symbol_time_frame_updater_thread
        self.symbol_evaluator = symbol_evaluator

        # notify symbol evaluator
        self.symbol_evaluator.add_evaluator_thread_manager(self.exchange, self.symbol, self.time_frame, self)

        self.matrix = self.symbol_evaluator.get_matrix(self.exchange)

        # Exchange
        # TODO : self.exchange.update_balance(self.symbol)

        self.thread_name = "TA THREAD MANAGER - {0} - {1} - {2}".format(self.symbol,
                                                                        self.exchange.get_name(),
                                                                        self.time_frame)
        self.logger = logging.getLogger(self.thread_name)

        # Create Evaluator
        self.evaluator = Evaluator()
        self.evaluator.set_config(self.config)
        self.evaluator.set_symbol(self.symbol)
        self.evaluator.set_time_frame(self.time_frame)
        self.evaluator.set_exchange(self.exchange)
        self.evaluator.set_symbol_evaluator(self.symbol_evaluator)

        # Add threaded evaluators that can notify the current thread
        self.evaluator.set_social_eval(self.symbol_evaluator.get_crypto_currency_evaluator().get_social_eval_list(), self)
        self.evaluator.set_real_time_eval(real_time_ta_eval_list, self)

        # Create static evaluators
        self.evaluator.set_ta_eval_list(self.evaluator.get_creator().create_ta_eval_list(self.evaluator))

        # Register in refreshing threads
        self.symbol_time_frame_updater_thread.register_evaluator_thread_manager(self.time_frame, self)

    def get_refreshed_times(self):
        return self.symbol_time_frame_updater_thread.get_refreshed_times(self.time_frame)

    def get_evaluator(self):
        return self.evaluator

    def notify(self, notifier_name):
        if self.get_refreshed_times() > 0:
            self.logger.debug("** Notified by {0} **".format(notifier_name))
            self._refresh_eval(notifier_name)
        else:
            self.logger.debug("Notification by {0} ignored".format(notifier_name))

    def _refresh_eval(self, ignored_evaluator=None):
        # update eval
        self.evaluator.update_ta_eval(ignored_evaluator)

        # update matrix
        self._refresh_matrix()

        # update strategies matrix
        self.symbol_evaluator.update_strategies_eval(self.matrix, self.exchange, ignored_evaluator)

        # calculate the final result
        self.symbol_evaluator.finalize(self.exchange)
        self.logger.debug("MATRIX : {0}".format(self.matrix.get_matrix()))

    def _refresh_matrix(self):
        self.matrix = self.symbol_evaluator.get_matrix(self.exchange)

        for ta_eval in self.evaluator.get_ta_eval_list():
            ta_eval.ensure_eval_note_is_not_expired()
            self.matrix.set_eval(EvaluatorMatrixTypes.TA, ta_eval.get_name(),
                                 ta_eval.get_eval_note(), self.time_frame)

        for social_eval in self.evaluator.get_social_eval_list():
            social_eval.ensure_eval_note_is_not_expired()
            self.matrix.set_eval(EvaluatorMatrixTypes.SOCIAL, social_eval.get_name(),
                                 social_eval.get_eval_note(), None)

        for real_time_eval in self.evaluator.get_real_time_eval_list():
            real_time_eval.ensure_eval_note_is_not_expired()
            self.matrix.set_eval(EvaluatorMatrixTypes.REAL_TIME, real_time_eval.get_name(),
                                 real_time_eval.get_eval_note())

    def start_threads(self):
        pass

    def stop_threads(self):
        for thread in self.evaluator.get_real_time_eval_list():
            thread.stop()

    def join_threads(self):
        for thread in self.evaluator.get_real_time_eval_list():
            thread.join()

    def get_symbol_time_frame_updater_thread(self):
        return self.symbol_time_frame_updater_thread

    def get_exchange(self):
        return self.exchange
