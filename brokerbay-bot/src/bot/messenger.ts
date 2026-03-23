import { Bot, InlineKeyboard } from 'grammy';
import type { IMessenger, InlineButton } from '../types';

export class TelegramMessenger implements IMessenger {
  constructor(private bot: Bot) {}

  async sendMessage(chatId: string | number, text: string, parseMode?: string): Promise<void> {
    await this.bot.api.sendMessage(chatId, text, {
      parse_mode: (parseMode as 'MarkdownV2' | 'HTML') || 'MarkdownV2',
    });
  }

  async sendPhoto(chatId: string | number, photo: string | Buffer, caption?: string): Promise<void> {
    if (typeof photo === 'string') {
      await this.bot.api.sendPhoto(chatId, photo, { caption });
    } else {
      await this.bot.api.sendPhoto(chatId, new InputFile(photo), { caption });
    }
  }

  async sendButtons(
    chatId: string | number,
    text: string,
    buttons: InlineButton[][],
    parseMode?: string,
  ): Promise<void> {
    const keyboard = new InlineKeyboard();
    for (const row of buttons) {
      for (const btn of row) {
        keyboard.text(btn.text, btn.callbackData);
      }
      keyboard.row();
    }

    await this.bot.api.sendMessage(chatId, text, {
      parse_mode: (parseMode as 'MarkdownV2' | 'HTML') || 'MarkdownV2',
      reply_markup: keyboard,
    });
  }
}

// Re-export InputFile for photo support
import { InputFile } from 'grammy';
