"""Safely pass values between threads and async tasks."""

from collections import deque
from contextlib import contextmanager
from threading import Condition
from typing import Deque, Generic, TypeVar, Generator

from anyio.to_thread import run_sync


_T = TypeVar("_T")


class ThreadAsyncQueue(Generic[_T]):
    """A queue to safely pass values of type `_T` between threads and async tasks.

    All methods are safe to call concurrently from any thread or task.

    Unlike queue.Queue, this class supports
    a `done_putting()` method to make common producer/consumer patterns easier,
    and a `get_async()` method to support async consumers.

    Unlike asyncio.Queue and AnyIO memory object streams,
    you can use this class to communicate between async tasks and threads
    without the threads having to wait for the event loop to be free
    every time they access the queue.
    """

    def __init__(self) -> None:
        """Initialize the queue."""
        self._is_closed = False
        self._deque: Deque[_T] = deque()
        self._condition = Condition()

    def put(self, value: _T) -> None:
        """Add a value to the back of the queue.

        Returns immediately, without blocking. The queue can grow without bound.

        Raises:
            QueueClosed: If `done_putting()` has already been called.
        """
        with self._condition:
            if self._is_closed:
                raise QueueClosed("Can't add more values when queue is already closed.")
            else:
                self._deque.append(value)
                self._condition.notify()

    def done_putting(self) -> None:
        """Signal that no more values will be `put()`, closing the queue.

        If other threads or tasks are calling `get()`,
        you probably have to call `done_putting()` eventually,
        to let them know when they can stop waiting.
        Forgetting to call `done_putting()` can leave them waiting forever.
        Consider using `with putting()` to make this easier.

        Raises:
            QueueClosed: If `done_putting()` has already been called.
                Wanting to close the queue more than once can suggest a structural
                problem,
                prone to race conditions depending on what closes the queue first.
                (This opinion is also held by Golang in its channel API.)
        """
        with self._condition:
            if self._is_closed:
                raise QueueClosed("Can't close when queue is already closed.")
            else:
                self._is_closed = True
                self._condition.notify_all()

    @contextmanager
    def putting(self) -> Generator[None, None, None]:
        """Return a context manager that, when exited, calls `done_putting()`."""  # noqa: D402,E501
        try:
            yield
        finally:
            self.done_putting()

    def get(self) -> _T:
        """Remove and return the value at the front of the queue.

        If the queue is empty, block until a value is available.
        If you're calling from an async task, use `get_async()` instead.

        Raises:
            QueueClosed: If `done_putting()` has been called.
                If any values were in the queue when `done_putting()` was called,
                this will raise only after those values have been retrieved.
        """
        with self._condition:
            while True:
                if len(self._deque) > 0:
                    return self._deque.popleft()
                elif self._is_closed:
                    raise QueueClosed("Queue closed; no more items to get.")
                else:
                    # We don't have anything to return.
                    # Wait for something to change, then check again.
                    self._condition.wait()

    async def get_async(self) -> _T:
        """Like `get()`, except yield to the event loop while waiting.

        Warning:
            A waiting `get_async()` won't be interrupted by an async cancellation.
            The proper way to interrupt a waiting `get_async()` is to close the queue,
            just like you have to do with `get()`.
        """
        return await run_sync(
            self.get,
            # We keep `cancellable` False so we don't leak this helper thread.
            # If we made it True, an async cancellation here would detach us
            # from the helper thread and allow the thread to "run to completion"--
            # but if no more values are ever enqueued, and the queue is never closed,
            # completion would never happen and it would hang around forever.
            cancellable=False,
        )


class QueueClosed(Exception):
    """See `ThreadAsyncQueue.done_putting()`."""

    pass
