import { AccountHeading } from "@/components/account/AccountHeading";
import { PersonaManager } from "@/components/account/PersonaManager";
export default function PersonasPage() {
  return (
    <>
      <AccountHeading name="personas" cockpit />
      <PersonaManager />
    </>
  );
}
