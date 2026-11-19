import { useState } from 'react'
import { ArrowDownToLine, ArrowRight, Database, FileCheck2, FileText, Search, SlidersHorizontal } from 'lucide-react'
import type { Answer, Catalog, Config, Evaluation, Investigation, Row, Run } from './api'
import { display, exportJson, modeName, number, percent, sourceName, stateName, useResource } from './api'
import { InvestigationResult, QueryResult } from './Analysis'
import { Empty, ErrorBox, Facts, Fold, PageHead, Pending, Table } from './ui'

function Preparation() {
  return <Fold title="数据准备说明"><p>在项目根目录按照 README 生成合成示例，或导入本地 Olist CSV。导入完成后刷新本页，核对数据来源、快照与各表行数。</p></Fold>
}
export function DataPage() {
  const { data, error, retry } = useResource<Catalog>('catalog')
  const [tab, setTab] = useState('tables')
  return <><PageHead title="数据与指标" sub="检查数据快照、表粒度、指标口径与导入质量。"/>
    {error ? <><ErrorBox message={error} retry={retry}/><Preparation/></> : !data ? <Pending/> : <>
      <div className="panel snapshot"><span className="quick-icon blue"><Database size={21}/></span><div><h2>{sourceName(data.source)}</h2><p>快照 <code>{display(data.snapshot)}</code>{(data.imported_at || data.audit?.imported_at) && <> · 导入于 {data.imported_at || data.audit?.imported_at}</>}</p></div></div>
      <div className="tabs" aria-label="数据视图">{[['tables','数据字典'],['metrics','指标目录'],['quality','数据质量']].map(([id,name]) => <button key={id} aria-pressed={tab === id} onClick={() => setTab(id)}>{name}</button>)}</div>
      <section className="panel"><div className="panel-head"><div><h2>{tab === 'tables' ? '源表与分析视图' : tab === 'metrics' ? '指标定义' : '导入质量报告'}</h2><p>{tab === 'tables' ? '展开表名可查看字段和统计粒度。' : tab === 'metrics' ? '订单、商品与评价指标的计算依据。' : '当前快照的缺失、重复与样本审计。'}</p></div></div>
        {tab === 'tables' && (data.tables?.length ? data.tables.map(t => <Fold key={t.name} title={t.name + ' · ' + number(t.rows) + ' 行'}><p>粒度 · {t.grain}</p>{Array.isArray(t.columns) ? <Table caption={t.name + ' 字段说明'} rows={t.columns.map(col => col !== null && typeof col === 'object' ? col as Row : { name: col })}/> : <Facts value={t.columns}/>}</Fold>) : <Empty title="尚无源表"/>)}
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
  return <><PageHead title="评估记录" sub="查看固定题集的执行结果，比较基线与完整工作流。" action={data && results.length > 0 ? <button className="secondary" onClick={() => exportJson(data,'evaluation')}><ArrowDownToLine size={16}/>导出评估</button> : undefined}/>
    {error ? <ErrorBox message={error} retry={retry}/> : !data ? <Pending/> : <>
      <section className="panel"><div className="panel-head"><div className="symbol-heading"><span className="icon-tile purple"><FileCheck2 size={19}/></span><h2>评估概况</h2></div><span className="pill">{stateName(data.status)}</span></div>
        {data.mode != null && <p className="report-scope">{modeName(String(data.mode))} · {sourceName(String(data.source))}{data.model ? ' · ' + display(data.model) : ''}{data.human_review === 'pending' ? ' · 题集待人工复核' : ''}</p>}
        {data.summary && Object.keys(data.summary).length > 0 ? (Array.isArray(data.summary) ? <Table rows={summary} caption="评估汇总"/> : <Facts value={data.summary}/>) : <Empty title="尚无评估汇总">在本地运行 README 的评估命令后，刷新此页查看成绩。</Empty>}
        {Object.keys(data).some(k => !['results','status','summary'].includes(k)) && <Fold title="评估环境与元数据"><Facts value={Object.fromEntries(Object.entries(data).filter(([k]) => !['results','status','summary'].includes(k)))}/></Fold>}
      </section>
      <section className="panel"><div className="panel-head"><div><h2>逐题结果</h2><p>共 {results.length} 条记录</p></div>{results.length > 0 && <label className="search"><Search size={16}/><input aria-label="搜索评估结果" placeholder="搜索记录" value={filter} onChange={e => setFilter(e.target.value)}/></label>}</div>
        {matches.length ? <Table rows={matches} caption="逐题评估记录"/> : <Empty title={filter ? '没有匹配的记录' : '尚无逐题结果'}/>}
      </section></>}
    {config && !config.configured && <div className="notice"><SlidersHorizontal size={18}/><span>当前使用离线演示。在本地环境文件配置兼容模型服务、模型名称和密钥，再重启服务，即可开展真实模型评估。</span></div>}</>
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
  return <><PageHead title="运行历史" sub="回看本地保存的提问、调查与查询证据。"/>
    {error ? <ErrorBox message={error} retry={retry}/> : !data ? <Pending/> :
    <section className="panel"><div className="panel-head"><div className="symbol-heading"><span className="icon-tile blue"><FileText size={19}/></span><h2>最近运行</h2></div><span className="pill">{data.runs.length} 条</span></div>
    {id ? <button className="quiet" onClick={() => setId('')}>返回全部记录</button> : data.runs.length ? <div className="history-list">{data.runs.map(r => <button key={r.request_id} aria-expanded={id === r.request_id} onClick={() => setId(id === r.request_id ? '' : r.request_id)}><span className="history-text"><strong>{r.question || '配送与差评调查'}</strong><small>{r.created_at} · {modeName(r.mode)} · {r.request_id}</small></span><span className="pill">{stateName(r.status)}</span><ArrowRight size={16}/></button>)}</div> : <Empty title="尚无运行记录" action={<a className="quiet" href="#ask">前往分析工作台<ArrowRight size={15}/></a>}>运行一次分析或调查后，可在这里复核结果。</Empty>}</section>}
    {id && <><h2 className="selected-question">{data?.runs.find(r => r.request_id === id)?.question}</h2><RunDetail key={id} id={id}/></>}</>
}
