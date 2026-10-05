import type { AnchorHTMLAttributes } from "react";
export const usePathname = () => "/clients/fixture-chart";
export const useSearchParams = () => new URLSearchParams();
export const useRouter = () => ({
  push: () => {},
  replace: () => {},
  refresh: () => {},
});
export default function Link({
  children,
  ...props
}: AnchorHTMLAttributes<HTMLAnchorElement>) {
  return <a {...props}>{children}</a>;
}
