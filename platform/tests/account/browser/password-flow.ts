/** No credential changes or network activity from a rendered fixture. */
export async function changeAccountPassword() {
  return {
    changed: false,
    complete: false,
    error: "Credential actions are unavailable in this fictional preview.",
  };
}
export async function finishAccountSecurity() {
  return false;
}
export async function signOutAccountSessions() {
  return false;
}
