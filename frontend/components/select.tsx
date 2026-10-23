"use client";
import { useEffect, useId, useRef, useState, type KeyboardEvent } from "react";

export type SelectOption = { value: string; label: string; disabled?: boolean };

type BaseProps = {
  options: SelectOption[];
  placeholder?: string;
  disabled?: boolean;
  name?: string;
  label?: string;
  describedBy?: string;
};

type SingleProps = BaseProps & { multiple?: false; value: string; onChange: (value: string) => void };
type MultiProps = BaseProps & { multiple: true; value: string[]; onChange: (value: string[]) => void };

export function Select(props: SingleProps | MultiProps) {
  const { options, placeholder = "Choose an answer", disabled = false, name, label, describedBy } = props;
  const multiple = props.multiple === true;
  const current = multiple ? (props.value as string[]) : [props.value as string];
  const id = useId();
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const trigger = useRef<HTMLButtonElement>(null);
  const panel = useRef<HTMLDivElement>(null);
  const selectedIndex = options.findIndex(option => current.includes(option.value));
  const labels = options.filter(option => current.includes(option.value)).map(option => option.label);

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: MouseEvent) => {
      const target = event.target as Node;
      if (!panel.current?.contains(target) && !trigger.current?.contains(target)) setOpen(false);
    };
    document.addEventListener("mousedown", onPointerDown);
    return () => document.removeEventListener("mousedown", onPointerDown);
  }, [open]);

  useEffect(() => {
    if (!open || active < 0) return;
    panel.current?.querySelector<HTMLElement>(`[data-index="${active}"]`)?.scrollIntoView({ block: "nearest" });
  }, [open, active]);

  const step = (from: number, direction: number) => {
    if (!options.length) return -1;
    let index = from;
    for (let count = 0; count < options.length; count++) {
      index = (index + direction + options.length) % options.length;
      if (!options[index].disabled) return index;
    }
    return from;
  };

  function show() {
    setActive(selectedIndex >= 0 && !options[selectedIndex].disabled ? selectedIndex : step(-1, 1));
    setOpen(true);
  }

  function choose(index: number) {
    const option = options[index];
    if (!option || option.disabled) return;
    if (multiple) {
      const values = props.value as string[];
      props.onChange(values.includes(option.value) ? values.filter(item => item !== option.value) : [...values, option.value]);
      return;
    }
    props.onChange(option.value);
    setOpen(false);
    trigger.current?.focus();
  }

  function onKeyDown(event: KeyboardEvent<HTMLButtonElement>) {
    if (disabled) return;
    if (!open) {
      if (["ArrowDown", "ArrowUp", "Enter", " "].includes(event.key)) { event.preventDefault(); show(); }
      return;
    }
    if (event.key === "Escape") { event.preventDefault(); setOpen(false); trigger.current?.focus(); }
    else if (event.key === "ArrowDown") { event.preventDefault(); setActive(index => step(index, 1)); }
    else if (event.key === "ArrowUp") { event.preventDefault(); setActive(index => step(index, -1)); }
    else if (event.key === "Home") { event.preventDefault(); setActive(step(-1, 1)); }
    else if (event.key === "End") { event.preventDefault(); setActive(step(0, -1)); }
    else if (event.key === "Enter" || event.key === " ") { event.preventDefault(); choose(active); }
    else if (event.key === "Tab") setOpen(false);
  }

  return <span className="select">
    {name && <input type="hidden" name={name} value={multiple ? (props.value as string[]).join(",") : (props.value as string)} />}
    <button ref={trigger} type="button" className="select-trigger" role="combobox" aria-haspopup="listbox"
      aria-expanded={open} aria-controls={`${id}-list`} aria-describedby={describedBy} aria-label={label}
      aria-activedescendant={open && active >= 0 ? `${id}-${active}` : undefined}
      disabled={disabled} onClick={() => (open ? setOpen(false) : show())} onKeyDown={onKeyDown}>
      <span className={labels.length ? undefined : "select-placeholder"}>{labels.length ? labels.join(", ") : placeholder}</span>
      <svg className="select-chevron" aria-hidden width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m6 9 6 6 6-6" /></svg>
    </button>
    {open && <div ref={panel} className="select-panel" id={`${id}-list`} role="listbox" aria-multiselectable={multiple || undefined}>
      {options.map((option, index) => <div key={option.value} id={`${id}-${index}`} data-index={index} role="option"
        aria-selected={current.includes(option.value)} aria-disabled={option.disabled || undefined}
        className={`select-option${index === active ? " is-active" : ""}`}
        onMouseEnter={() => { if (!option.disabled) setActive(index); }}
        onMouseDown={event => event.preventDefault()} onClick={() => choose(index)}>
        <span className="select-check" aria-hidden>{current.includes(option.value) ? "✓" : ""}</span>
        <span>{option.label}</span>
      </div>)}
    </div>}
  </span>;
}
