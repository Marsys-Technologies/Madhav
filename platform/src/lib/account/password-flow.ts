"use client";
import {
  EmailAuthProvider,
  reauthenticateWithCredential,
  updatePassword,
  signOut,
} from "firebase/auth";
import { auth } from "@/lib/firebase/client";
export type PasswordResult = {
  changed: boolean;
  complete: boolean;
  error?: string;
  ownerId?: string;
};
/** Passwords go to Firebase Auth only, and are never persisted by this module. */
export async function finishAccountSecurity(
  expectedOwner: string,
): Promise<boolean> {
  const user = auth.currentUser;
  if (!user || user.uid !== expectedOwner) return false;
  try {
    const idToken = await user.getIdToken(true);
    if (auth.currentUser?.uid !== expectedOwner) return false;
    const response = await fetch("/api/account/security", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ idToken }),
    });
    if (!response.ok || auth.currentUser?.uid !== expectedOwner) return false;
    await signOut(auth);
    return auth.currentUser == null;
  } catch {
    return false;
  }
}
export async function changeAccountPassword(
  current: string,
  next: string,
): Promise<PasswordResult> {
  const user = auth.currentUser;
  if (!user?.email)
    return {
      changed: false,
      complete: false,
      error: "Sign in again to change your password.",
    };
  try {
    await reauthenticateWithCredential(
      user,
      EmailAuthProvider.credential(user.email, current),
    );
  } catch {
    return {
      changed: false,
      complete: false,
      error: "Current password could not be verified. Try again.",
    };
  }
  if (auth.currentUser?.uid !== user.uid)
    return {
      changed: false,
      complete: false,
      error: "The signed-in account changed. Sign in again before continuing.",
    };
  try {
    await updatePassword(user, next);
  } catch {
    return {
      changed: false,
      complete: false,
      error: "Password could not be changed. Try again.",
    };
  }
  const complete = await finishAccountSecurity(user.uid);
  return complete
    ? { changed: true, complete: true }
    : {
        ownerId: user.uid,
        changed: true,
        complete: false,
        error:
          "Password changed. Signing out other sessions could not be completed. Retry the sign-out step.",
      };
}
export async function signOutAccountSessions(
  current: string,
): Promise<boolean> {
  const user = auth.currentUser;
  if (!user?.email || !current) return false;
  try {
    await reauthenticateWithCredential(
      user,
      EmailAuthProvider.credential(user.email, current),
    );
    return finishAccountSecurity(user.uid);
  } catch {
    return false;
  }
}
