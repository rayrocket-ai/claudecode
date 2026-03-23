import PQueue from 'p-queue';
import pino from 'pino';
import { config } from '../config';

const logger = pino({ level: config.logLevel });

// Single-concurrency queue to prevent parallel browser sessions
const taskQueue = new PQueue({ concurrency: 1 });

taskQueue.on('active', () => {
  logger.debug({ pending: taskQueue.pending, size: taskQueue.size }, 'Task started');
});

taskQueue.on('idle', () => {
  logger.debug('Task queue idle');
});

export async function enqueue<T>(name: string, fn: () => Promise<T>): Promise<T> {
  logger.info({ task: name, queueSize: taskQueue.size }, 'Enqueuing task');
  return taskQueue.add(async () => {
    logger.info({ task: name }, 'Executing task');
    try {
      const result = await fn();
      logger.info({ task: name }, 'Task completed');
      return result;
    } catch (err) {
      logger.error({ task: name, err }, 'Task failed');
      throw err;
    }
  }) as Promise<T>;
}

export { taskQueue };
