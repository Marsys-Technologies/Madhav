import type { ReactNode, ComponentType, AnchorHTMLAttributes } from 'react'

type LinkProps = AnchorHTMLAttributes<HTMLAnchorElement> & {
  href: string
  children?: ReactNode
}

export default function Link({ href, children, ...rest }: LinkProps) {
  return (
    <a href={href} {...rest}>
      {children}
    </a>
  )
}

export function usePathname(): string {
  if (typeof window === 'undefined') return '/clients/chart-1/consult/conv-1'
  return new URLSearchParams(window.location.search).get('pathname') ?? '/clients/chart-1/consult/conv-1'
}

export function useRouter() {
  return {
    push: () => {},
    replace: () => {},
    refresh: () => {},
    back: () => {},
  }
}

export function redirect(target: string): never {
  throw new Error(`NEXT_REDIRECT:${target}`)
}

export function notFound(): never {
  throw new Error('NEXT_NOT_FOUND')
}

export function dynamic<P extends object>(_loader: () => Promise<{ default: ComponentType<P> }>): ComponentType<P> {
  return function DynamicStub() {
    return null
  }
}

export const auth = {}
export const firebaseDefault = {}
