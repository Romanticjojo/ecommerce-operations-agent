import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { ArrowRight, ArrowUpRight, ChevronRight, CornerDownLeft, Languages } from 'lucide-react'
import { api, errorText, useResource } from './api'
import type { Answer, Config, Skill } from './api'
import { BAD_RANGE, DateFields, Investigate, QueryResult } from './Analysis'
import { DataPage } from './Library'
import { ErrorBox, Fold, PageHead } from './ui'

const examples = [
  'What is total item revenue?',
  'Show monthly item revenue.',
  'Show the top 10 product categories by item revenue in 2018.',
]
const tools = [
  { id: '', name: 'Questions & skills', href: '#ask' },
  { id: 'delivery', name: 'Delivery comparison', href: '#ask/delivery' },
  { id: 'data', name: 'Data reference', href: '#ask/data' },
]

function SkillDirectory({ skills, selected, busy, choose }: {
  skills: Skill[]; selected: string; busy: boolean; choose: (id: string) => void
}) {
  return <aside className="skill-directory" aria-label="Analysis skills">
    <h2>Analysis skills</h2>
    <div className="desktop-skills">{skills.map(s =>
      <button key={s.id} type="button" aria-pressed={s.id === selected} disabled={busy} onClick={() => choose(s.id)}>
        <span>{s.title}</span><ChevronRight size={15} aria-hidden="true"/>
      </button>
    )}</div>
    <select className="mobile-skills" aria-label="Choose an analysis skill" disabled={busy} value={selected} onChange={e => choose(e.target.value)}>
      <option value="">Choose a skill…</option>{skills.map(s => <option key={s.id} value={s.id}>{s.title}</option>)}
    </select>
  </aside>
}

export function Ask({ config, tool = '' }: { config?: Config; tool?: string }) {
  const catalog = useResource<{skills: Skill[]}>('skills')
  const [selected, setSelected] = useState('')
  const skill = catalog.data?.skills.find(s => s.id === selected)
  const [question, setQuestion] = useState('')
  const [language, setLanguage] = useState('en')
  const [start, setStart] = useState(''), [end, setEnd] = useState('')
  const [result, setResult] = useState<Answer>()
  const [busy, setBusy] = useState(false), [error, setError] = useState('')
  const resultAnchor = useRef<HTMLDivElement>(null)
  const input = useRef<HTMLTextAreaElement>(null)
  const effectiveQuestion = skill?.question || question.trim()
  function choose(id: string) {
    setSelected(id)
    setResult(undefined)
    setError('')
  }
  async function submit(event: FormEvent) {
    event.preventDefault()
    if (busy || !effectiveQuestion) return
    if (start && end && start >= end) { setError(BAD_RANGE); return }
    setBusy(true)
    setError('')
    setResult(undefined)
    try {
      setResult(await api<Answer>('query', {
        question: effectiveQuestion, skill_id: skill?.id, language: skill ? 'en' : language,
        start: start || undefined, end: end || undefined,
      }))
    } catch (err) { setError(errorText(err)) }
    finally { setBusy(false) }
  }
  useEffect(() => {
    if (result && resultAnchor.current?.offsetParent) resultAnchor.current.focus()
  }, [result])
  const dates = (start || end) ? 'Purchase dates · ' + (start || 'First purchase') + ' to ' + (end || 'Last purchase') : 'Purchase dates'
  return <div className="ask-workbench">
    <PageHead title="Ask the agent" sub="Ask a business question or choose a skill to analyze the current snapshot."/>
    <nav className="ask-tools" aria-label="Agent tools">{tools.map(t =>
      <a key={t.id} href={t.href} aria-current={tool === t.id ? 'page' : undefined}>{t.name}</a>
    )}</nav>
    <div hidden={!!tool}>
      {catalog.error && <ErrorBox message={'Skill library unavailable. ' + catalog.error} retry={catalog.retry}/>}
      <div className="ask-layout">
        {catalog.data && <SkillDirectory skills={catalog.data.skills} selected={selected} busy={busy} choose={choose}/>}
        <div className="ask-composer">
          <form className="form-panel question-form" onSubmit={submit}>
            {skill ? <div className="skill-sheet">
              <button type="button" className="back-question" disabled={busy} onClick={() => {
                choose('')
                requestAnimationFrame(() => input.current?.focus())
              }}>← Back to custom question</button>
              <h2>{skill.title}</h2><p className="skill-description">{skill.description}</p>
              <dl className="skill-brief"><div><dt>Scope</dt><dd>{skill.scope}</dd></div><div><dt>Question</dt><dd>{skill.question}</dd></div></dl>
              <Fold title="Analysis steps"><ol className="sop-steps">{skill.steps.map((s, i) => <li key={i}>{s}</li>)}</ol>
                {['merchant-score', 'reviews-aftercare'].includes(skill.id) && <a className="report-link" href="https://github.com/Romanticjojo/ecommerce-operations-agent/blob/main/docs/merchant-scoring.md" target="_blank" rel="noreferrer">Scoring and review methodology<ArrowUpRight size={15}/></a>}
              </Fold>
            </div> : <>
              <h2><label htmlFor="question">Business question</label></h2>
              <textarea id="question" ref={input} placeholder={examples[2]} maxLength={1500} required disabled={busy}
                value={question} onChange={e => setQuestion(e.target.value)}
                onKeyDown={e => { if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') { e.preventDefault(); e.currentTarget.form?.requestSubmit() } }}/>
            </>}
            <Fold title={dates}><DateFields {...{ start, end, setStart, setEnd }} disabled={busy}/></Fold>
            <div className="options-line">
              {skill ? <span className="field-note">Local skill · English</span> :
                <label className="language"><Languages size={16}/>Answer language<select value={language} disabled={busy} onChange={e => setLanguage(e.target.value)}><option value="en">English</option><option value="zh">Chinese</option></select></label>}
              <button className="primary" disabled={busy || !effectiveQuestion}><CornerDownLeft size={16}/>{busy ? 'Running…' : skill ? 'Run skill' : 'Run analysis'}</button>
            </div>
            {busy && <p role="status">Reading the snapshot…</p>}{error && <ErrorBox message={error}/>}
          </form>
          {!skill && !result && !busy && <section className="examples"><h2>Example questions</h2>
            {config?.mode === 'demo' && <p>These questions and all analysis skills run offline.</p>}
            <div>{examples.map(q => <button key={q} onClick={() => { setQuestion(q); input.current?.focus() }}><span>{q}</span><ArrowRight size={15}/></button>)}</div>
          </section>}
        </div>
      </div>
      {result && <div tabIndex={-1} ref={resultAnchor} className="result-anchor" aria-label="Completed analysis"><QueryResult key={result.request_id} result={result}/></div>}
    </div>
    {tool === 'delivery' && <Investigate/>}
    {tool === 'data' && <DataPage/>}
  </div>
}
