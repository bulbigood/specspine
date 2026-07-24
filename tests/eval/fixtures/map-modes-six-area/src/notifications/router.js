export function deliver(event, preferences, providers) {
  const channel = preferences.channelFor(event.userId);
  return providers[channel].send(event);
}
