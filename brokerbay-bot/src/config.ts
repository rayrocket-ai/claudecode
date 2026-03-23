import { z } from 'zod';
import dotenv from 'dotenv';
import path from 'path';

dotenv.config({ path: path.resolve(__dirname, '..', '.env') });

const configSchema = z.object({
  brokerbayEmail: z.string().min(1, 'BROKERBAY_EMAIL is required'),
  brokerbayPassword: z.string().min(1, 'BROKERBAY_PASSWORD is required'),
  discordBotToken: z.string().min(1, 'DISCORD_BOT_TOKEN is required'),
  discordClientId: z.string().min(1, 'DISCORD_CLIENT_ID is required'),
  discordAllowedUserIds: z
    .string()
    .min(1, 'DISCORD_ALLOWED_USER_IDS is required')
    .transform((val) => val.split(',').map((id) => id.trim())),
  discordGuildId: z.string().optional(),
  googleMapsApiKey: z.string().min(1, 'GOOGLE_MAPS_API_KEY is required'),
  sessionPath: z.string().default('./session/brokerbay.json'),
  nodeEnv: z.enum(['development', 'production', 'test']).default('development'),
  logLevel: z.string().default('info'),
  headless: z
    .string()
    .default('false')
    .transform((val) => val === 'true'),
});

const parsed = configSchema.safeParse({
  brokerbayEmail: process.env.BROKERBAY_EMAIL,
  brokerbayPassword: process.env.BROKERBAY_PASSWORD,
  discordBotToken: process.env.DISCORD_BOT_TOKEN,
  discordClientId: process.env.DISCORD_CLIENT_ID,
  discordAllowedUserIds: process.env.DISCORD_ALLOWED_USER_IDS,
  discordGuildId: process.env.DISCORD_GUILD_ID,
  googleMapsApiKey: process.env.GOOGLE_MAPS_API_KEY,
  sessionPath: process.env.SESSION_PATH,
  nodeEnv: process.env.NODE_ENV,
  logLevel: process.env.LOG_LEVEL,
  headless: process.env.HEADLESS,
});

if (!parsed.success) {
  console.error('Invalid environment configuration:');
  for (const issue of parsed.error.issues) {
    console.error(`  ${issue.path.join('.')}: ${issue.message}`);
  }
  process.exit(1);
}

export const config = parsed.data;
