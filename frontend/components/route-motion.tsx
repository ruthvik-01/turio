"use client";
import NextLink from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useLayoutEffect, useRef, type ComponentProps, type ReactNode } from "react";

const EASE = "cubic-bezier(.675,.15,.1,1)";
const Navigation = createContext<((href: string, immediate?: boolean) => void) | null>(null);

export function useImmediateNavigation() {
  const navigate = useContext(Navigation);
  const router = useRouter();
  return (href: string) => navigate ? navigate(href, true) : router.push(href);
}

export function ButtonLabel({ children }: { children: ReactNode }) {
  return <span className="button-label"><span className="button-label-track"><span>{children}</span><span aria-hidden="true">{children}</span></span></span>;
}

export function TransitionLink({ children, onClick, ...props }: ComponentProps<typeof NextLink>) {
  const navigate = useContext(Navigation);
  const rolling = typeof children === "string" && props.className?.split(" ").includes("button");
  return <NextLink {...props} onClick={event => {
    onClick?.(event);
    if (!navigate || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.currentTarget.target === "_blank") return;
    const target = new URL(event.currentTarget.href);
    if (target.origin !== location.origin || target.pathname === location.pathname) return;
    event.preventDefault(); navigate(target.pathname + target.search + target.hash);
  }}>{rolling ? <ButtonLabel>{children}</ButtonLabel> : children}</NextLink>;
}

export function MotionProvider({ children }: { children: ReactNode }) {
  const path = usePathname();
  const router = useRouter();
  const animations = useRef(new Set<Animation>());
  const previous = useRef<string | null>(null);
  const pending = useRef(false);
  const navigationVersion = useRef(0);
  const alive = useRef(true);
  const reduced = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const cancel = useCallback(() => {
    for (const animation of animations.current) animation.cancel();
    animations.current.clear();
  }, []);
  const animate = useCallback((element: Element, frames: Keyframe[], duration: number, delay = 0) => {
    const animation = element.animate(frames, { duration, delay, easing: EASE, fill: "backwards" });
    animations.current.add(animation);
    animation.finished.catch(() => {}).finally(() => animations.current.delete(animation));
    return animation;
  }, []);

  const navigate = useCallback(async (href: string, immediate = false) => {
    if (immediate) { navigationVersion.current++; pending.current = false; cancel(); router.push(href); return; }
    if (pending.current) return;
    const root = document.getElementById("main-content");
    if (!root || reduced()) { router.push(href); return; }
    pending.current = true;
    const version = ++navigationVersion.current;
    const exit = root.animate(
      [{ opacity: 1, transform: "translateY(0)" }, { opacity: 0, transform: "translateY(-10px)" }],
      { duration: 240, easing: "cubic-bezier(0.25, 1, 0.5, 1)", fill: "forwards" }
    );
    animations.current.add(exit);
    await Promise.race([exit.finished.catch(() => {}), new Promise<void>(resolve => setTimeout(resolve, 260))]);
    if (alive.current && version === navigationVersion.current) router.push(href);
  }, [router, cancel]);

  useEffect(() => {
    alive.current = true;
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const stop = () => { if (media.matches) cancel(); };
    media.addEventListener("change", stop);
    return () => { alive.current = false; media.removeEventListener("change", stop); cancel(); };
  }, [cancel]);

  useLayoutEffect(() => {
    navigationVersion.current++;
    cancel(); pending.current = false;
    const changed = previous.current !== null && previous.current !== path;
    previous.current = path;
    const root = document.getElementById("main-content");
    if (!root || reduced()) return;
    const seen = new WeakSet<Element>();
    let entered = false;
    const reveal = () => {
      if (reduced()) return;
      const heading = root.querySelector("main h1");
      if (!heading) return;
      if (!entered) {
        entered = true;
        if (changed && path !== "/") {
          animate(root, [
            { opacity: 0, transform: "translateY(18px)" },
            { opacity: 1, transform: "translateY(0)" }
          ], 520);
        }
        animate(heading, [
          { opacity: 0, transform: "translateY(14px)" },
          { opacity: 1, transform: "translateY(0)" }
        ], 540, changed ? 40 : 0);
        const actions = root.querySelector(".landing .actions, .auth-card");
        if (actions) { seen.add(actions); animate(actions, [{ transform: "translateY(16px)", opacity: 0 }, { transform: "translateY(0)", opacity: 1 }], 540, 80); }
      }
      const panels = [...root.querySelectorAll("main > .panel, main > section.panel, main .job-card, .step-card, .next-up-card")].slice(0, 24);
      panels.forEach((panel, index) => {
        if (seen.has(panel)) return;
        seen.add(panel);
        animate(panel, [{ transform: "translateY(12px)", opacity: 0 }, { transform: "translateY(0)", opacity: 1 }], 500, Math.min(index * 35 + 60, 280));
      });
    };
    reveal();
    const observer = new MutationObserver(reveal);
    observer.observe(root, { childList: true, subtree: true });
    return () => { observer.disconnect(); cancel(); };
  }, [path, cancel, animate]);

  return <Navigation.Provider value={navigate}>{children}</Navigation.Provider>;
}
