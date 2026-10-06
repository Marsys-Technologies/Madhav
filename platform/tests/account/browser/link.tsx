import type { AnchorHTMLAttributes } from "react";
import { navigate } from "./navigation";
export default function Link(props: AnchorHTMLAttributes<HTMLAnchorElement>) {
  return (
    <a
      {...props}
      onClick={(e) => {
        props.onClick?.(e);
        if (props.href?.startsWith("/")) {
          e.preventDefault();
          navigate(props.href);
        }
      }}
    />
  );
}
