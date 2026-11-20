import { useState } from 'react'
import { ArrowDownToLine, ArrowRight, Database, FileCheck2, FileText, Search, SlidersHorizontal } from 'lucide-react'
import type { Answer, Catalog, Config, Evaluation, Investigation, Row, Run } from './api'
import { display, exportJson, modeName, number, percent, sourceName, stateName, useResource } from './api'
import { InvestigationResult, QueryResult } from './Analysis'
import { Empty, ErrorBox, Facts, Fold, PageHead, Pending, Table } from './ui'

function Preparation() {
  return <Fold title="Data setup"><p>From the project root, follow the README to import the Olist CSV files or generate a synthetic sample. Refresh this page to check the source, snapshot ID, and row counts.</p></Fold>
}
export function DataPage() {
  const { data, error, retry } = useResource<Catalog>('catalog')
  const [tab, setTab] = useState('tables')
  return <><div className="tool-heading"><h2>Data reference</h2><p>Check the source tables, metric definitions and import quality behind an answer.</p></div>
    {error ? <><ErrorBox message={error} retry={retry}/><Preparation/></> : !data ? <Pending/> : <>
      <div className="panel snapshot"><span className="quick-icon blue"><Database size={21}/></span><div><h2>{sourceName(data.source)}</h2><p>Snapshot <code>{display(data.snapshot)}</code>{(data.imported_at || data.audit?.imported_at) && <> · Imported {data.imported_at || data.audit?.imported_at}</>}</p></div></div>
      <div className="tabs" aria-label="Data views">{[['tables','Data dictionary'],['metrics','Metric catalog'],['quality','Data quality']].map(([id,name]) => <button key={id} aria-pressed={tab === id} onClick={() => setTab(id)}>{name}</button>)}</div>
      <section className="panel"><div className="panel-head"><div><h2>{tab === 'tables' ? 'Source tables and analytical views' : tab === 'metrics' ? 'Metric definitions' : 'Import quality report'}</h2><p>{tab === 'tables' ? 'Expand a table to see its fields and what each row represents.' : tab === 'metrics' ? 'How order, item, and review metrics are calculated.' : 'Missing values, duplicate records, and sample checks for this snapshot.'}</p></div></div>
        {tab === 'tables' && (data.tables?.length ? data.tables.map(t => <Fold key={t.name} title={t.name + ' · ' + number(t.rows) + ' rows'}><p>Row grain · {t.grain}</p>{Array.isArray(t.columns) ? <Table caption={t.name + ' fields'} rows={t.columns.map(col => col !== null && typeof col === 'object' ? col as Row : { name: col })}/> : <Facts value={t.columns}/>}</Fold>) : <Empty title="No source tables"/>)}
        {tab === 'metrics' && <div className="definition-list">{(data.metrics || []).map(m => <article key={m.id}><h3>{m.label} <code>{m.id}</code></h3><p>{m.definition}</p></article>)}</div>}
        {tab === 'quality' && <Facts value={data.quality}/>}
      </section><Preparation/>
    </>}</>
}
export function EvalPage({ config }: { config?: Config }) {
  const { data, error, retry } = useResource<Evaluation>('evaluation')
  const [filter, setFilter] = useState('')
  const results = Array.isArray(data?.results) ? data.results : []
  const summary = Array.isArray(data?.summary) ? data.summary.map(r => ({ ...r, variant: modeName(String(r.variant)), accuracy: percent(r.accuracy), execution_accuracy: percent(r.execution_accuracy), sql_success_rate: percent(r.sql_success_rate) })) : []
  const matches = results.filter(r => !filter.trim() || JSON.stringify(r).toLowerCase().includes(filter.trim().toLowerCase()))
  return <><PageHead title="Evaluation" sub="Compare the baseline and full workflow on the same set of questions." action={data && results.length > 0 ? <button className="secondary" onClick={() => exportJson(data,'evaluation')}><ArrowDownToLine size={16}/>Export evaluation</button> : undefined}/>
    {error ? <ErrorBox message={error} retry={retry}/> : !data ? <Pending/> : <>
      <section className="panel"><div className="panel-head"><div className="symbol-heading"><span className="icon-tile purple"><FileCheck2 size={19}/></span><h2>Evaluation summary</h2></div><span className="pill">{stateName(data.status)}</span></div>
        {data.mode != null && <p className="report-scope">{modeName(String(data.mode))} · {sourceName(String(data.source))}{data.model ? ' · ' + display(data.model) : ''}{data.human_review === 'pending' ? ' · Question set pending human review' : ''}</p>}
        {data.summary && Object.keys(data.summary).length > 0 ? (Array.isArray(data.summary) ? <Table rows={summary} caption="Evaluation summary"/> : <Facts value={data.summary}/>) : <Empty title="No evaluation summary yet">Run the evaluation command in the README, then refresh to see the results.</Empty>}
        {Object.keys(data).some(k => !['results','status','summary'].includes(k)) && <Fold title="Evaluation settings and metadata"><Facts value={Object.fromEntries(Object.entries(data).filter(([k]) => !['results','status','summary'].includes(k)))}/></Fold>}
      </section>
      <section className="panel"><div className="panel-head"><div><h2>Results by question</h2><p>{results.length} {results.length === 1 ? 'record' : 'records'}</p></div>{results.length > 0 && <label className="search"><Search size={16}/><input aria-label="Search evaluation results" placeholder="Search records" value={filter} onChange={e => setFilter(e.target.value)}/></label>}</div>
        {matches.length ? <Table rows={matches} caption="Evaluation results by question"/> : <Empty title={filter ? 'No matching records' : 'No question results yet'}/>}
      </section></>}
    {config && !config.configured && <div className="notice"><SlidersHorizontal size={18}/><span>Offline mode is active. To evaluate a live model, set its endpoint, model name, and API key in the local environment file, then restart the service.</span></div>}</>
}
function RunDetail({ id }: { id: string }) {
  const { data, error, retry } = useResource<Answer | Investigation>('runs/' + encodeURIComponent(id))
  if (error) return <ErrorBox message={error} retry={retry}/>
  if (!data) return <Pending/>
  return 'groups' in data ? <InvestigationResult result={data} grain={data.grain || 'timestamp'}/> : <QueryResult result={data}/>
}
export function History() {
  const { data, error, retry } = useResource<{ runs: Run[] }>('runs')
  const [id, setId] = useState<string>('')
  return <><PageHead title="Run history" sub="Revisit questions, investigations, and their evidence from this workspace."/>
    {error ? <ErrorBox message={error} retry={retry}/> : !data ? <Pending/> :
    <section className="panel"><div className="panel-head"><div className="symbol-heading"><span className="icon-tile blue"><FileText size={19}/></span><h2>Recent runs</h2></div><span className="pill">{data.runs.length} {data.runs.length === 1 ? 'run' : 'runs'}</span></div>
    {id ? <button className="quiet" onClick={() => setId('')}>Back to all runs</button> : data.runs.length ? <div className="history-list">{data.runs.map(r => <button key={r.request_id} aria-expanded={id === r.request_id} onClick={() => setId(id === r.request_id ? '' : r.request_id)}><span className="history-text"><strong>{r.question || 'Delivery and review investigation'}</strong><small>{r.created_at} · {modeName(r.mode)} · {r.request_id}</small></span><span className="pill">{stateName(r.status)}</span><ArrowRight size={16}/></button>)}</div> : <Empty title="No runs yet" action={<a className="quiet" href="#ask">Ask the agent<ArrowRight size={15}/></a>}>Run an analysis or investigation to see the results here.</Empty>}</section>}
    {id && <><h2 className="selected-question">{data?.runs.find(r => r.request_id === id)?.question}</h2><RunDetail key={id} id={id}/></>}</>
}
