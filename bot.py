import os
import logging
import sys

from aiohttp import web

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from handlers import main

# Bot token from config
TOKEN = os.environ['TG_TOKEN']

# Webserver settings
# bind localhost only to prevent any external access
WEB_SERVER_HOST = os.environ['WEB_SERVER_HOST']
# Port for incoming request from reverse proxy. Should be any available port
WEB_SERVER_PORT = int(os.environ['WEB_SERVER_PORT'])

# Path to webhook route, on which Telegram will send requests
WEBHOOK_PATH = os.environ['WEBHOOK_URL_PATH']
# Secret key to validate requests from Telegram (optional)
WEBHOOK_SECRET = os.environ['WEBHOOK_SECRET']
# Base URL for webhook will be used to generate webhook URL for Telegram,
BASE_WEBHOOK_URL = os.environ['WEBHOOK_HOST']

# All handlers should be attached to the Router (or Dispatcher)
router_main = Router()

main.register_handlers_main(router_main)


async def on_startup(bot: Bot) -> None:
    # Set webhook to get updates from tg
    await bot.set_webhook(f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}", secret_token=WEBHOOK_SECRET)


def main() -> None:
    # Dispatcher is a root router, all routers should be attached to Dispatcher
    dp = Dispatcher()
    dp.include_router(router_main)

    # Register startup hook to initialize webhook
    dp.startup.register(on_startup)

    # Initialize Bot instance with default bot properties which will be passed to all API calls
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # Create aiohttp.web.Application instance
    app = web.Application()

    # Create an instance of request handler,
    # aiogram has few implementations for different cases of usage
    # In this example we use SimpleRequestHandler which is designed to handle simple cases
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET,
    )
    # Register webhook handler on application
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)

    # Mount dispatcher startup and shutdown hooks to aiohttp application
    setup_application(app, dp, bot=bot)

    # And finally start webserver
    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    main()
