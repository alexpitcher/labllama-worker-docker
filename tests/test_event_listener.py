# tests/test_event_listener.py

import unittest
from unittest.mock import MagicMock, patch
from worker.event_listener import EventListener

class DummyClient:
    def __init__(self, events):
        self._events = events
    def events(self, decode, filters):
        yield from self._events

class TestEventListener(unittest.TestCase):
    @patch("worker.event_listener.docker.DockerClient")
    def test_container_start_and_die(self, mock_docker_client):
        # Prepare fake Docker events
        fake_events = [
            {"status": "start", "id": "cid123", "time": 1620000000,
             "Actor": {"Attributes": {"name": "testapp", "exitCode": ""}}},
            {"status": "die", "id": "cid123", "time": 1620000010,
             "Actor": {"Attributes": {"name": "testapp", "exitCode": "0"}}}
        ]
        # Make DockerClient().events() return our fake events
        instance = mock_docker_client.return_value
        instance.events.return_value = iter(fake_events)

        running = set()
        listener = EventListener(running)
        # Override the client with our dummy
        listener.client = DummyClient(fake_events)
        # Run one iteration
        listener.run()
        
        # After events, running should not contain "cid123"
        self.assertNotIn("cid123", running)

if __name__ == "__main__":
    unittest.main()