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
  const [total, setTotal] = useState(0);
  useEffect(() => {
    if (selected) input.current?.form?.requestSubmit();
  }, [selected]);
  useEffect(() => {
    if (!open) return;
    let current = true;
    setLoading(true); setError(""); setSuggestions([]); setActive(-1);
    const timer = setTimeout(() => {
      api<{ companies: Company[]; total: number }>(`/jobs/companies?q=${encodeURIComponent(text)}&limit=20`)
        .then(data => { if (current) { setSuggestions(data.companies); setTotal(data.total); } })
        .catch(error => { if (current) setError(error.message); })
        .finally(() => { if (current) setLoading(false); });
    }, 200);
    return () => { current = false; clearTimeout(timer); };
  }, [text, open]);

  function choose(company: Company) {
    setText(company.company); setSelected(company); setOpen(false); setActive(-1);
  }
  const resolvedCompany = selected?.company
    || suggestions.find(company => company.company.toLowerCase() === text.trim().toLowerCase() || company.slug.toLowerCase() === text.trim().toLowerCase())?.company
    || text.trim();
  return <div className="company-filter" onBlur={event => {
    if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false);
  }}>
    <label htmlFor={id}>Company</label>
    <input ref={input} id={id} role="combobox" aria-autocomplete="list" aria-expanded={open}
      aria-controls={`${id}-options`} aria-activedescendant={open && active >= 0 ? `${id}-option-${active}` : undefined}
      autoComplete="off" placeholder="Type a company name…" value={text}
      onFocus={() => setOpen(true)}
      onChange={event => {
        setText(event.target.value); setSelected(null); setOpen(true); setActive(-1); setSuggestions([]);
      }}
      onKeyDown={event => {
        if (event.key === "Escape") { setOpen(false); setActive(-1); }
        if (event.key === "ArrowDown" || event.key === "ArrowUp") {
          event.preventDefault(); setOpen(true);
          setActive(index => !suggestions.length ? -1 : index < 0 ? (event.key === "ArrowDown" ? 0 : suggestions.length - 1) : (index + (event.key === "ArrowDown" ? 1 : -1) + suggestions.length) % suggestions.length);
        }
        const exact = suggestions.find(company => company.company.toLowerCase() === text.trim().toLowerCase() || company.slug.toLowerCase() === text.trim().toLowerCase());
        if (event.key === "Enter" && open && (suggestions[active] || exact)) {
          event.preventDefault(); choose(suggestions[active] || exact!);
        }
      }} />
    <input type="hidden" name="company" value={resolvedCompany} />
    {open && <div className="company-suggestions">
      {!loading && !error && total > suggestions.length && <p className="small muted" role="status">Showing {suggestions.length} of {total.toLocaleString()} companies. Type a name to search the full catalog.</p>}
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
