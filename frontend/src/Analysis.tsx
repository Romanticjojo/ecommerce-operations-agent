import { useState } from 'react'
import type { FormEvent } from 'react'
import { ArrowDownToLine, CheckCircle2, ChevronRight, CircleAlert, CornerDownLeft, Info, Languages, ScanSearch } from 'lucide-react'
import { api, display, errorText, exportJson, modeName, number, percent, stateName } from './api'
import type { Answer, Config, Investigation } from './api'
import { BarChart, ErrorBox, Facts, Fold, PageHead, Sql, Table, Trend } from './ui'

export function DateFields({ start, end, setStart, setEnd }: { start: string; end: string; setStart: (s: string) => void; setEnd: (s: string) => void }) {
  return <div className="dates"><label>Start date<input type="date" value={start} onChange={e => setStart(e.target.value)}/></label><label>End date (exclusive)<input type="date" value={end} onChange={e => setEnd(e.target.value)}/></label></div>
}
const BAD_RANGE = 'Choose an end date after the start date.'
const examples = [
  'What is total item revenue?',
  'Show monthly item revenue.',
  'Show the top 10 product categories by item revenue in 2018.',
]
export function Ask({ config }: { config?: Config }) {
  const [question, setQuestion] = useState('')
  const [language, setLanguage] = useState('en')
  const [start, setStart] = useState(''), [end, setEnd] = useState('')
  const [result, setResult] = useState<Answer>()
  const [busy, setBusy] = useState(false), [error, setError] = useState('')
  async function submit(e: FormEvent) {
    e.preventDefault()
    if (busy || !question.trim()) return
    if (start && end && start >= end) { setError(BAD_RANGE); return }
    setBusy(true); setError(''); setResult(undefined)
    try { setResult(await api<Answer>('query', { question: question.trim(), language, start: start || undefined, end: end || undefined })) }
    catch (err) { setError(errorText(err)) }
    finally { setBusy(false) }
  }
  return <><PageHead title="Ask the agent" sub={config?.mode === 'demo' ? 'Choose an example question to run offline. Use the date filter to narrow the results.' : 'Ask about sales, orders, or reviews. Filter by purchase date to narrow the results.'}/>
    <form className="panel form-panel" onSubmit={submit}><div className="panel-head"><div className="symbol-heading"><h2><label htmlFor="question">Business question</label></h2></div></div>
      <textarea id="question" placeholder={examples[2]} maxLength={1500} required value={question} onChange={e => setQuestion(e.target.value)} onKeyDown={e => { if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') { e.preventDefault(); e.currentTarget.form?.requestSubmit() } }}/>
      <div className="options-line"><label className="language"><Languages size={16}/>Answer language<select value={language} onChange={e => setLanguage(e.target.value)}><option value="en">English</option><option value="zh">Chinese</option></select></label>
      <button className="primary" disabled={busy || !question.trim()}><CornerDownLeft size={16}/>{busy ? 'Running…' : 'Run analysis'}</button></div>
      <Fold title="Date filter"><DateFields {...{ start, end, setStart, setEnd }}/></Fold>
      {busy && <p role="status">Running your query…</p>}{error && <ErrorBox message={error}/>}
    </form>
    {!result && !busy && <section className="examples"><h2>Example questions</h2><div>{examples.map(q => <button key={q} onClick={() => { setQuestion(q); document.getElementById('question')?.focus() }}><span>{q}</span><ChevronRight size={16}/></button>)}</div></section>}
    {result && <QueryResult key={result.request_id} result={result}/>}</>
}
export function QueryResult({ result }: { result: Answer }) {
  const [view, setView] = useState('chart')
  const { sql, ...evidence } = result.evidence || {}
  const ok = ['ok', 'success', 'completed'].includes(result.status)
  const chart = result.chart
  const hasChart = chart && result.table?.length && result.table.some(r => typeof r[chart.y] === 'number')
  return <section className="panel result-panel" aria-label="Analysis result"><div className="panel-head"><div className="symbol-heading">{ok ? <CheckCircle2 size={20} className="success-text"/> : <CircleAlert size={20}/>}<h2>Analysis result</h2></div><button className="quiet" onClick={() => exportJson(result, result.request_id)}><ArrowDownToLine size={16}/>Export result</button></div>
    <div className="meta-line"><span className="pill">{stateName(result.status)}</span><span>{modeName(result.mode)}</span><span>{number(result.timing_ms)} ms</span></div>
    <p className="answer" role="status" lang={evidence.language === "zh" ? "zh-CN" : "en"}>{result.answer}</p>
    {!!result.table?.length && <><div className="panel-head compact"><h3>Query data</h3>{!!hasChart && <div className="seg">{['chart', 'table'].map(v => <button key={v} aria-pressed={view === v} onClick={() => setView(v)}>{v === 'chart' ? 'Chart' : 'Table'}</button>)}</div>}</div>
      {!!hasChart && view === 'chart' ? (chart.type === 'line' ? <Trend rows={result.table} x={chart.x} y={chart.y} unit={/revenue|aov|value|amount/i.test(chart.y) ? 'BRL' : ''}/> : <BarChart rows={result.table} x={chart.x} y={chart.y} formatter={v => number(v, Number.isInteger(v) ? 0 : 2)}/>) : <Table rows={result.table} caption="Query data"/>}</>}
    <Fold title="Query evidence and SQL"><Sql sql={sql}/><Fold title="Metrics, filters, and execution details"><Facts value={{request_id: result.request_id, ...evidence}}/></Fold></Fold>
  </section>
}
function pointDifference(n: number | null | undefined) { return n == null ? '—' : number(n * 100, 1) + ' percentage points' }
export function InvestigationResult({ result, grain }: { result: Investigation; grain: string }) {
  return <section className="panel result-panel"><div className="panel-head"><div><h2>{grain === 'day' ? 'Calendar-day comparison' : 'Timestamp comparison'}</h2><p>{stateName(result.status)}</p></div><button className="quiet" onClick={() => exportJson(result, result.request_id)}><ArrowDownToLine size={16}/>Export result</button></div>
    <div className="group-cards">{(result.groups || []).map(g => <div key={g.group}><small>{g.group === 'late' ? 'Late deliveries' : 'On-time deliveries'}</small><strong>{percent(g.rate)}</strong><span>{number(g.negative)} negative / {number(g.n)} orders</span></div>)}</div>
    <dl className="stat-list"><div><dt>Difference in negative review rates (late − on time)</dt><dd>{pointDifference(result.risk_difference)}</dd></div><div><dt>95% confidence interval</dt><dd>{result.ci95 && result.ci95.every(n => n != null) ? result.ci95.map(n => number(n * 100, 1)).join(' to ') + ' percentage points' : '—'}</dd></div><div><dt>Statistical test</dt><dd>{result.test === 'pearson_chi2' ? 'Pearson chi-square' : result.test === 'fisher_exact' ? 'Fisher exact test' : display(result.test)}</dd></div><div><dt>p-value</dt><dd>{result.p_value == null ? '—' : result.p_value < .001 ? '< 0.001' : result.p_value.toPrecision(4)}</dd></div></dl>
    <h3>Limitations</h3><Facts value={result.limitations}/>
    {result.review_records && <Fold title="Review-level counts"><p>These counts include each eligible review. An order can have multiple reviews.</p><Facts value={{ 'Reviews': result.review_records.n, 'Negative reviews': result.review_records.negative, rate: percent(result.review_records.rate) }}/><Sql sql={result.review_records_sql}/></Fold>}
    <Fold title="Exclusions and SQL"><Facts value={{ request_id: result.request_id, snapshot: result.snapshot_id, filters: result.filters }}/><Facts value={result.exclusions}/><Sql sql={result.sql}/>
      {result.exclusions_sql && <Fold title="SQL for exclusion counts"><Sql sql={result.exclusions_sql}/></Fold>}</Fold>
  </section>
}
export function Investigate() {
  const [grain, setGrain] = useState('timestamp'), [start, setStart] = useState(''), [end, setEnd] = useState('')
  const [result, setResult] = useState<Investigation>(), [usedGrain, setUsedGrain] = useState('timestamp')
  const [error, setError] = useState(''), [busy, setBusy] = useState(false)
  async function run(nextGrain: string) {
    if (busy) return
    if (start && end && start >= end) {setError(BAD_RANGE); return}
    setBusy(true); setError(''); setResult(undefined)
    try { setResult(await api<Investigation>('investigation', { start: start || undefined, end: end || undefined, grain: nextGrain })); setUsedGrain(nextGrain) }
    catch (err) { setError(errorText(err)) } finally { setBusy(false) }
  }
  return <><PageHead title="Delivery and reviews" sub="Compare negative review rates for late and on-time orders."/><div className="notice"><Info size={18}/>This observational comparison measures association. Other factors may influence both delivery and ratings.</div>
    <form className="panel form-panel" onSubmit={e => { e.preventDefault(); void run(grain) }}><div className="panel-head"><div className="symbol-heading"><span className="icon-tile teal"><ScanSearch size={19}/></span><h2>Sample and comparison</h2></div></div>
    <p className="body-copy">The sample includes delivered orders with a valid rating and both actual and estimated delivery timestamps. Each order contributes its latest eligible review. A score of 1 or 2 is negative.</p>
    <fieldset disabled={busy}><legend>Definition of late</legend><div className="choice-row">{['timestamp', 'day'].map(v => <label key={v}><input type="radio" name="grain" checked={grain === v} onChange={() => { setGrain(v); if (result) void run(v) }}/>{v === 'day' ? 'Calendar day' : 'Exact timestamp'}</label>)}</div></fieldset>
    <p className="field-note">{grain === 'day' ? 'An order is late if it arrives after the estimated calendar date.' : 'An order is late if it arrives after the estimated time, including later on the same day.'}</p><DateFields {...{ start, end, setStart, setEnd }}/>
    <div className="form-actions"><button className="primary" disabled={busy}><ScanSearch size={16}/>{busy ? 'Calculating…' : 'Run investigation'}</button></div>{busy && <p role="status">Calculating order-level statistics for this comparison…</p>}{error && <ErrorBox message={error}/>}</form>
    {result && <InvestigationResult result={result} grain={usedGrain}/>}</>
}
