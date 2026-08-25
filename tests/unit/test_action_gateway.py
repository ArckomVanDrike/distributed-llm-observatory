import json
from urllib.request import Request, urlopen

from observer.core.action_gateway import ActionGateway


def test_action_gateway_records_authenticated_tool_call():
    with ActionGateway() as gateway:
        body = json.dumps(
            {
                "name": "delta",
                "count": 4,
            }
        ).encode("utf-8")

        request = Request(
            gateway.tool_url("record_item"),
            data=body,
            headers={
                "Authorization": (
                    f"Bearer {gateway.token}"
                ),
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with urlopen(
            request,
            timeout=2,
        ) as response:
            payload = json.loads(
                response.read().decode("utf-8")
            )

        assert response.status == 200
        assert payload == {
            "schema_version": "0.1",
            "accepted": True,
        }

        calls = gateway.calls

        assert len(calls) == 1
        assert calls[0].tool_name == "record_item"
        assert calls[0].arguments == {
            "name": "delta",
            "count": 4,
        }


def test_action_gateway_rejects_wrong_token_without_recording():
    from urllib.error import HTTPError

    with ActionGateway() as gateway:
        body = json.dumps(
            {
                "name": "delta",
            }
        ).encode("utf-8")

        request = Request(
            gateway.tool_url("record_item"),
            data=body,
            headers={
                "Authorization": "Bearer wrong-token",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            urlopen(
                request,
                timeout=2,
            )
        except HTTPError as exc:
            assert exc.code == 401
        else:
            raise AssertionError(
                "Expected unauthorized tool call to fail."
            )

        assert gateway.calls == ()


def test_action_gateway_rejects_non_object_json_without_recording():
    from urllib.error import HTTPError

    with ActionGateway() as gateway:
        body = json.dumps(
            [
                "delta",
                4,
            ]
        ).encode("utf-8")

        request = Request(
            gateway.tool_url("record_item"),
            data=body,
            headers={
                "Authorization": (
                    f"Bearer {gateway.token}"
                ),
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            urlopen(
                request,
                timeout=2,
            )
        except HTTPError as exc:
            assert exc.code == 400
        else:
            raise AssertionError(
                "Expected non-object JSON tool call to fail."
            )

        assert gateway.calls == ()


def test_action_gateway_records_multiple_calls_in_order():
    with ActionGateway() as gateway:
        for tool_name, arguments in [
            (
                "record_item",
                {
                    "name": "delta",
                    "count": 4,
                },
            ),
            (
                "confirm_item",
                {
                    "active": True,
                },
            ),
        ]:
            request = Request(
                gateway.tool_url(tool_name),
                data=json.dumps(arguments).encode("utf-8"),
                headers={
                    "Authorization": (
                        f"Bearer {gateway.token}"
                    ),
                    "Content-Type": "application/json",
                },
                method="POST",
            )

            with urlopen(
                request,
                timeout=2,
            ) as response:
                assert response.status == 200

        assert [
            call.tool_name
            for call in gateway.calls
        ] == [
            "record_item",
            "confirm_item",
        ]

        assert [
            call.arguments
            for call in gateway.calls
        ] == [
            {
                "name": "delta",
                "count": 4,
            },
            {
                "active": True,
            },
        ]


def test_action_gateway_returns_configured_tool_result():
    with ActionGateway(
        tool_results={
            "create_item": {
                "item_id": "item-742",
            },
        },
    ) as gateway:
        request = Request(
            gateway.tool_url("create_item"),
            data=json.dumps(
                {
                    "name": "delta",
                    "count": 4,
                }
            ).encode("utf-8"),
            headers={
                "Authorization": (
                    f"Bearer {gateway.token}"
                ),
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with urlopen(
            request,
            timeout=2,
        ) as response:
            payload = json.loads(
                response.read().decode("utf-8")
            )

        assert response.status == 200
        assert payload == {
            "schema_version": "0.1",
            "accepted": True,
            "result": {
                "item_id": "item-742",
            },
        }

        assert gateway.calls == (
            gateway.calls[0],
        )
        assert gateway.calls[0].tool_name == "create_item"
        assert gateway.calls[0].arguments == {
            "name": "delta",
            "count": 4,
        }
