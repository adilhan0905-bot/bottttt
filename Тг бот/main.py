import logging
from telegram import BotCommand
from telegram.ext import Application

from bot.config import Config
from bot.handlers import start, objects, worktypes, materials, norms, tasks, purchases, finances, sheets

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def post_init(application: Application) -> None:
    await application.bot.set_my_commands([
        BotCommand("start", "Меню"),
    ])
    logger.info("Системное меню установлено")


def main():
    Config.validate()
    application = (
        Application.builder()
        .token(Config.BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    handlers = []
    handlers += start.get_handlers()
    handlers += objects.get_handlers()
    handlers += worktypes.get_handlers()
    handlers += materials.get_handlers()
    handlers += norms.get_handlers()
    handlers += tasks.get_handlers()
    handlers += purchases.get_handlers()
    handlers += finances.get_handlers()
    handlers += sheets.get_handlers()

    for h in handlers:
        application.add_handler(h)

    logger.info("Бот запущен. Ожидание сообщений...")
    # Синхронный вызов – библиотека сама создаст event loop
    application.run_polling()


if __name__ == "__main__":
    main()