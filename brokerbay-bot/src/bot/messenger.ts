import {
  Client,
  TextChannel,
  ActionRowBuilder,
  ButtonBuilder,
  ButtonStyle,
  AttachmentBuilder,
} from 'discord.js';
import type { IMessenger, InlineButton } from '../types';

export class DiscordMessenger implements IMessenger {
  constructor(private client: Client) {}

  private async getChannel(channelId: string): Promise<TextChannel> {
    const channel = await this.client.channels.fetch(channelId);
    if (!channel || !channel.isTextBased()) {
      throw new Error(`Channel ${channelId} not found or not a text channel`);
    }
    return channel as TextChannel;
  }

  async sendMessage(channelId: string, text: string): Promise<void> {
    const channel = await this.getChannel(channelId);
    await channel.send(text);
  }

  async sendPhoto(channelId: string, photo: string | Buffer, caption?: string): Promise<void> {
    const channel = await this.getChannel(channelId);
    if (typeof photo === 'string') {
      await channel.send({ content: caption || '', files: [photo] });
    } else {
      const attachment = new AttachmentBuilder(photo, { name: 'image.png' });
      await channel.send({ content: caption || '', files: [attachment] });
    }
  }

  async sendButtons(
    channelId: string,
    text: string,
    buttons: InlineButton[][],
  ): Promise<void> {
    const channel = await this.getChannel(channelId);
    const rows = buttons.map((rowButtons) => {
      const row = new ActionRowBuilder<ButtonBuilder>();
      for (const btn of rowButtons) {
        row.addComponents(
          new ButtonBuilder()
            .setCustomId(btn.callbackData)
            .setLabel(btn.text)
            .setStyle(ButtonStyle.Primary),
        );
      }
      return row;
    });

    await channel.send({ content: text, components: rows });
  }
}
