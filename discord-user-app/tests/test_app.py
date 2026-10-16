import unittest
from unittest.mock import AsyncMock, Mock

import discord

from app import App, Run


def interaction(user_id=123):
    value = Mock()
    value.user.id = user_id
    value.response.send_message = AsyncMock()
    value.followup.send = AsyncMock()
    value.edit_original_response = AsyncMock()
    return value


class AppTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.app = App()

    async def asyncTearDown(self):
        await self.app.close()

    async def test_user_install_and_count_limits(self):
        commands = self.app.tree.get_commands()
        self.assertEqual({c.name for c in commands}, {"repeat", "stop"})
        payload = commands[0].to_dict(self.app.tree)
        self.assertEqual(payload["integration_types"], [1])
        self.assertEqual(set(payload["contexts"]), {0, 1, 2})
        count = next(p for p in payload["options"] if p["name"] == "count")
        self.assertEqual((count["min_value"], count["max_value"]), (1, 5))

    async def test_five_messages_and_private_status(self):
        value = interaction()
        await self.app.repeat(value, "hello", 5)
        self.assertEqual(value.followup.send.await_count, 5)
        self.assertFalse(value.followup.send.call_args.kwargs["ephemeral"])
        self.assertEqual(value.followup.send.call_args.kwargs["allowed_mentions"].to_dict()["parse"], [])
        value.edit_original_response.assert_awaited_once_with(content="Completed: 5/5 messages sent.")
        self.assertFalse(self.app.runs)

    async def test_stop_during_send(self):
        value = interaction()
        async def stop_during_send(*args, **kwargs):
            await self.app.stop(interaction())
        value.followup.send.side_effect = stop_during_send
        await self.app.repeat(value, "hello", 5)
        self.assertEqual(value.followup.send.await_count, 1)
        value.edit_original_response.assert_awaited_once_with(content="Stopped: 1/5 messages sent.")
        self.assertFalse(self.app.runs)

    async def test_other_users_can_repeat(self):
        value = interaction(456)
        await self.app.repeat(value, "hello", 5)
        self.assertEqual(value.followup.send.await_count, 5)

    async def test_stop_only_affects_callers_run(self):
        first, second = Run(), Run()
        self.app.runs.update({123: first, 456: second})
        await self.app.stop(interaction(456))
        self.assertFalse(first.stop.is_set())
        self.assertTrue(second.stop.is_set())

    async def test_different_users_can_run_independently(self):
        value, second = interaction(), interaction(456)
        async def start_second(*args, **kwargs):
            await self.app.repeat(second, "friend", 1)
        value.followup.send.side_effect = start_second
        await self.app.repeat(value, "hello", 1)
        second.followup.send.assert_awaited_once()
        self.assertFalse(self.app.runs)

    async def test_no_overlapping_runs(self):
        value = interaction()
        second = interaction()
        async def try_overlap(*args, **kwargs):
            await self.app.repeat(second, "other", 1)
        value.followup.send.side_effect = try_overlap
        await self.app.repeat(value, "hello", 1)
        second.followup.send.assert_not_awaited()
        self.assertFalse(self.app.runs)

    async def test_unexpected_failure_cleans_up(self):
        value = interaction()
        value.followup.send.side_effect = RuntimeError("test")
        with self.assertRaises(RuntimeError):
            await self.app.repeat(value, "hello", 1)
        self.assertFalse(self.app.runs)

    async def test_discord_error_stops_without_retry(self):
        value = interaction()
        response = Mock(status=403, reason="Forbidden")
        value.followup.send.side_effect = discord.Forbidden(response, {"code": 50013, "message": "Missing Permissions"})
        await self.app.repeat(value, "hello", 5)
        self.assertEqual(value.followup.send.await_count, 1)
        value.edit_original_response.assert_awaited_once_with(
            content="Stopped after a Discord error (HTTP 403, code 50013): 0/5 messages sent.")
        self.assertFalse(self.app.runs)
