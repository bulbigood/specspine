export function exportTrace(spans, sink) {
  return spans.length ? sink.sendBatch(spans) : Promise.resolve();
}
