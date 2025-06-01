# tests/test_metrics_collector.py

import unittest
from unittest.mock import MagicMock, patch
from worker.metrics_collector import MetricsCollector
from worker.config import Config

class TestMetricsCollector(unittest.TestCase):
    @patch("worker.metrics_collector.redis.Redis")
    @patch("worker.metrics_collector.docker.DockerClient")
    @patch("worker.metrics_collector.requests.post")
    def test_send_heartbeat_and_metrics(self, mock_post, mock_docker, mock_redis):
        # Set up Redis mock
        redis_instance = mock_redis.return_value
        # Set up Docker mock: no running containers initially
        docker_instance = mock_docker.return_value
        docker_instance.containers.get.side_effect = Exception("not found")
        
        running = set()
        queue = []
        collector = MetricsCollector(running, queue)
        # Override real Docker and Redis with mocks
        collector.client = docker_instance
        collector.redis = redis_instance

        # Simulate one iteration of run()
        collector._send_heartbeat()
        # Redis.set should be called
        redis_instance.set.assert_called_with(f"heartbeat:{Config.HOST_ID}", unittest.mock.ANY, ex=2 * Config.POLL_INTERVAL)

        docker_instance.containers.get.assert_not_called()  # no containers to fetch

        # Simulate metric POST error
        mock_post.return_value.ok = False
        mock_post.return_value.status_code = 500
        collector._collect_and_send_metrics()
        # Should record an error in the queue
        self.assertTrue(any("Metrics POST failure" in msg for msg in queue))

if __name__ == "__main__":
    unittest.main()