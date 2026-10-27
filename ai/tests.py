"""AI boundary tests: synthetic identities, mocked Groq, no database access."""
from types import SimpleNamespace
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, Mock, patch

from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import AnonymousUser
from django.test import SimpleTestCase, override_settings
from rest_framework_simplejwt.tokens import AccessToken

from ai import agent, nodes, orchestrator
from ai.service import AIDataAccessDisabled, PROTECTED_OPERATION_UNAVAILABLE, execute_sql
from apps.core.websocketauth import JwtWebSocketAuthMiddleware
from config.consumers import AIChatConsumer


def principal(active=True):
    return SimpleNamespace(is_authenticated=True, is_active=active)


class AssistantRoutingTests(SimpleTestCase):
    def model(self, intent="general", answer="General knowledge answer."):
        model = Mock()
        model.invoke.side_effect = [SimpleNamespace(content=intent), SimpleNamespace(content=answer)]
        return model

    def test_general_questions_for_all_identity_types(self):
        for user in (None, AnonymousUser(), principal(), principal(False)):
            with self.subTest(user=user), patch("ai.agent.get_llm", return_value=self.model()) as get_llm:
                result = orchestrator.ask_assistant("What is malaria?", user)
                self.assertEqual(result["answer"], "General knowledge answer.")
                self.assertNotIn("user", result)
                self.assertEqual(get_llm.return_value.invoke.call_count, 2)

    def test_public_state_never_receives_identity_or_permissions(self):
        with patch.object(orchestrator.public_graph, "invoke", return_value={"answer": "ok"}) as invoke:
            orchestrator.ask_assistant(" hello ", principal(False))
            invoke.assert_called_once_with({"question": "hello"})

    def test_active_user_selects_authenticated_graph_without_private_context(self):
        with patch.object(orchestrator.authenticated_graph, "invoke", return_value={"answer": "ok"}) as invoke:
            orchestrator.ask_assistant("hello", principal())
            invoke.assert_called_once_with({"question": "hello"})

    def test_protected_intents_and_unknown_labels_fail_closed(self):
        for user in (AnonymousUser(), principal(), principal(False)):
            for intent in ("user", "database_read", "database_write", "unexpected"):
                with self.subTest(intent=intent, user=user), patch("ai.agent.get_llm", return_value=self.model(intent)) as llm:
                    result = orchestrator.ask_assistant("Show or change hospital records", user)
                    self.assertEqual(result["answer"], PROTECTED_OPERATION_UNAVAILABLE)
                    self.assertEqual(llm.return_value.invoke.call_count, 1)

    def test_classifier_misrouting_cannot_access_records_or_execute_writes(self):
        for question in ("Show all patient records", "Delete all invoices", "Show my private profile"):
            with self.subTest(question=question), patch("ai.agent.get_llm", return_value=self.model()), patch("ai.service.execute_sql", side_effect=AssertionError("DB reached")) as sql, patch("ai.agent.format_user_context", side_effect=AssertionError("Private context reached")) as context:
                orchestrator.ask_assistant(question, AnonymousUser())
                sql.assert_not_called()
                context.assert_not_called()

    def test_graphs_have_no_protected_nodes_and_drop_extra_state(self):
        for graph in (orchestrator.public_graph, orchestrator.authenticated_graph, orchestrator.graph):
            self.assertFalse({"generate_sql", "execute_sql", "generate_user_answer"} & set(graph.get_graph().nodes))
            with patch("ai.agent.get_llm", return_value=self.model()):
                result = graph.invoke({"question": "Hello", "user": principal(), "result": {"secret": "private"}})
                self.assertNotIn("user", result)
                self.assertNotIn("result", result)

    def test_direct_executor_fails_before_opening_cursor(self):
        with patch("django.db.backends.base.base.BaseDatabaseWrapper.cursor", side_effect=AssertionError("DB reached")) as cursor:
            for sql in ("SELECT 1", "UPDATE x SET y=1", "DELETE FROM x", "INSERT INTO x VALUES (1)"):
                with self.assertRaises(AIDataAccessDisabled):
                    execute_sql(sql)
            cursor.assert_not_called()

    def test_legacy_nodes_and_agent_helpers_cannot_bypass_guards(self):
        state = {"question": "private", "user": principal(), "sql": "SELECT 1", "result": {"private": "data"}}
        with patch("ai.agent.get_llm", side_effect=AssertionError("Model reached")):
            for node in (nodes.generate_sql_node, nodes.execute_sql_node, nodes.generate_user_answer_node, nodes.generate_answer_node):
                self.assertEqual(node(state)["answer"], PROTECTED_OPERATION_UNAVAILABLE)
            for fn, args in ((agent.generate_sql, ("question",)), (agent.generate_user_answer, ("question", principal())), (agent.generate_answer, ("question", {"private": "data"}))):
                with self.assertRaises(AIDataAccessDisabled):
                    fn(*args)

    def test_invalid_questions(self):
        for question in (None, [], {}, 2, "", "   "):
            with self.assertRaises(ValueError):
                orchestrator.ask_assistant(question)


class ChatSocketTests(IsolatedAsyncioTestCase):
    def setUp(self):
        self.settings_override = override_settings(AI_CHAT_MAX_MESSAGE_BYTES=128)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)

    async def open_socket(self, user=None):
        socket = WebsocketCommunicator(AIChatConsumer.as_asgi(), "/ws/chat/")
        if user is not None:
            socket.scope["user"] = user
        connected, _ = await socket.connect()
        self.assertTrue(connected)
        self.assertEqual(await socket.receive_json_from(), {"type": "connection", "message": "Connected to AI assistant."})
        return socket

    async def test_anonymous_and_authenticated_general_chat(self):
        for user in (None, principal(), principal(False)):
            with patch("ai.agent.get_llm") as llm:
                llm.return_value.invoke.side_effect = [SimpleNamespace(content="general"), SimpleNamespace(content="Hello")]
                socket = await self.open_socket(user)
                try:
                    await socket.send_json_to({"message": "Hello"})
                    self.assertEqual(await socket.receive_json_from(), {"type": "answer", "message": "Hello"})
                finally:
                    await socket.disconnect()

    async def test_protected_request_is_unavailable_on_socket(self):
        for user in (None, principal(), principal(False)):
            for intent in ("user", "database_read", "database_write"):
                with patch("ai.agent.get_llm") as llm:
                    llm.return_value.invoke.return_value = SimpleNamespace(content=intent)
                    socket = await self.open_socket(user)
                    try:
                        await socket.send_json_to({"message": "Get or change private records"})
                        self.assertEqual(await socket.receive_json_from(), {"type": "answer", "message": PROTECTED_OPERATION_UNAVAILABLE})
                    finally:
                        await socket.disconnect()

    async def test_malformed_empty_non_string_and_oversized_messages(self):
        with patch("config.consumers.ask_assistant") as ask:
            socket = await self.open_socket()
            try:
                for text in ('{', 'null', '[]', '"hello"', '{}', '{"message": 12}', '{"message": []}', '{"message": "  "}', 'x' * 129):
                    await socket.send_to(text_data=text)
                    self.assertEqual((await socket.receive_json_from())["type"], "error")
                await socket.send_to(bytes_data=b"binary")
                self.assertEqual((await socket.receive_json_from())["type"], "error")
                ask.assert_not_called()
            finally:
                await socket.disconnect()

    async def test_payload_identity_is_ignored(self):
        with patch("config.consumers.ask_assistant", return_value={"answer": "safe"}) as ask:
            socket = await self.open_socket()
            try:
                await socket.send_json_to({"message": "hello", "user": {"is_superuser": True}})
                await socket.receive_json_from()
                ask.assert_called_once_with("hello", user=None)
            finally:
                await socket.disconnect()

    async def test_exception_is_not_exposed_and_connection_survives(self):
        with patch("config.consumers.ask_assistant", side_effect=[RuntimeError("private secret"), {"answer": "recovered"}]):
            socket = await self.open_socket()
            try:
                await socket.send_json_to({"message": "hello"})
                response = await socket.receive_json_from()
                self.assertEqual(response["type"], "error")
                self.assertNotIn("secret", response["message"])
                await socket.send_json_to({"message": "hello"})
                self.assertEqual(await socket.receive_json_from(), {"type": "answer", "message": "recovered"})
            finally:
                await socket.disconnect()

    async def test_missing_invalid_and_expired_jwt_are_anonymous(self):
        expired = AccessToken()
        expired["user_id"] = 1
        expired["exp"] = 0
        for query in ("", "?token=bad", "?token=" + str(expired)):
            with patch("apps.core.websocketauth.get_user", new_callable=AsyncMock) as lookup, patch("config.consumers.ask_assistant", return_value={"answer": "public"}) as ask:
                socket = WebsocketCommunicator(JwtWebSocketAuthMiddleware(AIChatConsumer.as_asgi()), "/ws/chat/" + query)
                try:
                    self.assertTrue((await socket.connect())[0])
                    await socket.receive_json_from()
                    await socket.send_json_to({"message": "Hello"})
                    self.assertEqual((await socket.receive_json_from())["message"], "public")
                    self.assertFalse(ask.call_args.kwargs["user"].is_authenticated)
                    lookup.assert_not_called()
                finally:
                    await socket.disconnect()

    async def test_valid_jwt_uses_middleware_identity(self):
        token = AccessToken()
        token["user_id"] = 123
        user = principal()
        with patch("apps.core.websocketauth.get_user", new_callable=AsyncMock, return_value=user) as lookup, patch("config.consumers.ask_assistant", return_value={"answer": "general"}) as ask:
            socket = WebsocketCommunicator(JwtWebSocketAuthMiddleware(AIChatConsumer.as_asgi()), "/ws/chat/?token=" + str(token))
            try:
                self.assertTrue((await socket.connect())[0])
                await socket.receive_json_from()
                await socket.send_json_to({"message": "Hello"})
                await socket.receive_json_from()
                lookup.assert_awaited_once_with(123)
                self.assertIs(ask.call_args.kwargs["user"], user)
            finally:
                await socket.disconnect()

    async def test_real_asgi_origin_boundary(self):
        from config.asgi import application
        from django.conf import settings
        allowed = settings.AI_WEBSOCKET_ALLOWED_ORIGINS[0]
        for origin, expected in ((allowed, True), ("https://untrusted.invalid", False), (None, False)):
            headers = [(b"origin", origin.encode())] if origin else []
            socket = WebsocketCommunicator(application, "/ws/chat/", headers=headers)
            try:
                self.assertEqual((await socket.connect())[0], expected)
                if expected:
                    self.assertEqual((await socket.receive_json_from())["type"], "connection")
            finally:
                await socket.disconnect()
