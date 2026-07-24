export function receive(request, verifier, dedupe, queue) {
  verifier.verify(request);
  if (dedupe.seen(request.id)) return "duplicate";
  dedupe.record(request.id);
  return queue.enqueue(request.body);
}
