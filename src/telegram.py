import asyncio
from telegram import Bot

def emoji(side):
    return "🟢" if side == "LONG" else "🔴"

class TelegramBot:
    def __init__(self, token, chat_id):
        self.bot = Bot(token)
        self.chat_id = chat_id

    async def send_signal(self, signal):
        msg = (
            f"🚨 <b>NEW SIGNAL</b> 🚨\n"
            f"📊 <b>{signal['symbol']}/{signal['timeframe']}</b>\n"
            f"📈 Direction: <b>{'BUY' if signal['side'] == 'LONG' else 'SELL'}</b>\n"
            f"🎯 Strategy: {signal['strategy']}\n"
            f"💰 Entry: <b>{signal['entry']:.2f}</b>\n"
            f"🛑 Stop Loss: <b>{signal['sl']:.2f}</b> ({signal['sl_multiplier']:.1f}x ATR)\n"
            f"🎯 Targets: {', '.join([f'{tp:.2f} ({m:.1f}x ATR)' for tp, m in zip(signal['tp'], signal['tp_multipliers'])])}\n"
            f"✅ Confidence: <b>{int(round(signal['confidence'] * 100))}%</b>\n"
            f"⚡ Momentum: {signal['momentum_cat']}\n"
            f"🔢 SLNO: <b>{signal['slno']}</b>"
        )
        await self._send(msg)

    async def send_trade_close(self, trade, exit_info):
        profit = exit_info['exit_price'] - trade['entry'] if trade['side'] == 'LONG' else trade['entry'] - exit_info['exit_price']
        profit_emoji = "✅" if profit > 0 else "❌"
        
        msg = (
            f"{profit_emoji} <b>TRADE CLOSED</b> {emoji(trade['side'])}\n"
            f"📊 <b>{trade['symbol']}/{trade['timeframe']}</b>\n"
            f"💰 Entry: <b>{trade['entry']:.2f}</b>\n"
            f"🚪 Exit: <b>{exit_info['exit_price']:.2f}</b>\n"
            f"💸 P&L: <b>{profit:+.2f}</b>\n"
            f"📋 Reason: {exit_info['reason']}\n"
            f"🔢 SLNO: <b>{trade['slno']}</b>"
        )
        await self._send(msg)

    async def send_error(self, err):
        msg = f"⚠️ Bot Error:\n<pre>{err}</pre>"
        await self._send(msg)

    async def send_status(self, trades):
        if not trades:
            msg = "No active trades."
        else:
            msg = "<b>Active Trades:</b>\n"
            for t in trades:
                msg += (
                    f"{emoji(t['side'])} {t['symbol']}/{t['timeframe']} | "
                    f"Entry: {t['entry']} | SL: {t['sl']} | "
                    f"TPs: {', '.join([str(x) for x in t['tp']])}\n"
                    f"Confidence: {t['confidence']:.2f} | "
                    f"SLNO: {t['slno']}\n"
                )
        await self._send(msg)

    async def _send(self, msg, retry=2):
        for i in range(retry):
            try:
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=msg,
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )
                break
            except Exception as e:
                if i == retry - 1:
                    print(f"Telegram send failed: {e}")
                await asyncio.sleep(2)