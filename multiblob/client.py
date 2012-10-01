import logging
import optparse
import socket
import sys

from cogen.core import schedulers, sockets, coroutines
import pyglet

from multiblob import input, modes, state, window

class MultiblobApplication(object):
    udp_address = '0.0.0.0'
    udp_port = 5566

    network_interval = 0.05
    rule_interval = 0.05

    def __init__(self):
        pass

    def _setup_config(self, args):
        parser = optparse.OptionParser()
        parser.add_option("-d", "--debug", action="store_true", default=False,
                help="Turn on debug logging, defaults to false."
                )
        parser.add_option("-f", "--fullscreen", action="store_true", default=False,
                help="Run the game in fullscreen mode, defaults to false."
                )
        parser.add_option("-s", "--screen", type="int", default=0,
                help="Put the window on the given screen, defaults to 0, which is the first screen."
                )

        options, args = parser.parse_args(args)

        self.configuration = {
                'debug'      : options.debug,
                'fullscreen' : options.fullscreen,
                'screen'     : options.screen,
                }

    def _setup_logging(self):
        self.log = logging.getLogger()

        if self.configuration.get('debug', False):
            log_level = logging.DEBUG
        else:
            log_level = logging.ERROR

        logging.basicConfig(
                level = log_level
                )

    def _setup_state(self):
        self.log.info(u"Setting up game state...")
        self.state = state.GameState()
        #self.state.reset_simple()

    def _setup_input(self):
        self.log.info(u"Setting up input system...")
        self.input_system = input.InputSystem(self)

    def _setup_modes(self):
        self.log.info(u"Setting up game modes...")
        self.modes = {
                'intro' : modes.IntroMode(self),
                'main' : modes.MainMode(self),
                'outro' : modes.OutroMode(self),
                }

        self.set_mode('intro')

    def _setup_window(self):
        self.log.info(u"Setting up graphics context...")
        self.window = window.GameWindow(
                #                renderers = [
                #                    renderers.FacetRenderer(),
                #                    renderers.BlobsRenderer(),
                #                    renderers.DebugRenderer(),
                #                    ],
                #                state = self.state,
                application   = self,
                configuration = self.configuration,
                )
        self.mouse_simulator = input.MouseMultitouchSimulator(self.input_system)
        self.window.push_handlers(self.mouse_simulator)

        pyglet.clock.schedule_interval(self.update_rules, self.rule_interval)

        self.state.reset_simple()

    def _setup_resources(self):
        self.log.info(u"Setting up resources...")
        pyglet.resource.path.append('@multiblob.data')
        pyglet.resource.reindex()

    def _setup_network(self):
        self.log.info(u"Setting up networking...")
        self.runner = schedulers.Scheduler()
        self._runner_iter = self.runner.iter_run()
        pyglet.clock.schedule_interval(self._step_network, self.network_interval)

        self.log.info(u"Listening on port '%d'...", self.udp_port)
        self.udp_socket = sockets.Socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.bind((self.udp_address, self.udp_port))

    def update_rules(self, dt):
        if self.mode:
            self.mode.update_rules(dt)

    def _cleanup_network(self):
        self.log.info(u"Closing UDP socket...")
        self.udp_socket.close()

    def _step_network(self, dt):
        try:
            self._runner_iter.next()
        except StopIteration:
            self.runner.add(self._receive_udp)
            self._runner_iter = self.runner.iter_run()

    @coroutines.coro
    def _receive_udp(self):
        while True:
            data = yield self.udp_socket.recv(1024)
            self.log.debug(u"Received UDP data: '%s'.", data)
            self.input_system.parse_packet(data)

    def set_mode(self, mode_name):
        if mode_name in self.modes:
            if getattr(self, 'mode', False):
                self.mode.deactivate()
            self.mode = self.modes[mode_name]
            self.mode.activate()
        else:
            self.log.error(u"Failed to switch to mode '%s': No such mode known.", mode_name)

    def run(self, args=None):
        if args is None:
            args = sys.argv[1:]

        self._setup_config(args)
        self._setup_logging()
        self._setup_resources()
        self._setup_state()
        self._setup_input()
        self._setup_window()
        self._setup_modes()
        self._setup_network()

        self.log.info(u"Starting mainloop...")
        pyglet.app.run()
        self.log.info(u"Mainloop done, exiting...")

        self._cleanup_network()

        return 0

def main():
    app = MultiblobApplication()
    sys.exit(app.run())

if __name__ == '__main__':
    main()
