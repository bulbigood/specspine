export function indexRecord(record, writer) {
  return writer.upsert(record.id, record.version, record);
}

export function removeRecord(id, writer) {
  return writer.remove(id);
}
