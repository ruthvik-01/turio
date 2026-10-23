"""Windows API-loop browser dispatch without employer traffic."""
import asyncio
import sys
import threading
import pytest

pytestmark = pytest.mark.skipif(sys.platform != 'win32', reason='Windows event-loop compatibility')


def test_browser_subprocess_and_callbacks_use_compatible_loops():
    from app.adapters.ashby import browser_operation
    async def scenario():
        owner=asyncio.get_running_loop()
        async def callback(*args):
            assert asyncio.get_running_loop() is owner
            return 'owned'
        class Adapter:
            load_resume=staticmethod(callback)
            authorize=staticmethod(callback)
            @browser_operation
            async def operation(self):
                assert isinstance(asyncio.get_running_loop(),asyncio.ProactorEventLoop)
                assert await self.load_resume('resume')=='owned'
                assert await self.authorize({})=='owned'
                process=await asyncio.create_subprocess_exec(sys.executable,'-c','pass')
                assert await process.wait()==0
                return 'complete'
        assert await Adapter().operation()=='complete'
    with asyncio.Runner(loop_factory=asyncio.SelectorEventLoop) as runner:runner.run(scenario())


def test_cancellation_waits_for_browser_cleanup():
    from app.adapters.ashby import browser_operation
    started,cleaned=threading.Event(),threading.Event()
    async def scenario():
        class Adapter:
            load_resume=None
            authorize=None
            @browser_operation
            async def operation(self):
                started.set()
                try:await asyncio.Event().wait()
                finally:cleaned.set()
        operation=asyncio.create_task(Adapter().operation())
        assert await asyncio.to_thread(started.wait,5)
        operation.cancel()
        with pytest.raises(asyncio.CancelledError):await operation
        assert cleaned.is_set()
    with asyncio.Runner(loop_factory=asyncio.SelectorEventLoop) as runner:runner.run(scenario())
