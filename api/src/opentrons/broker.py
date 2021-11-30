import logging
from typing import Callable, Dict, List
from typing_extensions import Literal

from opentrons.commands import types

MODULE_LOG = logging.getLogger(__name__)


class Broker:
    def __init__(self) -> None:
        self.subscriptions: Dict[
            Literal["command"],
            List[Callable[[types.CommandMessage], None]],
        ] = {}
        self.logger: logging.Logger = MODULE_LOG

    def subscribe(
        self,
        topic: Literal["command"],
        handler: Callable[[types.CommandMessage], None],
    ) -> Callable[[], None]:
        self.subscriptions.setdefault(topic, [])

        def unsubscribe() -> None:
            if handler in self.subscriptions[topic]:
                self.subscriptions[topic].remove(handler)

        if handler not in self.subscriptions[topic]:
            self.subscriptions[topic].append(handler)

        return unsubscribe

    def publish(self, topic: Literal["command"], message: types.CommandMessage) -> None:
        for handler in self.subscriptions.get(topic, []):
            handler(message)

    def set_logger(self, logger: logging.Logger) -> None:
        self.logger = logger
