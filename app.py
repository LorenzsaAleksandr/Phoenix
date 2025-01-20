import asyncio
import os
from playwright.async_api import async_playwright
from loguru import logger

import utils
import settings
from restore_wallet import restore_wallet
from phoenix import PhoenixTrade
from wallets import WALLETS

# Получаем путь к текущему пользователю
user_profile = os.getenv("USERPROFILE")
# Строим полный путь к расширению
extension_path = os.path.join(user_profile, "AppData", "Local", "Google", "Chrome", "User Data", "Default",
                              "Extensions", "aflkmfhebedbjioipglgcbcmnbpgliof", "0.10.111_0")


async def process_wallet(wallet):
    async with async_playwright() as p:
        # Устанавливаем proxy, если указано
        proxy = await utils.format_proxy(settings.proxy) if settings.proxy else None

        # Аргументы запуска
        args = [
            f"--disable-extensions-except={extension_path}",
            f"--load-extension={extension_path}",
        ]
        if settings.headless:
            args.append("--headless=new")

        # Запуск браузера
        context = await p.chromium.launch_persistent_context(
            '',
            headless=False,
            args=args,
            proxy=proxy,
            locale="en-US",
            slow_mo=settings.slow_mo,
        )

        # Восстановление кошелька
        if not await restore_wallet(context=context, wallet=wallet):
            logger.error(f'{wallet.address}: Can not restore wallet')
            return

        logger.success('Wallet restored. Starting trade...')

        # Создание объекта PhoenixTrade
        trade = PhoenixTrade(context=context, wallet=wallet)
        await trade.connect_wallet()
        await trade.sell_token("SOL", amount=settings.sol_to_sell)
        await trade.sell_token("USDC")

        logger.info('All tasks completed.')


async def main():
    tasks = [process_wallet(wallet) for wallet in WALLETS]
    await asyncio.gather(*tasks)


if __name__ == '__main__':
    asyncio.run(main())
