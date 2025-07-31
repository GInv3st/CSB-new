import asyncio
import time
from telegram import Bot

def emoji(side):
    return "🟢" if side == "LONG" else "🔴"

class TelegramBot:
    def __init__(self, token, chat_id):
        self.bot = Bot(token)
        self.chat_id = chat_id

    async def test_connection(self):
        """Test Telegram bot connection"""
        try:
            # Test bot info
            bot_info = await self.bot.get_me()
            # Test send capability
            await self.bot.send_message(
                chat_id=self.chat_id,
                text="🔍 Bot connection test - OK",
                parse_mode="HTML"
            )
            return True
        except Exception as e:
            raise Exception(f"Telegram connection failed: {e}")

    async def send_signal(self, signal):
        # Calculate risk/reward ratios
        entry = signal['entry']
        sl = signal['sl']
        sl_distance = abs(entry - sl)
        sl_pct = (sl_distance / entry) * 100
        
        # Calculate R:R for each TP
        rr_ratios = []
        for tp in signal['tp']:
            tp_distance = abs(tp - entry)
            rr = tp_distance / sl_distance if sl_distance > 0 else 0
            rr_ratios.append(rr)
        
        # Calculate TP percentages
        tp_pcts = [(abs(tp - entry) / entry) * 100 for tp in signal['tp']]
        
        # Direction emoji
        direction_emoji = "🔴" if signal['side'] == 'SHORT' else "🟢"
        
        # Analysis level
        confidence_pct = signal['confidence'] * 100
        if confidence_pct >= 70:
            level = "HIGH"
        elif confidence_pct >= 50:
            level = "MEDIUM"
        else:
            level = "LOW"
        
        msg = (
            f"🎯 LOGICAL SIGNAL {direction_emoji}\n\n"
            f"📊 {signal['symbol']} | {signal['timeframe'].upper()}\n"
            f"🎯 {'SHORT' if signal['side'] == 'SHORT' else 'LONG'} @ ${entry:.4f} (REAL PRICE)\n\n"
            f"🛡️ Stop Loss: ${sl:.4f} ({sl_pct:.2f}%)\n"
            f"💰 Take Profits:\n"
        )
        
        # Add each TP with R:R
        for i, (tp, tp_pct, rr) in enumerate(zip(signal['tp'], tp_pcts, rr_ratios), 1):
            msg += f"   TP{i}: ${tp:.4f} ({tp_pct:.2f}%) [R:R {rr:.1f}]\n"
        
        msg += (
            f"\n🧠 Analysis ⚠️:\n"
            f"   Signal Strength: {signal.get('momentum', 50):.1f}%\n"
            f"   Final Confidence: {confidence_pct:.1f}%\n"
            f"   Level: {level}\n"
            f"   Volatility: NORMAL\n"
            f"   ATR: ${signal.get('atr_value', 0):.6f}\n\n"
            f"🎪 Strategy: {signal['strategy'].upper().replace(' ', '_')}\n"
            f"🔍 Signal ID: {signal['symbol'][:3]}{signal['slno']}\n"
            f"💡 {level} SIGNAL - {'High' if level == 'HIGH' else 'Acceptable'} risk/reward\n"
            f"⏰ Time: {time.strftime('%H:%M:%S')}\n\n"
            f"🤖 100% LOGICAL ANALYSIS\n"
            f"📊 Data: 200 candles\n"
            f"🚀 NO RANDOM ELEMENTS!"
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