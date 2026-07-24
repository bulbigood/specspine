export function createSession(user, sessions) {
  return sessions.save({ userId: user.id, state: "active" });
}

export function revokeSession(id, sessions) {
  return sessions.revoke(id);
}
