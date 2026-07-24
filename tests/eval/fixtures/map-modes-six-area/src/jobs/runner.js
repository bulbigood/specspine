export function run(job, queue, deadLetters) {
  try {
    return job.execute();
  } catch (error) {
    return job.attempts < 3
      ? queue.retry(job)
      : deadLetters.store(job, error);
  }
}
