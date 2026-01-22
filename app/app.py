import requests
import json
import os

from dotenv import load_dotenv
from pathlib import Path

from result import Result
from scraper import getResult




load_dotenv()  # loads .env from current directory

def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

# Constants
API_VERSION = "/api/v4"

BASE_URL = require_env("MATTERMOST_BASE_URL") + API_VERSION
CHANNEL_ID = require_env("MATTERMOST_CHANNEL_ID")
BOT_USER_ID = require_env("MATTERMOST_BOT_USER_ID")
BOT_TOKEN = require_env("MATTERMOST_BOT_TOKEN")

AUTH_HEADER = {
    "Authorization": "Bearer " + BOT_TOKEN
}

class HttpError(Exception):
    """Custom exception for HTTP errors."""
    pass

def pretty_print(data):
    print(json.dumps(data, indent=2, ensure_ascii=False))

def send_request(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    json_payload: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, str]] = None,
    timeout: int = 10,
) -> Any:
    """
    Send an HTTP request.

    :param method: HTTP method (GET, POST, PUT, DELETE, PATCH)
    :param url: Full request URL
    :param headers: Optional headers dict
    :param json_payload: Optional JSON payload (for POST/PUT/PATCH)
    :param params: Optional query parameters
    :param timeout: Request timeout in seconds
    :return: Parsed JSON or raw text response
    :raises HttpError: on HTTP or request failure
    """

    try:
        if headers is None:
            headers = AUTH_HEADER
        
        response = requests.request(
            method=method.upper(),
            url=url,
            headers=headers,
            json=json_payload,
            params=params,
            timeout=timeout,
        )
        print(f"Sent request {url}:\n" f"{json.dumps(json_payload, indent=2) if json_payload else '{}'}")
        print("\n")
    except requests.RequestException as exc:
        raise HttpError(f"Request failed: {exc}") from exc

    # HTTP-level error handling
    if not response.ok:
        raise HttpError(
            f"HTTP {response.status_code} error\n"
            f"URL: {url}\n"
            f"Response: {response.text}"
        )

    # Try to decode JSON, fall back to text
    try:
        return response.json()
    except ValueError:
        return response.text

def createMessage(result: Result) -> str:
    message = ""
    for restaurant in result.restaurants:
        message += f"**:{restaurant.emoji}: {restaurant.name}**\n"
        for meal in restaurant.meals:
            if meal.price is not None:
                message += f"- {meal.name}: {meal.price:.2f} €\n"
            else:
                message += f"- {meal.name}: N/A\n"
        message += "\n"
    return message


def main():
    try:
        #response = send_request(
        #    method="GET",
        #    url=BASE_URL + "/api/v4/system/pings",
        #)
        #pretty_print(response)

        # TODO: get format
        result = getResult()
        message = createMessage(result)

        # Post
        response = send_request(
            method="POST",
            url=BASE_URL + "/posts",
            json_payload = {
                "channel_id" : CHANNEL_ID,
                "message" : message
            }
        )

        # React
        # TODO: emoji per name

        POST_ID = response["id"]

        for restaurant in result.restaurants:
            emoji = restaurant.emoji
            response = send_request(
            method = "POST",
            url = BASE_URL + "/reactions",
            json_payload={
                "user_id": BOT_USER_ID,
                "post_id": POST_ID,
                "emoji_name": emoji,
                "create_at": 0
                }
            )
            pretty_print(response)

    except HttpError as e:
        print(e)


if __name__ == "__main__":
    main()
