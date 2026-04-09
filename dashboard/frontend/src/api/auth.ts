import client from './client';
import type { TokenResponse, User } from '../types';

export async function login(email: string, password: string): Promise<TokenResponse> {
  const { data } = await client.post<TokenResponse>('/auth/login', { email, password });
  return data;
}

export async function register(email: string, username: string, password: string): Promise<TokenResponse> {
  const { data } = await client.post<TokenResponse>('/auth/register', { email, username, password });
  return data;
}

export async function getMe(): Promise<User> {
  const { data } = await client.get<User>('/auth/me');
  return data;
}
