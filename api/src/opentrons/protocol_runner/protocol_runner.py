"""Protocol run control and management."""
from typing import Optional

from opentrons.protocol_engine import ProtocolEngine

from .protocol_file import ProtocolFile, ProtocolFileType
from .task_queue import TaskQueue, TaskQueuePhase
from .json_file_reader import JsonFileReader
from .json_command_translator import JsonCommandTranslator
from .python_file_reader import PythonFileReader
from .python_context_creator import PythonContextCreator
from .python_executor import PythonExecutor


class ProtocolRunner:
    """An interface to manage and control a protocol run.

    The ProtocolRunner is primarily responsible for feeding a ProtocolEngine
    with commands and control signals. These commands and signals are
    generated by protocol files, hardware signals, or externally via
    the HTTP robot-server.

    A ProtocolRunner controls a single run. Once the run is finished,
    you will need a new ProtocolRunner to do another run.
    """

    def __init__(
        self,
        protocol_engine: ProtocolEngine,
        task_queue: Optional[TaskQueue] = None,
        json_file_reader: Optional[JsonFileReader] = None,
        json_command_translator: Optional[JsonCommandTranslator] = None,
        python_file_reader: Optional[PythonFileReader] = None,
        python_context_creator: Optional[PythonContextCreator] = None,
        python_executor: Optional[PythonExecutor] = None,
    ) -> None:
        """Initialize the ProtocolRunner with its dependencies."""
        self._protocol_engine = protocol_engine
        self._task_queue = task_queue or TaskQueue()
        self._json_file_reader = json_file_reader or JsonFileReader()
        self._json_command_translator = (
            json_command_translator or JsonCommandTranslator()
        )
        self._python_file_reader = python_file_reader or PythonFileReader()
        self._python_context_creator = python_context_creator or PythonContextCreator()
        self._python_executor = python_executor or PythonExecutor()

    def load(self, protocol_file: ProtocolFile) -> None:
        """Load a ProtocolFile into managed ProtocolEngine.

        Calling this method is only necessary if the runner will be used
        to control the run of a file-based protocol.
        """
        file_type = protocol_file.file_type

        if file_type == ProtocolFileType.JSON:
            self._load_json(protocol_file)

        elif file_type == ProtocolFileType.PYTHON:
            self._load_python(protocol_file)

    def play(self) -> None:
        """Start or resume the run."""
        self._protocol_engine.play()

        if not self._task_queue.is_started():
            self._task_queue.add(
                phase=TaskQueuePhase.CLEANUP,
                func=self._protocol_engine.stop,
                wait_until_complete=True,
            )
            self._task_queue.start()

    def pause(self) -> None:
        """Pause the run."""
        self._protocol_engine.pause()

    async def stop(self) -> None:
        """Stop (cancel) the run."""
        await self._protocol_engine.halt()

    async def join(self) -> None:
        """Wait for the run to complete, propagating any errors.

        This method may be called before the run starts, in which case,
        it will wait for the run to start before waiting for completion.
        """
        return await self._task_queue.join()

    def _load_json(self, protocol_file: ProtocolFile) -> None:
        protocol = self._json_file_reader.read(protocol_file)
        commands = self._json_command_translator.translate(protocol)
        for request in commands:
            self._protocol_engine.add_command(request=request)

    def _load_python(self, protocol_file: ProtocolFile) -> None:
        protocol = self._python_file_reader.read(protocol_file)
        context = self._python_context_creator.create(self._protocol_engine)
        self._task_queue.add(
            phase=TaskQueuePhase.RUN,
            func=self._python_executor.execute,
            protocol=protocol,
            context=context,
        )
