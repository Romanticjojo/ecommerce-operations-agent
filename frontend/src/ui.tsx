import { useEffect, useId, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { AlertCircle, Check, ChevronDown, Clipboard, Database, FileSearch, LoaderCircle, RefreshCw } from 'lucide-react'
import { display, label, number } from './api'
import type { Row } from './api'

export function PageHead({ title, sub, action }: { title: string; sub?: string; action?: ReactNode }) {
  return <header className="page-head"><div><h1>{title}</h1>{sub && <p>{sub}</p>}</div>{action}</header>
}
export function Pending() {
  return <div className="blank" role="status"><LoaderCircle className="spin" size={22}/>正在读取数据…</div>
}
export function ErrorBox({ message, retry }: { message: string; retry?: () => void }) {
  return <div className="error" role="alert"><AlertCircle size={19}/><span>{message}</span>{retry && <button className="quiet" onClick={retry}><RefreshCw size={15}/>重试</button>}</div>
}
export function Empty({ title, children, action }: { title: string; children?: ReactNode; action?: ReactNode }) {
  return <div className="empty"><FileSearch size={28}/><strong>{title}</strong>{children && <p>{children}</p>}{action}</div>
}
export function Table({ rows, caption = '数据表' }: { rows?: Row[]; caption?: string }) {
  if (!rows?.length) return <Empty title="没有可显示的数据"/>
  const keys = [...new Set(rows.flatMap(r => Object.keys(r)))]
  return <div className="table-scroll" tabIndex={0} role="region" aria-label={caption}><table><caption className="sr-only">{caption}</caption>
    <thead><tr>{keys.map(k => <th key={k} scope="col">{label(k)}</th>)}</tr></thead>
    <tbody>{rows.map((r, i) => <tr key={i}>{keys.map(k => <td key={k}>{display(r[k])}</td>)}</tr>)}</tbody>
  </table></div>
}
export function Facts({ value }: { value: unknown }) {
  if (Array.isArray(value)) return value.length ? <ul className="fact-items">{value.map((item, i) => <li key={i}><Facts value={item}/></li>)}</ul> : <div className="fact-value">无</div>
  if (!value || typeof value !== 'object') return <div className="fact-value">{display(value)}</div>
  return <dl className="facts">{Object.entries(value).map(([k, v]) =>
    <div key={k}><dt>{label(k)}</dt><dd>{v !== null && typeof v === 'object' ? <Facts value={v}/> : display(v)}</dd></div>)}</dl>
}
export function Fold({ title, children, open }: { title: string; children: ReactNode; open?: boolean }) {
  return <details className="fold" open={open}><summary>{title}<ChevronDown size={16}/></summary><div className="fold-body">{children}</div></details>
}
export function Sql({ sql }: { sql: unknown }) {
  const [feedback, setFeedback] = useState('')
  if (typeof sql !== 'string' || !sql.trim()) return null
  async function copy() {
    try {
      await navigator.clipboard.writeText(String(sql)); setFeedback('已复制 SQL')
    } catch { setFeedback('请选中下方 SQL 并复制。') }
  }
  return <section className="sql"><div><span><Database size={15}/>执行 SQL</span><button className="copy" onClick={copy}>{feedback === '已复制 SQL' ? <Check size={15}/> : <Clipboard size={15}/>}复制 SQL</button></div>
    <pre tabIndex={0}>{sql}</pre><span className="copy-message" role="status">{feedback}</span></section>
}
export const chartColors = ['#0071e3', '#3187d9', '#5098d6', '#65a0c9', '#82adbf', '#97b6bd']
export function BarChart({ rows, x, y, formatter = number }: { rows: Row[]; x: string; y: string; formatter?: (n: number) => string }) {
  const valid = rows.filter(r => typeof r[y] === 'number' && Number.isFinite(r[y]))
  if (!valid.length) return <Empty title="没有可绘制的数据"/>
  const max = Math.max(1, ...valid.map(r => Math.abs(Number(r[y]))))
  return <ol className="bars">{valid.map((r, i) => <li key={i}><div><span className="rank">{String(i + 1).padStart(2, '0')}</span>
    <span className="category">{display(r[x]).replaceAll('_', ' ')}</span><strong>{formatter(Number(r[y]))}</strong></div>
    <div className="track"><i style={{ width: Math.abs(Number(r[y])) / max * 100 + '%', background: chartColors[Math.min(i, 5)] }}/></div></li>)}</ol>
}
function tick(value: number) {
  return new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(value)
}
export function Trend({ rows, x, y, unit }: { rows: Row[]; x: string; y: string; unit: string }) {
  const chart = useRef<HTMLDivElement>(null)
  const uid = useId().replace(/[^a-z0-9]/gi, '')
  const [width, setWidth] = useState(540)
  const [index, setIndex] = useState<number | null>(null)
  useEffect(() => {
    const target = chart.current
    if (!target) return
    const observer = new ResizeObserver(entries => setWidth(Math.max(160, Math.floor(entries[0].contentRect.width))))
    observer.observe(target)
    return () => observer.disconnect()
  }, [])
  const values = rows.map((r, i) => ({ x: String(r[x]), y: r[y], i }))
    .filter((p): p is { x: string; y: number; i: number } => typeof p.y === 'number' && Number.isFinite(p.y))
  if (values.length === 0) return <Empty title="当前指标没有数据"/>
  const bottom = 165, top = 16, left = 40, right = width - 14
  const topValue = Math.max(0, ...values.map(p => p.y))
  const lowValue = Math.min(0, ...values.map(p => p.y))
  const size = 10 ** Math.floor(Math.log10(Math.max(1, topValue - lowValue) / 3))
  const step = Math.ceil(Math.max(1, topValue - lowValue) / 3 / size) * size
  const min = Math.floor(lowValue / step) * step
  const max = Math.max(min + 3 * step, Math.ceil(topValue / step) * step)
  const ticks = Array.from({ length: Math.round((max - min) / step) + 1 }, (_, i) => min + i * step)
  const yPos = (n: number) => bottom - (n - min) / (max - min) * (bottom - top)
  const months = values.map(p => /^(\d{4})-(\d{2})/.exec(p.x))
  const axis = x === 'month' && months.every(m => m !== null)
    ? months.map(m => Number(m![1]) * 12 + Number(m![2])) : values.map(p => p.i)
  const first = Math.min(...axis), last = Math.max(...axis)
  const pos = values.map((p,i) => ({ ...p, px: first === last ? (right + left) / 2 : left + (axis[i] - first) / (last - first) * (right - left), py: yPos(p.y) }))
  const line = pos.map(p => p.px + ',' + p.py).join(' ')
  const active = index === null ? null : pos[Math.min(index, pos.length - 1)]
  const labels = Math.max(2, Math.floor((right - left) / 85))
  const markIndices = new Set(Array.from({length: Math.min(labels, pos.length)}, (_, i) => Math.round(i * (pos.length - 1) / Math.max(1, Math.min(labels, pos.length) - 1))))
  return <div className="trend" ref={chart}>
    <div className="axis-unit">{unit}</div>
    <svg viewBox={'0 0 ' + width + ' 196'} style={{ width: '100%', height: 196 }} role="img" tabIndex={0}
      aria-label={label(y) + '趋势，可用左右方向键查看每个值。'}
      onFocus={() => setIndex(0)} onBlur={() => setIndex(null)}
      onKeyDown={e => { if (['ArrowRight', 'ArrowLeft'].includes(e.key)) { e.preventDefault(); setIndex(n => Math.max(0, Math.min(pos.length - 1, (n ?? 0) + (e.key === 'ArrowRight' ? 1 : -1)))) } }}
      onPointerMove={e => { const at = e.clientX - e.currentTarget.getBoundingClientRect().left; setIndex(pos.reduce((best, p, i) => Math.abs(p.px - at) < Math.abs(pos[best].px - at) ? i : best, 0)) }}
      onPointerLeave={() => setIndex(null)}>
      <defs><linearGradient id={uid} x1="0" x2="0" y1="0" y2="1"><stop stopColor="#1584ed" stopOpacity=".22"/><stop offset="1" stopColor="#1584ed" stopOpacity=".015"/></linearGradient></defs>
      {ticks.map(v => <g key={v}><line x1={left} x2={right} y1={yPos(v)} y2={yPos(v)} stroke="#dddfe4" strokeDasharray="3 4"/><text x={left - 8} y={yPos(v) + 4} textAnchor="end">{tick(v)}</text></g>)}
      <polygon points={pos[0].px + ',' + bottom + ' ' + line + ' ' + pos[pos.length - 1].px + ',' + bottom} fill={'url(#' + uid + ')'}/>
      <polyline points={line} fill="none" stroke="#0071e3" strokeWidth="2.8" strokeLinejoin="round" strokeLinecap="round"/>
      {pos.filter((_,i) => markIndices.has(i)).map(p => <g key={p.i}><circle cx={p.px} cy={p.py} r="3.4" stroke="#0071e3" strokeWidth="2" fill="white"/><text x={p.px} y={188} textAnchor={p === pos[0] ? 'start' : p === pos[pos.length - 1] ? 'end' : 'middle'}>{p.x.slice(0, 7)}</text></g>)}
      {active && <g><line x1={active.px} x2={active.px} y1={top} y2={bottom} stroke="#579ce4" strokeDasharray="3 4"/><circle cx={active.px} cy={active.py} r="4.8" fill="#0071e3" stroke="white" strokeWidth="2"/></g>}
    </svg>
    {active && <div className="chart-tip" role="status">{active.x} · {number(active.y, unit === 'BRL' ? 2 : 0)} {unit}</div>}
  </div>
}
