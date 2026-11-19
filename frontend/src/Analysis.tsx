import { useState } from 'react'
import type { FormEvent } from 'react'
import { ArrowDownToLine, CheckCircle2, ChevronRight, CircleAlert, CornerDownLeft, Info, Languages, ScanSearch, Sparkles } from 'lucide-react'
import { api, display, errorText, exportJson, modeName, number, percent, stateName } from './api'
import type { Answer, Config, Investigation } from './api'
import { BarChart, ErrorBox, Facts, Fold, PageHead, Sql, Table, Trend } from './ui'

export function DateFields({ start, end, setStart, setEnd }: { start: string; end: string; setStart: (s: string) => void; setEnd: (s: string) => void }) {
  return <div className="dates"><label>开始日期<input type="date" value={start} onChange={e => setStart(e.target.value)}/></label><label>结束日期（不含当日）<input type="date" value={end} onChange={e => setEnd(e.target.value)}/></label></div>
}
const BAD_RANGE = '结束日期须晚于开始日期，请调整时间范围。'
const examples = ['Show the top 10 product categories by item revenue in 2018.', '按月统计商品成交额', 'Are late deliveries associated with negative customer reviews?']
export function Ask({ config }: { config?: Config }) {
  const [question, setQuestion] = useState('')
  const [language, setLanguage] = useState('zh')
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
  return <><PageHead title="分析工作台" sub="用中文或英文提问，查看经营数据和实际执行的查询。"/>
    <form className="panel form-panel" onSubmit={submit}><div className="panel-head"><div className="symbol-heading"><span className="icon-tile blue"><Sparkles size={19}/></span><h2><label htmlFor="question">经营问题</label></h2></div><span className="pill">{modeName(config?.mode)}</span></div>
      <textarea id="question" placeholder="例如：2018 年哪些品类的商品成交额最高？" maxLength={1500} required value={question} onChange={e => setQuestion(e.target.value)} onKeyDown={e => { if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') { e.preventDefault(); e.currentTarget.form?.requestSubmit() } }}/>
      <div className="options-line"><label className="language"><Languages size={16}/>回答语言<select value={language} onChange={e => setLanguage(e.target.value)}><option value="zh">中文</option><option value="en">English</option></select></label>
      <button className="primary" disabled={busy || !question.trim()}><CornerDownLeft size={16}/>{busy ? '正在执行…' : '运行分析'}</button></div>
      <Fold title="日期筛选"><DateFields {...{ start, end, setStart, setEnd }}/></Fold>
      {busy && <p role="status">已提交问题，正在等待查询服务返回结果。</p>}{error && <ErrorBox message={error}/>}
    </form>
    {!result && !busy && <section className="examples"><h2>试试这些问题</h2><div>{examples.map(q => <button key={q} onClick={() => { setQuestion(q); document.getElementById('question')?.focus() }}><Sparkles size={16}/><span>{q}</span><ChevronRight size={16}/></button>)}</div></section>}
    {result && <QueryResult key={result.request_id} result={result}/>}</>
}
export function QueryResult({ result }: { result: Answer }) {
  const [view, setView] = useState('chart')
  const { sql, ...evidence } = result.evidence || {}
  const ok = ['ok', 'success', 'completed'].includes(result.status)
  const chart = result.chart
  const hasChart = chart && result.table?.length && result.table.some(r => typeof r[chart.y] === 'number')
  return <section className="panel result-panel" aria-label="分析结果"><div className="panel-head"><div className="symbol-heading">{ok ? <CheckCircle2 size={20} className="success-text"/> : <CircleAlert size={20}/>}<h2>分析结果</h2></div><button className="quiet" onClick={() => exportJson(result, result.request_id)}><ArrowDownToLine size={16}/>导出结果</button></div>
    <div className="meta-line"><span className="pill">{stateName(result.status)}</span><span>{modeName(result.mode)}</span><span>{number(result.timing_ms)} ms</span></div>
    <p className="answer" role="status" lang={evidence.language === "en" ? "en" : "zh-CN"}>{result.answer}</p>
    {!!result.table?.length && <><div className="panel-head compact"><h3>查询数据</h3>{!!hasChart && <div className="seg">{['chart', 'table'].map(v => <button key={v} aria-pressed={view === v} onClick={() => setView(v)}>{v === 'chart' ? '图表' : '表格'}</button>)}</div>}</div>
      {!!hasChart && view === 'chart' ? (chart.type === 'line' ? <Trend rows={result.table} x={chart.x} y={chart.y} unit={/revenue|aov|value|amount/i.test(chart.y) ? 'BRL' : ''}/> : <BarChart rows={result.table} x={chart.x} y={chart.y} formatter={v => number(v, Number.isInteger(v) ? 0 : 2)}/>) : <Table rows={result.table} caption="查询数据"/>}</>}
    <Fold title="查询证据与 SQL"><Facts value={{request_id: result.request_id, ...evidence}}/><Sql sql={sql}/></Fold>
  </section>
}
function pointDifference(n: number | null | undefined) { return n == null ? '—' : number(n * 100, 1) + ' 个百分点' }
export function InvestigationResult({ result, grain }: { result: Investigation; grain: string }) {
  return <section className="panel result-panel"><div className="panel-head"><div><h2>{grain === 'day' ? '按日比较' : '按时间戳比较'}结果</h2><p>{stateName(result.status)}</p></div><button className="quiet" onClick={() => exportJson(result, result.request_id)}><ArrowDownToLine size={16}/>导出结果</button></div>
    <div className="group-cards">{(result.groups || []).map(g => <div key={g.group}><small>{g.group === 'late' ? '延迟送达' : '准时送达'}</small><strong>{percent(g.rate)}</strong><span>{number(g.negative)} 笔差评 / {number(g.n)} 笔订单</span></div>)}</div>
    <dl className="stat-list"><div><dt>差评率差值（延迟 − 准时）</dt><dd>{pointDifference(result.risk_difference)}</dd></div><div><dt>95% 置信区间</dt><dd>{result.ci95 && result.ci95.every(n => n != null) ? result.ci95.map(n => number(n * 100, 1)).join(' 至 ') + ' 个百分点' : '—'}</dd></div><div><dt>检验方法</dt><dd>{display(result.test)}</dd></div><div><dt>p 值</dt><dd>{result.p_value == null ? '—' : result.p_value < .001 ? '< 0.001' : result.p_value.toPrecision(4)}</dd></div></dl>
    <h3>样本限制</h3><Facts value={result.limitations}/>
    {result.review_records && <Fold title="评价记录级统计"><p>按有效评价记录计数，同一笔订单可包含多条评价。</p><Facts value={{ '评价记录数': result.review_records.n, '差评记录数': result.review_records.negative, rate: percent(result.review_records.rate) }}/><Sql sql={result.review_records_sql}/></Fold>}
    <Fold title="排除记录与 SQL"><Facts value={{ request_id: result.request_id, snapshot: result.snapshot_id, filters: result.filters }}/><Facts value={result.exclusions}/><Sql sql={result.sql}/>
      {result.exclusions_sql && <Fold title="排除计数 SQL"><Sql sql={result.exclusions_sql}/></Fold>}</Fold>
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
  return <><PageHead title="差评调查" sub="比较延迟送达与准时送达订单的差评率。"/><div className="notice"><Info size={18}/>观察性关联，不能证明因果。</div>
    <form className="panel form-panel" onSubmit={e => { e.preventDefault(); void run(grain) }}><div className="panel-head"><div className="symbol-heading"><span className="icon-tile teal"><ScanSearch size={19}/></span><h2>样本与比较口径</h2></div></div>
    <p className="body-copy">纳入已送达、有有效评分且实际与预计送达时间齐全的订单。每单取一条有效评价，1–2 分计为差评。</p>
    <fieldset disabled={busy}><legend>延迟定义</legend><div className="choice-row">{['timestamp', 'day'].map(v => <label key={v}><input type="radio" name="grain" checked={grain === v} onChange={() => { setGrain(v); if (result) void run(v) }}/>{v === 'day' ? '按日比较' : '按时间戳比较'}</label>)}</div></fieldset>
    <p className="field-note">{grain === 'day' ? '实际送达日期晚于预计日期计为延迟。' : '实际送达时间晚于预计时间计为延迟，包括同日较晚送达。'}</p><DateFields {...{ start, end, setStart, setEnd }}/>
    <div className="form-actions"><button className="primary" disabled={busy}><ScanSearch size={16}/>{busy ? '正在调查…' : '运行调查'}</button></div>{busy && <p role="status">正在按所选口径计算订单级统计。</p>}{error && <ErrorBox message={error}/>}</form>
    {result && <InvestigationResult result={result} grain={usedGrain}/>}</>
}
