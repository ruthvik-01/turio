"use client";
import { useEffect, useId, useRef, useState } from "react";
import { api } from "@/lib/api";

type Company = { company: string; slug: string };

export function CompanyFilter() {
  const id = useId();
  const input = useRef<HTMLInputElement>(null);
  const [text, setText] = useState("");
  const [selected, setSelected] = useState<Company | null>(null);
  const [suggestions, setSuggestions] = useState<Company[]>([]);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    if (selected) input.current?.form?.requestSubmit();
  }, [selected]);
  useEffect(() => {
    if (!open) return;
    let current = true;
    setLoading(true); setError(""); setSuggestions([]); setActive(-1);
    const timer = setTimeout(() => {
      api<{ companies: Company[] }>(`/jobs/companies?q=${encodeURIComponent(text)}&limit=20`)
        .then(data => { if (current) setSuggestions(data.companies); })
        .catch(error => { if (current) setError(error.message); })
        .finally(() => { if (current) setLoading(false); });
    }, 200);
    return () => { current = false; clearTimeout(timer); };
  }, [text, open]);

  function choose(company: Company) {
    setText(company.company); setSelected(company); setOpen(false); setActive(-1);
    input.current?.setCustomValidity("");
  }
  return <div className="company-filter" onBlur={event => {
    if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false);
  }}>
    <label htmlFor={id}>Company</label>
    <input ref={input} id={id} role="combobox" aria-autocomplete="list" aria-expanded={open}
      aria-controls={`${id}-options`} aria-activedescendant={open && active >= 0 ? `${id}-option-${active}` : undefined}
      autoComplete="off" placeholder="Search companies…" value={text}
      onFocus={() => setOpen(true)}
      onChange={event => {
        setText(event.target.value); setSelected(null); setOpen(true); setActive(-1); setSuggestions([]);
        event.target.setCustomValidity(event.target.value.trim() ? "Choose a company from the suggestions, or clear this field." : "");
      }}
      onKeyDown={event => {
        if (event.key === "Escape") { setOpen(false); setActive(-1); }
        if (event.key === "ArrowDown" || event.key === "ArrowUp") {
          event.preventDefault(); setOpen(true);
          setActive(index => !suggestions.length ? -1 : index < 0 ? (event.key === "ArrowDown" ? 0 : suggestions.length - 1) : (index + (event.key === "ArrowDown" ? 1 : -1) + suggestions.length) % suggestions.length);
        }
        if (event.key === "Enter" && open && active >= 0 && suggestions[active]) {
          event.preventDefault(); choose(suggestions[active]);
        }
      }} />
    <input type="hidden" name="company" value={selected?.company || ""} />
    {open && <div className="company-suggestions">
      <ul id={`${id}-options`} role="listbox" aria-label="Company suggestions">
        {suggestions.map((company, index) => <li key={company.slug} id={`${id}-option-${index}`} role="option"
          aria-selected={index === active} onMouseDown={event => event.preventDefault()}
          onMouseEnter={() => setActive(index)} onClick={() => choose(company)}>
          <span>{company.company}</span><small className="muted">{company.slug}</small>
        </li>)}
      </ul>
      {(loading || error || !suggestions.length) && <p className="small muted" role="status">{loading ? "Searching companies…" : error || "No catalog companies found."}</p>}
    </div>}
  </div>;
}
